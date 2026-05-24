## Summary

Plan and Execute is an agentic workflow that breaks a complex, open-ended task into discrete numbered steps using a planner LLM call, then drives each step through an executor that carries forward the accumulated results as context. A built-in validation gate after each step allows the workflow to detect failures and trigger a full re-plan before continuing, ensuring the final synthesized report reflects only validated work. This pattern benefits engineers and technical leads who need to automate multi-stage technical tasks — such as API design, CI/CD setup, or database migrations — without manual checkpointing.

---

## Detailed Specification

### 1. Purpose

Decompose an arbitrary complex technical task into a validated, sequentially executed plan and synthesize the results into a coherent final report.

---

### 2. High-level Description

The `plan_and_execute` WORKFLOW accepts a single TEXT input `@task` and produces a TEXT output `@final_report`. It opens with two GENERATE calls: `plan` decomposes the task into a numbered list of steps stored in `@plan`, and `count_steps` parses that list to produce a numeric `@step_count` that gates the main loop. A WHILE loop indexed by `@step_index` drives sequential execution: for each iteration, `extract_step` pulls the current step from `@plan`, `execute_step` runs it with the accumulated `@results` as prior context, and `validate_step` judges the output. An EVALUATE on `@validation` branches on the sentinel token `'failed'`: on failure, `replan` regenerates `@plan` for the remaining work, `count_steps` recalculates the bound, and both `@step_index` and `@results` reset to restart execution from scratch; on success, the step result is appended to `@results` and `@step_index` advances. After the loop, `synthesize` combines `@task` and `@results` into `@final_report`, and the workflow RETURNs with `status='complete'` and `steps_executed=@step_index`. Two EXCEPTION handlers cover `MaxIterationsReached` (partial synthesis) and `BudgetExceeded` (immediate return of raw results).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW plan_and_execute` | `WORKFLOW` | Top-level named orchestration unit with `INPUT`/`OUTPUT` declarations |
| `plan(...)` | `CREATE FUNCTION plan` | Prompt template: decomposes `@task` into a numbered step list |
| `count_steps(...)` | `CREATE FUNCTION count_steps` | Prompt template: parses `@plan` and returns a numeric count |
| `extract_step(...)` | `CREATE FUNCTION extract_step` | Prompt template: extracts step `@step_index` from `@plan` |
| `execute_step(...)` | `CREATE FUNCTION execute_step` | Prompt template: runs one step with `@results` as rolling context |
| `validate_step(...)` | `CREATE FUNCTION validate_step` | Prompt template: judges step output; emits sentinel token `'failed'` or passes |
| `replan(...)` | `CREATE FUNCTION replan` | Prompt template: regenerates `@plan` from the failure point |
| `synthesize(...)` | `CREATE FUNCTION synthesize` | Prompt template: merges all `@results` into a final narrative report |
| `GENERATE ... INTO @var` | `GENERATE` | Every LLM call; result bound to a named variable |
| `WHILE @step_index < @step_count DO` | `WHILE` | Loop bounded by LLM-derived step count; exits when all steps validated |
| `EVALUATE @validation WHEN 'failed'` | `EVALUATE` | Semantic branch on sentinel token; drives re-plan vs. advance |
| `@results`, `@step_index`, `@plan`, `@step_count` | SPL `@vars` | Shared mutable state threaded through all GENERATE calls |
| `RETURN ... WITH status='complete'` | `RETURN WITH` | Non-trivial status token drives external caller branching |
| `RETURN ... WITH status='partial'` | `RETURN WITH` | Emitted by `MaxIterationsReached` handler; signals incomplete output |
| `RETURN ... WITH status='budget_limit'` | `RETURN WITH` | Emitted by `BudgetExceeded` handler; signals cost cutoff |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION` | Typed handler: partial synthesis on loop runaway |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION` | Typed handler: hard stop on cost limit |

---

### 4. Logical Functions / Prompts

**`plan`**
- Role: Phase 1 planner — transforms the raw `@task` into a structured, numbered list of actionable steps.
- Key conventions: output must be a numbered list (e.g. `1. ... 2. ...`) so that `count_steps` and `extract_step` can parse it deterministically; no prose preamble.

**`count_steps`**
- Role: Counts the steps in `@plan` and returns a single integer used as the WHILE loop bound.
- Key conventions: output is a bare integer with no surrounding text; called once at plan time and again after every re-plan.

**`extract_step`**
- Role: Retrieves step number `@step_index` from `@plan` as an isolated instruction string.
- Key conventions: takes both `@plan` and `@step_index`; output is a single step description with no list prefix.

**`execute_step`**
- Role: Carries out one plan step, using `@results` (all prior validated outputs) as rolling context to maintain continuity.
- Key conventions: prompt includes both the step instruction and the accumulated `@results` block; output is free-form technical content representing completed work.

**`validate_step`**
- Role: Quality gate — evaluates whether `@step_result` satisfactorily addresses `@current_step`.
- Key conventions: must emit the sentinel token `'failed'` anywhere in its output to trigger the EVALUATE branch; any other output (e.g. `'passed'`, `'ok'`) is treated as success.

**`replan`**
- Role: Recovery planner — given the original `@task`, the failed `@plan`, the failure index `@step_index`, and the bad `@step_result`, generates a revised plan for the remaining work.
- Key conventions: output is a fresh numbered list in the same format as `plan`; the entire `@plan` is replaced and execution restarts from step 0.

**`synthesize`**
- Role: Phase 4 narrator — merges `@task` and the full `@results` log into a coherent, human-readable final report.
- Key conventions: called both on clean completion and inside the `MaxIterationsReached` exception handler (producing a partial report); prompt should instruct the LLM to acknowledge any incomplete steps when called from the exception path.

---

### 5. Control Flow

Execution starts with sequential GENERATE calls to `plan` and `count_steps`, initializing `@step_index = 0` and `@results = ''`. The WHILE loop runs while `@step_index < @step_count`. Inside each iteration, three GENERATE calls run in order — `extract_step`, `execute_step`, `validate_step` — and the EVALUATE on `@validation` branches:

- **`'failed'` branch**: `replan` and `count_steps` regenerate the plan; `@step_index` and `@results` reset to 0 and `''`; the loop restarts from the beginning.
- **Else branch**: the step result is appended to `@results` with a Markdown heading, and `@step_index` increments.

When the loop exits naturally, `synthesize` produces `@final_report` and the workflow RETURNs with `status='complete'` and `steps_executed=@step_index`. If the loop hits the system iteration ceiling, `MaxIterationsReached` fires: `synthesize` is called on whatever partial `@results` exist and the workflow RETURNs with `status='partial'`. If the cost ceiling is hit at any point, `BudgetExceeded` fires and `@results` is returned directly with `status='budget_limit'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Decompose an arbitrary complex technical task into a validated, sequentially executed plan and synthesize the results into a coherent final report." --mode workflow

# Step 2 — compile to any target
spl3 splc compile plan_and_execute.spl --lang python/pocketflow
spl3 splc compile plan_and_execute.spl --lang python/langgraph
spl3 splc compile plan_and_execute.spl --lang go
```