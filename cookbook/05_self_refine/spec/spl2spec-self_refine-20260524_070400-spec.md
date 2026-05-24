## Summary

This workflow implements the **Self-Refine** pattern: it generates an initial response to a task, then iteratively critiques and rewrites that response until a critic model approves it or a budget ceiling is reached. It is useful for anyone who wants LLM-generated content to undergo automatic quality review without human intervention, such as developers building content pipelines, research assistants, or documentation tools.

---

## Detailed Specification

### 1. Purpose

Produce a high-quality, critic-approved text response to an arbitrary task by iteratively drafting, critiquing, and refining using two independently configurable LLM models.

---

### 2. High-level Description

The `self_refine` WORKFLOW accepts a task description and orchestrates three CREATE FUNCTIONs — `draft`, `critique`, and `refine` — across a WHILE loop capped by `@max_iterations`. On entry, it calls `draft` via GENERATE to produce an initial response, binding the result to `@current`. The loop then calls `critique` via GENERATE using a separate critic model; the critic either outputs the sentinel token `[APPROVED]` or actionable feedback. An EVALUATE on `@feedback` branches on `contains('[APPROVED]')`: if approved, the workflow RETURNs immediately with `status='complete'` and the iteration count; otherwise it increments `@iteration`, calls `refine` via GENERATE to produce an improved `@current`, and continues. If the WHILE condition exhausts without approval, the workflow RETURNs `@current` with `status='max_iterations'`. The design deliberately separates the writer model (`@writer_model`) from the critic model (`@critic_model`) so each role can be assigned the most cost-effective or capable model independently. Each intermediate artifact — drafts, feedback files, and the final output — is persisted to disk via CALL `write_file` side-effects, making every iteration auditable. EXCEPTION handlers catch `MaxIterationsReached` (writing the last draft and returning `status='partial'`) and `BudgetExceeded` (returning `status='budget_limit'` with whatever content was last produced).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW self_refine` | `WORKFLOW` | Top-level named orchestration unit with typed `INPUT:` / `OUTPUT:` declarations |
| `CREATE FUNCTION draft` | `CREATE FUNCTION` | Prompt template with `{task}` slot; instructs the writer LLM |
| `CREATE FUNCTION critique` | `CREATE FUNCTION` | Prompt template with `{current}` slot; instructs the critic LLM; uses `[APPROVED]` sentinel |
| `CREATE FUNCTION refine` | `CREATE FUNCTION` | Prompt template with `{current}` and `{feedback}` slots; instructs the writer LLM |
| `GENERATE draft(...) INTO @current` | `GENERATE ... INTO @var` | LLM call bound to writer model; result stored in shared state variable |
| `GENERATE critique(...) INTO @feedback` | `GENERATE ... INTO @var` | LLM call bound to critic model; result drives EVALUATE branch |
| `GENERATE refine(...) INTO @current` | `GENERATE ... INTO @var` | LLM call bound to writer model; overwrites `@current` in place |
| `WHILE @iteration < @max_iterations DO` | `WHILE condition DO ... END` | Iterative refinement gate; terminates on budget or approval |
| `EVALUATE @feedback WHEN contains('[APPROVED]')` | `EVALUATE @var WHEN ... THEN ... ELSE ... END` | Semantic branch on sentinel token; drives early-exit vs. continue path |
| `RETURN @current WITH status='complete'` | `RETURN @var WITH status=` | Non-trivial early exit; status drives caller behaviour |
| `RETURN @current WITH status='max_iterations'` | `RETURN @var WITH status=` | Normal loop-exhaustion exit path |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO NONE` | Side-effect tool call; persists drafts/feedback/final to disk |
| `@iteration`, `@current`, `@feedback` | SPL `@var` shared state | Mutable workflow-scoped variables threaded through the loop body |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION WHEN <Type> THEN` | Runtime exception handler; graceful partial-result recovery |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type> THEN` | Token-budget overrun handler; returns last good draft |

---

### 4. Logical Functions / Prompts

**`draft`**
- **Role:** Produces the first version of the response. Called once before the refinement loop begins.
- **Key conventions:** Instructs the LLM to act as an "expert writer" and produce a "high-quality response." No sentinel tokens; free-form text output. Bound exclusively to `@writer_model`.

**`critique`**
- **Role:** Quality-gates the current draft. Its output either terminates the loop early or supplies actionable feedback to drive the next refinement.
- **Key conventions:** Uses a hard sentinel: the model must output exactly `[APPROVED]` and nothing else if the content is acceptable. The prompt explicitly instructs the critic *not* to output `[APPROVED]` unless the content truly needs no further work, reducing false-positive approvals. Bound exclusively to `@critic_model`.

**`refine`**
- **Role:** Rewrites the current draft in light of specific feedback. Called once per non-approved iteration; its output replaces `@current`.
- **Key conventions:** Takes both `{current}` (the draft) and `{feedback}` (the critic's notes) as slots. Instructs the writer to produce an "improved version now," keeping generation grounded in the feedback rather than rewriting freely. Bound exclusively to `@writer_model`.

---

### 5. Control Flow

1. **Initialisation** — `@iteration` is set to `0`; an initial draft is generated and written to `draft_0.md`.
2. **Loop entry** — WHILE `@iteration < @max_iterations`: the critique function is called and its output written to `feedback_N.md`.
3. **EVALUATE branch** — if `@feedback` contains `[APPROVED]`, `final.md` is written and the workflow RETURNs `@current` with `status='complete'` and the current iteration count (early-exit, no further loop iterations).
4. **Refinement path** — otherwise, `@iteration` is incremented, `refine` is called to overwrite `@current`, and `draft_N.md` is written; control returns to the WHILE condition.
5. **Loop exhaustion** — if the WHILE condition becomes false without an approval, `final.md` is written and the workflow RETURNs `@current` with `status='max_iterations'`.
6. **Exception paths** — `MaxIterationsReached` writes `final.md` and returns `status='partial'`; `BudgetExceeded` returns immediately with `status='budget_limit'` using whatever `@current` holds.

The three non-trivial RETURN statuses (`complete`, `max_iterations`, `partial`, `budget_limit`) are all meaningful signals a caller or orchestrating workflow can branch on.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as the text2spl input)
spl3 text2spl --description "Produce a high-quality, critic-approved text response to an \
arbitrary task by iteratively drafting, critiquing, and refining using two independently \
configurable LLM models. The workflow generates an initial draft, then loops up to \
max_iterations times: a critic model reviews the draft and either outputs an [APPROVED] \
sentinel to terminate early or provides actionable feedback; a writer model then refines \
the draft before the next iteration. Each draft and feedback artifact is written to disk. \
The workflow returns with status=complete on approval, status=max_iterations on loop \
exhaustion, and handles MaxIterationsReached and BudgetExceeded exceptions." \
--mode workflow --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```