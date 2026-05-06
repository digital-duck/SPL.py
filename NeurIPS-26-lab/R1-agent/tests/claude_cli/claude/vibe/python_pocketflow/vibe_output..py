#!/usr/bin/env python3
"""
Research Agent — PocketFlow implementation.

Graph topology:
  DecideAction ─"search"→ SearchWeb ─"decide"→ DecideAction   (loop)
               ─"answer"→ AnswerQuestion                        (terminal)
"""

import os
import re
import sys
import yaml

import openai
from duckduckgo_search import DDGS
from pocketflow import Node, Flow

# ── Configuration ─────────────────────────────────────────────────────────────
LLM_MODEL          = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
MAX_ITERATIONS     = int(os.getenv("MAX_ITERATIONS", "8"))

# ── LLM helper ────────────────────────────────────────────────────────────────
def call_llm(prompt: str, model: str = None) -> str:
    model = model or LLM_MODEL
    if OPENROUTER_API_KEY:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    else:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


# ── DuckDuckGo search tool ────────────────────────────────────────────────────
def search_web_duckduckgo(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search error: {exc}"
    if not hits:
        return "No results found."
    return "\n\n".join(
        f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}"
        for r in hits
    )


# ── YAML parsing with block-scalar fallback ───────────────────────────────────
_MULTILINE_KEYS = {"thinking", "reason", "answer"}
_KEY_RE = re.compile(r"^(\s*)(" + "|".join(_MULTILINE_KEYS) + r"):\s+(.+)$")


def _fix_block_scalars(yaml_str: str) -> str:
    """Rewrite `key: inline-value` → `key: |\n  value` for known multi-line keys."""
    out = []
    for line in yaml_str.splitlines():
        m = _KEY_RE.match(line)
        if m:
            indent, key, value = m.group(1), m.group(2), m.group(3)
            out.append(f"{indent}{key}: |")
            out.append(f"{indent}  {value}")
        else:
            out.append(line)
    return "\n".join(out)


def parse_yaml_safely(raw: str) -> dict:
    """Extract YAML from a fenced block; retry with block-scalar fixup on parse error."""
    fence = re.search(r"```(?:yaml)?\s*\n(.*?)```", raw, re.DOTALL)
    yaml_str = fence.group(1).strip() if fence else raw.strip()

    try:
        result = yaml.safe_load(yaml_str)
        if isinstance(result, dict):
            return result
    except yaml.YAMLError:
        pass

    fixed = _fix_block_scalars(yaml_str)
    try:
        result = yaml.safe_load(fixed)
        if isinstance(result, dict):
            return result
        raise ValueError(f"YAML parsed to {type(result).__name__}, expected dict")
    except yaml.YAMLError as exc:
        raise ValueError(
            f"YAML parse failed after block-scalar fixup: {exc}\n\nRaw:\n{yaml_str}"
        )


# ── Prompts ───────────────────────────────────────────────────────────────────
_DECIDE_PROMPT = """\
You are a research agent. Answer a research question by iteratively searching the web.

### CONTEXT
Question: {question}

Previous research:
{context}

### ACTION SPACE
Choose exactly one action and respond with ONLY the fenced YAML block below.

**search** — retrieve more information (use when context is insufficient)
**answer** — synthesize a final answer (use when you have enough information)

```yaml
thinking: |
  <chain-of-thought about what you know and what is still missing>
action: search
reason: |
  <why this action is appropriate right now>
search_query: <concise single-line search string>
answer: |
  <leave empty when action is search>
```

Rules:
- `thinking`, `reason`, `answer` MUST use `|` block-scalar notation.
- `action` must be exactly the word `search` or `answer`.
- `search_query` is a plain single-line string; only populate it when action is `search`.
"""

_ANSWER_PROMPT = """\
You are a research agent. Write a comprehensive, well-organized answer using the research below.

### CONTEXT
Question: {question}

Accumulated research:
{context}

## YOUR ANSWER:
"""


# ── Nodes ─────────────────────────────────────────────────────────────────────

class DecideAction(Node):
    """
    Reasoning core.  GENERATEs a structured YAML decision:
    `action: search` (loop continues) or `action: answer` (loop exits).
    """

    def prep(self, shared: dict):
        return {
            "question":  shared["question"],
            "context":   shared.get("context", "No previous search"),
            "iteration": shared.get("iteration", 0),
        }

    def exec(self, prep_res: dict) -> dict:
        if prep_res["iteration"] >= MAX_ITERATIONS:
            print(f"[DecideAction] Max iterations ({MAX_ITERATIONS}) reached — forcing answer.")
            return {"action": "answer", "thinking": "", "reason": "max iterations",
                    "search_query": "", "answer": ""}

        prompt = _DECIDE_PROMPT.format(
            question=prep_res["question"],
            context=prep_res["context"],
        )
        print(f"[DecideAction] iter={prep_res['iteration'] + 1} — reasoning...")
        raw = call_llm(prompt)
        decision = parse_yaml_safely(raw)
        action = decision.get("action", "").strip().lower()
        query  = decision.get("search_query", "").strip()
        print(f"[DecideAction] → action={action!r}  query={query!r}")
        return decision

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        shared["iteration"] = prep_res["iteration"] + 1
        action = str(exec_res.get("action", "answer")).strip().lower()
        if action == "search":
            shared["search_query"] = exec_res.get("search_query", "").strip()
            return "search"
        return "answer"


class SearchWeb(Node):
    """
    Tool-call node (no LLM).  Executes DuckDuckGo search and appends
    a SEARCH/RESULTS block to shared["context"].
    """

    def prep(self, shared: dict):
        return shared.get("search_query", "")

    def exec(self, query: str) -> str:
        print(f"[SearchWeb] Querying DuckDuckGo: {query!r}")
        return search_web_duckduckgo(query)

    def post(self, shared: dict, query: str, results: str) -> str:
        block = f"SEARCH: {query}\nRESULTS:\n{results}"
        prev  = shared.get("context", "No previous search")
        shared["context"] = block if prev == "No previous search" \
                            else f"{prev}\n\n---\n\n{block}"
        return "decide"


class AnswerQuestion(Node):
    """
    Terminal synthesis node.  GENERATEs a comprehensive prose answer
    from the full accumulated context and stores it in shared["answer"].
    """

    def prep(self, shared: dict):
        return {
            "question": shared["question"],
            "context":  shared.get("context", "No previous search"),
        }

    def exec(self, prep_res: dict) -> str:
        print("[AnswerQuestion] Synthesizing final answer...")
        return call_llm(_ANSWER_PROMPT.format(**prep_res))

    def post(self, shared: dict, prep_res: dict, answer: str) -> str:
        shared["answer"] = answer
        return "done"


# ── Flow factory ──────────────────────────────────────────────────────────────

def create_agent_flow() -> Flow:
    decide = DecideAction()
    search = SearchWeb()
    answer = AnswerQuestion()

    decide - "search" >> search   # search branch  → web tool → loop back
    decide - "answer" >> answer   # answer branch  → terminate
    search - "decide" >> decide   # loop back edge

    return Flow(start=decide)


# ── Public API ────────────────────────────────────────────────────────────────

def run_research_agent(question: str) -> str:
    """Run the full research loop and return the final answer string."""
    shared = {
        "question":  question,
        "context":   "No previous search",
        "iteration": 0,
    }
    create_agent_flow().run(shared)
    return shared.get("answer", "(no answer generated)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    question = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else (
            "What are the key differences between transformer and mamba "
            "architectures for long-sequence modeling?"
        )
    )

    print("=" * 70)
    print(f"Research Agent  |  model={LLM_MODEL}  |  max_iter={MAX_ITERATIONS}")
    print(f"Question: {question}")
    print("=" * 70)

    final_answer = run_research_agent(question)

    print("\n" + "=" * 70)
    print("FINAL ANSWER")
    print("=" * 70)
    print(final_answer)