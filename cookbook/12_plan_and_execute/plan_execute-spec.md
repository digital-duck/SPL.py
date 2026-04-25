## 0. High-level Description

This workflow implements a **plan-and-execute** agentic pattern in which a planner LLM first decomposes a software engineering task into a numbered list of steps, and then an executor LLM carries out each step one at a time before finally generating runnable source files. The planning phase uses the `plan` FUNCTION to produce a structured implementation roadmap (3–6 steps, no prose), and a two-step `count_steps`/`extract_step` function pair enables the WHILE loop to iterate over each step by integer index. Each iteration calls `execute_step` (which produces a brief design-note and file list, deliberately withholding code) and immediately calls `validate_step`, a binary classifier that returns the sentinel token `"passed"` or `"failed"`; a nested EVALUATE branch on the validation result either advances the index or triggers a `replan` call that regenerates the tail of the plan from the failed step onward, resetting `@step_index` to zero and restarting the loop — subject to a `@max_replans` guard that accepts a step as-is once the limit is hit. Code generation is deferred entirely to a second WHILE loop (Phase 5), which uses `outline_files`/`count_files`/`extract_file` to enumerate every source file and calls `generate_file` once per file (one LLM call per file to avoid truncation), enforcing a fenced-code-block format with a mandatory `# filename:` comment on the first line inside the fence; each generated file is immediately persisted via the `write_code_files` CALL side-effect tool. A pervasive LOGGING strategy emits INFO at phase boundaries, DEBUG for per-step and per-file progress, and WARN on validation failures and replan exhaustion; all intermediate artefacts (plan, per-step notes, final report) are also written to `@log_dir` via `write_file` CALLs. Two EXCEPTION handlers provide graceful degradation: `MaxIterationsReached` triggers a partial summarize-and-return, while `BudgetExceeded` returns whatever accumulated results exist immediately.

---

## 1. Purpose

Given a plain-English software task, automatically produce a validated implementation plan, step-by-step design notes, and a full set of generated, runnable source files written to disk.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@task` | `'Build a REST API for a todo app'` | Plain-English description of the software task to implement |
| `@output_dir` | `''` (empty) | Filesystem path where generated source files are written; if empty, files are not written to disk |
| `@max_steps` | `5` | Upper bound on the number of plan steps the LLM may produce |
| `@max_replans` | `3` | Maximum number of times a failed step may trigger a full replan before being accepted as-is |
| `@log_dir` | `'cookbook/12_plan_and_execute/logs-spl'` | Directory where intermediate artefacts (plan, step notes, final report) are logged as Markdown files |

---

## 3. Process

1. **Initialise** local variables: `@step_index := 0`, `@results := ''`, `@replan_count := 0`. Emit an INFO log with the task string.
2. **Phase 1 — Plan.** Call `GENERATE plan(@task)` to produce a numbered 3–6 step implementation plan. Write the plan to `@log_dir/plan.md` via `write_file`.
3. **Phase 2 — Count steps.** Call `GENERATE count_steps(@plan, @max_steps)` to obtain an integer step count capped at `@max_steps`. Log the count at DEBUG level.
4. **Phase 3 — Step execution loop.** Enter a WHILE loop that runs while `@step_index < @step_count`:
   1. Extract the current step text with `GENERATE extract_step(@plan, @step_index)`.
   2. Produce a brief design note and file list with `GENERATE execute_step(@current_step, @results)`.
   3. Validate the design note with `GENERATE validate_step(@current_step, @step_result)` — expects `"passed"` or `"failed"`.
   4. **EVALUATE `@validation`:**
      - **`"failed"` branch:** Increment `@replan_count`. Log a WARN. Evaluate `@replan_count` against `@max_replans`:
        - **At or above limit:** Log a WARN, accept the step as-is by appending `@step_result` to `@results`, write `step_N.md`, advance `@step_index`.
        - **Below limit:** Call `GENERATE replan(...)` to regenerate the plan from the failed step onward, recount steps, reset `@step_index := 0` and `@results := ''`, and restart the loop.
      - **`ELSE` (passed) branch:** Append step result to `@results`, write `step_N.md` via `write_file`, advance `@step_index`. Log completion at DEBUG level.
5. **Phase 4 — File outline.** After all steps pass, call `GENERATE outline_files(@task, @results)` to enumerate every source file needed (including a mandatory `README.md`). Count entries with `GENERATE count_files(@file_outline)`. Log the file count at INFO level.
6. **Phase 5 — Code generation loop.** Enter a second WHILE loop over `@file_index < @file_count`:
   1. Extract the current file description with `GENERATE extract_file(@file_outline, @file_index)`.
   2. Generate complete, runnable code with `GENERATE generate_file(@task, @results, @current_file)` — output must be a single fenced code block whose first interior line is a `# filename:` comment.
   3. Write the file to `@output_dir` using the `write_code_files` CALL tool; capture the written filename in `@file_written`. Log at DEBUG level.
   4. Advance `@file_index`.
7. **Phase 6 — Summary.** Call `GENERATE summarize(@task, @results, @file_outline)` to produce a 3–5 sentence human-readable summary. Write it to `@log_dir/final_report.md`.
8. **RETURN** `@final_report` with metadata: `status = 'complete'`, `steps_executed = @step_index`, `files_generated = @file_count`.

---

## 4. Error Handling

- **`MaxIterationsReached`** — The workflow calls `GENERATE summarize(...)` on whatever results and file outline have accumulated, then RETURNs `@final_report` with `status = 'partial'` and the current `steps_executed` count, allowing a partial delivery rather than a hard failure.
- **`BudgetExceeded`** — Immediately RETURNs the raw `@results` string (accumulated step notes, no summary, no files) with `status = 'budget_limit'`, halting all further LLM calls to avoid additional cost.
- **Step validation failure + replan exhaustion (inline guard, not an EXCEPTION)** — When `@replan_count >= @max_replans`, the EVALUATE branch accepts the failing step's output as-is rather than looping indefinitely, ensuring the WHILE loop always terminates.

---

## 5. Output

The workflow returns `@final_report` (type `TEXT`), a 3–5 sentence prose summary describing what was built and how to run it.

| Field | Type | Values / Notes |
|---|---|---|
| `status` | string | `'complete'` — all steps executed and all files generated; `'partial'` — interrupted by max iterations; `'budget_limit'` — halted by cost cap |
| `steps_executed` | integer | Number of plan steps that were processed before return |
| `files_generated` | integer | Number of source files generated and written to disk (only present on `'complete'` status) |

In addition, the following artefacts are written to the filesystem as side-effects:
- `@log_dir/plan.md` — the raw implementation plan
- `@log_dir/step_N.md` — one design-note file per executed step
- `@log_dir/final_report.md` — the summary report
- `@output_dir/<filename>` — one runnable source file per entry in the file outline (when `@output_dir` is non-empty)