## Summary

This workflow implements a **plan-and-execute** agentic pattern: given a complex open-ended task, an LLM first decomposes it into numbered steps, then executes each step sequentially while accumulating results, and finally synthesizes a structured report. If any step fails validation, the workflow replans from scratch rather than silently skipping the failure. Engineers and product teams building autonomous task-completion agents benefit from this pattern when tasks are too complex for a single LLM call.

---

## Detailed Specification

### 1. Purpose

Decompose a complex user-specified task into an ordered plan, execute each step with accumulated context, validate output quality, replan on failure, and return a synthesized final report with execution metadata.

---

### 2. High-level Description

The `plan_and_execute` WORKFLOW accepts a single TEXT input `@task` and produces a `@final_report` TEXT output. It operates in four phases driven by GENERATE calls and a WHILE loop. In Phase 1, the `plan` function decomposes `@task` into a numbered list of steps stored in `@plan`; the `count_steps` function then parses `@plan` to extract a numeric `@step_count` that controls the loop bound. Phase 2 enters a WHILE loop over `@step_index` from 0 to `@step_count - 1`: for each iteration, `extract_step` pulls the current step text from the plan, `execute_step` runs it against the accumulated `@results` string for context, and `validate_step` assesses whether the output is acceptable. An EVALUATE on the validation output branches on the sentinel token `'failed'`: on failure, `replan` rewrites the entire plan given the failing step and its output, `count_steps` recalculates the bound, and `@step_index` and `@results` reset to zero, restarting execution from the top of the new plan; on any other validation outcome, the step result is appended to `@results` and `@step_index` increments. Phase 3, after the loop completes, calls `synthesize` to merge `@task` and `@results` into `@final_report`, returned with `status='complete'` and a `steps_executed` count. EXCEPTION handlers for `MaxIterationsReached` and `BudgetExceeded` provide graceful degradation by synthesizing a partial report or returning raw results respectively.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW plan_and_execute` | `WORKFLOW` | Top-level orchestration; INPUT `@task TEXT`, OUTPUT `@final_report TEXT` |
| `plan(@task)` | `CREATE FUNCTION plan` | Decomposes task into a numbered step list |
| `count_steps(@plan)` | `CREATE FUNCTION count_steps` | Parses plan text; returns numeric count for loop bound |
| `extract_step(@plan, @step_index)` | `CREATE FUNCTION extract_step` | Retrieves step N from plan text by index |
| `execute_step(@current_step, @results)` | `CREATE FUNCTION execute_step` | Runs one step with prior results as context |
| `validate_step(@current_step, @step_result)` | `CREATE FUNCTION validate_step` | Emits sentinel `'failed'` or a passing token |
| `replan(@task, @plan, @step_index, @step_result)` | `CREATE FUNCTION replan` | Rewrites plan from failure point; returns new plan text |
| `synthesize(@task, @results)` | `CREATE FUNCTION synthesize` | Merges task goal and all step results into final report |
| `WHILE @step_index < @step_count DO` | `WHILE` | Iterates over plan steps; bound is dynamic (replan resets it) |
| `EVALUATE @validation WHEN 'failed'` | `EVALUATE` | Branches on sentinel token; drives replan-or-advance logic |
| `RETURN @final_report WITH status='complete'` | `RETURN` | Non-trivial: carries `steps_executed` count and terminal status |
| `RETURN @final_report WITH status='partial'` | `RETURN` | Non-trivial: degraded exit from `MaxIterationsReached` handler |
| `RETURN @results WITH status='budget_limit'` | `RETURN` | Non-trivial: hard-stop exit from `BudgetExceeded` handler |
| `@step_index`, `@results`, `@plan`, `@step_count` | Shared `@vars` | Mutable workflow state across GENERATE calls and loop iterations |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION` | Triggers synthesize on partial results; emits `status='partial'` |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION` | Returns raw accumulated results; emits `status='budget_limit'` |

---

### 4. Logical Functions / Prompts

**`plan`**
- Role: Task decomposition. Converts an open-ended `@task` string into an ordered, numbered list of actionable sub-steps.
- Conventions: Output must be a numbered list parseable by `count_steps` and `extract_step`; each line represents one discrete step.

**`count_steps`**
- Role: Plan parser. Reads `@plan` text and returns a bare integer representing the total number of steps.
- Conventions: Output is a single integer token; no surrounding prose, to allow direct numeric comparison in the WHILE condition.

**`extract_step`**
- Role: Step retrieval. Given `@plan` and a zero-based `@step_index`, returns the text of step N.
- Conventions: Index is passed as a parameter; output is a single step description string.

**`execute_step`**
- Role: Step executor. Carries out `@current_step` using `@results` as accumulated context from prior steps.
- Conventions: May produce prose, code, commands, or artifacts depending on domain; output is appended verbatim to `@results`.

**`validate_step`**
- Role: Quality gate. Assesses whether `@step_result` adequately addresses `@current_step`.
- Conventions: Must emit the sentinel token `'failed'` on failure; any other output (e.g., `'passed'`, `'ok'`) is treated as success by the EVALUATE branch.

**`replan`**
- Role: Recovery planner. Given the original `@task`, current `@plan`, the failing `@step_index`, and `@step_result`, produces a revised numbered plan.
- Conventions: Returns a complete replacement plan (not a diff); `count_steps` is called immediately after to recalibrate the loop bound.

**`synthesize`**
- Role: Report generator. Combines `@task` (original goal) with `@results` (all step outputs) into a coherent final deliverable.
- Conventions: Called both on successful completion and in the `MaxIterationsReached` exception handler; must tolerate incomplete `@results`.

---

### 5. Control Flow

1. **Initialization**: `@step_index` is set to `0`; `@results` is set to empty string.
2. **Planning**: `plan(@task)` → `@plan`; `count_steps(@plan)` → `@step_count`.
3. **Execution loop** (`WHILE @step_index < @step_count`):
   - `extract_step` retrieves step N; `execute_step` runs it; `validate_step` evaluates output.
   - **EVALUATE branch on `'failed'`**: `replan` rewrites `@plan`, `count_steps` refreshes `@step_count`, `@step_index` and `@results` reset to `0`/`''` — loop restarts from step 0 of the new plan.
   - **EVALUATE else**: step result appended to `@results`, `@step_index` incremented — loop continues.
4. **Synthesis**: `synthesize(@task, @results)` → `@final_report`. RETURN WITH `status='complete'`, `steps_executed=@step_index`.
5. **Exception — `MaxIterationsReached`**: fires if the WHILE loop guard is exceeded by the runtime; `synthesize` is called on partial `@results`, RETURN WITH `status='partial'`.
6. **Exception — `BudgetExceeded`**: fires on token/cost budget exhaustion; RETURN raw `@results` WITH `status='budget_limit'`, skipping synthesis.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile plan_and_execute.spl --lang python/pocketflow
spl3 splc compile plan_and_execute.spl --lang python/langgraph
spl3 splc compile plan_and_execute.spl --lang go
```