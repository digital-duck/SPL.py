## Summary

This workflow implements the **Self-Refine** pattern: it generates an initial draft response to a task, then iteratively critiques and improves it until either a critic LLM approves the result or a maximum iteration budget is exhausted. It is designed for content-generation use cases — writing, summarization, explanation — where quality can be meaningfully improved through structured feedback loops, benefiting developers and researchers who need higher-quality LLM outputs without manual review.

---

## Detailed Specification

### 1. Purpose

Produce a high-quality text response to an arbitrary task by iteratively refining a draft through automated critique, halting early when the content is approved or when a configurable iteration limit is reached.

---

### 2. High-level Description

The `self_refine` WORKFLOW implements the iterative self-refinement pattern using three CREATE FUNCTIONs and a WHILE loop that drives critique-and-rewrite cycles. On startup, a `draft` function generates the initial response using a configurable writer model (default: `gemma3`); this output is stored in the shared variable `@current` and written to disk via a CALL to `write_file`. The WHILE loop then runs up to `@max_iterations` times: each iteration invokes the `critique` function on a separate critic model (default: `llama3.2`) to evaluate `@current`, storing the result in `@feedback`. An EVALUATE block inspects `@feedback` for the sentinel token `[APPROVED]`; if found, the workflow immediately writes the final output and RETURNs `@current` with `status='complete'` and the iteration count. If not approved, the `refine` function rewrites `@current` using the actionable feedback, incrementing the iteration counter, and the loop continues. If the loop exhausts without approval, the best-effort draft is saved and the workflow RETURNs with `status='max_iterations'`. Two EXCEPTION handlers cover abnormal termination: `MaxIterationsReached` returns with `status='partial'`, and `BudgetExceeded` returns with `status='budget_limit'`. All intermediate drafts and feedback files are persisted to a configurable log directory throughout execution.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Concept | SPL Equivalent | Notes |
|---|---|---|
| Named orchestration workflow | `WORKFLOW self_refine` | Declares the top-level pipeline with typed INPUT/OUTPUT |
| Reusable prompt templates | `CREATE FUNCTION draft`, `critique`, `refine` | Parameterized with `{task}`, `{current}`, `{feedback}` slots |
| LLM call storing result | `GENERATE <fn>(...) INTO @<var>` | Uses `WITH OUTPUT BUDGET` and `USING MODEL` per call |
| File side-effect | `CALL write_file(...) INTO NONE` | Persists drafts, feedback, and final output to `@log_dir` |
| Iteration control | `WHILE @iteration < @max_iterations DO ... END` | Guards against infinite refinement |
| Branching on LLM output | `EVALUATE @feedback WHEN contains('[APPROVED]') THEN ... ELSE ... END` | Sentinel token `[APPROVED]` triggers early exit |
| Non-trivial early exit | `RETURN @current WITH status='complete', iterations=@iteration` | Fires inside EVALUATE when approved |
| Loop-exhausted exit | `RETURN @current WITH status='max_iterations', iterations=@iteration` | Fires after WHILE terminates normally |
| Shared mutable state | `@current`, `@iteration`, `@feedback` | Passed between GENERATE calls across loop iterations |
| Abnormal termination | `EXCEPTION WHEN MaxIterationsReached THEN ...` / `WHEN BudgetExceeded THEN ...` | Returns `status='partial'` or `status='budget_limit'` |
| Multi-model design | `@writer_model` vs `@critic_model` parameters | Writer and critic are independently configurable LLMs |

---

### 4. Logical Functions / Prompts

**`draft(task TEXT)`**
- **Role:** Generates the initial response before any critique has occurred.
- **Prompt conventions:** Frames the LLM as "an expert writer"; no sentinel tokens; free-form prose output. Used once before the loop.

**`critique(current TEXT)`**
- **Role:** Evaluates the current draft and either approves it or provides actionable improvement notes.
- **Prompt conventions:** Uses a strict sentinel token `[APPROVED]` — the prompt instructs the model to output *exactly* this token and nothing else if no improvements are needed. Any other output is treated as feedback. The sentinel must not be emitted unless the content is genuinely complete; this is enforced by the prompt's explicit warning.

**`refine(current TEXT, feedback TEXT)`**
- **Role:** Rewrites the draft incorporating specific feedback from the critic.
- **Prompt conventions:** Presents both the existing draft and the critic's feedback as distinct labeled sections; asks the model to produce the improved version directly. Output replaces `@current` for the next iteration.

---

### 5. Control Flow

1. **Initialization** — `@iteration` is set to `0`; `draft(@task)` is called and stored in `@current`; the draft is written to `draft_0.md`.
2. **WHILE loop** — Condition: `@iteration < @max_iterations`. On each pass:
   - `critique(@current)` → `@feedback`, written to `feedback_{iteration}.md`.
   - **EVALUATE** on `@feedback`:
     - `contains('[APPROVED]')` → write `final.md`, **RETURN** with `status='complete'` (early exit).
     - **ELSE** → increment `@iteration`, call `refine(@current, @feedback)` → update `@current`, write `draft_{iteration}.md`, continue loop.
3. **Loop exhausted** — WHILE exits without approval; write `final.md`, **RETURN** with `status='max_iterations'`.
4. **Exception paths** — `MaxIterationsReached` writes `final.md` and returns `status='partial'`; `BudgetExceeded` returns `status='budget_limit'` without writing.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 2 above as text2spl input)
spl3 text2spl --description "Produce a high-quality text response to an arbitrary task \
  by iteratively refining a draft through automated critique using three functions (draft, \
  critique, refine), a WHILE loop guarded by max_iterations, an EVALUATE branch on the \
  [APPROVED] sentinel token for early exit, multi-model support for writer and critic, \
  CALL write_file side-effects for logging, and EXCEPTION handlers for MaxIterationsReached \
  and BudgetExceeded." --mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```