## Summary

This workflow implements a multi-stage research-to-prose pipeline where a topic is progressively transformed through research, analysis, and writing steps, each potentially assigned to a different LLM model. A quality-gated refinement loop then iterates on the final draft until a numeric quality threshold is met or a maximum iteration count is reached. Non-technical stakeholders benefit from receiving a polished, quality-assured written summary on any topic, with intermediate artifacts saved to disk for auditing.

---

## Detailed Specification

### 1. Purpose

Given a freeform topic string, produce a high-quality two-paragraph prose summary by chaining a research agent, an analysis agent, and a writing agent, then iteratively refining the draft until a quality reviewer scores it above 0.7.

---

### 2. High-level Description

The `multi_model_pipeline` WORKFLOW accepts a topic, a maximum iteration count (default 3), and a log directory. It first invokes three sequential GENERATE calls — `research`, `analyze`, and `write_summary` — each targeting a designated model via `USING MODEL`, and persists each intermediate result to disk with CALL `write_file`. After this linear pipeline produces an initial draft, the workflow enters a WHILE loop bounded by `@max_iterations`. Inside the loop, a GENERATE call to `quality_check` returns a numeric score (0.0–1.0); an EVALUATE block branches on that score: if it exceeds 0.7, the workflow immediately writes the final artifact and issues a RETURN WITH `status = 'high_quality'`, terminating the loop early; otherwise `write_summary` is called again against the already-computed analysis, the iteration counter is incremented, and the new draft is saved. If the loop exhausts all iterations without meeting the threshold, the workflow falls through to a RETURN WITH `status = 'max_iterations'`. Two EXCEPTION handlers cover typed runtime errors (`MaxIterationsReached`, `ModelOverloaded`), each returning the best available draft with a distinct status token.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `PocketFlow Node` | `CREATE FUNCTION` | Each logical agent role is a named prompt template |
| `Node.exec()` | `GENERATE <fn>(...) INTO @var` | Executes one LLM call and captures output |
| `GENERATE ... USING MODEL` | `GENERATE <fn>(...) USING MODEL '<id>' INTO @var` | Per-step model selection; decouples task from provider |
| `write_file side-effect` | `CALL write_file(...) INTO NONE` | Persists artifacts without consuming the result |
| `iterative refinement loop` | `WHILE @iteration < @max_iterations DO ... END` | Bounded retry with counter guard |
| `score threshold branch` | `EVALUATE @quality WHEN > 0.7 THEN ... ELSE ... END` | Semantic branch on numeric LLM output |
| `early exit on quality` | `RETURN @draft WITH status = 'high_quality', score = @quality` | Non-trivial status drives loop termination |
| `loop exhausted exit` | `RETURN @draft WITH status = 'max_iterations', score = @quality` | Fallback path after WHILE exits normally |
| `typed error recovery` | `EXCEPTION WHEN MaxIterationsReached / ModelOverloaded THEN` | Named exception handlers with distinct status tokens |
| `shared pipeline state` | `@facts`, `@analysis`, `@draft`, `@quality`, `@iteration` | SPL `@vars` thread state across all steps |

---

### 4. Logical Functions / Prompts

**`research(topic TEXT)`**
- Role: Opens the pipeline; acts as a domain expert to gather factual grounding material.
- Prompt conventions: Instructs the model to focus on accuracy, include statistics and recent developments, and keep output concise. No sentinel tokens; output is free-form prose used as context for the next step.

**`analyze(facts TEXT)`**
- Role: Mid-pipeline reasoning step; distills raw research into three prioritised insights.
- Prompt conventions: Requires exactly three insights, each accompanied by a significance rating on a 1–10 integer scale. Structured output (numbered list with rating) makes downstream writing deterministic.

**`write_summary(analysis TEXT)`**
- Role: Converts structured analysis into polished, human-readable prose; called once initially and again on each refinement iteration.
- Prompt conventions: Mandates exactly two paragraphs — first for findings, second for implications/outlook. No scoring or sentinel tokens; output is the candidate draft.

**`quality_check(text TEXT)`**
- Role: Acts as an automated quality gate; the sole source of the numeric signal that drives the WHILE/EVALUATE control flow.
- Prompt conventions: Instructs the model to return **only** a single floating-point number (0.0–1.0) representing the average of clarity, accuracy, and completeness scores. The bare-number output contract is critical: the EVALUATE condition performs a numeric comparison directly against `@quality`.

---

### 5. Control Flow

1. **Initialisation** — LOGGING emits a pipeline-start event; `@iteration` and `@quality` are set to 0.
2. **Linear pipeline** — Three sequential GENERATE calls transform `@topic → @facts → @analysis → @draft`; each result is written to disk via CALL `write_file`.
3. **Quality loop** — WHILE `@iteration < @max_iterations`:
   - GENERATE `quality_check(@draft)` → `@quality`
   - EVALUATE `@quality`:
     - `WHEN > 0.7`: write final file, RETURN WITH `status = 'high_quality'` — **loop exits immediately**.
     - `ELSE`: regenerate draft from `@analysis`, increment `@iteration`, persist new draft — **loop continues**.
4. **Loop exhaustion fallback** — If WHILE exits naturally (counter reaches `@max_iterations` without meeting threshold), write final file and RETURN WITH `status = 'max_iterations'`.
5. **Exception paths** — `MaxIterationsReached` → RETURN WITH `status = 'partial'`; `ModelOverloaded` → RETURN WITH `status = 'model_overloaded'`. Both yield the best available `@draft`.

The three non-trivial RETURN status tokens (`high_quality`, `max_iterations`, `partial`, `model_overloaded`) allow a calling workflow to branch on outcome quality.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 1 as the description)
spl3 text2spl --description "Given a freeform topic string, produce a high-quality \
two-paragraph prose summary by chaining a research agent, an analysis agent, and a \
writing agent, then iteratively refining the draft until a quality reviewer scores \
it above 0.7." --mode workflow

# Step 2 — compile to any target
spl3 splc compile multi_model_pipeline.spl --lang python/pocketflow
spl3 splc compile multi_model_pipeline.spl --lang python/langgraph
spl3 splc compile multi_model_pipeline.spl --lang go
```