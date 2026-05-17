## Summary

This workflow implements the Self-Refine pattern: it generates an initial draft response to a task, then iteratively critiques and improves that draft until a critic model signals approval or a maximum iteration budget is exhausted. It benefits content creators, knowledge workers, and AI pipeline engineers who need higher-quality LLM outputs than a single-shot generation can reliably provide.

---

## Detailed Specification

### 1. Purpose

Produce a polished, critic-approved text response to an arbitrary input task by running an automated write → critique → refine loop across two configurable LLM models.

---

### 2. High-level Description

The `self_refine` WORKFLOW accepts a task description and uses three CREATE FUNCTIONs across a two-model setup to iteratively improve its output. The `draft` function primes a writer model to produce an initial high-quality response, which is stored in the shared variable `@current`. A WHILE loop then drives up to `@max_iterations` rounds of critique and refinement: in each round the `critique` function instructs a separate critic model to either emit the sentinel token `[APPROVED]` (signalling no further improvements are needed) or return specific actionable feedback. An EVALUATE on `@feedback` branches on the presence of `[APPROVED]`—if detected, the workflow exits early via RETURN WITH `status='complete'` and the iteration count; otherwise the `refine` function feeds the current draft and the feedback back to the writer model to produce an improved `@current`. Every intermediate and final artifact is persisted to disk via CALL `write_file` side-effects, giving a full audit trail of drafts and feedback. If the loop exhausts its budget without approval, the workflow commits the best-effort draft with RETURN WITH `status='max_iterations'`. Two named EXCEPTION handlers catch `MaxIterationsReached` and `BudgetExceeded` to ensure a partial result is always returned rather than a hard failure.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW self_refine` | `WORKFLOW` | Top-level orchestrator; declares typed inputs and a single output `@result` |
| `CREATE FUNCTION draft` | `CREATE FUNCTION` | Prompt template with `{task}` slot; roles the LLM as an expert writer |
| `CREATE FUNCTION critique` | `CREATE FUNCTION` | Prompt template with `{current}` slot; roles the LLM as a strict critic; emits `[APPROVED]` sentinel |
| `CREATE FUNCTION refine` | `CREATE FUNCTION` | Prompt template with `{current}` and `{feedback}` slots; produces improved draft |
| `GENERATE ... INTO @current` | `GENERATE` | Calls writer model (`@writer_model`) for draft/refine; respects `OUTPUT BUDGET` token cap |
| `GENERATE ... INTO @feedback` | `GENERATE` | Calls critic model (`@critic_model`) for critique; separate model from writer |
| `WHILE @iteration < @max_iterations DO` | `WHILE` | Drives the critique–refine loop; terminates on approval or iteration budget exhaustion |
| `EVALUATE @feedback WHEN contains('[APPROVED]')` | `EVALUATE` | Branches on sentinel token presence; early-exit path vs. continue path |
| `RETURN @current WITH status='complete', iterations=@iteration` | `RETURN` | Non-trivial early exit: critic approved, loop terminated before budget |
| `RETURN @current WITH status='max_iterations'` | `RETURN` | Non-trivial exit: loop budget exhausted without approval |
| `RETURN @current WITH status='partial'` | `RETURN` | Exception fallback: partial result committed on `MaxIterationsReached` |
| `RETURN @current WITH status='budget_limit'` | `RETURN` | Exception fallback: token budget exceeded mid-loop |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect: persists drafts and feedback to `@log_dir` for auditability |
| `@current`, `@feedback`, `@iteration` | SPL `@vars` | Shared mutable state across loop iterations |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION` | Named handler; commits best-effort draft |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION` | Named handler; returns current draft with budget-limit status |

---

### 4. Logical Functions / Prompts

**`draft(task TEXT)`**
- **Role:** Generates the initial response; entry point of the workflow before the refinement loop begins.
- **Key conventions:** System persona is "expert writer." No sentinel tokens. Free-form text output. Bounded by `@output_budget` tokens.

**`critique(current TEXT)`**
- **Role:** Evaluates the current draft and decides whether it is publication-ready or needs specific improvements.
- **Key conventions:** System persona is "strict critic." Outputs the sentinel `[APPROVED]` (exact string, nothing else) when no improvements are warranted. Otherwise outputs specific, actionable free-form feedback. The prompt explicitly warns against premature approval.

**`refine(current TEXT, feedback TEXT)`**
- **Role:** Produces an improved draft by incorporating the critic's feedback; replaces `@current` each iteration.
- **Key conventions:** System persona is "expert writer." Both the prior draft and the feedback are injected verbatim. Output is a complete rewrite, not a diff. Bounded by `@output_budget` tokens.

---

### 5. Control Flow

1. **Initialization:** `@iteration` is set to 0; logging records the task and parameters.
2. **Initial generation:** `draft(@task)` is called via GENERATE into `@current`; the result is written to `draft_0.md`.
3. **WHILE loop:** Repeats while `@iteration < @max_iterations`:
   - GENERATE `critique(@current)` into `@feedback`; write to `feedback_{iteration}.md`.
   - EVALUATE `@feedback`:
     - **WHEN `contains('[APPROVED]')`:** write `final.md`, RETURN WITH `status='complete'` and current iteration count — loop terminates immediately.
     - **ELSE:** increment `@iteration`, GENERATE `refine(@current, @feedback)` into `@current`, write to `draft_{iteration}.md`, continue loop.
4. **Budget exhausted:** Loop exits naturally; write `final.md`, RETURN WITH `status='max_iterations'`.
5. **Exception paths:** `MaxIterationsReached` → write `final.md`, RETURN WITH `status='partial'`; `BudgetExceeded` → RETURN WITH `status='budget_limit'` (no file write).

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```