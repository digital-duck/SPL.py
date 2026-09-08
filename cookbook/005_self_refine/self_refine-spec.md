## 0. High-level Description

This workflow implements the **self-refine** pattern, an iterative quality-improvement loop in which a writer model produces an initial draft and a separate critic model repeatedly evaluates it until the output meets a quality bar or a resource limit is reached. Three CREATE FUNCTIONs define the prompt templates: `draft` primes an expert-writer persona to respond to an open-ended task; `critique` primes a strict-critic persona and uses the sentinel token `[APPROVED]` as an unambiguous signal that no further work is needed; and `refine` re-invokes the expert-writer persona with both the current draft and the critique to produce an improved version. Control flow is governed by a WHILE loop bounded by `@max_iterations`, and within each iteration an EVALUATE branch inspects `@feedback` for the `[APPROVED]` sentinel — triggering an early RETURN with `status='complete'` if found, or incrementing the counter and calling `refine` otherwise; if the loop exhausts its iterations the workflow falls through to a RETURN with `status='max_iterations'`. A **multi-model design** is central: `@writer_model` (defaulting to `gemma3`) drives all GENERATE calls to `draft` and `refine`, while `@critic_model` (defaulting to `llama3.2`) drives GENERATE calls to `critique`. Every draft, feedback round, and final output is persisted via CALL `write_file` into a configurable `@log_dir`, and LOGGING statements at INFO, DEBUG, and WARN levels trace the workflow's progress; two EXCEPTION handlers catch `MaxIterationsReached` (saves best-effort output) and `BudgetExceeded` (returns whatever exists with `status='budget_limit'`).

---

## 1. Purpose

Automatically refines a written response to a user-supplied task by alternating between a writer LLM and a critic LLM until the critic approves the output or iteration/budget limits are hit.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@task` | `'What are the benefits of meditation?'` | The writing task or question the workflow should address |
| `@output_budget` | `2000` | Maximum tokens allowed per GENERATE call |
| `@max_iterations` | `3` | Maximum number of critique–refine cycles before halting |
| `@writer_model` | `'gemma3'` | Model used for `draft` and `refine` GENERATE calls |
| `@critic_model` | `'llama3.2'` | Model used for `critique` GENERATE calls |
| `@log_dir` | `'cookbook/05_self_refine/logs-spl'` | Directory path where intermediate and final files are written |

---

## 3. Process

1. Initialize `@iteration` to `0` and emit an INFO log announcing the start of the workflow.
2. GENERATE an initial draft by calling `draft(@task)` with `@writer_model`, storing the result in `@current`. Log "Initial draft ready" at INFO.
3. CALL `write_file` to save `@current` to `{@log_dir}/draft_0.md`.
4. Enter the WHILE loop, which continues as long as `@iteration < @max_iterations`.
5. Inside each loop iteration, log "critiquing" at DEBUG, then GENERATE a critique by calling `critique(@current)` with `@critic_model`, storing the result in `@feedback`.
6. CALL `write_file` to save `@feedback` to `{@log_dir}/feedback_{@iteration}.md`.
7. EVALUATE `@feedback`:
   - **If it contains `[APPROVED]`**: log approval at INFO, CALL `write_file` to save `@current` to `{@log_dir}/final.md`, then RETURN `@current` with `status='complete'` and `iterations=@iteration`.
   - **Otherwise**: increment `@iteration` by 1, GENERATE a refined draft by calling `refine(@current, @feedback)` with `@writer_model` into `@current`, log "Refined" at DEBUG, and CALL `write_file` to save `@current` to `{@log_dir}/draft_{@iteration}.md`. Return to step 4.
8. If the WHILE loop completes without approval, log a WARN that max iterations were reached, CALL `write_file` to save `@current` to `{@log_dir}/final.md`, and RETURN `@current` with `status='max_iterations'` and `iterations=@iteration`.

---

## 4. Error Handling

- **`MaxIterationsReached`**: CALL `write_file` to persist `@current` to `{@log_dir}/final.md`, then RETURN `@current` with `status='partial'` (best-effort result saved).
- **`BudgetExceeded`**: RETURN `@current` immediately (no file write) with `status='budget_limit'` (preserves whatever partial output exists at the time the budget is exhausted).

---

## 5. Output

The workflow returns `@result TEXT` — the best available draft text — along with structured metadata:

| Field | Possible Values | Meaning |
|---|---|---|
| `status` | `'complete'` | Critic approved the draft before max iterations |
| `status` | `'max_iterations'` | Loop exhausted without critic approval |
| `status` | `'partial'` | `MaxIterationsReached` exception caught |
| `status` | `'budget_limit'` | `BudgetExceeded` exception caught |
| `iterations` | integer ≥ 0 | Number of critique–refine cycles completed (present on `complete` and `max_iterations`) |