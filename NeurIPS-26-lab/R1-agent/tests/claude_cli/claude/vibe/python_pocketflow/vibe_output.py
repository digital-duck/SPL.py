import os
import re
import sys
import yaml
from duckduckgo_search import DDGS
from openai import OpenAI
from pocketflow import Node, Flow

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def call_llm(prompt: str, model: str = None) -> str:
    model = model or LLM_MODEL
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if openrouter_key:
        client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
    elif openai_key:
        client = OpenAI(api_key=openai_key)
    else:
        raise EnvironmentError("Set OPENROUTER_API_KEY or OPENAI_API_KEY")

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# YAML parsing with block-scalar fallback
# ---------------------------------------------------------------------------
_BLOCK_SCALAR_KEYS = ["search_query", "answer", "reasoning"]


def _force_block_scalars(text: str) -> str:
    lines = text.split("\n")
    out = []
    for line in lines:
        replaced = False
        for key in _BLOCK_SCALAR_KEYS:
            m = re.match(rf"^(\s*){re.escape(key)}:\s+(.+)$", line)
            if m:
                indent, value = m.group(1), m.group(2).strip()
                if not value.startswith("|") and not value.startswith(">"):
                    out.append(f"{indent}{key}: |")
                    out.append(f"{indent}  {value.strip(chr(39)).strip(chr(34))}")
                    replaced = True
                    break
        if not replaced:
            out.append(line)
    return "\n".join(out)


def parse_yaml_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:yaml)?\s*", "", text).replace("```", "").strip()

    try:
        result = yaml.safe_load(cleaned)
        if isinstance(result, dict):
            return result
    except yaml.YAMLError:
        pass

    # Retry after forcing block-scalar notation on known keys
    fallback = _force_block_scalars(cleaned)
    try:
        result = yaml.safe_load(fallback)
        if isinstance(result, dict):
            return result
    except yaml.YAMLError as exc:
        raise ValueError(
            f"YAML parse failed after block-scalar fallback: {exc}\n---\n{text}"
        )

    raise ValueError(f"LLM returned non-dict YAML:\n{text}")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
MAX_ITERATIONS = 5

_DECIDE_PROMPT = """\
You are a research agent tasked with answering the following question.

Question: {question}

Accumulated research context:
{context}

Iteration: {iteration} / {max_iter}

Decide your next action:
  • If you need more information → return action=search with a targeted search_query.
  • If you have sufficient information (or this is the final allowed iteration) → return action=answer.

Respond ONLY with valid YAML in one of these two shapes — no prose, no fences:

Shape A (need more info):
action: search
reasoning: |
  <why this search is needed>
search_query: <concise web search query>

Shape B (ready to answer):
action: answer
reasoning: |
  <why you have enough info>
answer: |
  <comprehensive, well-structured final answer>
"""

_SYNTHESIZE_PROMPT = """\
You are a research expert. Synthesize the following research context into a comprehensive answer.

Question: {question}

Research Context:
{context}

Provide a thorough, accurate, and well-organized answer. Cite specific facts from the context.
"""


# ---------------------------------------------------------------------------
# PocketFlow nodes
# ---------------------------------------------------------------------------
class DecideActionNode(Node):
    def prep(self, shared):
        return {
            "question": shared["question"],
            "context": shared.get("context") or "(no searches performed yet)",
            "iteration": shared.get("iteration", 0),
        }

    def exec(self, prep_res):
        prompt = _DECIDE_PROMPT.format(
            question=prep_res["question"],
            context=prep_res["context"],
            iteration=prep_res["iteration"],
            max_iter=MAX_ITERATIONS,
        )
        raw = call_llm(prompt)
        return parse_yaml_response(raw)

    def post(self, shared, prep_res, exec_res):
        shared["iteration"] = prep_res["iteration"] + 1
        action = str(exec_res.get("action", "")).strip().lower()

        if action == "search" and shared["iteration"] < MAX_ITERATIONS:
            query = str(exec_res.get("search_query", "")).strip() or shared["question"]
            shared["search_query"] = query
            print(f"[iter {shared['iteration']}] SEARCH → {query}")
            return "search"

        # action=answer or forced termination at MAX_ITERATIONS
        shared["_answer_draft"] = str(exec_res.get("answer", "")).strip()
        print(f"[iter {shared['iteration']}] ANSWER (action={action})")
        return "answer"


class SearchWebNode(Node):
    def prep(self, shared):
        return shared["search_query"]

    def exec(self, prep_res):
        query = prep_res
        snippets = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                snippets.append(
                    f"Title: {r.get('title', '')}\n"
                    f"URL:   {r.get('href', '')}\n"
                    f"Body:  {r.get('body', '')}"
                )
        return "\n\n".join(snippets) if snippets else "(no results found)"

    def post(self, shared, prep_res, exec_res):
        entry = f"\n\n--- Search: {prep_res} ---\n{exec_res}"
        shared["context"] = shared.get("context", "") + entry
        print(f"   Retrieved {exec_res.count('Title:')} snippet(s)")
        return "decide"


class AnswerQuestionNode(Node):
    def prep(self, shared):
        return {
            "question": shared["question"],
            "context": shared.get("context") or "(no context available)",
            "draft": shared.get("_answer_draft", ""),
        }

    def exec(self, prep_res):
        if prep_res["draft"]:
            return prep_res["draft"]
        prompt = _SYNTHESIZE_PROMPT.format(
            question=prep_res["question"],
            context=prep_res["context"],
        )
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        shared["status"] = "done"
        return "done"


# ---------------------------------------------------------------------------
# Flow assembly
# ---------------------------------------------------------------------------
def build_flow() -> Flow:
    decide = DecideActionNode()
    search = SearchWebNode()
    answer = AnswerQuestionNode()

    decide - "search" >> search
    decide - "answer" >> answer
    search - "decide" >> decide

    return Flow(start=decide)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What are the major AI research breakthroughs announced in early 2025?"
    )

    shared = {
        "question": question,
        "context": "",
        "iteration": 0,
    }

    print(f"Question : {question}")
    print("=" * 70)

    flow = build_flow()
    flow.run(shared)

    print("\n" + "=" * 70)
    print("FINAL ANSWER")
    print("=" * 70)
    print(shared.get("answer", "(no answer generated)"))
    print(f"\nStatus     : {shared.get('status', 'unknown')}")
    print(f"Iterations : {shared.get('iteration', 0)}")