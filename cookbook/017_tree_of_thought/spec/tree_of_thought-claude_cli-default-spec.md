## Summary

This workflow implements the Tree of Thought reasoning technique, exploring multiple independent reasoning paths in parallel across a configurable list of LLM models. Each model generates, develops, and self-scores its own path; the workflow then selects the strongest path, refines it into a polished solution, and verifies its soundness. Teams building complex problem-solving agents benefit by leveraging model diversity to avoid single-model blind spots.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality, verified solution to an open-ended problem by exploring, evaluating, and refining multiple reasoning paths across a dynamic list of LLM models.

---

### 2. High-level Description

The `tree_of_thought` WORKFLOW accepts a problem statement, a LIST of model identifiers, and a log directory as inputs. It iterates over each model using a WHILE loop, invoking three CREATE FUNCTIONs per iteration: `initial_approach` generates a unique high-level reasoning path for the problem, `develop` deepens that path with concrete steps and technical detail, and `evaluate_path` scores the developed path on a 1–10 feasibility scale, outputting only a numeric token. Each path and its score are stored in a keyed map `@results` indexed by model name, and the developed path is persisted to disk via a CALL to `write_file`. After the loop, `select_best` receives the full results map as JSON and identifies the highest-quality path, which `refine_solution` then polishes into a complete answer. A final GENERATE to `verify` checks solution soundness, returning the sentinel token `sound` on success or a critique string on failure; an EVALUATE branches on this output — returning `@best_solution` with `status = 'complete'` when sound, or invoking `synthesize_all` to merge insights from all paths and returning with `status = 'synthesized'` when not. EXCEPTION handlers catch `BudgetExceeded` (returning immediately with `status = 'budget_limit'`) and `HallucinationDetected` (retrying with temperature 0.1, up to 3 attempts).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW tree_of_thought` | `WORKFLOW` | Top-level orchestration; accepts `@problem`, `@models`, `@log_dir` as typed inputs |
| `CREATE FUNCTION initial_approach` | `CREATE FUNCTION` | Prompt template with `{problem}` slot; generates a unique reasoning path |
| `CREATE FUNCTION develop` | `CREATE FUNCTION` | Prompt template with `{path}`, `{problem}` slots; deepens the initial path |
| `CREATE FUNCTION evaluate_path` | `CREATE FUNCTION` | Prompt template; outputs a single numeric score (1–10); sentinel: numeric-only token |
| `CREATE FUNCTION select_best` | `CREATE FUNCTION` | Prompt template with `{results_map}` (JSON), `{problem}`; identifies best path by score |
| `CREATE FUNCTION refine_solution` | `CREATE FUNCTION` | Prompt template; converts winning path to a polished solution |
| `CREATE FUNCTION verify` | `CREATE FUNCTION` | Prompt template; outputs sentinel `sound` or a critique string |
| `CREATE FUNCTION synthesize_all` | `CREATE FUNCTION` | Prompt template; merges all paths into a comprehensive fallback solution |
| `GENERATE ... USING MODEL @current_model INTO @var` | `GENERATE` | LLM call dispatched to the model selected by loop index; result stored in `@var` |
| `WHILE @i < @count DO ... END` | `WHILE` | Iterates over model list by index; `@count` derived from `COUNT(@models)` |
| `EVALUATE @verification WHEN 'sound' THEN ... ELSE ... END` | `EVALUATE` | Branches on sentinel token from `verify`; drives `complete` vs `synthesized` status |
| `RETURN @best_solution WITH status = 'complete'` | `RETURN` | Non-trivial status token `complete`; terminates workflow on verified solution |
| `RETURN @best_solution WITH status = 'synthesized'` | `RETURN` | Non-trivial status token `synthesized`; signals fallback path was taken |
| `RETURN @best_solution WITH status = 'budget_limit'` | `RETURN` | Non-trivial status token from `BudgetExceeded` exception handler |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect only; writes per-model path logs and final solution to disk |
| `@results`, `@path_data`, `@best_path`, etc. | Shared `@vars` | Mutable workflow state; `@results` is a keyed map accumulating per-model outputs |
| `EXCEPTION WHEN BudgetExceeded THEN` | `EXCEPTION` | Graceful early exit; returns current best with budget status |
| `EXCEPTION WHEN HallucinationDetected THEN RETRY` | `EXCEPTION` | Retry with lowered temperature (0.1), max 3 attempts |

---

### 4. Logical Functions / Prompts

**`initial_approach(problem)`**
- **Role:** Seeds the Tree of Thought by generating a unique high-level reasoning path for the problem, one per model.
- **Conventions:** Open-ended prose; instructs the model to adopt a "unique perspective or specialized methodology" to maximize path diversity across models.

**`develop(path, problem)`**
- **Role:** Deepens a seed path by adding specific steps and technical detail, producing the substantive content that will be scored and potentially selected.
- **Conventions:** Takes both the prior path and the original problem to maintain coherence; output is the expanded path text stored in `@developed_path`.

**`evaluate_path(developed_path, problem)`**
- **Role:** Scores a developed path for feasibility and depth on a 1–10 scale.
- **Key convention:** Sentinel numeric-only output (`Output only the numeric score`) — no prose, enabling direct use as a comparable score value in `@path_data['score']`.

**`select_best(results_map, problem)`**
- **Role:** Acts as a meta-evaluator; receives the full `@results` map serialized as JSON (model → `{content, score}`) and returns the *content* of the best path as plain text.
- **Conventions:** Instructs the model to identify the highest-quality reasoning, not just the highest numeric score — allows qualitative override of raw scores.

**`refine_solution(path, problem)`**
- **Role:** Polishes the winning path into a complete, production-quality answer.
- **Conventions:** No special output format; free-form prose solution.

**`verify(solution, problem)`**
- **Role:** Quality gate; determines whether the refined solution is sound.
- **Key convention:** Binary sentinel output — `sound` on success, or a critique string on failure. The `EVALUATE` branch keys on the token `'sound'` to route to `complete` vs fallback paths.

**`synthesize_all(results_map, problem)`**
- **Role:** Fallback synthesizer; when verification fails, combines insights from all explored paths to produce a comprehensive solution rather than discarding parallel work.
- **Conventions:** Receives the full `@results` map; output replaces `@best_solution`.

---

### 5. Control Flow

**Initialization:** `@results` map and loop counters `@i`, `@count` are initialized; `@count` is set to `COUNT(@models)`.

**Exploration loop (WHILE):** `WHILE @i < @count` iterates once per model. Each iteration: selects `@current_model := @models[@i]`, calls `initial_approach` → `develop` → `evaluate_path` (all three GENERATEs using the current model for the first two), stores `{content, score}` in `@results[@current_model]`, writes the path to disk via CALL, then increments `@i`.

**Selection and refinement (linear):** After the loop, `select_best` picks the winner from `@results` into `@best_path`, then `refine_solution` polishes it into `@best_solution`, then `verify` checks it into `@verification`.

**Verification branch (EVALUATE):** `EVALUATE @verification WHEN 'sound'` — if the token is `sound`, RETURN with `status = 'complete'` and `paths_explored = @count`. ELSE, `synthesize_all` is called over all paths, and RETURN with `status = 'synthesized'` and `paths_explored = @count`.

**Exception paths:** `BudgetExceeded` exits immediately with `status = 'budget_limit'`. `HallucinationDetected` retries the failing GENERATE at `temperature = 0.1` up to 3 times before propagating.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile tree_of_thought.spl --lang python/pocketflow
spl3 splc compile tree_of_thought.spl --lang python/langgraph
spl3 splc compile tree_of_thought.spl --lang go
```