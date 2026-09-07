## Summary

This workflow sends a single user-supplied prompt simultaneously to three Google Gemini model tiers — Pro, Flash, and Lite — hosted on Google Cloud Vertex AI, then uses a fourth LLM call to evaluate and compare the three responses. It exists to help engineering teams quickly benchmark quality, latency, and cost trade-offs before committing to a model tier in production. Any developer or architect evaluating Vertex AI for a new use case benefits directly from the side-by-side comparison and deployment recommendation it produces.

---

## Detailed Specification

### 1. Purpose

Fan out a single prompt to three Gemini model tiers on Vertex AI in parallel, then synthesize a structured quality-versus-cost comparison and production deployment recommendation.

---

### 2. High-level Description

The WORKFLOW `vertex_quickstart` accepts a user prompt and three optional model identifiers (defaulting to `gemini-2.5-pro`, `gemini-2.5-flash`, and `gemini-2.0-flash-lite`) and produces a single comparison report as its OUTPUT variable `@comparison`. The core technique is a parallel fan-out: three independent GENERATE calls are issued concurrently as SQL-style CTEs, each targeting a different Gemini tier with the same system role ("You are a helpful, knowledgeable assistant.") and the user's prompt, storing results into `@answer_pro`, `@answer_flash`, and `@answer_lite`. Once all three responses are collected, a single sequential GENERATE call invokes the `compare_tiers` CREATE FUNCTION, which receives all three model names and their answers and instructs the LLM to evaluate accuracy, depth, conciseness, and cost-effectiveness before issuing a production deployment recommendation. Because the workflow is single-pass with no branching or retry logic, control flow is linear after the fan-out: parallel generation → sequential comparison → RETURN. The RETURN carries non-trivial metadata (`status='complete'`, plus the three resolved model names) so callers can inspect which tier variants were actually used. An EXCEPTION handler catches any `GenerationError` raised by the Vertex AI adapter — covering misconfigured projects, missing IAM permissions, or a disabled API — and returns a human-readable error string with `status='error'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW vertex_quickstart` | `WORKFLOW <name>` | Declares the named orchestration workflow with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION compare_tiers(...)` | `CREATE FUNCTION <name>` | Reusable prompt template with `{param}` slots for all three model names and answers |
| Parallel `WITH ... CTEs` (ask_pro, ask_flash, ask_lite) | `GENERATE <fn>(...) INTO @<var>` × 3, parallel | Three concurrent LLM calls, each `USING MODEL @model_*`; results collected via `INTO @answer_pro, @answer_flash, @answer_lite` |
| `GENERATE compare_tiers(...) INTO @comparison` | `GENERATE <fn>(...) INTO @<var>` | Sequential LLM call after fan-out completes |
| `RETURN @comparison WITH status='complete', model_pro=..., ...` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial return: `status='complete'` plus resolved model identifiers surfaced as metadata |
| `EXCEPTION WHEN GenerationError THEN ... WITH status='error'` | `EXCEPTION WHEN <Type> THEN ...` | Catches Vertex AI adapter errors; returns `status='error'` so callers can distinguish failure from success |
| `@prompt`, `@model_pro`, `@answer_pro`, `@comparison`, etc. | Shared state `@<var>` | Workflow-scoped variables threaded across all steps |

---

### 4. Logical Functions / Prompts

#### `ask_pro` / `ask_flash` / `ask_lite` (inline, no CREATE FUNCTION)

- **Role**: Each is an inline GENERATE within a named CTE. All three share the same system role and accept `@prompt` verbatim; they differ only in the `USING MODEL` clause.
- **Key prompt conventions**: System role is fixed — `"You are a helpful, knowledgeable assistant."` — keeping all three calls on equal footing so responses are directly comparable. No sentinel tokens or structured output format is enforced; raw natural-language answers are expected.

#### `compare_tiers` (CREATE FUNCTION)

- **Role**: The synthesis and evaluation step. Receives all six pieces of data — prompt, three model names, three answers — and produces a single free-form report.
- **Key prompt conventions**: Each model's response is delimited by a labeled section header (`=== {model_pro} (Pro — highest capability) ===`, etc.) to visually separate tiers for the evaluating LLM. The evaluation criteria are enumerated explicitly (accuracy/depth, conciseness, best value per query type). The prompt closes with a directive to conclude with a concrete production deployment recommendation, nudging the model toward a decisive output rather than an open-ended comparison.

---

### 5. Control Flow

1. **Initialization**: Workflow starts with four INPUT variables (`@prompt`, `@model_pro`, `@model_flash`, `@model_lite`), each with a default value, so the workflow is runnable with zero arguments.
2. **Parallel fan-out**: Three GENERATE calls execute concurrently (CTE semantics). There is no WHILE loop and no EVALUATE branch — all three calls are always made.
3. **Result collection**: The parallel block resolves into `@answer_pro`, `@answer_flash`, `@answer_lite` via a single `INTO` clause.
4. **Sequential comparison**: One GENERATE call invokes `compare_tiers` with all collected data, storing the result in `@comparison`.
5. **Termination**: `RETURN @comparison WITH status='complete'` closes the happy path, surfacing model identifiers as metadata. The `EXCEPTION WHEN GenerationError` handler intercepts any Vertex AI failure at any point and returns a diagnostic string with `status='error'`, terminating the workflow without re-raising.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile vertex_quickstart.spl --lang python/pocketflow
spl3 splc compile vertex_quickstart.spl --lang python/langgraph
spl3 splc compile vertex_quickstart.spl --lang go
```