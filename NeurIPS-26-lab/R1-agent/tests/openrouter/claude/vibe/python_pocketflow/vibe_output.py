#!/usr/bin/env python3
"""
Research Agent — PocketFlow implementation
Autonomously searches the web and synthesises a comprehensive answer.
"""

import os
import re
import sys
import yaml
import logging
from typing import Any, Optional
from duckduckgo_search import DDGS
from openai import OpenAI

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("research_agent")

# ── LLM helper ───────────────────────────────────────────────────────────────
_LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
_OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

def call_llm(prompt: str, model: str = None) -> str:
    """Call an OpenAI-compatible LLM and return the response text."""
    api_key = _OPENAI_API_KEY or _OPENROUTER_API_KEY
    if not api_key:
        raise EnvironmentError(
            "Set OPENAI_API_KEY or OPENROUTER_API_KEY before running."
        )
    base_url = _OPENAI_BASE_URL
    if _OPENROUTER_API_KEY and not _OPENAI_API_KEY:
        base_url = "https://openrouter.ai/api/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)
    chosen_model = model or _LLM_MODEL
    logger.debug("LLM call | model=%s | prompt_len=%d", chosen_model, len(prompt))
    response = client.chat.completions.create(
        model=chosen_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# ── YAML repair helper ────────────────────────────────────────────────────────
def _repair_yaml(raw: str) -> dict:
    """
    Attempt to parse YAML from an LLM response.
    Handles fenced code blocks and attempts block-scalar repair on failure.
    Raises ValueError (wrapping the original ParseError) if all attempts fail.
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"^```(?:yaml)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return yaml.safe_load(cleaned)
    except yaml.YAMLError as original_exc:
        logger.warning("YAML parse failed — attempting block-scalar repair: %s", original_exc)

    # Block-scalar repair: replace bare multiline values with literal blocks
    repaired_lines = []
    for line in cleaned.splitlines():
        # If a value contains a colon that isn't already quoted/blocked, quote it
        if re.match(r"^\s*\w+:\s+.+:.+", line):
            key, _, rest = line.partition(":")
            repaired_lines.append(f'{key}: "{rest.strip().replace(chr(34), chr(39))}"')
        else:
            repaired_lines.append(line)
    repaired = "\n".join(repaired_lines)

    try:
        return yaml.safe_load(repaired)
    except yaml.YAMLError as repair_exc:
        raise ValueError(
            f"YAML parse error (original + repair both failed).\n"
            f"Original error: {original_exc}\n"
            f"Repair error: {repair_exc}\n"
            f"Raw text:\n{raw}"
        ) from repair_exc


# ── PocketFlow base ───────────────────────────────────────────────────────────
class Node:
    """Minimal PocketFlow-style node."""

    def __init__(self, name: str):
        self.name = name
        self._successors: dict[str, "Node"] = {}

    def add_successor(self, node: "Node", action: str = "default") -> "Node":
        self._successors[action] = node
        return node

    def prep(self, shared: dict) -> Any:
        return None

    def exec(self, prep_result: Any) -> Any:
        return None

    def post(self, shared: dict, prep_result: Any, exec_result: Any) -> str:
        return "default"

    def run(self, shared: dict) -> str:
        prep_result = self.prep(shared)
        exec_result = self.exec(prep_result)
        action = self.post(shared, prep_result, exec_result)
        return action

    def get_successor(self, action: str) -> Optional["Node"]:
        return self._successors.get(action) or self._successors.get("default")


class Flow:
    """Minimal PocketFlow-style flow runner."""

    def __init__(self, start: Node):
        self.start = start

    def run(self, shared: dict) -> dict:
        current = self.start
        while current is not None:
            logger.info("▶ Node: %s", current.name)
            action = current.run(shared)
            logger.info("  ↳ action=%s", action)
            current = current.get_successor(action)
        return shared


# ── Nodes ─────────────────────────────────────────────────────────────────────

class DecideActionNode(Node):
    """
    Calls the LLM with the current question + accumulated context.
    Parses YAML response to determine next action: 'search' or 'answer'.
    """

    DECIDE_PROMPT = """\
You are a research agent. Your job is to answer the user's question by searching the web.

Question: {question}

Accumulated research context so far:
{context}

Decide what to do next. Respond ONLY with valid YAML in exactly this format:

thinking: |
  <your step-by-step reasoning about what you know and what you still need>
action: search   # or: answer
reason: <one sentence explaining your choice>
search_query: <search query string>   # include ONLY if action is search
answer: |
  <comprehensive answer>              # include ONLY if action is answer

Rules:
- If you need more information, set action to 'search' and provide a specific search_query.
- If you have enough information to give a thorough answer, set action to 'answer'.
- Never include both search_query and answer in the same response.
- Do NOT wrap your response in markdown fences.
"""

    def prep(self, shared: dict) -> str:
        question = shared.get("question", "")
        context = shared.get("context", "(none yet)")
        return self.DECIDE_PROMPT.format(question=question, context=context)

    def exec(self, prompt: str) -> dict:
        raw = call_llm(prompt)
        logger.debug("DecideAction raw LLM output:\n%s", raw)
        parsed = _repair_yaml(raw)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected a YAML mapping, got: {type(parsed)}")
        if "action" not in parsed:
            raise ValueError(f"YAML response missing 'action' key: {parsed}")
        return parsed

    def post(self, shared: dict, prep_result: Any, exec_result: dict) -> str:
        action = exec_result.get("action", "").strip().lower()
        shared["_decision"] = exec_result
        logger.info(
            "  Decision: action=%s | reason=%s",
            action,
            exec_result.get("reason", ""),
        )

        if action == "search":
            shared["search_query"] = exec_result.get("search_query", "")
            return "search"
        elif action == "answer":
            shared["answer"] = exec_result.get("answer", "")
            return "answer"
        else:
            logger.warning("Unknown action '%s' — defaulting to search", action)
            shared["search_query"] = exec_result.get("search_query", shared.get("question", ""))
            return "search"


class SearchWebNode(Node):
    """
    Performs a DuckDuckGo web search using the current search_query.
    Appends results to shared context with SEARCH/RESULTS delimiter convention.
    """

    MAX_RESULTS = 5

    def prep(self, shared: dict) -> str:
        return shared.get("search_query", "")

    def exec(self, query: str) -> str:
        if not query:
            return "(empty query — no results)"
        logger.info("  🔍 Searching: %s", query)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.MAX_RESULTS))
        except Exception as exc:
            logger.error("DuckDuckGo search failed: %s", exc)
            return f"(search failed: {exc})"

        if not results:
            return "(no results found)"

        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "")
            href = r.get("href", "")
            lines.append(f"[{i}] {title}\n    URL: {href}\n    {body}")
        return "\n\n".join(lines)

    def post(self, shared: dict, prep_result: str, exec_result: str) -> str:
        query = prep_result
        results_text = exec_result
        delimiter_block = (
            f"\n---\nSEARCH: {query}\nRESULTS:\n{results_text}\n---\n"
        )
        existing = shared.get("context", "")
        shared["context"] = existing + delimiter_block
        logger.info("  Context updated (total length: %d chars)", len(shared["context"]))
        return "decide"  # loop back to DecideAction


class AnswerQuestionNode(Node):
    """
    Generates a final comprehensive answer from accumulated context.
    Optionally writes the answer to a file.
    """

    ANSWER_PROMPT = """\
You are a research assistant. Using the research context below, write a comprehensive,
well-structured answer to the user's question. Cite sources where possible.

Question: {question}

Research Context:
{context}

Preliminary answer draft (refine and expand this):
{draft_answer}

Write a final, polished, thorough answer now:
"""

    def prep(self, shared: dict) -> dict:
        return {
            "question": shared.get("question", ""),
            "context": shared.get("context", ""),
            "draft_answer": shared.get("answer", ""),
        }

    def exec(self, prep_result: dict) -> str:
        prompt = self.ANSWER_PROMPT.format(**prep_result)
        return call_llm(prompt)

    def post(self, shared: dict, prep_result: Any, exec_result: str) -> str:
        shared["answer"] = exec_result
        shared["status"] = "done"
        logger.info("  ✅ Final answer generated (%d chars)", len(exec_result))

        output_file = shared.get("output_file")
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as fh:
                    fh.write(f"Question: {shared['question']}\n\n")
                    fh.write("=" * 60 + "\n\n")
                    fh.write(exec_result)
                    fh.write("\n")
                logger.info("  📄 Answer written to: %s", output_file)
            except OSError as exc:
                logger.error("Failed to write answer to file: %s", exc)

        return "done"


# ── Flow builder ──────────────────────────────────────────────────────────────

def build_research_flow() -> Flow:
    """Wire up the research agent graph and return a runnable Flow."""

    decide = DecideActionNode("DecideAction")
    search = SearchWebNode("SearchWeb")
    answer = AnswerQuestionNode("AnswerQuestion")

    # DecideAction → search → SearchWeb → decide → DecideAction (loop)
    decide.add_successor(search, "search")
    search.add_successor(decide, "decide")

    # DecideAction → answer → AnswerQuestion → done (exit)
    decide.add_successor(answer, "answer")

    return Flow(start=decide)


# ── Public entry point ────────────────────────────────────────────────────────

def run_research_agent(
    question: str,
    output_file: Optional[str] = None,
    max_iterations: int = 10,
) -> str:
    """
    Run the research agent for the given question.

    Args:
        question:      The research question to answer.
        output_file:   Optional path to write the final answer to.
        max_iterations: Safety cap on search iterations (not a hard PocketFlow
                        limit — enforced via a wrapper loop guard).

    Returns:
        The final answer string.
    """
    shared: dict = {
        "question": question,
        "context": "",
        "search_query": "",
        "answer": "",
        "status": "",
        "output_file": output_file,
        "_iteration": 0,
    }

    # We wrap the flow in a guard to prevent runaway loops.
    # The flow itself loops via node successors; we intercept by patching
    # SearchWebNode.post to count iterations.
    original_search_post = SearchWebNode.post

    def guarded_search_post(self, shared, prep_result, exec_result):
        shared["_iteration"] += 1
        if shared["_iteration"] >= max_iterations:
            logger.warning(
                "Max iterations (%d) reached — forcing answer action.", max_iterations
            )
            # Force the next DecideAction to answer by injecting a note
            shared["context"] += (
                "\n---\n[SYSTEM NOTE: Maximum search iterations reached. "
                "Synthesise an answer from the information gathered so far.]\n---\n"
            )
        return original_search_post(self, shared, prep_result, exec_result)

    SearchWebNode.post = guarded_search_post

    try:
        flow = build_research_flow()
        flow.run(shared)
    finally:
        SearchWebNode.post = original_search_post  # restore

    return shared.get("answer", "(no answer generated)")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Research Agent — autonomously searches the web to answer questions."
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="What are the main differences between transformer and mamba architectures for sequence modelling?",
        help="The research question to answer.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional file path to write the final answer to.",
    )
    parser.add_argument(
        "--max-iterations",
        "-m",
        type=int,
        default=6,
        help="Maximum number of web searches before forcing an answer (default: 6).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print(f