## 0. High-level Description

This workflow implements an iterative research agent using a WHILE-loop pattern driven by a GENERATE call to the `decide_action` function, which produces a structured YAML decision on each iteration. Three logical functions are defined: `decide_action` (a chain-of-thought reasoning prompt that evaluates accumulated context and returns either `action: search` with a `search_query` or `action: answer` with a final answer), `search_web` (a CALL side-effect that invokes DuckDuckGo and appends results to the shared `@context` variable), and `answer_question` (a GENERATE call that synthesizes accumulated research into a comprehensive final answer). The WHILE loop persists as long as `decide_action` returns `action: search`, with an EVALUATE branch directing execution to either CALL `search_web` (then loop back) or GENERATE `answer_question` (then terminate). A YAML-parsing fallback that forces block-scalar (`|`) notation on known keys and retries the parse acts as an implicit EXCEPTION handler for malformed LLM output. The workflow terminates with RETURN `@answer` WITH `status=done` after `answer_question` completes.

## 1. Purpose

Answers a user-supplied research question by iteratively deciding to search the web or synthesize a final answer, accumulating web search results in `@context` across multiple rounds until the agent determines it has sufficient information.

---

## Target Framework: PocketFlow

PocketFlow (https://github.com/the-pocket/PocketFlow) is a minimalist 100-line Python LLM orchestration framework. Use it as the runtime for this implementation.

### Core API

**Node** — the unit of computation. Subclass `Node` and implement three methods:

```python
from pocketflow import Node, Flow

class MyNode(Node):
    def prep(self, shared: dict):
        # Read from shared state; return data for exec()
        return shared["key"]

    def exec(self, prep_res):
        # Pure computation; receives prep() return value
        # Make LLM calls or tool calls here
        return result

    def post(self, shared: dict, prep_res, exec_res) -> str:
        # Write results back to shared state
        shared["output"] = exec_res
        # Return an action string that determines the next node
        return "default"   # or "search", "answer", "done", etc.
```

**Flow** — wires nodes into a graph and runs it:

```python
node_a = MyNodeA()
node_b = MyNodeB()
node_c = MyNodeC()

# Unconditional edge (action="default")
node_a >> node_b

# Conditional edges (action string returned from post())
node_b - "search" >> node_a   # loops back — implements WHILE
node_b - "answer" >> node_c   # exits loop

flow = Flow(start=node_a)
shared = {"question": "...", "context": ""}
flow.run(shared)
```

**Shared dict** — the global state passed through every `prep()` and `post()` call. All nodes read from and write to the same dict. Equivalent to workflow-scoped variables.

**Self-loop** — a node routing back to itself (or to an earlier node) implements a WHILE loop. The loop exits when `post()` returns an action with no registered successor.

### LLM calls

Call the LLM inside `exec()`. For the `claude_cli` adapter use subprocess; for `openrouter` use the OpenAI-compatible API:

```python
import os, requests

def call_llm(prompt: str, model: str = "google/gemini-3-flash-preview") -> str:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
```

### Web search

Use `duckduckgo_search` (already installed: `pip install duckduckgo-search`):

```python
from duckduckgo_search import DDGS

def search_web(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
```

### Minimal working pattern (reference)

```python
class DecideNode(Node):
    def prep(self, shared):
        return shared["question"], shared["context"]
    def exec(self, args):
        question, context = args
        raw = call_llm(f"Question: {question}\nContext: {context}\nDecide: search or answer?")
        return parse_yaml(raw)          # returns {"action": "search", "search_query": "..."} or {"action": "answer"}
    def post(self, shared, prep_res, exec_res):
        shared["decision"] = exec_res
        return exec_res.get("action", "answer")   # routes to "search" or "answer" branch

decide = DecideNode()
search = SearchNode()
answer = AnswerNode()

decide - "search" >> search
decide - "answer" >> answer
search >> decide               # back-edge: implements the WHILE loop

Flow(start=decide).run({"question": "...", "context": "No context yet."})
```

---

## Implementation Requirements

1. Use PocketFlow `Node`/`Flow` pattern as shown above — not a plain Python class.
2. The `decide_action` prompt must request YAML output with keys `action` and `search_query`.
3. Include a YAML parser with block-scalar (`|`) fallback retry for malformed LLM output.
4. Use DuckDuckGo (`duckduckgo_search`) for the search tool.
5. Use the OpenRouter API (`openrouter.ai`) for LLM calls. Read `OPENROUTER_API_KEY` from env.
6. The model should be configurable — default to `google/gemini-3-flash-preview` but accept
   any OpenRouter model ID.
7. Provide a `if __name__ == "__main__"` CLI entry point that accepts the question as a
   command-line argument.
8. Return the final answer with `status="done"` in the result dict.
