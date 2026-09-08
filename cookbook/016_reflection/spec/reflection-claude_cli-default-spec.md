## Summary

The Reflection Agent solves a given problem and then iteratively critiques its own answer, extracting specific issues and producing corrections until it reaches high confidence or exhausts a maximum number of reflection rounds. It exists to catch reasoning errors and gaps that a single-pass LLM response would miss. Engineers and researchers building quality-sensitive Q&A or analysis pipelines benefit most.

---

## Detailed Specification

### 1. Purpose

Produce a high-confidence, self-corrected answer to an open-ended problem by running a meta-cognitive loop that reflects on, scores, and revises the answer before committing.

---

### 2. High-level Description

The WORKFLOW `reflection_agent` accepts a problem statement, a maximum reflection budget, and a log directory, then emits a final answer with provenance metadata. It begins with a single GENERATE call to `solve`, producing an initial candidate answer that is immediately persisted via CALL `write_file`. A WHILE loop then iterates up to `@max_reflections` times: each iteration GENERATEs a `reflect` critique of the current answer, GENERATEs a `confidence_score` that yields a numeric value in (0, 1], and branches on that score using EVALUATE. When the score exceeds 0.85, the workflow writes the answer to `final.md` and RETURNs early with `status='confident'`; otherwise it GENERATEs `extract_issues` to distill actionable problems from the reflection, then GENERATEs `correct` to produce a revised answer, increments the iteration counter, and continues the loop. If the loop exhausts its budget, the best answer is committed with `status='best_effort'`. Two EXCEPTION handlers cover `MaxIterationsReached` (persist and return with `status='max_reflections'`) and `HallucinationDetected` (restart from a fresh `solve` call with `status='restarted'`). All intermediate artifacts — each candidate answer and each reflection — are logged to disk, providing a full audit trail of the reasoning evolution.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW reflection_agent` | `WORKFLOW <name>` | Declares the orchestration entry point with typed INPUT/OUTPUT |
| `solve`, `reflect`, `confidence_score`, `extract_issues`, `correct` | `CREATE FUNCTION <name>` | Five reusable prompt templates, each with `{param}` slots |
| `GENERATE solve(@problem) INTO @answer` | `GENERATE <fn>(...) INTO @<var>` | LLM call; result stored in `@answer` |
| `GENERATE reflect(...)`, `GENERATE confidence_score(...)`, etc. | `GENERATE <fn>(...) INTO @<var>` | All five functions follow the same GENERATE pattern |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO @<var>` | Side-effect tool call; result discarded (`NONE`) |
| `WHILE @iteration < @max_reflections DO ... END` | `WHILE <cond> DO ... END` | Bounds the reflection loop |
| `EVALUATE @confidence WHEN > 0.85 THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Numeric threshold branch; drives early exit vs. correction path |
| `RETURN @answer WITH status='confident', confidence=..., reflections=...` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial exit: confidence gate passed |
| `RETURN @answer WITH status='best_effort', ...` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial exit: loop budget exhausted |
| `EXCEPTION WHEN MaxIterationsReached THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named handler; persists answer before returning |
| `EXCEPTION WHEN HallucinationDetected THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named handler; resets by re-running `solve` |
| `@problem`, `@answer`, `@reflection`, `@issues`, `@confidence`, `@iteration` | Shared state (`@vars`) | Mutable variables threaded through all GENERATE and EVALUATE steps |

---

### 4. Logical Functions / Prompts

**`solve`**
- **Role:** Initial answer generation — the first-pass response to the problem with no prior context.
- **Key conventions:** Takes only `@problem` as input; expected to produce a complete, structured answer. Sets the baseline that all subsequent steps evaluate and revise.

**`reflect`**
- **Role:** Meta-cognitive critic — examines the current answer against the original problem to identify logical errors, missing cases, unsupported claims, or weak reasoning.
- **Key conventions:** Takes `@problem` and `@answer`; output is free-form critique prose. Does not itself propose fixes — diagnosis only.

**`confidence_score`**
- **Role:** Numeric assessor — converts the reflection critique into a scalar confidence value in the range (0, 1].
- **Key conventions:** Takes `@answer` and `@reflection`; must output a parseable float so the EVALUATE threshold (`> 0.85`) can fire. Acts as the loop termination signal.

**`extract_issues`**
- **Role:** Issue distiller — transforms verbose reflection prose into a concise, actionable list of specific problems to fix.
- **Key conventions:** Takes `@reflection`; output (`@issues`) is passed directly to `correct`, so it should be structured enough to guide targeted revision (e.g., numbered list or bullet points).

**`correct`**
- **Role:** Revision engine — rewrites the answer by addressing the extracted issues while staying grounded on the original problem.
- **Key conventions:** Takes `@answer`, `@issues`, and `@problem`; returns a complete revised answer (not a diff). Overwrites `@answer` in place for the next iteration.

---

### 5. Control Flow

1. **Init:** `@iteration := 0`, `@confidence := 0`; log start.
2. **Bootstrap:** GENERATE `solve(@problem)` → `@answer`; CALL `write_file` → `answer_0.md`.
3. **WHILE** `@iteration < @max_reflections`:
   - GENERATE `reflect(@problem, @answer)` → `@reflection`; write `reflection_{i}.md`.
   - GENERATE `confidence_score(@answer, @reflection)` → `@confidence`.
   - **EVALUATE** `@confidence`:
     - **> 0.85 →** write `final.md`; **RETURN** `status='confident'` *(early exit, loop terminates)*.
     - **ELSE →** GENERATE `extract_issues(@reflection)` → `@issues`; GENERATE `correct(@answer, @issues, @problem)` → `@answer`; `@iteration += 1`; write `answer_{i}.md`; continue loop.
4. **Post-loop (budget exhausted):** write `final.md`; **RETURN** `status='best_effort'`.
5. **EXCEPTION `MaxIterationsReached`:** write `final.md`; RETURN `status='max_reflections'`.
6. **EXCEPTION `HallucinationDetected`:** re-run GENERATE `solve(@problem)` → `@answer`; RETURN `status='restarted'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Produce a high-confidence, self-corrected answer to an open-ended problem by running a meta-cognitive loop that reflects on, scores, and revises the answer before committing. The WORKFLOW accepts a problem, a max-reflections budget, and a log directory. It calls solve once to get an initial answer, then enters a WHILE loop: each iteration calls reflect to critique the answer, confidence_score to get a numeric score, and branches via EVALUATE — if score > 0.85, write final.md and RETURN status=confident; otherwise call extract_issues and correct to revise the answer and continue. On budget exhaustion, RETURN status=best_effort. EXCEPTION handlers cover MaxIterationsReached and HallucinationDetected." --mode workflow

# Step 2 — compile to any target
spl3 splc compile reflection_agent.spl --lang python/pocketflow
spl3 splc compile reflection_agent.spl --lang python/langgraph
spl3 splc compile reflection_agent.spl --lang go
```