#!/usr/bin/env python3
"""
A1-agent-claude_cli-vibe.py
Ablation: one-shot vibe-coded implementation of the R1-agent workflow.
Generated directly from S1 spec Sections 0–1, without SPL IR steps.

Adapter: claude_cli  (subprocess: claude -p <prompt>)
"""

import re
import subprocess
import sys

import yaml
from pocketflow import Flow, Node

# ---------------------------------------------------------------------------
# LLM helper — claude_cli adapter
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# search_web — CALL side-effect via DuckDuckGo
# ---------------------------------------------------------------------------

def search_web(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No results found for: {query}"
        return "\n".join(
            f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
            for r in results
        )
    except Exception as exc:
        return f"Search error: {exc}"


# ---------------------------------------------------------------------------
# YAML parser with block-scalar fallback
# Forces `|` block-scalar on known multi-line keys before retrying parse.
# Acts as implicit EXCEPTION handler for malformed LLM YAML output.
# ---------------------------------------------------------------------------

_KNOWN_KEYS = ("action", "search_query", "answer", "reasoning")

def _force_block_scalars(raw: str) -> str:
    """Rewrite inline values on known keys to block-scalar `|` notation."""
    lines = raw.splitlines()
    out = []
    for line in lines:
        for key in _KNOWN_KEYS:
            pattern = rf'^(\s*{key}\s*:\s*)(.+)$'
            m = re.match(pattern, line)
            if m and not m.group(2).strip().startswith("|"):
                line = f"{m.group(1)}|\n  {m.group(2).strip()}"
                break
        out.append(line)
    return "\n".join(out)


def parse_yaml_safe(raw: str) -> dict:
    """Try parse; if it fails, apply block-scalar fixup and retry once."""
    # strip fences if present
    text = re.sub(r"^```(?:yaml)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    # fallback: force block scalars and retry
    fixed = _force_block_scalars(text)
    try:
        data = yaml.safe_load(fixed)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    return {"parse_error": raw[:200], "action": "answer"}


# ---------------------------------------------------------------------------
# Prompt templates — CREATE FUNCTION equivalents
# ---------------------------------------------------------------------------

DECIDE_ACTION_PROMPT = """\
You are a research agent. Evaluate the question and accumulated context, then decide the next action.

Question: {question}

Accumulated context:
{context}

Respond with a YAML block using these fields:
  action: search        (if you need more information)
  search_query: <query> (required when action is search)
or:
  action: answer        (if you have enough information to answer)

Use block-scalar `|` for multi-line values. Output YAML only — no prose, no fences."""

ANSWER_QUESTION_PROMPT = """\
You are a research assistant. Using only the information in the context below, write a comprehensive answer to the question.

Question: {question}

Context:
{context}

Provide a clear, well-structured answer."""


# ---------------------------------------------------------------------------
# PocketFlow nodes
# ---------------------------------------------------------------------------

class DecideActionNode(Node):
    """GENERATE decide_action(@question, @context) INTO @decision"""

    def prep(self, shared: dict):
        return shared["question"], shared["context"]

    def exec(self, args):
        question, context = args
        raw = call_llm(DECIDE_ACTION_PROMPT.format(question=question, context=context))
        return parse_yaml_safe(raw)

    def post(self, shared: dict, prep_res, exec_res: dict) -> str:
        shared["decision"] = exec_res
        action = exec_res.get("action", "").strip().lower()
        if "search" in action:
            return "search"
        return "answer"


class SearchWebNode(Node):
    """CALL search_web(@decision.search_query) → append to @context"""

    def prep(self, shared: dict):
        return shared["decision"].get("search_query", shared["question"])

    def exec(self, query: str) -> str:
        return search_web(query)

    def post(self, shared: dict, prep_res, exec_res: str) -> str:
        query = prep_res
        shared["context"] += f"\n\nSEARCH: {query}\nRESULTS:\n{exec_res}"
        return "decide"   # loop back


class AnswerQuestionNode(Node):
    """GENERATE answer_question(@question, @context) INTO @answer"""

    def prep(self, shared: dict):
        return shared["question"], shared["context"]

    def exec(self, args) -> str:
        question, context = args
        return call_llm(ANSWER_QUESTION_PROMPT.format(question=question, context=context))

    def post(self, shared: dict, prep_res, exec_res: str) -> str:
        shared["answer"] = exec_res
        shared["status"] = "done"
        return "done"   # terminal — no successor → flow ends


# ---------------------------------------------------------------------------
# Flow assembly
# ---------------------------------------------------------------------------

def build_flow() -> Flow:
    decide = DecideActionNode()
    search = SearchWebNode()
    answer = AnswerQuestionNode()

    decide - "search" >> search
    decide - "answer" >> answer
    search - "decide" >> decide   # WHILE loop back-edge

    return Flow(start=decide)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(question: str) -> dict:
    shared = {
        "question": question,
        "context": "No previous search.",
        "decision": {},
        "answer": "",
        "status": "",
    }
    build_flow().run(shared)
    return {"answer": shared["answer"], "status": shared["status"]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is PocketFlow and how do I install it?"
    result = run_agent(q)
    print(f"\nStatus: {result['status']}\n")
    print(f"Answer:\n{result['answer']}")
