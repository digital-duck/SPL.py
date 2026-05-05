#!/usr/bin/env python3
"""
Iterative Research Agent using PocketFlow
Implements a WHILE-loop driven research workflow with DuckDuckGo search
and OpenRouter LLM calls.
"""

import os
import sys
import re
import logging
import yaml
import requests
from typing import Any

from pocketflow import Node, Flow

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("research_agent")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "google/gemini-3-flash-preview"
MAX_ITERATIONS = 3  # safety cap on the WHILE loop


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Call OpenRouter-compatible LLM API.
    Reads OPENROUTER_API_KEY from environment.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")

    log.debug("Calling LLM (model=%s), prompt length=%d chars", model, len(prompt))

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/research-agent",
            "X-Title": "PocketFlow Research Agent",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    log.debug("LLM response length=%d chars", len(content))
    return content


# ---------------------------------------------------------------------------
# Web search helper
# ---------------------------------------------------------------------------
def search_web(query: str, max_results: int = 5) -> str:
    """
    Perform a DuckDuckGo text search and return formatted results.
    """
    from duckduckgo_search import DDGS

    log.info("Searching web: %r", query)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return f"[No results found for query: {query}]"
        formatted = "\n".join(
            f"- {r.get('title', 'No title')}: {r.get('body', '')}"
            for r in results
        )
        log.info("Found %d search results", len(results))
        return formatted
    except Exception as exc:
        log.warning("Search failed: %s", exc)
        return f"[Search error: {exc}]"


# ---------------------------------------------------------------------------
# YAML parser with block-scalar fallback (EXCEPTION handler for malformed output)
# ---------------------------------------------------------------------------
_BLOCK_SCALAR_KEYS = {"action", "search_query", "answer"}


def _apply_block_scalar_fallback(raw: str) -> str:
    """
    Force block-scalar (|) notation on known keys whose values span
    multiple lines or contain special characters, then retry the parse.
    This is the implicit exception handler for malformed LLM YAML output.
    """
    lines = raw.splitlines()
    fixed_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect "key: value" where value might be problematic
        match = re.match(r'^(\s*)(\w+):\s+(.+)$', line)
        if match:
            indent, key, value = match.group(1), match.group(2), match.group(3)
            if key in _BLOCK_SCALAR_KEYS and (
                ':' in value or '"' in value or "'" in value or len(value) > 80
            ):
                # Rewrite as block scalar
                fixed_lines.append(f"{indent}{key}: |")
                fixed_lines.append(f"{indent}  {value}")
                i += 1
                continue
        fixed_lines.append(line)
        i += 1
    return "\n".join(fixed_lines)


def parse_yaml_decision(raw: str) -> dict[str, Any]:
    """
    Parse the LLM decision YAML with a block-scalar fallback retry.
    Extracts YAML from markdown code fences if present.
    """
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:yaml)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # Attempt 1: direct parse
    try:
        result = yaml.safe_load(cleaned)
        if isinstance(result, dict):
            log.debug("YAML parsed successfully on first attempt")
            return result
    except yaml.YAMLError as exc:
        log.debug("First YAML parse failed: %s — trying block-scalar fallback", exc)

    # Attempt 2: block-scalar fallback
    fallback = _apply_block_scalar_fallback(cleaned)
    try:
        result = yaml.safe_load(fallback)
        if isinstance(result, dict):
            log.debug("YAML parsed successfully with block-scalar fallback")
            return result
    except yaml.YAMLError as exc:
        log.warning("Block-scalar fallback also failed: %s", exc)

    # Attempt 3: regex extraction of known keys
    log.warning("Falling back to regex extraction from raw LLM output")
    action_match = re.search(r'\baction\s*:\s*(\w+)', raw, re.IGNORECASE)
    query_match = re.search(r'search_query\s*:\s*(.+)', raw, re.IGNORECASE)
    answer_match = re.search(r'answer\s*:\s*(.+)', raw, re.IGNORECASE | re.DOTALL)

    action = action_match.group(1).strip().lower() if action_match else "answer"
    result: dict[str, Any] = {"action": action}
    if query_match:
        result["search_query"] = query_match.group(1).strip().strip('"\'')
    if answer_match:
        result["answer"] = answer_match.group(1).strip().strip('"\'')

    log.debug("Regex extraction result: %s", result)
    return result


# ---------------------------------------------------------------------------
# PocketFlow Nodes
# ---------------------------------------------------------------------------

class DecideActionNode(Node):
    """
    WHILE-loop driver node.
    Uses chain-of-thought reasoning to decide: search or answer.
    Returns action string "search" or "answer" to route the flow.
    """

    def prep(self, shared: dict) -> tuple[str, str, int]:
        question = shared.get("question", "")
        context = shared.get("context", "No context accumulated yet.")
        iteration = shared.get("iteration", 0)
        return question, context, iteration

    def exec(self, prep_res: tuple[str, str, int]) -> dict[str, Any]:
        question, context, iteration = prep_res
        model = os.getenv("RESEARCH_MODEL", DEFAULT_MODEL)

        prompt = f"""You are a research agent deciding the next action to answer a question.

QUESTION: {question}

ACCUMULATED CONTEXT:
{context}

ITERATION: {iteration + 1} of {MAX_ITERATIONS}

Think step-by-step:
1. Review the question and accumulated context carefully.
2. Determine if you have enough information to give a comprehensive, accurate answer.
3. If you need more information, identify the most useful search query.
4. If you have sufficient information (or reached the iteration limit), prepare to answer.

Respond ONLY with valid YAML in this exact format:

If you need to search:
```yaml
action: search
search_query: your specific search query here
reasoning: brief explanation of why this search is needed
```

If you have enough information to answer:
```yaml
action: answer
reasoning: brief explanation of why you have enough information
```

Important: Choose "answer" if context is sufficient OR if iteration >= {MAX_ITERATIONS - 1}.
"""
        log.info("DecideActionNode: calling LLM for decision (iteration=%d)", iteration + 1)
        raw = call_llm(prompt, model=model)
        log.debug("Raw decision output:\n%s", raw)
        decision = parse_yaml_decision(raw)
        log.info("Decision: action=%r", decision.get("action"))
        return decision

    def post(self, shared: dict, prep_res: tuple, exec_res: dict[str, Any]) -> str:
        _, _, iteration = prep_res
        shared["decision"] = exec_res
        shared["iteration"] = iteration + 1

        action = exec_res.get("action", "answer").strip().lower()

        # Safety cap: force answer after MAX_ITERATIONS
        if iteration >= MAX_ITERATIONS:
            log.warning("Maximum iterations (%d) reached — forcing answer", MAX_ITERATIONS)
            action = "answer"

        if action == "search":
            query = exec_res.get("search_query", "")
            if not query:
                log.warning("action=search but no search_query found — forcing answer")
                action = "answer"
            else:
                shared["current_query"] = query

        log.info("Routing to action: %r", action)
        return action  # "search" or "answer"


class SearchWebNode(Node):
    """
    CALL side-effect node.
    Invokes DuckDuckGo and appends results to shared @context.
    """

    def prep(self, shared: dict) -> str:
        return shared.get("current_query", "")

    def exec(self, query: str) -> str:
        if not query:
            return "[No query provided]"
        return search_web(query)

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        query = prep_res
        results = exec_res
        iteration = shared.get("iteration", 1)

        # Append to accumulated context
        separator = "\n\n" if shared.get("context", "No context accumulated yet.") != "No context accumulated yet." else ""
        existing = shared.get("context", "")
        if existing == "No context accumulated yet.":
            existing = ""

        new_entry = f"[Search {iteration}: {query!r}]\n{results}"
        shared["context"] = (existing + separator + new_entry).strip()

        log.info("Context updated — total length=%d chars", len(shared["context"]))

        # Loop back to DecideActionNode (implements the WHILE back-edge)
        return "default"


class AnswerQuestionNode(Node):
    """
    GENERATE node — synthesizes accumulated research into a final answer.
    Terminates the workflow with status="done".
    """

    def prep(self, shared: dict) -> tuple[str, str]:
        question = shared.get("question", "")
        context = shared.get("context", "No context accumulated.")
        return question, context

    def exec(self, prep_res: tuple[str, str]) -> str:
        question, context = prep_res
        model = os.getenv("RESEARCH_MODEL", DEFAULT_MODEL)

        prompt = f"""You are a knowledgeable research assistant. Based on the research context below,
provide a comprehensive, accurate, and well-structured answer to the question.

QUESTION: {question}

RESEARCH CONTEXT:
{context}

Instructions:
- Synthesize all relevant information from the context.
- Provide a clear, detailed, and well-organized answer.
- Cite specific facts from the research context where appropriate.
- If the context is insufficient, acknowledge limitations while answering as best you can.
- Write in a professional, informative tone.

ANSWER:"""

        log.info("AnswerQuestionNode: generating final answer")
        answer = call_llm(prompt, model=model)
        log.info("Final answer generated (%d chars)", len(answer))
        return answer

    def post(self, shared: dict, prep_res: tuple, exec_res: str) -> str:
        shared["answer"] = exec_res
        shared["status"] = "done"
        log.info("Workflow complete — status=done")
        return "done"


# ---------------------------------------------------------------------------
# Flow construction
# ---------------------------------------------------------------------------

def build_research_flow() -> tuple[Flow, dict]:
    """
    Wire the PocketFlow graph and return (flow, initial_shared_template).

    Graph topology:
        DecideActionNode --"search"--> SearchWebNode --"default"--> DecideActionNode
        DecideActionNode --"answer"--> AnswerQuestionNode
    """
    decide = DecideActionNode()
    search = SearchWebNode()
    answer = AnswerQuestionNode()

    # Conditional edges from DecideActionNode
    decide - "search" >> search   # WHILE loop body
    decide - "answer" >> answer   # exit loop

    # Back-edge: SearchWebNode loops back to DecideActionNode (implements WHILE)
    search >> decide

    # AnswerQuestionNode is a terminal node (no outgoing edges)

    flow = Flow(start=decide)
    return flow


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_research_agent(question: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """
    Run the iterative research agent for a given question.
    Returns the shared state dict with 'answer' and 'status' keys.
    """
    if model != DEFAULT_MODEL:
        os.environ["RESEARCH_MODEL"] = model

    shared: dict[str, Any] = {
        "question": question,
        "context": "No context accumulated yet.",
        "iteration": 0,
        "status": "running",
        "answer": None,
        "decision": None,
        "current_query": None,
    }

    log.info("=" * 60)
    log.info("Research Agent starting")
    log.info("Question: %s", question)
    log.info("Model: %s", os.getenv("RESEARCH_MODEL", DEFAULT_MODEL))
    log.info("=" * 60)

    flow = build_research_flow()
    flow.run(shared)

    return {
        "answer": shared.get("answer", ""),
        "status": shared.get("status", "unknown"),
        "iterations": shared.get("iteration", 0),
        "context_length": len(shared.get("context", "")),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Iterative Research Agent — PocketFlow implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python A1-agent-openrouter-claude-vibe.py "What are the latest developments in quantum computing?"
  python A1-agent-openrouter-claude-vibe.py "Who won the 2024 Nobel Prize in Physics?" --model google/gemini-flash-1.5
  python A1-agent-openrouter-claude-vibe.py "Explain the current state of fusion energy research" --max-iterations 5
        """,
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="What are the most recent breakthroughs in artificial intelligence?",
        help="The research question to answer (default: AI breakthroughs)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenRouter model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Maximum search iterations (default: {MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Override MAX_ITERATIONS if provided
    if args.max_iterations:
        MAX_ITERATIONS = args.max_iterations

    result = run_research_agent(args.question, model=args.model)

    print("\n" + "=" * 60)
    print("FINAL RESEARCH REPORT")
    print("=" * 60)
    print(f"Question: {args.question}")
    print("-" * 60)
    print(result["answer"])
    print("=" * 60)
    print(f"Status:         {result['status']}")
    print(f"Iterations:     {result['iterations']}")
    print(f"Context Length: {result['context_length']} chars")
    print("=" * 60)