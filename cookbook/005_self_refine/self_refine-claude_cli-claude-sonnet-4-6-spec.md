## Summary

This workflow implements the Self-Refine pattern: it generates an initial response to a task, then alternates between critiquing and rewriting that response until a critic model signals approval or a maximum number of iterations is reached. It exists to automate quality improvement cycles that would otherwise require human review loops. Content pipelines, writing assistants, and automated document generation systems are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Produce the highest-quality textual response to an arbitrary input task by repeatedly applying LLM-driven critique and revision until the output is explicitly approved or an iteration budget is exhausted.

---

### 2. High-level Description

The `self_refine` WORKFLOW orchestrates three CREATE FUNCTIONs — `draft`, `critique`, and `refine` — in a bounded WHILE loop that implements an automated quality-improvement cycle. An initial response is produced via GENERATE draft(@task) using a dedicated writer model, then immediately persisted as a side-effect via CALL write_file. Inside the WHILE loop, GENERATE critique(@current) invokes a separate critic model whose prompt is designed to emit either the exact sentinel token `[APPROVED]` or specific, actionable feedback; EVALUATE branches on this token — when the sentinel is present the workflow exits early via RETURN with status='complete', and when absent it increments the iteration counter and calls GENERATE refine(@current, @feedback) with the writer model to produce a revised draft. Every intermediate draft and feedback document is logged to disk via CALL write_file, providing full observability of the refinement trajectory. If the WHILE condition is exhausted without approval, the workflow commits the best-effort result via RETURN with status='max_iterations'. The multi-model split — gemma3 as writer, llama3.2 as critic — decouples generative quality from evaluative strictness, allowing each role to be tuned or swapped independently. Two EXCEPTION handlers provide graceful degradation: MaxIterationsReached yields RETURN with status='partial', and BudgetExceeded yields RETURN with status='budget_limit'.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct (as used) | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION draft(task TEXT)` | `CREATE FUNCTION <name>(<params>)` | Prompt template for initial generation; single input slot |
| `CREATE FUNCTION critique(current TEXT)` | `CREATE FUNCTION <name>(<params>)` | Evaluator template; enforces `[APPROVED]` sentinel discipline |
| `CREATE FUNCTION refine(current TEXT, feedback TEXT)` | `CREATE FUNCTION <name>(<params>)` | Revision template; two input slots bind prior draft and feedback |
| `WORKFLOW self_refine INPUT ... OUTPUT` | `WORKFLOW <name> INPUT ... OUTPUT DO ... END` | Top-level named orchestration with typed parameters and declared output |
| `GENERATE draft(@task) ... USING MODEL @writer_model INTO @current` | `GENERATE <fn>(...) INTO @<var>` | LLM call with explicit model selection and output token budget |
| `GENERATE critique(@current) ... USING MODEL @critic_model INTO @feedback` | `GENERATE <fn>(...) INTO @<var>` | LLM call on a different model; result drives EVALUATE branch |
| `GENERATE refine(@current, @feedback) ... INTO @current` | `GENERATE <fn>(...) INTO @<var>` | In-place reassignment of the working draft variable |
| `WHILE @iteration < @max_iterations DO ... END` | `WHILE <cond> DO ... END` | Bounded refinement loop; condition checked before each critique |
| `EVALUATE @feedback WHEN contains('[APPROVED]') THEN ... ELSE ... END` | `EVALUATE @<var> WHEN contains('...') THEN ... ELSE ... END` | Branch on sentinel token; the only non-trivial control-flow decision |
| `CALL write_file(f'...', @current) INTO NONE` | `CALL <tool>(...) INTO @<var>` | File-write side-effect; result discarded via `INTO NONE` |
| `RETURN @current WITH status='complete', iterations=@iteration` | `RETURN @<var> WITH <k>=<v>, ...` | Early-exit path; non-trivial status terminates the loop |
| `RETURN @current WITH status='max_iterations', iterations=@iteration` | `RETURN @<var> WITH <k>=<v>, ...` | Post-loop termination; non-trivial status signals budget exhaustion |
| `EXCEPTION WHEN MaxIterationsReached THEN` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for runaway iteration guard |
| `EXCEPTION WHEN BudgetExceeded THEN` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for token budget overflow |
| `@iteration`, `@current`, `@feedback` | SPL `@<var>` shared state | Mutable variables that persist and mutate across loop iterations |

---

### 4. Logical Functions / Prompts

**`draft`**
- **Role:** Produces the initial candidate response from scratch before any critique has occurred.
- **Key prompt conventions:** Expert writer persona; no output format constraints; no sentinel tokens; prompt is fully open-ended to maximize initial quality.

**`critique`**
- **Role:** Acts as the quality gatekeeper and the sole source of the loop-exit signal.
- **Key prompt conventions:** Strict critic persona; must emit the exact sentinel `[APPROVED]` as the entire response when no meaningful improvements remain; explicitly warned not to emit `[APPROVED]` prematurely; otherwise produces specific, actionable feedback. The sentinel must be exact — EVALUATE uses a `contains('[APPROVED]')` match.

**`refine`**
- **Role:** Produces an improved draft by incorporating the critic's feedback into the previous version.
- **Key prompt conventions:** Expert writer persona; receives both `{current}` (prior draft) and `{feedback}` (critic output) as named slots; instructed to write a complete improved version rather than a diff or partial edit.

---

### 5. Control Flow

**Initialization:** `@iteration` is set to 0 and GENERATE `draft` produces `@current`, which is written to `draft_0.md`.

**WHILE loop (`@iteration < @max_iterations`):** On each pass, GENERATE `critique` runs against the current draft and the result is written to `feedback_{iteration}.md`. EVALUATE then branches:

- **WHEN `[APPROVED]` detected:** `final.md` is written and the workflow exits immediately via RETURN with `status='complete'` and the iteration count — this is the primary happy-path termination.
- **ELSE (feedback present):** `@iteration` is incremented, GENERATE `refine` overwrites `@current`, and the new draft is written to `draft_{iteration}.md` before the WHILE condition is re-evaluated.

**Post-loop (budget exhausted):** If the WHILE condition becomes false without an approval, `final.md` is written and the workflow exits via RETURN with `status='max_iterations'`, signalling best-effort output.

**EXCEPTION handlers:** `MaxIterationsReached` writes `final.md` and returns `status='partial'`; `BudgetExceeded` returns `status='budget_limit'` without a file write, reflecting that no safe output may exist.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl \
  --description "Produce the highest-quality textual response to an arbitrary input task \
by repeatedly applying LLM-driven critique and revision until the output is explicitly \
approved or an iteration budget is exhausted." \
  --mode workflow

# Step 2 — compile to any target runtime
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```