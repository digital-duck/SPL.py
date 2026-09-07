## 0. High-level Description

This workflow implements a **Tree of Thought** pattern — a parallel multi-path reasoning technique where several distinct reasoning branches are explored, scored, and either selected or synthesized into a final answer. The workflow is driven by a `@models` LIST input, iterating over each model in a WHILE loop to generate and develop independent reasoning paths; this means the number of models directly controls the branching factor of the tree. Five CREATE FUNCTIONs handle the core reasoning pipeline: `initial_approach` generates a unique high-level path per model, `develop` deepens it with technical detail, `evaluate_path` scores it on a 1–10 numeric-only scale (enforced by a strict output-format constraint in the prompt), `select_best` picks the top path from a JSON map of all results, and `refine_solution` polishes the winner into a deliverable answer; two auxiliary functions — `verify` and `synthesize_all` — drive the post-refinement EVALUATE branch. The EVALUATE construct on `@verification` branches on the sentinel token `'sound'`: a passing verification RETURNs with `status='complete'`, while failure triggers a WARN-level LOG and falls back to `synthesize_all`, aggregating insights from every explored path and RETURNing with `status='synthesized'`. Each developed path is persisted via a CALL to `write_file` under a configurable `@log_dir`, and the final solution is written to `final_solution.md`. EXCEPTION handling covers two resource/quality limits: `BudgetExceeded` returns whatever solution has been computed so far, and `HallucinationDetected` retries with a low temperature (0.1) up to three times.

---

## 1. Purpose

Given a problem statement and a list of LLMs, explore one reasoning path per model, select and refine the best, verify its soundness, and return a polished solution (or a synthesis of all paths if verification fails).

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@problem` | `'Design a sustainable urban transport system.'` | The problem statement to solve |
| `@models` | `['gemma3', 'phi4-mini']` | Ordered list of model identifiers; one reasoning path is generated per entry |
| `@log_dir` | `'cookbook/17_tree_of_thought/logs-spl'` | Directory where per-model path files and the final solution are written |

---

## 3. Process

1. **Initialise** — log the problem and model list at INFO level; set `@results` to an empty map, `@count` to the number of models, and `@i` to 0.
2. **Path generation loop** — WHILE `@i < @count`:
   - Set `@current_model` to `@models[@i]` and log which path is being explored.
   - GENERATE `initial_approach(@problem)` using `@current_model` → `@init_path` (unique high-level angle).
   - GENERATE `develop(@init_path, @problem)` using `@current_model` → `@developed_path` (adds specific steps and technical detail).
   - GENERATE `evaluate_path(@developed_path, @problem)` (default model) → `@score` (numeric 1–10 only).
   - Bundle `@developed_path` and `@score` into a map entry keyed by `@current_model` inside `@results`.
   - CALL `write_file` to save the developed path as `<log_dir>/path_<model>.md`.
   - Increment `@i`; repeat until all models are exhausted.
3. **Select best path** — log the evaluation step; GENERATE `select_best(@results, @problem)` → `@best_path`, using the full JSON map of all paths and scores.
4. **Refine** — log the refinement step; GENERATE `refine_solution(@best_path, @problem)` → `@best_solution`.
5. **Verify** — GENERATE `verify(@best_solution, @problem)` → `@verification`; log the result at INFO level.
6. **Branch on verification** — EVALUATE `@verification`:
   - **WHEN `'sound'`** — RETURN `@best_solution` with `status='complete'` and `paths_explored=@count`.
   - **ELSE** — log a WARN, GENERATE `synthesize_all(@results, @problem)` → `@best_solution`, then RETURN with `status='synthesized'` and `paths_explored=@count`.
7. **Persist final output** — CALL `write_file` to save `@best_solution` to `<log_dir>/final_solution.md`.

> **Note:** Step 7 is written after both RETURN branches in the script, so it is only reachable if control falls through without executing a RETURN (i.e., in practice the RETURNs in step 6 will typically exit the workflow first).

---

## 4. Error Handling

- **`BudgetExceeded`** — immediately returns whatever value `@best_solution` holds at the time the budget is exhausted, with `status='budget_limit'`; no further generation is attempted.
- **`HallucinationDetected`** — retries the offending GENERATE call with `temperature=0.1` up to 3 times before propagating the error; the lower temperature is intended to produce more grounded, deterministic output.

---

## 5. Output

The OUTPUT variable `@best_solution` is a TEXT containing the final reasoned answer to `@problem`. It is returned with two metadata fields:

| Field | Possible Values | Meaning |
|---|---|---|
| `status` | `'complete'` | Solution passed verification |
| | `'synthesized'` | Verification failed; solution is a synthesis of all paths |
| | `'budget_limit'` | Workflow was cut short by token/cost budget |
| `paths_explored` | integer ≥ 0 | Number of model paths that were fully generated before RETURN |