## Summary

Bedrock Quickstart fans out a single user-supplied prompt to three AWS Bedrock models simultaneously, then uses a neutral judge model to compare and evaluate all three responses. It exists to give developers a fast, repeatable way to benchmark Bedrock model families side-by-side without writing custom evaluation code. Anyone choosing a production Bedrock model for a new application benefits directly from the structured evaluation output.

---

## Detailed Specification

### 1. Purpose

Run any prompt against three configurable AWS Bedrock models in parallel and return a structured comparison that identifies the most accurate, most concise, and most production-suitable response.

### 2. High-level Description

The WORKFLOW `bedrock_quickstart` accepts a free-text `@prompt` and three Bedrock model IDs as inputs, defaulting to Claude Sonnet 4, Claude Haiku 4.5, and Amazon Nova Pro. It employs a parallel fan-out pattern: three GENERATE calls (`ask_model_1`, `ask_model_2`, `ask_model_3`) are issued concurrently using a WITH/CTE construct, each sending the same system role instruction and user prompt to its designated model and capturing the result into `@answer_1`, `@answer_2`, and `@answer_3` respectively. Once all three responses are collected, a second GENERATE call invokes the CREATE FUNCTION `compare_models`, which instructs a neutral evaluator to reproduce the raw responses verbatim and then assess accuracy, conciseness, and production suitability. The workflow closes with a RETURN that surfaces the comparison text alongside status and model-identity metadata. An EXCEPTION handler for `GenerationError` catches any model invocation failure—due to region misconfiguration, missing model access, or IAM permission issues—and returns a descriptive error string with `status = 'error'`.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW bedrock_quickstart` | `WORKFLOW <name>` | Declares the named orchestration workflow with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION compare_models(...)` | `CREATE FUNCTION <name>` | Reusable prompt template with `{param}` slots; seven parameters covering prompt, three model IDs, and three answer texts |
| Parallel CTE fan-out (`WITH response_1, response_2, response_3`) | `GENERATE <fn>(...) INTO @<var>` × 3 | Three concurrent GENERATE calls using named prompt blocks; results selected INTO `@answer_1`, `@answer_2`, `@answer_3` |
| `GENERATE compare_models(...) INTO @comparison` | `GENERATE <fn>(...) INTO @<var>` | Single judging GENERATE call consuming all three answers |
| `RETURN @comparison WITH status='complete', model_1=..., model_2=..., model_3=...` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial RETURN: `status='complete'` confirms successful execution; model ID metadata enables downstream traceability |
| `EXCEPTION WHEN GenerationError THEN ... WITH status='error'` | `EXCEPTION WHEN <Type> THEN ...` | Catches Bedrock invocation failures; returns user-readable error with `status='error'` |
| `@prompt`, `@model_1/2/3`, `@answer_1/2/3`, `@comparison` | Shared state `@<var>` | Workflow-scoped variables threading inputs, intermediate answers, and final output |

### 4. Logical Functions / Prompts

**`ask_model_1` / `ask_model_2` / `ask_model_3`** (inline prompt blocks)
- **Role:** Fan-out query — each sends an identical system role (`"You are a helpful, knowledgeable assistant."`) and the user-supplied `@prompt` to one of the three target models. They differ only in the model ID specified via `USING MODEL`.
- **Key conventions:** Minimal system prompt to avoid biasing responses; no output format constraint, allowing free-form answers suitable for subsequent qualitative comparison.

**`compare_models`** (CREATE FUNCTION)
- **Role:** Neutral judge — receives the original prompt and all three model responses, reproduces each raw response verbatim under labeled section headers (`=== {model_id} ===`), then delivers a structured qualitative evaluation.
- **Key conventions:** The evaluator is instructed to be *neutral*; raw reproduction before evaluation prevents cherry-picking; three explicit evaluation axes (accuracy, conciseness, production recommendation) ensure consistent output structure across runs. No sentinel tokens or numeric scores — evaluation is narrative prose.

### 5. Control Flow

1. **Initialization** — Workflow receives `@prompt` and three model ID inputs (with defaults applied where omitted).
2. **Parallel fan-out** — Three GENERATE calls execute concurrently via the WITH/CTE construct; each captures its model's answer into a dedicated `@answer_N` variable.
3. **Judgment** — A single GENERATE call to `compare_models` consumes all collected answers and produces `@comparison`.
4. **Termination (success)** — RETURN delivers `@comparison` with `status='complete'` and the three model IDs as metadata. This is a non-trivial RETURN status signaling successful pipeline completion.
5. **Termination (failure)** — If any GENERATE raises `GenerationError`, the EXCEPTION handler short-circuits to a RETURN with a diagnostic message and `status='error'`.

There are no loops (no WHILE) and no conditional branches (no EVALUATE); the workflow is a linear fan-out → collect → judge → return pipeline.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Run any prompt against three configurable AWS Bedrock models \
  in parallel and return a structured comparison that identifies the most accurate, most \
  concise, and most production-suitable response." --mode workflow

# Step 2 — compile to any target
spl3 splc compile bedrock_quickstart.spl --lang python/pocketflow
spl3 splc compile bedrock_quickstart.spl --lang python/langgraph
spl3 splc compile bedrock_quickstart.spl --lang go
```