## Summary

This workflow teaches a topic to a specific audience by composing three reusable inner procedures — explanation, example generation, and reading-level calibration — under a single outer orchestrator. It exists to demonstrate how SPL supports deep composability through `PROCEDURE` units that can be called from a `WORKFLOW` (or from each other) without external orchestration. Content creators, educators, and documentation teams benefit by getting audience-tuned articles at configurable depth.

---

## Detailed Specification

### 1. Purpose

Generate a polished, audience-calibrated explanatory article on any topic by delegating subtasks to reusable inner procedures and assembling their outputs into a final result.

---

### 2. High-level Description

The `layered_explainer` WORKFLOW accepts a topic, a target audience, and an optional depth level, then produces a finished article in five sequential steps. It opens with a GENERATE call to `research_overview` that grounds all subsequent work in factual content. The resulting overview is passed via CALL to the `explain_layer` PROCEDURE, which itself issues a GENERATE to `explain` to produce a clear, jargon-free base explanation. Concurrently in logic (though sequentially in execution), a second CALL invokes the `make_example` PROCEDURE to produce a concrete illustrative example by calling `concrete_example` with the topic, base explanation, and audience as context. A third CALL delegates to the `calibrate_complexity` PROCEDURE, which first GENERATEs a reading-level assessment via `assess_reading_level`, then uses an EVALUATE branch to either GENERATE a simplified version (if the score exceeds the target grade of 8) or pass the text through unchanged — this is the only non-trivial control-flow branch in the system. All three procedure outputs converge in a final GENERATE call to `assemble_article`, which produces `@article`; the WORKFLOW then RETURNs `@article` with metadata `status='complete'` and the audience label. No exception handlers are defined; the system relies on each PROCEDURE's own scope to isolate failures.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW layered_explainer` | `WORKFLOW` | Top-level orchestrator; owns `@topic`, `@audience`, `@depth` |
| `PROCEDURE explain_layer(...)` | `CREATE FUNCTION` (reusable unit) | Inner procedure; encapsulates explanation prompt |
| `PROCEDURE make_example(...)` | `CREATE FUNCTION` (reusable unit) | Inner procedure; encapsulates example-generation prompt |
| `PROCEDURE calibrate_complexity(...)` | `CREATE FUNCTION` with internal EVALUATE | Inner procedure; contains the sole branch in the system |
| `GENERATE research_overview(@topic)` | `GENERATE <fn>(...)  INTO @var` | Produces raw factual overview |
| `GENERATE explain(...)` | `GENERATE <fn>(...) INTO @var` | Inside `explain_layer`; core explanation call |
| `GENERATE concrete_example(...)` | `GENERATE <fn>(...) INTO @var` | Inside `make_example`; produces illustrative example |
| `GENERATE assess_reading_level(...)` | `GENERATE <fn>(...) INTO @var` | Inside `calibrate_complexity`; drives EVALUATE |
| `GENERATE simplify(...)` | `GENERATE <fn>(...) INTO @var` | Conditional call within `calibrate_complexity` |
| `GENERATE assemble_article(...)` | `GENERATE <fn>(...) INTO @var` | Final assembly step in WORKFLOW |
| `CALL explain_layer(...) INTO @var` | `CALL <procedure>(...) INTO @var` | Invokes inner PROCEDURE from WORKFLOW |
| `CALL make_example(...) INTO @var` | `CALL <procedure>(...) INTO @var` | Invokes inner PROCEDURE from WORKFLOW |
| `CALL calibrate_complexity(...) INTO @var` | `CALL <procedure>(...) INTO @var` | Invokes inner PROCEDURE from WORKFLOW |
| `EVALUATE @reading_level WHEN > target_grade` | `EVALUATE @var WHEN ... THEN ... ELSE` | Only branch; decides whether to simplify |
| `RETURN @article WITH status='complete'` | `RETURN @var WITH k=v` | Non-trivial: carries `status` and `audience` metadata |
| `@overview`, `@base_explanation`, `@example`, `@calibrated_explanation`, `@article` | Shared SPL `@vars` | Intermediate state passed between steps and procedures |
| `TEXT DEFAULT 'clear and engaging'`, `INT DEFAULT 8` | Typed parameters with defaults | PROCEDURE parameter defaults; no external config needed |

---

### 4. Logical Functions / Prompts

**`research_overview`**
- Role: Kicks off the workflow by gathering factual, structured background on `@topic`.
- Conventions: Output should be comprehensive enough to serve as source material for the explanation step; no audience tuning at this stage.

**`explain`** (inside `explain_layer`)
- Role: Transforms raw overview content into a readable explanation tailored to the given audience and style.
- Conventions: Accepts a `style` parameter (default `'clear and engaging'`); should avoid domain jargon unless the audience demands it.

**`concrete_example`** (inside `make_example`)
- Role: Produces one specific, relatable example grounded in the base explanation to make the concept tangible.
- Conventions: Uses both `context` (the base explanation) and `audience` so the example matches the reader's frame of reference.

**`assess_reading_level`** (inside `calibrate_complexity`)
- Role: Returns a numeric or ordinal reading-grade signal for the provided text.
- Conventions: Output must be comparable to `target_grade` (integer); the EVALUATE branch interprets `> target_grade` as "too complex".

**`simplify`** (inside `calibrate_complexity`, conditional)
- Role: Rewrites the text to a lower reading level while preserving meaning.
- Conventions: Only invoked when `assess_reading_level` exceeds the threshold; otherwise the original text passes through unchanged.

**`assemble_article`**
- Role: Combines `@topic`, `@calibrated_explanation`, `@example`, and `@depth` into a coherent, publication-ready article.
- Conventions: The `@depth` parameter (`'standard'` or `'deep'`) controls verbosity/thoroughness of the final output.

---

### 5. Control Flow

1. **Entry** — WORKFLOW receives `@topic`, `@audience`, and optional `@depth`.
2. **Research** — GENERATE `research_overview` populates `@overview`.
3. **Explain** — CALL `explain_layer` (which internally GENERATEs `explain`) produces `@base_explanation`.
4. **Example** — CALL `make_example` (which internally GENERATEs `concrete_example`) produces `@example`.
5. **Calibrate (branch)** — CALL `calibrate_complexity` executes the system's only non-trivial branch:
   - GENERATE `assess_reading_level(@base_explanation)` → `@reading_level`
   - EVALUATE `@reading_level`:
     - **WHEN > 8** → GENERATE `simplify` → RETURN simplified text as `@calibrated_explanation`
     - **ELSE** → RETURN original text as `@calibrated_explanation`
6. **Assemble** — GENERATE `assemble_article` merges all collected variables into `@article`.
7. **Termination** — RETURN `@article` WITH `status='complete'`, `audience=@audience`. No loop; single-pass execution.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a polished, audience-calibrated explanatory article on any topic by delegating subtasks to reusable inner procedures and assembling their outputs into a final result." --mode workflow

# Step 2 — compile to any target
spl3 splc compile nested_procs.spl --lang python/pocketflow
spl3 splc compile nested_procs.spl --lang python/langgraph
spl3 splc compile nested_procs.spl --lang go
```