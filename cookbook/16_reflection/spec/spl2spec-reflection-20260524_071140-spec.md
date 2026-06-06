## Summary

The Reflection Agent solves a problem and then critiques its own answer in a loop, correcting errors until it reaches a confidence threshold or exhausts the allowed number of reflections. This meta-cognitive pattern catches reasoning gaps and shallow answers that a single LLM pass would miss. It benefits developers building high-stakes Q&A, system design, or explanation workflows where answer quality matters more than latency.

---

## Detailed Specification

### 1. Purpose

Iteratively improve an LLM-generated answer by having the model reflect on and score its own reasoning, extracting specific issues and rewriting the answer until confidence exceeds 0.85 or a maximum reflection budget is exhausted.

---

### 2. High-level Description

The `reflection_agent` WORKFLOW accepts a free-text `@problem`, a reflection budget `@max_reflections` (default 3), and a log directory. It opens with a single GENERATE call to `solve`, which produces an initial `@answer`. A WHILE loop then drives up to `@max_reflections` correction cycles: each iteration calls GENERATE `reflect` to produce a self-critique, then GENERATE `confidence_score` to extract a numeric confidence in the current answer. An EVALUATE block tests whether `@confidence > 0.85`; if so, the workflow exits early with `status='confident'`. Otherwise, GENERATE `extract_issues` distills the reflection into a concrete issue list, and GENERATE `correct` rewrites `@answer` incorporating those issues before the loop counter advances. After every LLM call, a CALL to `write_file` persists intermediate results for observability. If the loop runs to completion without crossing the threshold, the workflow RETURNs with `status='best_effort'`. Two EXCEPTION handlers cover `MaxIterationsReached` (commits the current answer with `status='max_reflections'`) and `HallucinationDetected` (restarts from a fresh GENERATE `solve` call and returns `status='restarted'`).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW reflection_agent` | `WORKFLOW` | Entry point; declares `INPUT`/`OUTPUT` contract |
| `solve`, `reflect`, `confidence_score`, `extract_issues`, `correct` | `CREATE FUNCTION` | Five prompt templates, each with a distinct role |
| `GENERATE solve(...) INTO @answer` | `GENERATE` | Initial LLM call; result bound to `@answer` |
| `GENERATE reflect(...) INTO @reflection` | `GENERATE` | Self-critique call; result bound to `@reflection` |
| `GENERATE confidence_score(...) INTO @confidence` | `GENERATE` | Numeric scoring call; drives loop exit condition |
| `GENERATE extract_issues(...) INTO @issues` | `GENERATE` | Distillation call; feeds `correct` |
| `GENERATE correct(...) INTO @answer` | `GENERATE` | Rewrite call; mutates `@answer` in place |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect only; persists logs, no return value consumed |
| `WHILE @iteration < @max_reflections DO ... END` | `WHILE` | Bounds the reflection budget |
| `EVALUATE @confidence WHEN > 0.85 THEN ... ELSE ... END` | `EVALUATE` | Numeric branch; early-exit vs. correction path |
| `RETURN @answer WITH status='confident'` | `RETURN WITH status=` | Non-trivial early exit; status drives caller branching |
| `RETURN @answer WITH status='best_effort'` | `RETURN WITH status=` | Budget-exhausted termination |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION WHEN` | Fallback if runtime raises max-iterations error |
| `EXCEPTION WHEN HallucinationDetected` | `EXCEPTION WHEN` | Recovery by restarting from `solve` |
| `@iteration`, `@confidence`, `@answer`, `@reflection`, `@issues` | SPL `@vars` | Shared mutable state across all steps in the workflow frame |

---

### 4. Logical Functions / Prompts

**`solve(@problem)`**
- Role: Produces the initial candidate answer to the problem.
- Conventions: Open-ended generation; no sentinel tokens. Output is prose or structured reasoning depending on the problem type.

**`reflect(@problem, @answer)`**
- Role: Meta-cognitive self-critique. Given the original problem and the current answer, the model identifies logical errors, missing considerations, weak reasoning, or factual gaps.
- Conventions: Output is a critique document (prose). Should be grounded against `@problem` to avoid generic feedback.

**`confidence_score(@answer, @reflection)`**
- Role: Translates the reflection into a single numeric confidence score for the current answer.
- Conventions: Output must be parseable as a float in [0, 1]. The EVALUATE threshold is `> 0.85`. Prompt should instruct the model to return only the number or a clearly delimited field.

**`extract_issues(@reflection)`**
- Role: Distills the free-form reflection into a structured, actionable list of specific issues to fix.
- Conventions: Output is a concise list (bullet or numbered). Feeds directly into `correct` as the repair agenda.

**`correct(@answer, @issues, @problem)`**
- Role: Rewrites `@answer` by addressing each item in `@issues` while staying grounded in `@problem`.
- Conventions: Should produce a complete replacement answer, not a diff or patch. Output overwrites `@answer` for the next loop iteration.

---

### 5. Control Flow

1. **Initialization** — `@iteration` and `@confidence` are set to 0; GENERATE `solve` produces the first `@answer`; `answer_0.md` is written.
2. **WHILE loop entry** — condition: `@iteration < @max_reflections` (default upper bound: 3).
3. **Per-iteration body**:
   - GENERATE `reflect` → `@reflection` → written to `reflection_{i}.md`
   - GENERATE `confidence_score` → `@confidence`
   - EVALUATE `@confidence`:
     - **`> 0.85` branch** → write `final.md`, RETURN WITH `status='confident'` (early exit, loop terminates)
     - **ELSE branch** → GENERATE `extract_issues` → `@issues`; GENERATE `correct` → new `@answer`; `@iteration` incremented; write `answer_{i}.md`
4. **Loop exhaustion** — if WHILE exits normally (budget spent, confidence never crossed threshold): write `final.md`, RETURN WITH `status='best_effort'`.
5. **Exception paths**:
   - `MaxIterationsReached` — write `final.md`, RETURN WITH `status='max_reflections'`
   - `HallucinationDetected` — GENERATE `solve` (fresh start), RETURN WITH `status='restarted'`

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2, High-level Description, as input)
spl3 text2spl --description "Build a reflection_agent WORKFLOW that accepts a free-text
problem, a max_reflections budget (default 3), and a log directory. Generate an initial
answer with a solve function, then run a WHILE loop up to max_reflections times. Each
iteration: generate a self-critique with reflect, score confidence with confidence_score,
and EVALUATE whether confidence exceeds 0.85. If so, write final.md and RETURN with
status=confident. Otherwise, extract specific issues with extract_issues, rewrite the
answer with correct, increment the iteration counter, and persist intermediate files via
CALL write_file. If the loop exhausts the budget, RETURN with status=best_effort.
Handle MaxIterationsReached and HallucinationDetected exceptions." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile reflection_agent.spl --lang python/pocketflow
spl3 splc compile reflection_agent.spl --lang python/langgraph
spl3 splc compile reflection_agent.spl --lang go
```