## Summary

Batch Test is an automated regression harness that runs a fixed set of cookbook recipes against two configurable LLM models simultaneously, then produces a structured PASS/FAIL report. It exists to give developers and CI/CD pipelines a single command that validates model compatibility across multiple prompt patterns at once. Teams adopting new local models (e.g. via Ollama) benefit immediately by seeing which recipes degrade under a new model without running each recipe individually.

---

## Detailed Specification

### 1. Purpose

Execute three representative cookbook recipes against two user-specified LLM models in parallel and return a concise PASS/FAIL report summarising which recipe-model combinations produced coherent output.

---

### 2. High-level Description

The `batch_test` WORKFLOW accepts two model identifiers as INPUT parameters (`@model_1`, `@model_2`) and fans out six LLM calls simultaneously using a parallel CTE block — two models × three recipes (Hello World, Ollama Proxy, Multilingual). Each CTE issues an inline GENERATE call with a purpose-specific system role and prompt, storing its result as a named column. The six results are collected via a single SELECT INTO, binding them into six SPL variables (`@hello_m1`, `@hello_m2`, `@proxy_m1`, `@proxy_m2`, `@multi_m1`, `@multi_m2`). A CREATE FUNCTION named `summarize_results` is then invoked via GENERATE, receiving all six raw outputs alongside the model names and recipe labels; the function's prompt instructs an LLM acting as a test reporter to classify each output as PASS or FAIL based on non-emptiness and coherence, and to emit a final tally line. The result is stored in `@report` and returned via RETURN WITH `status='complete'` and both model names as metadata. A single EXCEPTION handler catches any GenerationError from the parallel fan-out or the summarisation call, returning a fixed error string with `status='error'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW batch_test` | `WORKFLOW` | Top-level orchestration unit with typed INPUT/OUTPUT declarations |
| `INPUT: @model_1, @model_2` | `@var` shared state | Parameterised entry points with DEFAULT values; propagated into every CTE |
| `CREATE FUNCTION summarize_results(...)` | `CREATE FUNCTION` | Reusable prompt template with eleven `{param}` slots; returns TEXT |
| Parallel CTE block (`WITH … SELECT INTO`) | `GENERATE` (fan-out) | Six concurrent inline GENERATE calls; SPL's CTE syntax expresses parallelism |
| `GENERATE summarize_results(...) INTO @report` | `GENERATE <fn>(...) INTO @<var>` | Single aggregating LLM call after fan-out; result bound to output variable |
| `INTO @hello_m1, …, @multi_m2` | `@var` shared state | Six intermediate variables holding raw per-recipe-per-model outputs |
| `RETURN @report WITH status='complete', …` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'complete'` signals successful termination; carries model provenance metadata |
| `EXCEPTION WHEN GenerationError THEN … WITH status='error'` | `EXCEPTION WHEN <Type> THEN` | Catches any generation failure in fan-out or summarisation; emits `status='error'` |

---

### 4. Logical Functions / Prompts

**`summarize_results`**
- **Role:** Aggregating judge — receives all raw LLM outputs and produces the final human-readable report.
- **Key prompt conventions:**
  - System persona: "You are a test reporter."
  - PASS/FAIL criterion stated explicitly: non-empty + coherent = PASS; empty, error, or nonsensical = FAIL.
  - Structured output format enforced in the prompt: one line per recipe-model pair in the form `PASS|FAIL  recipe_name  (model)`.
  - Mandatory summary sentinel: final line must match `"Results: X/Y passed, Z failed"` — this acts as a machine-parseable termination token.
  - Eleven named parameters cover both model names, three recipe labels, and six raw outputs, ensuring the judge has full context without external state.

**Inline CTE prompts (Hello World, Ollama Proxy, Multilingual)**
- **Role:** Minimal smoke-test probes — each issues the simplest valid invocation of its recipe's prompt pattern.
- **Key conventions:**
  - Each CTE supplies a `system_role(...)` clause scoping the model's persona to the recipe under test.
  - Input is deliberately trivial (`'hello'`, `lang='English'`) so that any failure reflects model capability, not prompt complexity.
  - Output column aliases (`greeting`, `answer`, `response`) are recipe-semantic, not generic, to aid readability in the SELECT INTO clause.

---

### 5. Control Flow

1. **Initialisation** — WORKFLOW receives `@model_1` (default `gemma3`) and `@model_2` (default `llama3.2`).
2. **Parallel fan-out** — Six inline GENERATE calls fire concurrently inside the CTE block. There is no branching or looping here; all six run unconditionally.
3. **Collect results** — A single SELECT INTO binds the six CTE output columns into six `@vars`.
4. **Aggregation** — One GENERATE call invokes `summarize_results`, producing `@report`.
5. **Termination** — RETURN WITH `status='complete'` closes the success path; both model names are attached as metadata.
6. **Error path** — If any GENERATE (fan-out or aggregation) raises a GenerationError, the EXCEPTION handler fires and RETURN WITH `status='error'` terminates the workflow immediately with a fixed diagnostic string.

There is no WHILE loop and no EVALUATE branch; control flow is strictly linear with a single exception exit.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Execute three representative cookbook recipes against two
user-specified LLM models in parallel using a CTE fan-out, collect the six raw outputs
into variables, then call a CREATE FUNCTION named summarize_results to produce a
structured PASS/FAIL report. Return the report with status='complete' and model
provenance metadata. On GenerationError return status='error'." --mode workflow

# Step 2 — compile to any target
spl3 splc compile batch_test.spl --lang python/pocketflow
spl3 splc compile batch_test.spl --lang python/langgraph
spl3 splc compile batch_test.spl --lang go

# Step 3 — run directly
spl3 run cookbook/10_batch_test/batch_test.spl --adapter ollama
spl3 run cookbook/10_batch_test/batch_test.spl --adapter ollama \
    model_1=gemma3 model_2=mistral
```