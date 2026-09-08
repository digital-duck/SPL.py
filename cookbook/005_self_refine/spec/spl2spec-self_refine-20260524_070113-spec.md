## Summary

This workflow implements the **Self-Refine** pattern: a model writes a first draft, a second model critiques it, and the writer iteratively improves the draft until the critic is satisfied or a maximum iteration count is reached. It is useful for anyone who needs higher-quality written output than a single LLM pass can reliably produce, without manual human review in the loop.

---

## Detailed Specification

### 1. Purpose

Automatically improve a piece of written content through multi-model critique-and-refine cycles until the critic approves it or a budget of iterations is exhausted.

---

### 2. High-level Description

The `self_refine` WORKFLOW accepts a free-text task and produces a polished written response by running a draft–critique–refine loop. It uses three CREATE FUNCTION templates — `draft`, `critique`, and `refine` — each with a distinct prompt role. On entry, `draft` is called once via GENERATE to produce an initial response using a designated writer model. The workflow then enters a WHILE loop bounded by `@max_iterations`: on each iteration, `critique` is called via GENERATE using a separate critic model, and its output is checked with EVALUATE for the sentinel token `[APPROVED]`; if found, the workflow exits early with `RETURN … WITH status='complete'` and the current iteration count. If the critic returns actionable feedback instead, `@iteration` is incremented, `refine` is called via GENERATE to produce an improved draft, and the loop continues. Each intermediate draft and feedback file is persisted to disk via CALL `write_file` side-effects, providing a full audit trail. If the WHILE loop runs to exhaustion, the best-effort draft is committed with `RETURN … WITH status='max_iterations'`. Two EXCEPTION handlers cover the `MaxIterationsReached` and `BudgetExceeded` error types, each writing the current draft to disk and returning an appropriate non-trivial status.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `class GenerateDraftNode` | `CREATE FUNCTION draft(task TEXT)` | Initial generation prompt; writer model only |
| `class CritiqueNode` | `CREATE FUNCTION critique(current TEXT)` | Critic prompt; returns `[APPROVED]` or feedback |
| `class RefineNode` | `CREATE FUNCTION refine(current TEXT, feedback TEXT)` | Writer improvement prompt |
| `class Pipeline / Flow` | `WORKFLOW self_refine` | Top-level orchestration unit with INPUT/OUTPUT declarations |
| Loop counter / iteration state | `@iteration INTEGER` | SPL scalar variable incremented each cycle |
| `while iteration < max_iterations` | `WHILE @iteration < @max_iterations DO … END` | Bounds the critique-refine cycle |
| `if "[APPROVED]" in feedback` | `EVALUATE @feedback WHEN contains('[APPROVED]') THEN … ELSE … END` | Semantic branch on sentinel token |
| `return {"status": "complete"}` | `RETURN @current WITH status='complete', iterations=@iteration` | Early-exit on critic approval |
| `return {"status": "max_iterations"}` | `RETURN @current WITH status='max_iterations', iterations=@iteration` | Loop-exhaustion exit |
| `except MaxIterationsReached` | `EXCEPTION WHEN MaxIterationsReached THEN … RETURN … WITH status='partial'` | Typed error recovery |
| `except BudgetExceeded` | `EXCEPTION WHEN BudgetExceeded THEN … RETURN … WITH status='budget_limit'` | Token-budget overrun recovery |
| `write_file(path, content)` | `CALL write_file(…) INTO NONE` | Side-effect; persists drafts and feedback to `@log_dir` |
| LLM call with model selection | `GENERATE … WITH OUTPUT BUDGET @output_budget TOKENS USING MODEL @writer_model` | Model is a runtime parameter, not hardcoded |

---

### 4. Logical Functions / Prompts

**`draft(task TEXT)`**
- **Role:** Produces the first candidate response from scratch.
- **Prompt conventions:** Assigns the writer persona ("expert writer"); instructs the model to complete the task "thoroughly and well"; no output format constraints, prose response expected.

**`critique(current TEXT)`**
- **Role:** Acts as a quality gate; either halts the loop or generates improvement instructions.
- **Prompt conventions:** Assigns a "strict critic" persona. Uses `[APPROVED]` as an explicit sentinel token — the model must output *only* that token (nothing else) when no improvements are needed. Otherwise it must provide "specific, actionable feedback". The prompt explicitly warns the model not to output `[APPROVED]` unless truly warranted, reducing false positives.

**`refine(current TEXT, feedback TEXT)`**
- **Role:** Produces an improved draft by applying the critic's feedback.
- **Prompt conventions:** Assigns the same "expert writer" persona as `draft`; both the current draft and the critic's feedback are injected as named sections; instructs the model to "write the improved version now", discouraging meta-commentary.

---

### 5. Control Flow

1. **Initialization** — `@iteration` is set to `0`; `draft` is called once via GENERATE to produce `@current`.
2. **Loop entry** — `WHILE @iteration < @max_iterations`: `critique` is called via GENERATE to produce `@feedback`.
3. **Branch** — `EVALUATE @feedback WHEN contains('[APPROVED]')`:
   - **True path** — writes final file, `RETURN @current WITH status='complete'`, terminating immediately.
   - **False path** — increments `@iteration`, calls `refine` via GENERATE to update `@current`, writes draft file, then loops back to step 2.
4. **Loop exhaustion** — after `@max_iterations` cycles without approval, writes final file and `RETURN @current WITH status='max_iterations'`.
5. **Exceptions** — `MaxIterationsReached` writes current draft and returns `status='partial'`; `BudgetExceeded` returns `status='budget_limit'` immediately (no file write, budget may already be spent).

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Automatically improve a piece of written content through multi-model critique-and-refine cycles until the critic approves it or a budget of iterations is exhausted. Use three prompt functions: draft (writer model, initial response), critique (critic model, returns [APPROVED] sentinel or actionable feedback), and refine (writer model, improves draft from feedback). Loop with WHILE bounded by max_iterations; branch with EVALUATE on [APPROVED]; exit early with status=complete or at exhaustion with status=max_iterations. Persist all intermediate drafts and feedback via write_file side-effects. Handle MaxIterationsReached and BudgetExceeded exceptions." --mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```