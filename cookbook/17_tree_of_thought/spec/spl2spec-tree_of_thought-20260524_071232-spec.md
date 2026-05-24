## Summary

Tree of Thought (Dynamic) is a multi-model reasoning workflow that distributes problem-solving across a configurable list of LLMs, each exploring an independent reasoning path from first principles through a developed, scored chain of thought. The best-scoring path is refined into a final solution, verified for soundness, and—if verification fails—synthesized from all paths to ensure a robust answer. It benefits researchers, engineers, and decision-makers who need more thorough, self-critical answers than a single model or single prompt can produce.

---

## Detailed Specification

### 1. Purpose

Given a free-form problem statement and a list of LLM model names, this workflow generates, scores, and refines one independent reasoning path per model, then selects the strongest path, polishes it into a verified solution, and falls back to cross-path synthesis if verification fails.

---

### 2. High-level Description

The workflow implements the Tree-of-Thought pattern dynamically: rather than a fixed branching fan-out, the number of branches is determined at runtime by the length of the `@models` LIST input, allowing any number of reasoning paths without rewriting the workflow. A WHILE loop iterates over each model index; inside the loop, three sequential GENERATE calls use `initial_approach` to seed a high-level perspective, `develop` to deepen it with concrete steps, and `evaluate_path` to score it 1–10 on feasibility and depth—all using the current model as the LLM backend via `USING MODEL @current_model`. Each path's content and numeric score are stored in a nested map `@results` keyed by model name, and the developed path is persisted to disk with a CALL to `write_file`. After the loop, a single GENERATE call to `select_best` reviews the full `@results` map (serialized as JSON) and returns the highest-quality path; `refine_solution` then turns that path into a polished final answer, and `verify` outputs the sentinel token `'sound'` if the solution is correct or a brief critique otherwise. An EVALUATE block branches on that sentinel: matching `'sound'` triggers RETURN WITH `status = 'complete'`, while the ELSE branch calls `synthesize_all` over the entire results map and RETURNs WITH `status = 'synthesized'`. Two EXCEPTION handlers cover budget exhaustion (`BudgetExceeded` → early RETURN with `status = 'budget_limit'`) and hallucination detection (`HallucinationDetected` → RETRY with lowered temperature, up to 3 attempts).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW tree_of_thought` | `WORKFLOW` | Top-level named orchestration unit with INPUT/OUTPUT declarations |
| `CREATE FUNCTION initial_approach` | `CREATE FUNCTION` | Prompt template with `{problem}` slot; seeds a unique perspective |
| `CREATE FUNCTION develop` | `CREATE FUNCTION` | Prompt template with `{path}` and `{problem}` slots; deepens the path |
| `CREATE FUNCTION evaluate_path` | `CREATE FUNCTION` | Prompt template; produces a numeric 1-10 score as raw text |
| `CREATE FUNCTION select_best` | `CREATE FUNCTION` | Prompt template; accepts `{results_map}` (JSON) and returns best path content |
| `CREATE FUNCTION refine_solution` | `CREATE FUNCTION` | Prompt template; polishes the winning path into a complete solution |
| `CREATE FUNCTION verify` | `CREATE FUNCTION` | Prompt template; outputs sentinel `'sound'` or a critique string |
| `CREATE FUNCTION synthesize_all` | `CREATE FUNCTION` | Prompt template; merges all paths into a comprehensive answer |
| `GENERATE ... USING MODEL @current_model INTO @var` | `GENERATE` | LLM call dispatched to the per-iteration model; result bound to `@var` |
| `WHILE @i < @count DO ... END` | `WHILE` | Iterates over model list; `@count = COUNT(@models)`, `@i` incremented manually |
| `EVALUATE @verification WHEN 'sound' THEN ... ELSE ... END` | `EVALUATE` | Semantic branch on sentinel token; drives two distinct RETURN paths |
| `RETURN @best_solution WITH status = 'complete'` | `RETURN` | Non-trivial status drives caller-side branch logic |
| `RETURN @best_solution WITH status = 'synthesized'` | `RETURN` | Signals fallback synthesis path to caller |
| `RETURN @best_solution WITH status = 'budget_limit'` | `RETURN` | Early-exit under BudgetExceeded exception |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect tool call; persists per-model paths and final solution to disk |
| `@results`, `@path_data`, `@best_path`, etc. | SPL `@vars` | Shared mutable state across all steps within the workflow frame |
| `EXCEPTION WHEN BudgetExceeded THEN ...` | `EXCEPTION` | Typed handler for cost guard; returns partial result with budget status |
| `EXCEPTION WHEN HallucinationDetected THEN RETRY` | `EXCEPTION` | Typed handler with temperature dampening; up to 3 retries |

---

### 4. Logical Functions / Prompts

**`initial_approach`**
- Role: Seeds the reasoning tree for one model; produces a unique high-level perspective or methodology on the problem.
- Key conventions: Free-form prose; no scoring or sentinel tokens; instructs the model to focus on a *unique* perspective to maximize diversity across branches.

**`develop`**
- Role: Takes the initial approach and adds a second level of depth—concrete steps and technical detail.
- Key conventions: Receives both `{path}` (the seed) and `{problem}` as context; output is the enriched, step-level reasoning path that will be scored and potentially selected.

**`evaluate_path`**
- Role: Produces a numeric quality signal (1–10) for a developed path.
- Key conventions: Instructs the model to "output only the numeric score"—a strict output format constraint used as a sentinel. The score is stored as raw text in `@score` and packaged into `@results` alongside the path content.

**`select_best`**
- Role: Cross-path judge that reads the full `@results` map (JSON) and returns the content of the highest-quality path.
- Key conventions: Accepts `{results_map}` as a serialized JSON structure containing per-model `content` and `score`; the model is expected to reason across all entries and return the winning path's prose content directly.

**`refine_solution`**
- Role: Final polish pass on the selected path; converts a structured reasoning chain into a clean, complete solution.
- Key conventions: No scoring or branching output; pure generative refinement.

**`verify`**
- Role: Quality gate; outputs the sentinel string `'sound'` for a passing solution or a brief critique for a failing one.
- Key conventions: The sentinel `'sound'` is load-bearing—it is matched literally by the downstream EVALUATE block to determine which RETURN branch fires.

**`synthesize_all`**
- Role: Fallback aggregator; merges insights from all model paths into a single comprehensive answer when the refined solution fails verification.
- Key conventions: Accepts the full `{results_map}` (same JSON structure as `select_best`); no scoring output; produces a unified prose solution.

---

### 5. Control Flow

```
START
  │
  ├─ Initialize: @results = {}, @i = 0, @count = COUNT(@models)
  │
  └─ WHILE @i < @count DO
       │
       ├─ GENERATE initial_approach(@problem) USING MODEL @models[@i]  →  @init_path
       ├─ GENERATE develop(@init_path, @problem) USING MODEL @models[@i]  →  @developed_path
       ├─ GENERATE evaluate_path(@developed_path, @problem)  →  @score
       ├─ Store {content, score} into @results[@current_model]
       ├─ CALL write_file(path_{model}.md, @developed_path)
       └─ @i := @i + 1
     END
  │
  ├─ GENERATE select_best(@results, @problem)  →  @best_path
  ├─ GENERATE refine_solution(@best_path, @problem)  →  @best_solution
  ├─ GENERATE verify(@best_solution, @problem)  →  @verification
  │
  └─ EVALUATE @verification
       WHEN 'sound'  →  RETURN @best_solution WITH status='complete', paths_explored=@count
       ELSE          →  GENERATE synthesize_all(@results, @problem)  →  @best_solution
                         RETURN @best_solution WITH status='synthesized', paths_explored=@count

EXCEPTION WHEN BudgetExceeded  →  RETURN @best_solution WITH status='budget_limit'
EXCEPTION WHEN HallucinationDetected  →  RETRY temperature=0.1 LIMIT 3
```

Termination conditions: (1) normal RETURN with `status='complete'` after a verified solution, (2) fallback RETURN with `status='synthesized'` when verification fails, or (3) early RETURN with `status='budget_limit'` under the BudgetExceeded exception.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a free-form problem statement and a list of LLM model names, \
this workflow generates, scores, and refines one independent reasoning path per model, then selects \
the strongest path, polishes it into a verified solution, and falls back to cross-path synthesis if \
verification fails." --mode workflow

# Step 2 — compile to any target
spl3 splc compile tree_of_thought.spl --lang python/pocketflow
spl3 splc compile tree_of_thought.spl --lang python/langgraph
spl3 splc compile tree_of_thought.spl --lang go
```