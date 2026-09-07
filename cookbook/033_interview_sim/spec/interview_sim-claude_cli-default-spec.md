## Summary

The Interview Simulator is a multi-step LLM workflow that stages a realistic technical interview between two simulated personas — an interviewer and a job candidate — and then scores and narrates the result. It generates a complete question set upfront, has the candidate answer each question in character, evaluates every answer against a four-dimension rubric, and compiles everything into a polished evaluation report. Hiring managers, engineering teams, and candidate-coaching tools benefit by getting a reproducible, scored mock interview on any role, focus area, and difficulty level without human involvement.

---

## Detailed Specification

### 1. Purpose

Automate a full technical mock interview — question generation, candidate answering, per-answer scoring, and narrative evaluation — so that any role, focus area, and difficulty level can be rehearsed or assessed programmatically.

---

### 2. High-level Description

The `interview_sim` WORKFLOW accepts a role definition (either via a catalog key or freeform text), a candidate profile identifier, and session parameters (focus area, difficulty, number of questions, years of experience). It opens with two deterministic CALL steps that load the role-context document and candidate-profile document from external tools, grounding all subsequent LLM calls in concrete, stable reference material rather than model hallucination. A single GENERATE call then produces the full question set at once — avoiding per-question round-trips — after which three deterministic CALL steps unpack each individual question from the JSON payload.

Three parallel GENERATE calls (one per question) invoke the `answer_question` prompt, injecting both the `candidate_persona` function and the loaded candidate profile so the model stays in character. Three further GENERATE calls invoke `score_answer` using the `evaluation_rubric` function, which enforces a strict JSON output contract covering accuracy, depth, communication, experience (each 0–10), a computed total, and a one-sentence feedback string. The scores are then consolidated by a deterministic CALL to `aggregate_scores`, the full Q&A is assembled into a human-readable transcript by `compile_transcript`, and a final GENERATE call to `overall_evaluation` synthesises a narrative report grounded by those deterministic aggregates. On successful completion the WORKFLOW returns the evaluation report with `status='complete'`; an EXCEPTION handler for `GenerationError` degrades gracefully by returning the partial transcript with `status='partial'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW interview_sim` | `WORKFLOW <name>` | Top-level orchestration; declares typed INPUT/OUTPUT variables |
| `CREATE FUNCTION interviewer_persona` | `CREATE FUNCTION <name>` | Zero-LLM-cost system-prompt template injected as argument to GENERATE |
| `CREATE FUNCTION candidate_persona` | `CREATE FUNCTION <name>` | Zero-LLM-cost persona template; parameterised by role and experience |
| `CREATE FUNCTION evaluation_rubric` | `CREATE FUNCTION <name>` | Zero-LLM-cost rubric template; enforces JSON-only output contract |
| `CALL load_role(...)` | `CALL <tool>(...)` | Deterministic side-effect tool; returns role context document |
| `CALL load_candidate(...)` | `CALL <tool>(...)` | Deterministic side-effect tool; returns candidate profile |
| `CALL extract_question(...)` | `CALL <tool>(...)` | Deterministic JSON parse; replaces an LLM ask-question step |
| `CALL aggregate_scores(...)` | `CALL <tool>(...)` | Deterministic score summation; avoids LLM arithmetic errors |
| `CALL compile_transcript(...)` | `CALL <tool>(...)` | Deterministic assembly of Q&A pairs into formatted transcript |
| `GENERATE generate_question_set(...)` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call produces full question batch; grounded by role context |
| `GENERATE answer_question(...)` | `GENERATE <fn>(...) INTO @<var>` | One call per question; persona and profile injected as context |
| `GENERATE score_answer(...)` | `GENERATE <fn>(...) INTO @<var>` | One call per answer; rubric function enforces strict JSON output |
| `GENERATE overall_evaluation(...)` | `GENERATE <fn>(...) INTO @<var>` | Final narrative; grounded by deterministic aggregated scores |
| `@role_context`, `@candidate_profile`, `@score1`…`@score3`, etc. | Shared `@<var>` state | Variables flow across CALL and GENERATE steps throughout the workflow |
| `RETURN @evaluation_report WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial terminal status; confirms full pipeline success |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN <Type> THEN` | Catches LLM failures; returns partial transcript with `status='partial'` |

---

### 4. Logical Functions / Prompts

**`interviewer_persona(role, focus, difficulty)`**
- *Role:* Provides the system-prompt context for the interviewer agent. Injected as an argument to `generate_question_set` so the question-generation LLM adopts the correct professional stance.
- *Key conventions:* Instructs the model to ask exactly one question at a time, probe shallow answers, stay neutral, and withhold model-answer hints. No sentinel tokens; this is a persona injection, not a generation target.

**`candidate_persona(role, experience)`**
- *Role:* Provides the system-prompt context for the candidate agent. Injected into each `answer_question` call alongside the loaded candidate profile.
- *Key conventions:* Instructs the model to think aloud, reference plausible real-world experiences, acknowledge gaps honestly, and avoid bluffing. No sentinel tokens; pure persona framing.

**`evaluation_rubric()`**
- *Role:* Provides the scoring rubric injected into each `score_answer` call. Acts as both instruction and output-format contract.
- *Key conventions:* Defines four scored dimensions (accuracy, depth, communication, experience), each 0–10, plus a computed `total` (max 40) and a `feedback` string. Enforces **valid JSON only** — explicitly prohibits prose outside the JSON object. This sentinel contract allows `aggregate_scores` to parse output deterministically.

**`generate_question_set`** *(GENERATE target)*
- *Role:* Generates the complete set of interview questions in a single LLM call, returning a JSON array. Grounded by the role-context document and the interviewer persona.
- *Key conventions:* Batches all questions upfront to reduce round-trips; output is a structured JSON array consumed by the deterministic `extract_question` tool.

**`answer_question`** *(GENERATE target)*
- *Role:* Generates a candidate response to a single question, in character, grounded by the candidate profile document.
- *Key conventions:* Receives the question text, role, role context, candidate profile, and the candidate persona prompt; produces free-text prose in the candidate's voice.

**`score_answer`** *(GENERATE target)*
- *Role:* Evaluates a single candidate answer against the rubric, producing structured scores and feedback.
- *Key conventions:* Must return valid JSON matching the `evaluation_rubric` schema (`accuracy`, `depth`, `communication`, `experience`, `total`, `feedback`). Downstream `aggregate_scores` depends on this contract.

**`overall_evaluation`** *(GENERATE target)*
- *Role:* Synthesises a final narrative evaluation report combining the compiled transcript, aggregated scores, role/focus metadata, and the candidate profile.
- *Key conventions:* Receives deterministic inputs (transcript, agg_scores) to ensure the narrative is grounded rather than confabulated; produces the workflow's primary output variable `@evaluation_report`.

---

### 5. Control Flow

The workflow is **linear with a single error branch** — there is no WHILE loop and no EVALUATE branch in the happy path.

1. **Initialisation** — LOGGING records session parameters; `load_role` and `load_candidate` populate grounding documents via deterministic CALL steps.
2. **Question generation** — A single GENERATE call produces the full question batch as JSON; three deterministic CALL steps unpack `@q1`, `@q2`, `@q3`.
3. **Answer generation** — Three sequential GENERATE calls (one per question) populate `@a1`, `@a2`, `@a3` using the candidate persona and loaded profile.
4. **Scoring** — Three sequential GENERATE calls populate `@score1`, `@score2`, `@score3` by applying the rubric to each Q&A pair.
5. **Aggregation and assembly** — Two deterministic CALL steps produce `@agg_scores` and `@transcript`.
6. **Narrative generation** — One final GENERATE call over the deterministic inputs produces `@evaluation_report`.
7. **Termination** — `RETURN @evaluation_report WITH status='complete'` signals successful completion. If any GENERATE call raises `GenerationError`, the EXCEPTION handler fires and `RETURN @transcript WITH status='partial'` delivers the raw transcript with whatever scoring completed before the failure.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2, High-level Description, as text2spl input)
spl3 text2spl --description "Generate a WORKFLOW named interview_sim that accepts a role definition (via catalog key or freeform text), a candidate profile identifier, focus area, difficulty level, number of questions, and years of experience. Open with two deterministic CALL steps to load role-context and candidate-profile documents. Use a single GENERATE call to produce a full batch of interview questions as JSON, then use deterministic CALL steps to extract each individual question. For each question, GENERATE a candidate answer grounded by the candidate profile and a candidate_persona function. For each answer, GENERATE a score using a score_answer function that enforces a strict JSON output contract via an evaluation_rubric function covering accuracy, depth, communication, experience (each 0-10), total, and one-sentence feedback. Aggregate scores and compile the transcript with deterministic CALL steps. GENERATE a final overall_evaluation narrative grounded by the deterministic aggregated scores and transcript. RETURN the evaluation report with status='complete'. Add an EXCEPTION handler for GenerationError that returns the partial transcript with status='partial'." --mode workflow

# Step 2 — compile to any target
spl3 splc compile interview_sim.spl --lang python/pocketflow
spl3 splc compile interview_sim.spl --lang python/langgraph
spl3 splc compile interview_sim.spl --lang go
```