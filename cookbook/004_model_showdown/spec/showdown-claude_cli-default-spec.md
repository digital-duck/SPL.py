## Summary

Model Showdown submits the same user-supplied prompt to two local Ollama models simultaneously, then asks a third LLM call to evaluate and compare both responses side-by-side. It exists to give practitioners a fast, reproducible way to benchmark different local models against arbitrary questions without shell scripting. Teams evaluating which Ollama model to adopt for a task benefit most.

---

## Detailed Specification

### 1. Purpose

Run an identical prompt against two configurable Ollama models in parallel, then produce a structured comparative evaluation of both responses.

### 2. High-level Description

This workflow uses a parallel CTE pattern — two GENERATE calls (`ask_model_1`, `ask_model_2`) execute concurrently against independently configurable Ollama models, each using the `answer` function which passes the user prompt through with a standard helpful-assistant system role. Once both responses are collected into `@answer_1` and `@answer_2`, a second CREATE FUNCTION `compare_responses` is invoked via GENERATE to act as a neutral evaluator: it reproduces each model's raw output verbatim in labeled sections, then assesses quality, strengths, and weaknesses before naming the most helpful response. There is no WHILE loop; the flow is strictly linear — parallel generation followed by a single evaluation GENERATE. Three CALL side-effects write each individual model response and the final comparison to Markdown log files under a configurable log directory. The workflow RETURN carries `status='complete'` along with the two model names as metadata, making the result inspectable by callers. A top-level EXCEPTION handler catches `GenerationError` (either model failing) and short-circuits with `status='error'`.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW model_showdown` | `WORKFLOW <name>` | Declares the top-level orchestration unit with typed INPUT/OUTPUT |
| `CREATE FUNCTION answer` | `CREATE FUNCTION <name>` | Single-slot prompt template; passes `{prompt}` verbatim to the model |
| `CREATE FUNCTION compare_responses` | `CREATE FUNCTION <name>` | Multi-slot evaluator template; accepts prompt + two model name/answer pairs |
| Parallel CTE block (`WITH response_1 AS (...), response_2 AS (...)`) | `GENERATE <fn>(...) INTO @<var>` × 2, parallel | Two concurrent GENERATE calls; results selected INTO `@answer_1`, `@answer_2` |
| `GENERATE compare_responses(...) INTO @comparison` | `GENERATE <fn>(...) INTO @<var>` | Sequential evaluator call after parallel responses are collected |
| `CALL write_file(...) INTO NONE` × 3 | `CALL <tool>(...) INTO @<var>` | Side-effect file writes; result discarded (`INTO NONE`) |
| `@prompt`, `@model_1`, `@model_2`, `@answer_1`, `@answer_2`, `@comparison` | Shared state (`@vars`) | Workflow-scoped variables passed between steps |
| `RETURN @comparison WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token; surfaces model metadata to caller |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN <Type> THEN` | Catches generation failure from either parallel branch |
| `RETURN '...' WITH status='error'` | `RETURN @<var> WITH status=` | Error-path return with distinct status token |

### 4. Logical Functions / Prompts

**`answer`**
- **Role:** Minimal pass-through prompt used for both model calls. Sends the raw user question to whichever Ollama model is assigned, with a `system_role` of "helpful, knowledgeable assistant."
- **Key conventions:** Single `{prompt}` slot; no output format constraints; the model responds freely. Used twice — once per model — inside the parallel CTE.

**`compare_responses`**
- **Role:** Neutral judge that consumes both models' raw outputs and produces a structured comparative report.
- **Key conventions:** Instructs the LLM to first reproduce each response verbatim under `=== {model_name} ===` section headers (preserving ground truth), then evaluate quality and strengths/weaknesses per model, then conclude with a winner and rationale. No numeric scoring; qualitative prose evaluation only.

### 5. Control Flow

1. **Parallel generation** — `ask_model_1` and `ask_model_2` execute concurrently via the CTE block; both use the `answer` function with their respective models. Results land in `@answer_1` and `@answer_2`.
2. **Sequential evaluation** — `compare_responses` is called once with all collected inputs, producing `@comparison`.
3. **Side-effects** — Three `CALL write_file` steps persist individual responses and the comparison report to the log directory.
4. **Termination** — `RETURN @comparison WITH status='complete'` ends the happy path. No WHILE loop or EVALUATE branching exists; the only non-linear path is the `EXCEPTION WHEN GenerationError` handler, which returns immediately with `status='error'` if either model GENERATE fails.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Run an identical prompt against two configurable Ollama models in parallel, then produce a structured comparative evaluation of both responses." --mode workflow

# Step 2 — compile to any target
spl3 splc compile model_showdown.spl --lang python/pocketflow
spl3 splc compile model_showdown.spl --lang python/langgraph
spl3 splc compile model_showdown.spl --lang go
```