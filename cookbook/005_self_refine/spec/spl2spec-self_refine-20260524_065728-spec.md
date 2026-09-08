## Summary

This workflow implements the **Self-Refine** pattern: it generates an initial draft response to a user-supplied task, then alternates between a critic LLM and a writer LLM to iteratively improve the output until quality is approved or a budget limit is hit. It is designed for teams who need progressively higher-quality LLM text output without manual human review cycles. Non-technical stakeholders benefit from a transparent, logged trail of each draft and critique round that makes the improvement process auditable.

---

## Detailed Specification

### 1. Purpose

Automatically improve an LLM-generated text response through iterative critique and refinement cycles, returning the best available output along with a status indicating how the loop terminated.

---

### 2. High-level Description

The `self_refine` WORKFLOW accepts a task description and configuration parameters (token budget, iteration ceiling, writer model, critic model, log directory) and returns a refined TEXT result. It first calls the `draft` function via GENERATE to produce an initial response using the designated writer model, then enters a WHILE loop bounded by `@max_iterations`. Inside the loop, it uses GENERATE with the `critique` function and a separate critic model to evaluate the current draft; the critic either emits the sentinel token `[APPROVED]` or returns actionable feedback. An EVALUATE block inspects the feedback variable: if it contains `[APPROVED]`, the workflow immediately RETURNs with `status = 'complete'` and the iteration count; otherwise it increments the counter and calls GENERATE with the `refine` function to produce an improved draft. Every intermediate artifact (draft, feedback, final output) is persisted via CALL `write_file` side-effects into a structured log directory. If the WHILE loop exhausts without approval, the workflow RETURNs the best-effort draft with `status = 'max_iterations'`. Two EXCEPTION handlers provide fallback exits: `MaxIterationsReached` returns `status = 'partial'`, and `BudgetExceeded` returns `status = 'budget_limit'`, both writing the final artifact before exiting.

---

### 3. SPL ↔ SPL Construct Mapping

| Concept | SPL Construct | Notes |
|---|---|---|
| Named workflow with typed I/O | `WORKFLOW self_refine` | Declares `INPUT:` variables with defaults and a single `OUTPUT: @result TEXT` |
| Reusable prompt templates | `CREATE FUNCTION draft / critique / refine` | Each function takes typed TEXT params and returns TEXT; prompt bodies use `{param}` slot syntax |
| LLM call with model + token budget | `GENERATE <fn>(...) WITH OUTPUT BUDGET @output_budget TOKENS USING MODEL @writer_model INTO @var` | Writer model and critic model are resolved at runtime from INPUT variables |
| Iteration counter and mutable state | `@iteration := 0` / `@iteration := @iteration + 1` | SPL `@var` assignment; shared across WHILE body |
| Quality-gated refinement loop | `WHILE @iteration < @max_iterations DO ... END` | Loop terminates early via RETURN inside EVALUATE or exhausts naturally |
| Sentinel-token branching | `EVALUATE @feedback WHEN contains('[APPROVED]') THEN ... ELSE ... END` | Critic embeds `[APPROVED]` as an unambiguous exit signal; EVALUATE dispatches on it |
| Early-exit with status | `RETURN @current WITH status = 'complete', iterations = @iteration` | Non-trivial status drives caller-side branching; iteration count is observability metadata |
| Budget-exhaustion exit | `RETURN @current WITH status = 'max_iterations', iterations = @iteration` | Emitted after WHILE falls through; distinct from exception path |
| File persistence side-effects | `CALL write_file(path, content) INTO NONE` | Used for every draft, feedback, and final artifact; `INTO NONE` discards return value |
| Structured logging | `LOGGING '...' LEVEL INFO/DEBUG/WARN` | Observability at key checkpoints; not control flow |
| Typed error recovery | `EXCEPTION WHEN MaxIterationsReached THEN ... WHEN BudgetExceeded THEN ...` | Each handler commits the in-progress draft before returning a degraded status |

---

### 4. Logical Functions / Prompts

**`draft(task TEXT)`**
- **Role:** Produces the initial response to the user task; called exactly once before the refinement loop begins.
- **Conventions:** System persona is "expert writer"; open-ended instruction ("thorough and well") with no structured output format. No sentinel tokens.

**`critique(current TEXT)`**
- **Role:** Quality gate — evaluates the current draft and either approves it or returns improvement instructions.
- **Key conventions:** Sentinel token `[APPROVED]` must be emitted *alone on the line with nothing else* to signal loop exit; explicitly instructs the critic not to emit it unless truly satisfied. All other output is treated as actionable feedback piped into `refine`. This asymmetry (single token vs. free-form prose) keeps the EVALUATE branch simple and unambiguous.

**`refine(current TEXT, feedback TEXT)`**
- **Role:** Incorporates the critic's feedback into an improved version of the draft; called once per non-approved iteration.
- **Conventions:** Dual-slot prompt (`{current}` + `{feedback}`); persona is "expert writer"; imperative instruction ("Write the improved version now") minimises preamble in the output.

---

### 5. Control Flow

1. **Initialise** — set `@iteration = 0`, generate the initial `@current` draft via `draft(@task)`, write `draft_0.md`.
2. **WHILE loop** — repeat while `@iteration < @max_iterations`:
   - GENERATE `critique(@current)` → `@feedback`, write `feedback_{@iteration}.md`.
   - EVALUATE `@feedback`:
     - **`contains('[APPROVED]')`** → write `final.md`, RETURN `@current` with `status = 'complete'` and current iteration count. Loop exits immediately.
     - **ELSE** → increment `@iteration`, GENERATE `refine(@current, @feedback)` → `@current`, write `draft_{@iteration}.md`, continue loop.
3. **Loop exhausted** — write `final.md`, RETURN `@current` with `status = 'max_iterations'` and `@iteration`.
4. **Exception path** — `MaxIterationsReached` writes `final.md` and returns `status = 'partial'`; `BudgetExceeded` returns `status = 'budget_limit'` immediately (no file write).

The only branching construct with observable consequences is the EVALUATE inside the loop; all other flow is linear.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Build a self_refine workflow that generates an initial
draft for a user-supplied task using a writer model, then iteratively critiques it
with a critic model and refines it until the critic emits [APPROVED] or max_iterations
is reached. Use three prompt functions: draft, critique (sentinel [APPROVED]), and
refine. Log every artifact to a configurable log_dir via write_file. Return the best
output with status=complete, max_iterations, partial, or budget_limit." --mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```