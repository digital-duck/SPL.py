# Research Agent Workflow Specification

---

## 0. High-level Description

This workflow implements a **ReAct-style (Reason + Act) research agent** using three logical functions orchestrated in a WHILE-style loop: `DecideAction`, `SearchWeb`, and `AnswerQuestion`. The `DecideAction` function is the loop's brain — it receives the current question and all accumulated research context, then calls an LLM with a structured YAML-format prompt to produce one of two action tokens: `"search"` or `"answer"`. EVALUATE logic branches on that token: when the result is `"search"`, control passes to the `SearchWeb` function, which executes a DuckDuckGo web search as a CALL side-effect and appends the retrieved snippets to the shared context before returning control to `DecideAction`; when the result is `"answer"`, control passes to `AnswerQuestion`. The WHILE loop is implicit in the `search → SearchWeb → DecideAction` cycle, which continues until the LLM judges that sufficient information has been gathered. The `AnswerQuestion` function issues a second GENERATE call using the accumulated context to synthesize a final, comprehensive answer, storing it in the shared `@answer` variable and terminating the loop with `RETURN WITH status="done"`. A single LLM model (GPT-4o, swappable via an SPL adapter shim) serves all GENERATE calls; YAML block-scalar parsing with an automatic retry/fix pass acts as the EXCEPTION handler for malformed LLM output. The final answer is written to an optional output file via a CALL side-effect, and the workflow surfaces `@answer` to the caller.

---

## 1. Purpose

Given a natural-language research question, this workflow autonomously searches the web in iterative cycles — guided by an LLM reasoning loop — until it has gathered enough information to produce a comprehensive written answer, optionally saving that answer to a file.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_flow()` + `Flow(start=decide)` in `flow.py` | The `Flow` object is the workflow container; `start=decide` sets the entry node |
| `CREATE FUNCTION decide_action` | `DecideAction` node (`prep` + `exec` + `post`) | Prompt template lives in `exec()`; `{question}` and `{context}` are the param slots |
| `CREATE FUNCTION search_web` | `SearchWeb` node (`prep` + `exec` + `post`) | Wraps `search_web_duckduckgo()`; no LLM call, pure tool invocation |
| `CREATE FUNCTION answer_question` | `AnswerQuestion` node (`prep` + `exec` + `post`) | Second GENERATE call; synthesises final answer from accumulated context |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` inside `DecideAction.exec()` | Returns YAML block parsed into a Python dict |
| `GENERATE answer_question(...) INTO @answer` | `call_llm(prompt)` inside `AnswerQuestion.exec()` | Returns free-form prose stored in `shared["answer"]` |
| `CALL search_web_duckduckgo(...) INTO @results` | `search_web_duckduckgo(search_query)` in `SearchWeb.exec()` | Side-effect tool call; result appended to `shared["context"]` |
| `CALL write_file(...)` | `Path(out).write_text(...)` in `main.py` | Optional file-write side-effect triggered when `--out` is provided |
| `EVALUATE @decision WHEN contains('search') THEN ... ELSE ...` | `post()` returning `"search"` or `"answer"`; PocketFlow routes on that token | `decide - "search" >> search` and `decide - "answer" >> answer` in `flow.py` |
| `WHILE @decision == "search" DO ... END` | `search - "decide" >> decide` cycle in `flow.py` | Loop continues until LLM emits `action: answer` |
| `RETURN @answer WITH status="done"` | `AnswerQuestion.post()` returning `"done"` | Terminal token; no outgoing edge from `AnswerQuestion` |
| `EXCEPTION WHEN YAMLParseError THEN retry_with_fix` | `parse_yaml_safely()` with block-scalar rewrite + second `yaml.safe_load` attempt | Raises `ValueError` with diagnostic message if both attempts fail |
| Shared state (`@var`) | `shared` dict passed through all nodes | Keys: `question`, `context`, `search_query`, `answer` |

---

## 3. Logical Functions / Prompts

### 3.1 `decide_action` (DecideAction node)

- **Role:** Central reasoning hub; decides at each iteration whether more web research is needed or whether the agent has enough information to answer.
- **Prompt conventions:**
  - Receives `{question}` and `{context}` (cumulative search history).
  - Defines an explicit **ACTION SPACE** with two labelled options: `[1] search` and `[2] answer`.
  - Demands output as a **fenced YAML block** (` ```yaml … ``` `) with keys: `thinking` (block scalar `|`), `action` (`search` or `answer`), `reason` (block scalar `|`), `answer` (block scalar `|`, empty when searching), `search_query` (plain string).
  - Uses YAML **block scalar (`|`) sentinel** for all multi-line fields to prevent colon/quote parse failures.
  - Output is parsed by `extract_yaml_block()` + `parse_yaml_safely()`; a **retry-with-fix** pass auto-converts inline values to block scalars on `YAMLError`.
  - The `action` field acts as the **routing token** (`"search"` or `"answer"`).

### 3.2 `search_web` (SearchWeb node)

- **Role:** Pure tool-call node; no LLM involved. Executes a DuckDuckGo search for up to 5 results and formats them as `Title / URL / Snippet` triples.
- **Prompt conventions:** None — this is a CALL side-effect, not a GENERATE.
- **Output format:** Plain string of concatenated result triples, prepended with `SEARCH: <query>\nRESULTS:` and appended to `shared["context"]` so all future LLM calls see the full research trail.

### 3.3 `answer_question` (AnswerQuestion node)

- **Role:** Terminal GENERATE call; synthesises a comprehensive prose answer from the accumulated research context.
- **Prompt conventions:**
  - Receives `{question}` and `{context}` (full research history).
  - Minimal structure: a `### CONTEXT` header followed by a `## YOUR ANSWER:` directive.
  - No sentinel tokens or YAML — free-form prose output expected.
  - Result stored verbatim in `shared["answer"]` and surfaced to the caller.

---

## 4. Control Flow

```
START
  │
  ▼
[DecideAction] ── GENERATE decide_action(question, context) INTO @decision
  │
  ├─ EVALUATE @decision.action == "search"
  │     │
  │     ▼
  │   [SearchWeb] ── CALL search_web_duckduckgo(@search_query) INTO @results
  │     │             append results to @context
  │     │
  │     └──────────────────────────────────────────┐
  │                                                 │ (loop back)
  │                                                 ▼
  │                                          [DecideAction]
  │
  └─ EVALUATE @decision.action == "answer"
        │
        ▼
      [AnswerQuestion] ── GENERATE answer_question(question, context) INTO @answer
        │
        ▼
      RETURN @answer WITH status="done"
        │
        ▼
      [Optional] CALL write_file(@answer) ── if --out flag provided
        │
        ▼
       END
```

**Key control-flow notes:**

- The **WHILE loop** is structural: `SearchWeb` always returns the token `"decide"`, routing back to `DecideAction`. The loop has no hard iteration cap in the Python code — termination depends entirely on the LLM choosing `action: answer`.
- The **EVALUATE branch** in `DecideAction.post()` is the sole routing decision point; it drives two real edges (`"search"` and `"answer"`), making it a genuine SPL EVALUATE, not implicit linear flow.
- `RETURN WITH status="done"` is non-trivial: it is the only terminal token in the graph and signals successful completion to the `Flow` runner.
- The **EXCEPTION** path in `parse_yaml_safely()` is a local retry within `DecideAction.exec()` — it does not reroute the graph but raises `ValueError` (propagating as an unhandled exception) if both YAML parse attempts fail.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from the high-level description (Section 0 above as text2spl input)
spl3 text2spl \
  --description "This workflow implements a ReAct-style research agent using three logical \
functions orchestrated in a WHILE-style loop: DecideAction, SearchWeb, and AnswerQuestion. \
The DecideAction function receives the current question and accumulated research context, \
then calls an LLM with a structured YAML-format prompt to produce one of two action tokens: \
'search' or 'answer'. EVALUATE logic branches on that token: when the result is 'search', \
control passes to the SearchWeb function, which executes a DuckDuckGo web search as a CALL \
side-effect and appends retrieved snippets to the shared context before returning control to \
DecideAction; when the result is 'answer', control passes to AnswerQuestion. The WHILE loop \
is implicit in the search→SearchWeb→DecideAction cycle, continuing until the LLM judges \
sufficient information has been gathered. The AnswerQuestion function issues a second GENERATE \
call using accumulated context to synthesise a final answer, storing it in @answer and \
terminating with RETURN WITH status='done'. A single LLM model serves all GENERATE calls; \
YAML block-scalar parsing with an automatic retry/fix pass acts as the EXCEPTION handler for \
malformed LLM output. The final answer is written to an optional output file via a CALL \
side-effect." \
  --mode workflow \
  --out research_agent.spl

# Step 2 — compile to your target runtime
spl3 splc compile research_agent.spl --lang python/pocketflow   # original target
spl3 splc compile research_agent.spl --lang python/langgraph    # LangGraph variant
spl3 splc compile research_agent.spl --lang go                  # Go variant
```