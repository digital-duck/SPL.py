#!/usr/bin/env python3
"""
Iterative Research Agent using PocketFlow
Implements a WHILE-loop driven research workflow that searches the web
until sufficient information is gathered to answer a question.
"""

import os
import sys
import re
import logging
import yaml
import requests
from pocketflow import Node, Flow
from duckduckgo_search import DDGS

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("research_agent")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "google/gemini-3-flash-preview"
MAX_SEARCH_ROUNDS = 8          # safety cap — prevents infinite loops
MAX_SEARCH_RESULTS = 5         # DuckDuckGo results per query


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call the OpenRouter API and return the assistant's reply as a string."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Export it before running: export OPENROUTER_API_KEY=sk-..."
        )

    logger.debug("Calling LLM (model=%s) — prompt length=%d chars", model, len(prompt))

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
        timeout=90,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    logger.debug("LLM response length=%d chars", len(content))
    return content


# ---------------------------------------------------------------------------
# Web-search helper
# ---------------------------------------------------------------------------
def search_web(query: str) -> str:
    """Run a DuckDuckGo text search and return formatted results."""
    logger.info("🔍  Searching DuckDuckGo for: %s", query)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
        if not results:
            return f"[No results found for query: {query}]"
        formatted = "\n".join(
            f"- {r.get('title', 'No title')}: {r.get('body', 'No body')}"
            for r in results
        )
        logger.info("   → Retrieved %d results", len(results))
        return formatted
    except Exception as exc:  # noqa: BLE001
        logger.warning("DuckDuckGo search failed: %s", exc)
        return f"[Search error for query '{query}': {exc}]"


# ---------------------------------------------------------------------------
# YAML parser with block-scalar fallback (implicit EXCEPTION handler)
# ---------------------------------------------------------------------------
_KNOWN_KEYS = ("action", "search_query", "reasoning")


def _force_block_scalars(raw: str) -> str:
    """
    Rewrite known string values to use YAML block-scalar (|) notation so
    that embedded colons, newlines, and special characters don't break the
    parser.  This is the 'block-scalar fallback retry' required by the spec.
    """
    lines = raw.splitlines()
    patched: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        matched = False
        for key in _KNOWN_KEYS:
            # Match   key: some value   (plain scalar, not already block/flow)
            m = re.match(rf'^(\s*{re.escape(key)})\s*:\s*(.+)$', line)
            if m:
                indent = re.match(r'^(\s*)', line).group(1)
                value = m.group(2).strip()
                # Only rewrite if value is not already a YAML indicator
                if value and value[0] not in ("|", ">", "[", "{", '"', "'"):
                    patched.append(f"{indent}{key}: |\n{indent}  {value}")
                else:
                    patched.append(line)
                matched = True
                break
        if not matched:
            patched.append(line)
        i += 1
    return "\n".join(patched)


def parse_yaml_decision(raw: str) -> dict:
    """
    Parse the LLM's YAML decision output.
    Strategy:
      1. Strip markdown fences if present.
      2. Try direct yaml.safe_load.
      3. On failure, apply block-scalar rewrite and retry.
      4. On second failure, fall back to regex extraction.
      5. Guarantee a valid dict with at least {"action": "answer"}.
    """
    # Step 1: strip markdown code fences
    cleaned = re.sub(r"```(?:yaml)?\s*", "", raw, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace("```", "").strip()

    # Step 2: direct parse
    try:
        data = yaml.safe_load(cleaned)
        if isinstance(data, dict) and "action" in data:
            logger.debug("YAML parsed successfully on first attempt")
            return _normalise_decision(data)
    except yaml.YAMLError as exc:
        logger.debug("First YAML parse failed: %s", exc)

    # Step 3: block-scalar fallback retry
    patched = _force_block_scalars(cleaned)
    try:
        data = yaml.safe_load(patched)
        if isinstance(data, dict) and "action" in data:
            logger.debug("YAML parsed successfully after block-scalar rewrite")
            return _normalise_decision(data)
    except yaml.YAMLError as exc:
        logger.debug("Second YAML parse failed after block-scalar rewrite: %s", exc)

    # Step 4: regex extraction fallback
    logger.warning("Both YAML parse attempts failed — using regex fallback")
    action_match = re.search(r'\baction\s*[:\s]+(\w+)', raw, re.IGNORECASE)
    query_match = re.search(
        r'search_query\s*[:\s]+(.+?)(?:\n|$)', raw, re.IGNORECASE
    )
    action = action_match.group(1).strip().lower() if action_match else "answer"
    query = query_match.group(1).strip() if query_match else ""
    result = {"action": action}
    if query:
        result["search_query"] = query
    return _normalise_decision(result)


def _normalise_decision(data: dict) -> dict:
    """Normalise action values and strip block-scalar trailing newlines."""
    # Strip YAML block-scalar trailing whitespace from string values
    for key in list(data.keys()):
        if isinstance(data[key], str):
            data[key] = data[key].strip()

    action = str(data.get("action", "answer")).strip().lower()
    # Accept variants like "search_web", "do_search", etc.
    if "search" in action:
        data["action"] = "search"
    else:
        data["action"] = "answer"
    return data


# ---------------------------------------------------------------------------
# PocketFlow Nodes
# ---------------------------------------------------------------------------

class DecideActionNode(Node):
    """
    GENERATE node — calls the LLM with chain-of-thought reasoning to decide
    whether to search the web or synthesise a final answer.

    Returns action string "search" or "answer" from post() to route the flow.
    """

    def prep(self, shared: dict):
        return {
            "question": shared["question"],
            "context": shared.get("context", "No context accumulated yet."),
            "round": shared.get("search_round", 0),
            "model": shared.get("model", DEFAULT_MODEL),
        }

    def exec(self, prep_res: dict) -> dict:
        question = prep_res["question"]
        context = prep_res["context"]
        round_num = prep_res["round"]
        model = prep_res["model"]

        prompt = f"""You are a research agent deciding whether you have enough information to answer a question.

QUESTION: {question}

ACCUMULATED CONTEXT (from previous web searches):
{context}

SEARCH ROUND: {round_num} (maximum allowed: {MAX_SEARCH_ROUNDS})

INSTRUCTIONS:
- Carefully review the accumulated context above.
- If the context is insufficient to give a comprehensive, accurate answer, decide to search for more information.
- If you have enough information, decide to answer.
- If you have already done {MAX_SEARCH_ROUNDS} or more searches, you MUST decide to answer.
- When searching, provide a specific, targeted search query that will find the most useful information.
- Use chain-of-thought reasoning before deciding.

Respond with ONLY a YAML block (no markdown fences, no extra text):

reasoning: <your brief reasoning about whether you have enough information>
action: search
search_query: <specific search query to run>

OR

reasoning: <your brief reasoning about why you have enough information>
action: answer

YAML OUTPUT:"""

        logger.info("🤔  DecideAction (round %d) — calling LLM...", round_num)
        raw = call_llm(prompt, model=model)
        logger.debug("Raw LLM decision output:\n%s", raw)

        decision = parse_yaml_decision(raw)
        logger.info(
            "   → Decision: action=%s%s",
            decision["action"],
            f", query='{decision.get('search_query', '')}'"
            if decision["action"] == "search"
            else "",
        )
        return decision

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        shared["decision"] = exec_res
        action = exec_res.get("action", "answer")

        # Safety cap: force answer after MAX_SEARCH_ROUNDS
        if shared.get("search_round", 0) >= MAX_SEARCH_ROUNDS:
            logger.warning(
                "⚠️  Reached maximum search rounds (%d) — forcing answer",
                MAX_SEARCH_ROUNDS,
            )
            shared["decision"]["action"] = "answer"
            return "answer"

        return action  # "search" or "answer"


class SearchWebNode(Node):
    """
    CALL side-effect node — executes a DuckDuckGo search and appends
    results to the shared @context variable, then loops back to DecideAction.
    """

    def prep(self, shared: dict):
        decision = shared.get("decision", {})
        query = decision.get("search_query", shared.get("question", ""))
        return {
            "query": query,
            "current_context": shared.get("context", ""),
            "round": shared.get("search_round", 0),
        }

    def exec(self, prep_res: dict) -> str:
        query = prep_res["query"]
        if not query:
            logger.warning("Empty search query — skipping search")
            return ""
        return search_web(query)

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        round_num = prep_res["round"] + 1
        shared["search_round"] = round_num

        query = prep_res["query"]
        new_results = exec_res.strip()

        if new_results:
            separator = f"\n\n--- Search Round {round_num}: '{query}' ---\n"
            shared["context"] = shared.get("context", "") + separator + new_results
            logger.info("   → Context updated (total length: %d chars)", len(shared["context"]))
        else:
            logger.warning("   → No results appended (empty search output)")

        # Unconditional: loop back to DecideAction
        return "default"


class AnswerQuestionNode(Node):
    """
    GENERATE node — synthesises accumulated research context into a
    comprehensive final answer.  Terminates the workflow.
    """

    def prep(self, shared: dict):
        return {
            "question": shared["question"],
            "context": shared.get("context", "No context available."),
            "model": shared.get("model", DEFAULT_MODEL),
            "rounds": shared.get("search_round", 0),
        }

    def exec(self, prep_res: dict) -> str:
        question = prep_res["question"]
        context = prep_res["context"]
        model = prep_res["model"]
        rounds = prep_res["rounds"]

        prompt = f"""You are a research assistant. Using the web search results below, provide a comprehensive, well-structured answer to the question.

QUESTION: {question}

WEB SEARCH RESULTS (accumulated over {rounds} search round(s)):
{context}

INSTRUCTIONS:
- Synthesise the information from the search results into a clear, accurate, comprehensive answer.
- Organise your answer with appropriate structure (paragraphs, bullet points if helpful).
- Cite key facts from the search results where relevant.
- If the search results are insufficient, acknowledge the limitations while providing the best possible answer.
- Be thorough but concise.

FINAL ANSWER:"""

        logger.info("✍️   AnswerQuestion — synthesising final answer...")
        answer = call_llm(prompt, model=model)
        logger.info("   → Answer generated (%d chars)", len(answer))
        return answer

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        shared["answer"] = exec_res
        shared["status"] = "done"
        shared["search_rounds_used"] = prep_res["rounds"]

        # No successor registered for "done" — flow terminates
        return "done"


# ---------------------------------------------------------------------------
# Flow construction
# ---------------------------------------------------------------------------

def build_research_flow() -> Flow:
    """
    Wire the three nodes into the research agent flow:

        DecideAction --"search"--> SearchWeb --> DecideAction  (WHILE loop)
        DecideAction --"answer"--> AnswerQuestion              (exit loop)
    """
    decide = DecideActionNode()
    search = SearchWebNode()
    answer = AnswerQuestionNode()

    # Conditional edges from DecideAction
    decide - "search" >> search   # WHILE condition: keep searching
    decide - "answer" >> answer   # EXIT condition: synthesise answer

    # Back-edge: SearchWeb always returns to DecideAction (implements WHILE)
    search >> decide

    # AnswerQuestion has no outgoing edge — flow terminates after "done"

    return Flow(start=decide)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_research_agent(
    question: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Run the iterative research agent for the given question.

    Returns a dict with keys:
        answer       — the final synthesised answer (str)
        status       — "done" on success
        context      — accumulated search results
        search_rounds_used — number of search rounds performed
    """
    shared = {
        "question": question,
        "context": "",
        "search_round": 0,
        "model": model,
        "answer": None,
        "status": "pending",
    }

    logger.info("=" * 60)
    logger.info("🚀  Starting Research Agent")
    logger.info("   Question : %s", question)
    logger.info("   Model    : %s", model)
    logger.info("=" * 60)

    flow = build_research_flow()
    flow.run(shared)

    logger.info("=" * 60)
    logger.info("✅  Research complete — status=%s, rounds=%d",
                shared.get("status"), shared.get("search_rounds_used",