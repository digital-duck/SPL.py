## Summary

This workflow sends a single user-supplied prompt to three Azure OpenAI deployments simultaneously, then asks a fourth LLM call to compare and rank all three responses. It exists to help Azure customers validate quality and cost tradeoffs between GPT tiers — for example, GPT-4o versus GPT-4o-mini versus GPT-3.5-Turbo — without running separate scripts or manual experiments. The primary audience is ML engineers and solution architects deciding which Azure deployment tier best fits a production use case.

---

## Detailed Specification

### 1. Purpose

Dispatches a single prompt to three configurable Azure OpenAI deployments in parallel and returns a structured comparative evaluation covering accuracy, clarity, and cost-effectiveness, concluding with a production deployment recommendation.

---

### 2. High-level Description

The workflow implements a **fan-out / compare** pattern against the `azure_openai` adapter. On entry it accepts four INPUT variables: the prompt text and three deployment names, defaulting to `gpt-4o`, `gpt-4o-mini`, and `gpt-35-turbo`. The parallel fan-out is expressed with a `WITH … SELECT … INTO` construct — equivalent to `CALL PARALLEL` — that dispatches three simultaneous GENERATE calls, each targeting a distinct deployment via `USING MODEL @deployment_N`, and binds their results into `@answer_1`, `@answer_2`, and `@answer_3`. After the parallel phase completes, a single GENERATE call invokes the `compare_deployments` CREATE FUNCTION, which receives all three prompt/answer pairs and produces a structured evaluation, concluding with a "best fit for production" verdict. The workflow exits via RETURN WITH `status='complete'`, carrying the three deployment names as metadata so callers can correlate results. An EXCEPTION handler for `GenerationError` intercepts any deployment-level failure and exits with `status='error'` plus a human-readable diagnostic string.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW azure_openai_quickstart` | `WORKFLOW` | Named, parameterized entry point with INPUT / OUTPUT declarations |
| `CREATE FUNCTION compare_deployments(...)` | `CREATE FUNCTION` | Prompt template with 7 parameter slots; consumed by the comparison GENERATE step |
| `WITH … SELECT … INTO @answer_1, @answer_2, @answer_3` | `CALL PARALLEL` / parallel GENERATE | Fan-out: three simultaneous LLM calls, each routed to a different deployment via `USING MODEL` |
| `GENERATE compare_deployments(...) INTO @comparison` | `GENERATE … INTO @var` | Single sequential LLM call; invokes the compare_deployments function template |
| `RETURN @comparison WITH status='complete'` | `RETURN WITH status=` | Non-trivial: distinguishes the success path from the error path for callers |
| `EXCEPTION WHEN GenerationError THEN … WITH status='error'` | `EXCEPTION WHEN ExceptionType THEN` | Catches any deployment-level generation failure; returns diagnostic message with `status='error'` |
| `@prompt`, `@answer_1..3`, `@comparison` | SPL `@vars` | Shared mutable state that threads data from the parallel phase into the sequential comparison phase |

---

### 4. Logical Functions / Prompts

#### `ask_deployment_N` (inline, ×3)

- **Role:** Fan-out probe — sends the user's raw question to one Azure deployment with no preprocessing.
- **System role:** `'You are a helpful, knowledgeable assistant.'` — identical across all three calls.
- **Output format:** Free-form answer text, bound to `@answer_N`.
- **Key convention:** The exact same `@prompt` is sent to every deployment; only `USING MODEL @deployment_N` differs, isolating the variable under test.

#### `compare_deployments`

- **Role:** Judge — evaluates all three answers against structured criteria and recommends a deployment tier.
- **Evaluation axes:** Accuracy and completeness · Clarity and conciseness · Cost-effectiveness for the query type.
- **Output format:** Structured prose with labelled sections (`=== {deployment_N} ===`) followed by a concluding production recommendation.
- **Key convention:** Deployment names are injected as section headers so the LLM can reference them by name rather than by position, making the recommendation traceable.

---

### 5. Control Flow

Execution is a single pass with one parallel phase and no loops or branches:

1. **Parallel fan-out** — The `WITH … SELECT … INTO` block dispatches three GENERATE calls concurrently; execution blocks until all three complete and `@answer_1`, `@answer_2`, `@answer_3` are bound.
2. **Sequential comparison** — `GENERATE compare_deployments(…) INTO @comparison` performs one LLM call over the aggregated results.
3. **Termination** — `RETURN @comparison WITH status='complete'` exits the happy path. If any GENERATE step raises `GenerationError` (bad endpoint, invalid API key, missing deployment name), the EXCEPTION handler intercepts and exits with `status='error'` and a diagnostic string instead.

There is no WHILE loop and no EVALUATE branch; this is a strictly linear, single-pass workflow.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 1 as the --description)
spl3 text2spl \
  --description "Send a single user-supplied prompt to three configurable Azure OpenAI deployments in parallel and return a structured comparative evaluation of their responses, covering accuracy, clarity, and cost-effectiveness, concluding with a production deployment recommendation. Handle generation failures with a typed EXCEPTION handler." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile azure_openai_quickstart.spl --lang python/pocketflow
spl3 splc compile azure_openai_quickstart.spl --lang python/langgraph
spl3 splc compile azure_openai_quickstart.spl --lang go
```