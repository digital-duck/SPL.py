## Summary

This workflow researches a user-supplied topic, analyzes it for key insights, and writes a polished two-paragraph summary — each step delegated to a model best suited for that task. A quality-review loop then refines the draft until it scores above 0.7 (on a 0–1 scale) or exhausts a configurable iteration budget. Non-technical stakeholders receive a final, publication-ready summary with a logged quality score and all intermediate artifacts saved to disk.

---

## Detailed Specification

### 1. Purpose

Produce a high-quality, human-readable summary of any topic by chaining research, analysis, and writing steps across purpose-selected LLM models, then iteratively refining the output until it meets a quality threshold.

### 2. High-level Description

The `multi_model_pipeline` WORKFLOW accepts a topic string, an iteration cap, and a log directory, then orchestrates four CREATE FUNCTIONs in a fixed linear sequence followed by a conditional refinement loop. First, `research` retrieves factual, statistic-rich content about the topic using a fast model suited for retrieval tasks. Second, `analyze` applies a reasoning-oriented model to distill the research into the three most significant insights, each scored by importance. Third, `write_summary` uses a creative model to synthesize the analysis into a two-paragraph narrative covering findings and implications. All three intermediate results are persisted via CALL `write_file` before the refinement phase begins. A WHILE loop (bounded by `@max_iterations`) then repeatedly invokes `quality_check`, a numeric-scoring function that returns a single float between 0.0 and 1.0 averaging clarity, accuracy, and completeness. Inside the loop, EVALUATE branches on that score: if it exceeds 0.7 the workflow immediately RETURNs the draft WITH `status='high_quality'` and the final score; otherwise `write_summary` is called again on the same analysis to regenerate the draft, the iteration counter increments, and the loop continues. If the loop exhausts `@max_iterations` without crossing the threshold, a fallback RETURN emits the best draft WITH `status='max_iterations'`. Named EXCEPTION handlers cover `MaxIterationsReached` and `ModelOverloaded`, each returning the partial draft with a descriptive status token. Every stage logs progress at appropriate levels (INFO, DEBUG, WARN) and writes intermediate artifacts (`research.md`, `analysis.md`, `draft_N.md`, `final.md`) to the log directory.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW multi_model_pipeline` | `WORKFLOW` | Declares the named orchestration entry point with typed INPUT/OUTPUT |
| `CREATE FUNCTION research` | `CREATE FUNCTION` | Prompt template with `{topic}` slot; targets fast retrieval model |
| `CREATE FUNCTION analyze` | `CREATE FUNCTION` | Prompt template with `{facts}` slot; targets reasoning model |
| `CREATE FUNCTION write_summary` | `CREATE FUNCTION` | Prompt template with `{analysis}` slot; targets creative model |
| `CREATE FUNCTION quality_check` | `CREATE FUNCTION` | Prompt template with `{text}` slot; returns a bare float sentinel |
| `GENERATE research(@topic) USING MODEL 'gemma3' INTO @facts` | `GENERATE` | Per-step model selection; result stored in shared `@facts` |
| `GENERATE analyze(@facts) USING MODEL 'gemma3' INTO @analysis` | `GENERATE` | Per-step model selection; result stored in shared `@analysis` |
| `GENERATE write_summary(@analysis) USING MODEL 'gemma3' INTO @draft` | `GENERATE` | Per-step model selection; result stored in mutable `@draft` |
| `GENERATE quality_check(@draft) INTO @quality` | `GENERATE` | No model override; inherits default; output is a numeric score |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect tool; no return value consumed |
| `WHILE @iteration < @max_iterations DO ... END` | `WHILE` | Bounded refinement loop; terminates on threshold or iteration cap |
| `EVALUATE @quality WHEN > 0.7 THEN ... ELSE ... END` | `EVALUATE` | Numeric branch; drives early exit or draft regeneration |
| `RETURN @draft WITH status='high_quality', score=@quality` | `RETURN WITH` | Non-trivial status token drives loop exit and caller behavior |
| `RETURN @draft WITH status='max_iterations', score=@quality` | `RETURN WITH` | Non-trivial fallback status after loop exhaustion |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION` | Named handler; emits `status='partial'` |
| `EXCEPTION WHEN ModelOverloaded` | `EXCEPTION` | Named handler; emits `status='model_overloaded'` |
| `@facts`, `@analysis`, `@draft`, `@quality`, `@iteration` | SPL `@vars` | Shared mutable state across all steps and the refinement loop |

---

### 4. Logical Functions / Prompts

**`research(topic TEXT)`**
- Role: Opens the pipeline by gathering raw factual material — statistics, recent developments — about the topic.
- Prompt conventions: Persona is "research specialist"; instructs thoroughness and factual accuracy; no sentinel token; free-form prose output stored in `@facts`.

**`analyze(facts TEXT)`**
- Role: Reduces raw research to three ranked insights with significance scores.
- Prompt conventions: Persona is "data analyst"; instructs exactly three insights each with a 1–10 significance rating; structured prose output stored in `@analysis`.

**`write_summary(analysis TEXT)`**
- Role: Converts structured analysis into a publication-ready two-paragraph narrative; called once initially and re-called inside the refinement loop on each failed quality check.
- Prompt conventions: Persona is "professional writer"; paragraph 1 = key findings, paragraph 2 = implications and outlook; free-form prose output stored in `@draft`.

**`quality_check(text TEXT)`**
- Role: Numeric gatekeeper that scores the current draft to decide whether the loop continues or exits.
- Prompt conventions: Persona is "quality reviewer"; three named dimensions (clarity, accuracy, completeness); **output must be a single bare float** (0.0–1.0, the average) — this is a sentinel token that EVALUATE reads as a numeric comparand stored in `@quality`.

---

### 5. Control Flow

1. **Initialization** — Log pipeline start; GENERATE `research` → `@facts`; write artifact.
2. **Analysis** — GENERATE `analyze` → `@analysis`; write artifact.
3. **Initial draft** — GENERATE `write_summary` → `@draft`; write `draft_0.md`; set `@iteration := 0`, `@quality := 0`.
4. **Refinement loop** — WHILE `@iteration < @max_iterations`:
   - GENERATE `quality_check(@draft)` → `@quality`.
   - EVALUATE `@quality`:
     - **`> 0.7`** → write `final.md`; RETURN WITH `status='high_quality'` — loop terminates immediately.
     - **ELSE** → GENERATE `write_summary(@analysis)` → `@draft`; increment `@iteration`; write `draft_{N}.md`; continue loop.
5. **Fallback termination** — Loop exits without meeting threshold; write `final.md`; RETURN WITH `status='max_iterations'`.
6. **Exception paths** — `MaxIterationsReached` → RETURN WITH `status='partial'`; `ModelOverloaded` → RETURN WITH `status='model_overloaded'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 1 above as text2spl input)
spl3 text2spl \
  --description "Produce a high-quality, human-readable summary of any topic by chaining research, analysis, and writing steps across purpose-selected LLM models, then iteratively refining the output until it meets a quality threshold." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile multi_model_pipeline.spl --lang python/pocketflow
spl3 splc compile multi_model_pipeline.spl --lang python/langgraph
spl3 splc compile multi_model_pipeline.spl --lang go
```