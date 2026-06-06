## Summary

This workflow implements the **Self-Refine** pattern: it drafts a response to an open-ended task, then iteratively critiques and rewrites it until either a critic model signals approval or a maximum iteration budget is exhausted. The goal is to produce higher-quality LLM output than a single-shot generation by pairing a writer model with a separate critic model in a quality loop. Non-technical stakeholders can think of it as an automated "write → review → revise" editorial cycle.

---

## Detailed Specification

### 1. Purpose

Produce a polished written response to an arbitrary task by running an automated critique-and-refinement loop between a writer model and a critic model, exiting early when the critic approves the draft or gracefully capping output when iteration or token budgets are reached.

---

### 2. High-level Description

The `self_refine` WORKFLOW accepts a free-text `@task`, an output token budget, a maximum iteration count, separate model identifiers for the writer and critic roles, and a log directory for audit files. It begins by invoking the `draft` CREATE FUNCTION through a GENERATE call to produce an initial written response stored in `@current`. The workflow then enters a WHILE loop bounded by `@iteration < @max_iterations`, which on each pass invokes the `critique` CREATE FUNCTION (using the critic model) to evaluate `@current` and store structured feedback in `@feedback`. An EVALUATE branch inspects `@feedback` for the sentinel token `[APPROVED]`: if present, the workflow immediately exits via RETURN with `status='complete'` and the iteration count; if absent, it increments `@iteration` and invokes the `refine` CREATE FUNCTION (using the writer model) to produce an improved `@current`. If the loop exhausts all iterations without approval, the workflow commits the best-effort draft with `status='max_iterations'`. Throughout execution, CALL side-effects write each draft and feedback file to disk under `@log_dir`. Two EXCEPTION handlers cover `MaxIterationsReached` (returning `status='partial'`) and `BudgetExceeded` (returning `status='budget_limit'`), ensuring clean termination under resource constraints. The deliberate separation of `@writer_model` and `@critic_model` inputs makes multi-model ablation straightforward without changing the workflow logic.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `class` / node | `WORKFLOW self_refine` | Top-level orchestration unit |
| Prompt template | `CREATE FUNCTION draft(task)` | Initial generation prompt |
| Prompt template | `CREATE FUNCTION critique(current)` | Quality-gate prompt; uses `[APPROVED]` sentinel |
| Prompt template | `CREATE FUNCTION refine(current, feedback)` | Revision prompt |
| LLM call → variable | `GENERATE <fn>(...) INTO @var` | Each GENERATE binds result to a named SPL variable |
| Token budget | `WITH OUTPUT BUDGET @output_budget TOKENS` | Applied to all three GENERATE calls |
| Model selection | `USING MODEL @writer_model` / `@critic_model` | Per-call model dispatch; writer and critic differ |
| Iteration loop | `WHILE @iteration < @max_iterations DO ... END` | Bounds the critique-refine cycle |
| Sentinel branch | `EVALUATE @feedback WHEN contains('[APPROVED]') THEN ... ELSE ... END` | Drives early exit vs. continued refinement |
| Early exit | `RETURN @current WITH status='complete', iterations=@iteration` | Non-trivial status; terminates the loop |
| Budget-exhausted exit | `RETURN @current WITH status='max_iterations', iterations=@iteration` | Post-loop fallthrough |
| File side-effect | `CALL write_file(...) INTO NONE` | Persists drafts, feedback, and final artifact |
| Shared mutable state | `@current`, `@iteration`, `@feedback` | SPL `@vars` mutated across loop iterations |
| Error recovery | `EXCEPTION WHEN MaxIterationsReached THEN ...` | Returns `status='partial'` |
| Error recovery | `EXCEPTION WHEN BudgetExceeded THEN ...` | Returns `status='budget_limit'` |

---

### 4. Logical Functions / Prompts

**`draft(task TEXT)`**
- **Role:** Produces the initial candidate response before any critique.
- **Conventions:** Instructs the model to act as "an expert writer," complete the task "thoroughly and well," and write a high-quality response immediately — no structured output format required, free-form prose.

**`critique(current TEXT)`**
- **Role:** Acts as a quality gate; determines whether the current draft is publication-ready or still improvable.
- **Conventions:** Uses a hard sentinel token `[APPROVED]` — the model must reply with *only* `[APPROVED]` (and nothing else) if the draft needs no further work. Any other response is treated as actionable feedback. The prompt explicitly warns the critic not to approve prematurely, reducing false positives. The EVALUATE construct reads this sentinel.

**`refine(current TEXT, feedback TEXT)`**
- **Role:** Produces an improved draft by applying the critic's feedback to the current draft.
- **Conventions:** Both the full draft and the full feedback string are injected verbatim into the prompt slots `{current}` and `{feedback}`. No structured output format; the model is instructed to write "the improved version now."

---

### 5. Control Flow

1. **Initialization** — `@iteration` is set to `0`; GENERATE `draft(@task)` produces `@current`; the draft is written to `draft_0.md`.
2. **Loop entry** — `WHILE @iteration < @max_iterations DO` guards the critique-refine cycle.
3. **Critique** — GENERATE `critique(@current)` → `@feedback`; feedback written to `feedback_{@iteration}.md`.
4. **Branch** — EVALUATE `@feedback`:
   - `WHEN contains('[APPROVED]')` → write `final.md`, RETURN `@current` with `status='complete'` and current `@iteration`. Loop terminates.
   - `ELSE` → increment `@iteration`, GENERATE `refine(@current, @feedback)` → `@current`, write `draft_{@iteration}.md`, continue loop.
5. **Loop exhaustion** — if the WHILE condition becomes false (all iterations consumed without approval), write `final.md`, RETURN `@current` with `status='max_iterations'`.
6. **Exception paths** — `MaxIterationsReached` writes `final.md` and returns `status='partial'`; `BudgetExceeded` returns `status='budget_limit'` immediately without writing.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 1 above as text2spl input)
spl3 text2spl \
  --description "Produce a polished written response to an arbitrary task by running an \
automated critique-and-refinement loop between a writer model and a critic model, exiting \
early when the critic approves the draft or gracefully capping output when iteration or \
token budgets are reached." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```