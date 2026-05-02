## 0. High-level Description

This workflow implements a **ReAct-style (Reason + Act) research agent** using three logical functions composed in a single WORKFLOW. The `decide_action` function (GENERATE) receives the original question and any accumulated search context, emits a YAML-structured response containing a chain-of-thought reasoning block, a chosen action (`search` or `answer`), a search query, and an optional direct answer. The workflow's core loop is expressed as a WHILE construct: while the LLM chooses the `search` action, the `search_web` tool (CALL) is invoked with the generated query and its results are appended to the shared `@context` variable, then control returns to `decide_action` for re-evaluation. Once `decide_action` selects the `answer` action, an `answer_question` function (GENERATE) synthesises a final comprehensive response using the accumulated `@context`. The workflow terminates with RETURN `@answer` WITH `status='complete'`. No multi-model design is used; a single LLM handles both the decide and answer roles. Exception handling applies to YAML parse failures within the decide step, retrying with coerced block-scalar formatting before raising a `ValueError`.

---

## 1. Purpose

Answers an arbitrary research question by autonomously deciding when to search the web (via DuckDuckGo) and when sufficient evidence has been gathered to compose a final, evidence-grounded answer.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_flow()` + `Flow(start=decide)` in `flow.py` | Top-level orchestration unit |
| `CREATE FUNCTION decide_action` | `DecideAction.exec()` | Emits YAML with `action`, `search_query`, `answer` fields |
| `CREATE FUNCTION answer_question` | `AnswerQuestion.exec()` | Synthesises final answer from accumulated context |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` inside `DecideAction.exec()` | YAML parse + retry logic is inline post-processing |
| `GENERATE answer_question(...) INTO @answer` | `call_llm(prompt)` inside `AnswerQuestion.exec()` | Single LLM call; no structured output required |
| `CALL search_web(@query) INTO @results` | `search_web_duckduckgo(search_query)` in `SearchWeb.exec()` | Side-effect tool call; no LLM involved |
| `WHILE @decision.action == 'search' DO ... END` | `search - "decide" >> decide` cycle in `flow.py` + `return "decide"` in `SearchWeb.post()` | Graph edge creates an unbounded loop until `answer` is chosen |
| `EVALUATE @decision WHEN contains('search') THEN ... ELSE ... END` | `DecideAction.post()` branching on `exec_res["action"]` | Routes to `SearchWeb` or `AnswerQuestion` |
| `@context` (shared SPL variable) | `shared["context"]` dict key | Accumulates `"SEARCH: <q>\nRESULTS: <r>"` blocks across iterations |
| `@query` | `shared["search_query"]` | Written by `DecideAction.post()`, read by `SearchWeb.prep()` |
| `@answer` | `shared["answer"]` | Written by `AnswerQuestion.post()`, read by caller in `main.py` |
| `RETURN @answer WITH status='complete'` | `return "done"` from `AnswerQuestion.post()`; `shared["answer"]` printed in `main.py` | PocketFlow has no explicit status field; `"done"` edge signals termination |
| `EXCEPTION WHEN YAMLParseError THEN ... END` | `parse_yaml_safely()` retry block in `DecideAction.exec()` | Coerces inline scalar fields to block scalars, re-raises as `ValueError` on second failure |

---

## 3. Logical Functions / Prompts

### `decide_action`
- **Role**: The agent's "brain" — given the question and all prior search context, decides the next action.
- **Key prompt conventions**:
  - Uses an explicit **ACTION SPACE** section enumerating `[1] search` and `[2] answer` with typed parameters.
  - Response format is a **fenced YAML block** (` ```yaml ... ``` `).
  - `thinking` and `reason` fields use YAML **block scalar (`|`)** to safely embed multi-sentence prose with colons.
  - `search_query` is a single plain-string field (no `|`) to ease downstream string extraction.
  - A two-pass YAML parser handles models that omit the `|` sentinel: first `yaml.safe_load`, then a line-by-line coercion that injects `|` for known multi-line keys before retrying.

### `answer_question`
- **Role**: Terminal synthesiser — converts accumulated `@context` (a concatenated log of all search queries and their snippets) into a final prose answer.
- **Key prompt conventions**:
  - Minimal structure: a `### CONTEXT` header with the question and research dump, followed by a `## YOUR ANSWER:` directive.
  - No structured output (no YAML, no sentinel tokens); the raw LLM completion is the answer.
  - No scoring or quality gate; the decide loop handles evidence sufficiency.

---

## 4. Control Flow

```
INPUT: @question

1. GENERATE decide_action(question=@question, context=@context) INTO @decision
2. EVALUATE @decision
     WHEN action == 'search' THEN
         CALL search_web(query=@decision.search_query) INTO @results
         @context ← @context + "\n\nSEARCH: " + @query + "\nRESULTS: " + @results
         GOTO 1   ← (WHILE loop body)
     WHEN action == 'answer' THEN
         @context ← @decision.answer   ← (direct answer cached without search)
         EXIT WHILE
3. GENERATE answer_question(question=@question, context=@context) INTO @answer
4. RETURN @answer WITH status='complete'

EXCEPTION WHEN YAMLParseError THEN
    retry with coerced block scalars → raise ValueError on second failure
END
```

The loop is **unbounded** by design: the LLM controls termination by choosing `answer`. There is no explicit max-iteration guard in this implementation.

---

## 5. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a ReAct-style research agent \
using three logical functions composed in a single WORKFLOW. The decide_action \
function receives the original question and accumulated search context, emits a \
YAML-structured response containing chain-of-thought reasoning, a chosen action \
(search or answer), a search query, and an optional direct answer. The workflow \
core loop is a WHILE construct: while the LLM chooses search, the search_web tool \
is called with the generated query and results are appended to @context, then \
control returns to decide_action. Once decide_action selects answer, \
answer_question synthesises a final response using @context. The workflow \
terminates with RETURN @answer WITH status=complete. Exception handling covers \
YAML parse failures in the decide step." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile research_agent.spl --lang python/pocketflow
spl3 splc compile research_agent.spl --lang python/langgraph
spl3 splc compile research_agent.spl --lang go
```