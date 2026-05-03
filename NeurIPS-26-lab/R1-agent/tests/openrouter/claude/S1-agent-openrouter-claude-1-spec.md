## 0. High-level Description

This workflow implements a **research agent** using a WHILE-loop-driven, graph-structured LLM orchestration pattern in which a central decision function repeatedly evaluates whether sufficient information has been gathered to answer a user's question. The workflow begins by invoking a `DecideAction` CREATE FUNCTION that receives the original question and any accumulated research context, then GENERATEs a YAML-structured LLM response containing a `thinking` rationale, an `action` field (either `search` or `answer`), a `reason`, and optionally a `search_query` or `answer`; an EVALUATE branch on the `action` field then routes execution either into a `SearchWeb` CALL — which performs a live DuckDuckGo web search as a side-effect tool call and appends the results to a shared `@context` variable — or into an `AnswerQuestion` CREATE FUNCTION that GENERATEs a final comprehensive answer from the accumulated context. The WHILE loop continues redirecting from `SearchWeb` back to `DecideAction` until the LLM's YAML output contains `action: answer`, at which point the EVALUATE exits the loop and control passes to `AnswerQuestion`. The workflow maintains shared state across iterations through SPL `@vars` (`@question`, `@context`, `@search_query`, `@answer`), accumulating search results in `@context` with each iteration using a `SEARCH: … RESULTS: …` delimiter convention. An optional CALL side-effect writes the final answer to a file path when one is specified. Exception handling covers YAML parse failures in the `DecideAction` response via an EXCEPTION WHEN ParseError handler that attempts block-scalar repair before re-raising as a ValueError, and the workflow concludes with RETURN `@answer` WITH `status=done`.

---

## 1. Purpose

This workflow enables an end user to pose any open-ended research question and receive a comprehensive, web-grounded answer produced by an LLM agent that autonomously decides how many web searches to perform before synthesising a final response.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_flow()` + `flow.run(shared)` in `main.py` | The `Flow` object and its `.run()` call constitute the named workflow entry point |
| `CREATE FUNCTION DecideAction` | `class DecideAction(Node)` with `prep` / `exec` / `post` | Prompt is assembled in `exec`; YAML parsing also lives here |
| `CREATE FUNCTION SearchWeb` | `class SearchWeb(Node)` with `prep` / `exec` / `post` | Side-effect tool call wrapping `search_web_duckduckgo()` |
| `CREATE FUNCTION AnswerQuestion` | `class AnswerQuestion(Node)` with `prep` / `exec` / `post` | Final synthesis prompt; no loop-back |
| `GENERATE DecideAction(...) INTO @decision` | `response = call_llm(prompt)` inside `DecideAction.exec()` | Result parsed from YAML into `decision` dict |
| `GENERATE AnswerQuestion(...) INTO @answer` | `answer = call_llm(prompt)` inside `AnswerQuestion.exec()` | Plain-text LLM response stored in `shared["answer"]` |
| `CALL search_web(...) INTO @results` | `results = search_web_duckduckgo(search_query)` in `SearchWeb.exec()` | External I/O side-effect; result concatenated into `@context` |
| `CALL write_file(...)` | `Path(out).write_text(...)` in `main.py` | Optional file-save side-effect triggered when `--out` is supplied |
| `WHILE action != "answer" DO` | `decide - "search" >> search; search - "decide" >> decide` graph cycle | PocketFlow edge routing implements the loop implicitly via node return values |
| `EVALUATE @decision WHEN contains("search")` | `if exec_res["action"] == "search":` in `DecideAction.post()` | Routes to `SearchWeb` or `AnswerQuestion` based on parsed YAML `action` field |
| `RETURN @answer WITH status=done` | `return "done"` in `AnswerQuestion.post()`; `shared["answer"]` read in `main.py` | Terminal node signals completion; answer extracted from shared store |
| `EXCEPTION WHEN ParseError THEN` | `except yaml.YAMLError` with block-scalar repair + re-raise as `ValueError` | Two-stage fallback: regex repair attempted, then hard failure |
| `@question` (shared SPL var) | `shared["question"]` | Read-only across all nodes |
| `@context` (shared SPL var) | `shared["context"]` | Mutated by `SearchWeb.post()` each iteration; read by `DecideAction.prep()` |
| `@search_query` (shared SPL var) | `shared["search_query"]` | Written by `DecideAction.post()` when action is `search`; read by `SearchWeb.prep()` |
| `@answer` (shared SPL var) | `shared["answer"]` | Written once by `AnswerQuestion.post()`; read by `main.py` for output |
| `{param}` slot in CREATE FUNCTION | f-string interpolation inside `exec()` prompt strings | `{question}`, `{context}`, `{search_query}` injected at call time |

---

## 3. Logical Functions / Prompts

### 3.1 `DecideAction`

- **Role in the workflow:** The central reasoning engine and loop controller. It is called on every iteration (including the first) and determines whether the agent has enough information to answer or must search further.
- **Key prompt conventions:**
  - Receives `{question}` and `{context}` (accumulated search history, defaulting to `"No previous search"` on the first call).
  - Defines a numbered **ACTION SPACE** block listing two actions: `search` (with a `query` parameter) and `answer` (with an `answer` parameter).
  - Instructs the LLM to respond in a fenced `yaml` code block containing five fields: `thinking` (block scalar `|`), `action` (literal `search` or `answer`), `reason` (block scalar `|`), `answer` (block scalar `|`, empty when searching), and `search_query` (plain string, empty when answering).
  - **Sentinel / output format:** YAML fenced block delimited by ` ```yaml ` … ` ``` `; parsed with `yaml.safe_load`; fallback regex repair converts bare `key: value` lines to `key: |` block scalars when a `YAMLError` is raised.
  - **Routing output:** `post()` returns the string `"search"` or `"answer"` to select the next graph edge.

### 3.2 `SearchWeb`

- **Role in the workflow:** A side-effect CALL node that executes a live web search and appends structured results to the shared context. It always routes back to `DecideAction`.
- **Key prompt conventions:**
  - No LLM call; this is a pure tool-call node.
  - Input: `@search_query` string from shared state.
  - Output format: up to 5 DuckDuckGo results serialised as `Title: … \nURL: … \nSnippet: …` blocks joined by `\n\n`.
  - Context accumulation pattern: `shared["context"] += "\n\nSEARCH: <query>\nRESULTS: <results>"` — acts as a structured log readable by subsequent `DecideAction` calls.
  - **Routing output:** `post()` always returns `"decide"`, unconditionally looping back.

### 3.3 `AnswerQuestion`

- **Role in the workflow:** The terminal synthesis node. Called exactly once, when `DecideAction` has determined that the accumulated `@context` is sufficient to answer the question.
- **Key prompt conventions:**
  - Receives `{question}` and `{context}` (full accumulated research log).
  - Prompt structure: a `### CONTEXT` section followed by a `## YOUR ANSWER:` directive requesting a "comprehensive answer using the research results."
  - No structured output format enforced — plain prose is expected and stored verbatim in `@answer`.
  - **Routing output:** `post()` returns `"done"`, which is the terminal signal causing the PocketFlow `Flow` to halt.

---

## 4. Control Flow

```
START
  │
  ▼
GENERATE DecideAction(@question, @context) INTO @decision
  │
  ├─ EVALUATE @decision WHEN action == "search"
  │     │
  │     ▼
  │   CALL search_web(@search_query) INTO @results          [side-effect]
  │   @context ← @context + "\n\nSEARCH: …\nRESULTS: …"
  │     │
  │     └──────────────────────────────────────────────────┐
  │                                               (loop back — WHILE)
  │
  └─ EVALUATE @decision WHEN action == "answer"
        │
        ▼
      GENERATE AnswerQuestion(@question, @context) INTO @answer
        │
        ▼
      [OPTIONAL] CALL write_file(@out, @answer)              [side-effect]
        │
        ▼
      RETURN @answer WITH status=done
```

**Detailed narrative:**

1. **Initialisation:** `@question` is set from CLI input; `@context` is initialised to `"No previous search"` implicitly on first access.
2. **WHILE loop (implicit graph cycle):** `DecideAction` is entered. Each call GENERATEs a YAML decision. The EVALUATE on `action` either exits the loop (`answer`) or continues it (`search`).
3. **Loop body:** When `action == "search"`, `@search_query` is written to shared state, `SearchWeb` executes the DuckDuckGo CALL, appends to `@context`, and returns `"decide"` to re-enter `DecideAction`. This cycle repeats indefinitely until the LLM chooses `action: answer`.
4. **EXCEPTION handling (within DecideAction):** If `yaml.safe_load` raises `YAMLError`, a repair pass converts problematic lines to block-scalar form and retries. If the second parse also fails, a `ValueError` is raised — mapping to `EXCEPTION WHEN ParseError THEN raise`.
5. **Termination:** When `action == "answer"`, `AnswerQuestion` is entered, GENERATEs the final prose answer into `@answer`, optionally CALLs the file-write tool, and RETURNs WITH `status=done`.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a research agent using a WHILE-loop-driven, \
graph-structured LLM orchestration pattern in which a central decision function repeatedly evaluates \
whether sufficient information has been gathered to answer a user's question. The workflow begins by \
invoking a DecideAction CREATE FUNCTION that receives the original question and any accumulated \
research context, then GENERATEs a YAML-structured LLM response containing a thinking rationale, \
an action field (either search or answer), a reason, and optionally a search_query or answer; an \
EVALUATE branch on the action field then routes execution either into a SearchWeb CALL — which \
performs a live DuckDuckGo web search as a side-effect tool call and appends the results to a shared \
@context variable — or into an AnswerQuestion CREATE FUNCTION that GENERATEs a final comprehensive \
answer from the accumulated context. The WHILE loop continues redirecting from SearchWeb back to \
DecideAction until the LLM YAML output contains action: answer, at which point the EVALUATE exits \
the loop and control passes to AnswerQuestion. The workflow maintains shared state across iterations \
through SPL @vars (@question, @context, @search_query, @answer), accumulating search results in \
@context with each iteration using a SEARCH: … RESULTS: … delimiter convention. An optional CALL \
side-effect writes the final answer to a file path when one is specified. Exception handling covers \
YAML parse failures in the DecideAction response via an EXCEPTION WHEN ParseError handler that \
attempts block-scalar repair before re-raising as a ValueError, and the workflow concludes with \
RETURN @answer WITH status=done." \
--mode workflow

# Step 2 — compile to any target runtime
spl3 splc compile research_agent.spl --lang python/pocketflow
spl3 splc compile research_agent.spl --lang python/langgraph
spl3 splc compile research_agent.spl --lang go
```