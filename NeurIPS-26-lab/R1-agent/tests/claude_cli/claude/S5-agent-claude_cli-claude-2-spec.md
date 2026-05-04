## 0. High-level Description

This workflow implements a ReAct-style web search agent that iteratively decides whether to search or answer using a structured YAML decision loop. Two `CREATE FUNCTION` prompts are defined: `decide_action` prompts the LLM to reason about the accumulated context and return a fenced YAML block containing `action: search` (with `search_query`) or `action: answer`; `answer_question` synthesizes all accumulated context into a final prose answer. Execution begins with `InitNode` which seeds `@context`, `@iteration`, `@done`, and `@decision`. A `LoopCheckNode` guards the WHILE condition (`@done != "true" AND @iteration < 10`) by returning `"continue"` or `"exit"`. On each iteration `DecideActionNode` calls the LLM, then `ParseYamlNode` attempts `yaml.safe_load` on the fenced YAML response; a YAML parse failure routes to `ForceBlockScalarsNode` (which strips inline quotes) and `RetryParseNode` — if the retry also fails the flow terminates with `status="error"`. On clean parse, `EvaluateDecisionNode` inspects `decision["action"]` and routes to either `SearchWebNode` (stub tool, appends to `@context`, loops back) or `AnswerQuestionNode` (final LLM synthesis, sets `@done="true"`, terminates with `status="complete"`). The `search_web_tool` is a stub intended to be replaced with a live search API. There is no explicit EXCEPTION block; unhandled `subprocess.CalledProcessError` would propagate from `call_llm`.

---

## 1. Purpose

Answers a user research question by autonomously looping through web-search and reasoning steps — up to 10 iterations — until the LLM decides it has sufficient context to deliver a final synthesized answer.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW web_search_agent` | `build_flow() → Flow(start=init)` | Node graph replaces declarative WORKFLOW header |
| `INPUT @question TEXT` | `shared["question"]` set before `Flow.run()` | Read-only throughout; passed into every prompt |
| `OUTPUT @answer TEXT` | `shared["answer"]` written by `AnswerQuestionNode.post()` | Returned in result dict by `run_web_search_agent()` |
| `@context := 'No previous search'` | `InitNode.post()` sets `shared["context"]` | Accumulates `SEARCH: / RESULTS:` blocks each iteration |
| `@iteration := 0`, `@done := 'false'` | `InitNode.post()` seeds `shared["iteration"]`, `shared["done"]` | String `"true"/"false"` mirror SPL string convention |
| `WHILE @done != 'true' AND @iteration < 10 DO` | `LoopCheckNode.prep/exec/post` returning `"continue"` or `"exit"` | `"exit"` has no successor → flow terminates (max iterations) |
| `@iteration := @iteration + 1` | `shared["iteration"] += 1` in `DecideActionNode.post()` | Incremented after LLM call; LoopCheckNode reads updated value next pass |
| `GENERATE decide_action(@question, @context) INTO @raw_response` | `DecideActionNode.exec()` → `call_llm(prompt)` | Expects fenced ` ```yaml ``` ` block in response |
| `CALL parse_yaml(@raw_response) INTO @parse_result` | `ParseYamlNode.exec()` → `parse_yaml_tool(raw)` | Extracts YAML from code fence; returns `{"parse_error": ...}` on failure |
| `EVALUATE @parse_result WHEN contains('parse_error')` | `ParseYamlNode.post()` returning `"parse_error"` or `"evaluate"` | Drives YAML error-recovery path |
| `CALL force_block_scalars(@raw_response) INTO @fixed_response` | `ForceBlockScalarsNode.exec()` → `force_block_scalars_tool(raw)` | Strips inline quotes from YAML values |
| `CALL parse_yaml(@fixed_response) INTO @retry_result` | `RetryParseNode.exec()` → `parse_yaml_tool(fixed)` | Second parse attempt after fixup |
| `RETURN @retry_result WITH status='error'` | `RetryParseNode.post()` sets `shared["status"]="error"`, returns `"error"` (terminal) | Unrecoverable YAML failure path |
| `EVALUATE @decision WHEN contains('action: search')` | `EvaluateDecisionNode.post()` checks `decision.get("action") == "search"` | Non-search action falls through to answer path |
| `CALL extract_field(@decision, 'search_query') INTO @search_query` | `SearchWebNode.exec()` calls `extract_field_tool(decision, "search_query")` | Inline within `SearchWebNode`; not a separate node |
| `CALL search_web(@search_query) INTO @search_results` | `search_web_tool(query)` → stub returning placeholder string | Replace with SerpAPI / Tavily / DuckDuckGo for production |
| `@context := @context + '\nSEARCH: ...'` | `SearchWebNode.post()` appends to `context` from `prep_res` | Uses value captured at `prep()` time (consistent within iteration) |
| `GENERATE answer_question(@question, @context) INTO @answer` | `AnswerQuestionNode.exec()` → `call_llm(ANSWER_QUESTION_PROMPT.format(...))` | Free-form prose synthesis |
| `@done := 'true'` | `AnswerQuestionNode.post()` sets `shared["done"] = "true"` | Signals loop exit, though flow terminates via `"done"` action (no successor) |
| `RETURN @answer WITH status='complete'` | `shared["status"] = "complete"` + `"done"` terminal action | `"done"` has no successor registered → flow ends |
| Adapter: `claude_cli` | `subprocess.run(["claude", "-p", prompt])` | No `--model` flag; defaults to Claude's own default |

---

## 3. Logical Functions / Prompts

### `decide_action`
- **Role:** Reasoning core of the ReAct loop. Given the accumulated `@context`, decides whether to search further or answer.
- **Output:** Fenced ` ```yaml ``` ` block with keys `action` (`search` or `answer`) and `search_query` (only when `action: search`).
- **Error recovery:** If the raw LLM response fails YAML parse, `force_block_scalars_tool` strips inline quotes and the parse is retried once. A second failure terminates the flow with `status="error"`.

### `answer_question`
- **Role:** Terminal synthesis step. Consumes `@question` and the full accumulated `@context` to produce the final user-facing answer.
- **Output:** Free-form prose; no structured format required.

### Tool calls (not prompts)
- `parse_yaml_tool(raw)` — extracts content from ` ```yaml ``` ` fence and calls `yaml.safe_load`; returns `{"parse_error": ...}` on failure.
- `force_block_scalars_tool(raw)` — strips `"..."` and `'...'` inline quoting from YAML values to coerce block-scalar compatibility.
- `extract_field_tool(decision, field)` — `dict.get(field, "")` with `str()` cast.
- `search_web_tool(query)` — stub; returns `"[stub: search results for '...']"`.

---

## 4. Control Flow

```
INPUT @question
@context ← "No previous search"; @iteration ← 0; @done ← "false"

── WHILE @done != "true" AND @iteration < 10 ───────────────────────────
│
│  GENERATE decide_action(@question, @context) INTO @raw_response
│  @iteration += 1
│
│  CALL parse_yaml(@raw_response) INTO @parse_result
│  EVALUATE @parse_result
│    WHEN contains("parse_error") THEN
│      CALL force_block_scalars(@raw_response) INTO @fixed_response
│      CALL parse_yaml(@fixed_response) INTO @retry_result
│      EVALUATE @retry_result
│        WHEN contains("parse_error") THEN RETURN status="error"  ──────── ✗
│        ELSE @decision := @retry_result
│      END
│    ELSE @decision := @parse_result
│  END
│
│  EVALUATE @decision
│    WHEN action == "search" THEN
│      CALL search_web(@decision["search_query"]) INTO @search_results
│      @context += "\nSEARCH: ... RESULTS: ..."
│      → loop back
│    ELSE (action == "answer")
│      GENERATE answer_question(@question, @context) INTO @answer
│      @done ← "true"
│      RETURN @answer WITH status="complete"  ───────────────────────── ✓
│  END
│
└────────────────────────────────────────────────────────────────────────
(loop exits via @iteration >= 10 → RETURN status="max_iterations_reached", answer="")
```

**Observed run (2026-05-04):** Question `"Who invented telephone"` → 2 iterations, `status=complete`. The agent performed one search then synthesized a multi-perspective answer covering Bell, Gray, Meucci, and Reis.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — regenerate SPL from this spec
spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-agent-claude_cli-claude-2-spec.md)" \
    --mode workflow --adapter claude_cli

# Step 2 — run
spl3 run web_search_agent.spl --adapter claude_cli \
    --param question="Who invented the telephone?"

# Step 3 — recompile to any target
spl3 splc compile web_search_agent.spl --lang python/pocketflow --llm \
    --adapter claude_cli --model claude
spl3 splc compile web_search_agent.spl --lang python/langgraph
spl3 splc compile web_search_agent.spl --lang go
```
