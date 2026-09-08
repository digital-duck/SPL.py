## Summary

This workflow sends a single user-supplied prompt to three Azure OpenAI deployments simultaneously and then asks a fourth LLM call to evaluate and rank the three responses. It exists to help platform engineers and AI teams objectively compare GPT model tiers — such as GPT-4o, GPT-4o-mini, and GPT-3.5-Turbo — deployed in their own Azure subscription before committing to one in production. The output is a structured written verdict covering accuracy, clarity, and cost-effectiveness.

---

## Detailed Specification

### 1. Purpose

Execute a single prompt against three configurable Azure OpenAI deployments in parallel, then produce a comparative evaluation identifying which deployment best suits the query type for production use.

---

### 2. High-level Description

The `azure_openai_quickstart` WORKFLOW accepts four runtime inputs: a `@prompt` string and three Azure deployment names (`@deployment_1`, `@deployment_2`, `@deployment_3`), all with sensible defaults. The workflow opens with a parallel fan-out step implemented as three concurrent GENERATE calls — one per deployment — each invoking a `system_role` of helpful assistant before forwarding `@prompt`; the results land in `@answer_1`, `@answer_2`, and `@answer_3` respectively. Once all three responses are collected, a second GENERATE call invokes the `compare_deployments` CREATE FUNCTION, which constructs a structured evaluation prompt containing all three deployment names, their answers, and explicit scoring criteria (accuracy and completeness, clarity and conciseness, and cost-effectiveness), producing a plain-text verdict in `@comparison`. Control flow is strictly linear — there is no WHILE loop or EVALUATE branch — and the workflow terminates with a RETURN that carries `status='complete'` alongside the three deployment names as metadata. An EXCEPTION handler catches any `GenerationError` (e.g., bad endpoint, invalid API key, or missing deployment name) and returns a diagnostic message with `status='error'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW azure_openai_quickstart` | `WORKFLOW <name>` | Declares the named orchestration entry point with typed `INPUT` / `OUTPUT` blocks |
| `CREATE FUNCTION compare_deployments(...)` | `CREATE FUNCTION <name>` | Reusable prompt template with eight `{param}` slots; returns TEXT |
| Parallel `WITH ... AS (PROMPT ... GENERATE ...)` | `GENERATE <fn>(...) INTO @<var>` | Three concurrent GENERATE calls fanned out via CTE syntax; each targets a different `USING MODEL` |
| `GENERATE compare_deployments(...) INTO @comparison` | `GENERATE <fn>(...) INTO @<var>` | Sequential aggregation call after fan-out resolves |
| `@prompt`, `@answer_1/2/3`, `@comparison` | Shared-state `@<var>` | Workflow-scoped variables passed between steps |
| `RETURN @comparison WITH status='complete', ...` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'complete'` plus deployment-name metadata |
| `EXCEPTION WHEN GenerationError THEN ... WITH status='error'` | `EXCEPTION WHEN <Type> THEN ...` | Catches deployment/auth failures; emits `status='error'` |

---

### 4. Logical Functions / Prompts

**`ask_deployment_1 / ask_deployment_2 / ask_deployment_3`** (inline, not named functions)
- **Role:** Fan-out generation nodes; each issues the verbatim user prompt to one Azure deployment.
- **Key conventions:** Fixed `system_role` of `"You are a helpful, knowledgeable assistant."` applied uniformly across all three; model identity is controlled entirely by `USING MODEL @deployment_N`, making deployment selection a runtime parameter rather than a hard-coded model name.

**`compare_deployments`** (CREATE FUNCTION)
- **Role:** Aggregator and judge; receives all three (deployment-name, answer) pairs and renders a structured verdict.
- **Key prompt conventions:** Section headers use `=== {deployment_N} ===` as sentinel delimiters to visually separate answers. The rubric is explicit and ordered: (1) accuracy and completeness, (2) clarity and conciseness, (3) cost-effectiveness. The function concludes by asking for a production recommendation, steering the LLM toward a decisive output rather than an open-ended comparison.

---

### 5. Control Flow

1. **Initialization** — Runtime inputs are bound: `@prompt` (default: `'Explain the CAP theorem in two sentences.'`), `@deployment_1` (`gpt-4o`), `@deployment_2` (`gpt-4o-mini`), `@deployment_3` (`gpt-35-turbo`).
2. **Parallel fan-out** — Three GENERATE calls execute concurrently via CTE semantics; each forwards `@prompt` to its respective Azure deployment. All three must resolve before execution advances.
3. **Sequential aggregation** — A single GENERATE call invokes `compare_deployments`, consuming the three answers and producing `@comparison`.
4. **Termination** — RETURN emits `@comparison` with `status='complete'` and the three deployment names as metadata. No loops or conditional branches exist in the happy path.
5. **Error path** — Any `GenerationError` at any stage short-circuits to the EXCEPTION handler, which returns a diagnostic string with `status='error'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 above as text2spl input)
spl3 text2spl \
  --description "Execute a single prompt against three configurable Azure OpenAI deployments \
in parallel, then produce a comparative evaluation identifying which deployment best suits \
the query type for production use. The workflow fans out a prompt to three concurrent GENERATE \
calls each targeting a different USING MODEL, collects results into @answer_1/2/3, then calls \
a compare_deployments CREATE FUNCTION that evaluates accuracy, clarity, and cost-effectiveness \
and recommends one deployment. A RETURN WITH status='complete' closes the happy path; an \
EXCEPTION WHEN GenerationError returns status='error'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile azure_openai_quickstart.spl --lang python/pocketflow
spl3 splc compile azure_openai_quickstart.spl --lang python/langgraph
spl3 splc compile azure_openai_quickstart.spl --lang go
```