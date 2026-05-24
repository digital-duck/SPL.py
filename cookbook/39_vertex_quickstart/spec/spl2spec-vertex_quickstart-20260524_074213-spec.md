## Summary

This workflow submits an identical prompt to three Google Vertex AI Gemini model tiers—Pro, Flash, and Lite—simultaneously, then asks a fourth LLM call to judge which tier delivered the best quality-to-cost ratio for that specific query. It exists to give engineering teams a fast, repeatable way to decide which Gemini tier to deploy in production. Product managers and ML engineers benefit by seeing all three responses side-by-side with a concrete deployment recommendation.

---

## Detailed Specification

### 1. Purpose

Run the same user prompt concurrently across three Gemini model tiers on Google Vertex AI and produce a comparative evaluation that recommends the best tier for production use.

---

### 2. High-level Description

The workflow `vertex_quickstart` accepts a single user `@prompt` and three configurable model names (`@model_pro`, `@model_flash`, `@model_lite`), all with sensible defaults. It opens a parallel CTE block—equivalent to `CALL PARALLEL`—that fans the prompt out to all three Gemini tiers at the same time, capturing each answer into `@answer_pro`, `@answer_flash`, and `@answer_lite`. Once all three branches complete, a single `GENERATE` call invokes the `CREATE FUNCTION compare_tiers`, which acts as an LLM judge: it receives the original prompt, each model's name, and each model's answer, then scores on accuracy, depth, conciseness, and cost-value before issuing a production deployment recommendation. The result is stored in `@comparison` and returned via `RETURN` with `status = 'complete'` alongside the three model name metadata fields. If any Vertex AI call raises a `GenerationError`—due to missing project credentials, IAM misconfiguration, or a disabled API—the `EXCEPTION WHEN GenerationError` handler returns a descriptive error message with `status = 'error'` instead of crashing.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW vertex_quickstart` | `WORKFLOW` | Top-level named orchestration unit with `INPUT:` / `OUTPUT:` declarations |
| `CREATE FUNCTION compare_tiers(...)` | `CREATE FUNCTION` | Reusable prompt template with `{param}` slots; acts as LLM judge |
| `WITH ... AS (PROMPT ... GENERATE ...)` CTE block | `CALL PARALLEL` | Concurrent fan-out; all three tier calls execute simultaneously via `asyncio.gather` |
| `GENERATE compare_tiers(...) INTO @comparison` | `GENERATE ... INTO @var` | Single LLM call capturing judge output into a workflow variable |
| `@prompt`, `@answer_pro`, `@answer_flash`, `@answer_lite`, `@comparison` | SPL `@vars` | Shared mutable workflow state threaded through all steps |
| `RETURN @comparison WITH status='complete'` | `RETURN @var WITH status=` | Non-trivial terminal status signals clean completion to the caller |
| `EXCEPTION WHEN GenerationError THEN ... WITH status='error'` | `EXCEPTION WHEN ExceptionType` | Typed error recovery; catches Vertex AI credential/API failures |

---

### 4. Logical Functions / Prompts

**Inline tier prompts (`ask_pro`, `ask_flash`, `ask_lite`)**
- **Role**: Identical single-turn generation calls, one per Gemini tier. Each uses the same system role (`You are a helpful, knowledgeable assistant.`) and the same `@prompt` value.
- **Key conventions**: No sentinel tokens, no structured output format. These are pure open-ended generation calls—the output is unstructured prose captured as-is into `@answer_*` variables.
- **Model dispatch**: Each branch is pinned to its own model via `USING MODEL @model_pro / @model_flash / @model_lite`, making the tier comparison concrete and swappable at run time.

**`compare_tiers` (CREATE FUNCTION)**
- **Role**: LLM judge. Receives all three responses and acts as an evaluator, not a generator.
- **Key prompt conventions**:
  - Structures input with labeled sections (`=== {model_pro} (Pro — highest capability) ===`) to make the three outputs unambiguous to the judge model.
  - Defines three explicit evaluation axes: accuracy/depth, conciseness, and cost-value fit.
  - Requires a terminal recommendation sentence naming the tier to deploy in production—providing an actionable, parseable conclusion.
- **Output format**: Free-form prose culminating in a deployment recommendation; no JSON or sentinel tokens required.

---

### 5. Control Flow

```
START
  │
  ├─ [CALL PARALLEL / CTE fan-out]
  │     ├─ ask_pro   → @answer_pro    (USING MODEL @model_pro)
  │     ├─ ask_flash → @answer_flash  (USING MODEL @model_flash)
  │     └─ ask_lite  → @answer_lite   (USING MODEL @model_lite)
  │       (all three execute concurrently; barrier waits for all to complete)
  │
  ├─ GENERATE compare_tiers(...) INTO @comparison
  │
  └─ RETURN @comparison WITH status='complete'

EXCEPTION
  └─ GenerationError → RETURN error message WITH status='error'
```

There is no `WHILE` loop and no `EVALUATE` branch—execution is a single parallel fan-out followed by a single judge call. The only branching is the exception handler. `status='complete'` vs `status='error'` are both non-trivial because a caller composing this workflow must distinguish clean output from a failed Vertex AI call.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl \
  --description "Run the same user prompt concurrently across three Gemini model tiers \
on Google Vertex AI (Pro, Flash, Lite) using a parallel fan-out. Capture each answer, \
then invoke a CREATE FUNCTION judge that evaluates accuracy, conciseness, and \
cost-value fit across all three responses and recommends a production tier. \
Return the comparison with status='complete', or handle GenerationError with status='error'." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile vertex_quickstart.spl --lang python/langgraph
spl3 splc compile vertex_quickstart.spl --lang python/pocketflow
spl3 splc compile vertex_quickstart.spl --lang go
```