## Summary

Interview Simulator is an LLM workflow that runs a structured technical interview between two AI personas — an interviewer and a candidate — then scores and narrates the result. It separates deterministic data loading (role definitions, candidate profiles, question extraction, score aggregation) from LLM reasoning (question generation, candidate answering, per-answer scoring, final narrative), keeping costs low and outputs reproducible. Hiring teams, educators, and interview-prep tools can use it to simulate realistic technical interviews at configurable role, focus area, and difficulty levels.

---

## Detailed Specification

### 1. Purpose

Generate a complete, scored technical interview transcript between a configurable role/candidate pair, producing a structured evaluation report with per-answer scores and an overall narrative assessment.

---

### 2. High-level Description

The `interview_sim` WORKFLOW accepts role and candidate configuration either via named keys (looked up deterministically with `load_role` and `load_candidate` CALL tools) or as free-form text parameters, then proceeds through nine sequential steps. Three CREATE FUNCTION templates — `interviewer_persona`, `candidate_persona`, and `evaluation_rubric` — are injected as system context into LLM calls rather than executed as standalone generations, making them zero-cost prompt scaffolds. A single GENERATE call to `generate_question_set` produces the full question bank upfront as JSON, which three deterministic CALL invocations to `extract_question` then parse into individual variables `@q1`, `@q2`, `@q3` — replacing what would otherwise be three separate LLM calls. Each question is answered by a separate GENERATE call to `answer_question`, grounded by the candidate profile and `candidate_persona` system context; each answer is then scored by a GENERATE call to `score_answer` using the `evaluation_rubric` template, producing structured JSON per answer. Deterministic CALL tools `aggregate_scores` and `compile_transcript` assemble the raw scores and Q&A pairs without any LLM cost, and a final GENERATE to `overall_evaluation` writes a prose narrative over the assembled transcript. The workflow terminates with RETURN WITH `status='complete'`; an EXCEPTION WHEN `GenerationError` handler catches any LLM failure and falls back to RETURN WITH `status='partial'`, preserving the transcript even if the final evaluation fails.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW interview_sim` | `WORKFLOW` | Top-level named workflow; accepts 7 INPUT vars, emits `@evaluation_report` |
| `CREATE FUNCTION interviewer_persona` | `CREATE FUNCTION` | Zero-cost system prompt scaffold; injected into LLM calls as context, not called standalone |
| `CREATE FUNCTION candidate_persona` | `CREATE FUNCTION` | Same pattern — system context injection for candidate answering calls |
| `CREATE FUNCTION evaluation_rubric` | `CREATE FUNCTION` | Returns a fixed scoring rubric string; shared across all three `score_answer` GENERATE calls |
| `CALL load_role(...)` | `CALL` tool | Deterministic — reads role definition from data store, no LLM |
| `CALL load_candidate(...)` | `CALL` tool | Deterministic — reads candidate profile from data store, no LLM |
| `CALL extract_question(...)` ×3 | `CALL` tool | Deterministic JSON parse; replaces three LLM `ask_question` calls |
| `CALL aggregate_scores(...)` | `CALL` tool | Deterministic numeric aggregation over three JSON score objects |
| `CALL compile_transcript(...)` | `CALL` tool | Deterministic formatter — assembles Q/A/score triples into structured text |
| `GENERATE generate_question_set(...)` | `GENERATE ... INTO @var` | Single LLM call produces full question bank as JSON |
| `GENERATE answer_question(...)` ×3 | `GENERATE ... INTO @var` | LLM call per question; grounded by `@candidate_profile` and `candidate_persona` |
| `GENERATE score_answer(...)` ×3 | `GENERATE ... INTO @var` | LLM call per answer; outputs structured JSON with four dimension scores + feedback |
| `GENERATE overall_evaluation(...)` | `GENERATE ... INTO @var` | Final LLM call; writes prose narrative over deterministic `@transcript` and `@agg_scores` |
| `@q1/@q2/@q3`, `@a1/@a2/@a3`, `@score1/@score2/@score3` | SPL `@vars` | Intermediate state threaded through sequential steps |
| `RETURN ... WITH status='complete'` | `RETURN @var WITH status=` | Happy-path termination; carries role/focus/difficulty metadata |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN <Type>` | Catches any LLM generation failure; returns `status='partial'` with transcript preserved |
| `RETURN ... WITH status='partial'` | `RETURN @var WITH status=` | Fallback termination driven by exception handler — non-trivial branch |

---

### 4. Logical Functions / Prompts

**`interviewer_persona(role, focus, difficulty)`**
- Role: System context that conditions the LLM to behave as a professional technical interviewer. Injected into `generate_question_set` calls.
- Key conventions: Enforces one-question-at-a-time discipline, neutral tone, no answer leakage, follow-up on vague responses. Parameterized by `{role}`, `{focus}`, `{difficulty}`.

**`candidate_persona(role, experience)`**
- Role: System context that conditions the LLM to behave as a job candidate. Injected into all three `answer_question` calls.
- Key conventions: Instructs honest answering grounded in the candidate's profile, think-aloud style, concrete examples, explicit acknowledgment of gaps rather than bluffing.

**`evaluation_rubric()`**
- Role: Parameterless scoring rubric shared across all three `score_answer` calls.
- Key conventions: Four dimensions — accuracy, depth, communication, experience — each 0–10, summing to a `total` out of 40. **Sentinel**: "Return valid JSON only — no prose outside the JSON." Output format: `{"accuracy": N, "depth": N, "communication": N, "experience": N, "total": N, "feedback": "..."}`.

**`generate_question_set`**
- Role: Produces the full interview question bank in a single LLM call, grounded by role context and interviewer persona.
- Key conventions: Generates `num_questions` questions as JSON. Batching all questions upfront avoids per-question LLM latency and enables deterministic extraction in Step 4.

**`answer_question`**
- Role: Simulates the candidate responding to a single question, grounded by `@candidate_profile` and `candidate_persona` system context.
- Key conventions: Response should be specific, reference plausible past experience, and honestly surface gaps. Called once per question (`@q1`, `@q2`, `@q3`).

**`score_answer`**
- Role: Scores one Q&A pair against the evaluation rubric.
- Key conventions: Must emit valid JSON matching the rubric schema. Receives `@role_context` for domain grounding. The JSON sentinel in `evaluation_rubric()` suppresses prose contamination.

**`overall_evaluation`**
- Role: Writes a final prose narrative over the complete, deterministically assembled `@transcript` and numeric `@agg_scores`.
- Key conventions: Receives `@candidate_profile` for contextual framing. This is the only LLM call that consumes the full interview context end-to-end.

---

### 5. Control Flow

The workflow is strictly linear — there are no WHILE loops and no EVALUATE branches on the happy path.

1. **Initialization** — `load_role` and `load_candidate` CALL tools resolve role and candidate data deterministically.
2. **Question generation** — a single GENERATE to `generate_question_set` produces all questions as JSON; three CALL invocations to `extract_question` parse them into `@q1`, `@q2`, `@q3`.
3. **Answer generation** — three sequential GENERATE calls to `answer_question` produce `@a1`, `@a2`, `@a3`, each conditioned on the same candidate persona and profile.
4. **Scoring** — three sequential GENERATE calls to `score_answer` produce JSON score objects `@score1`, `@score2`, `@score3`.
5. **Aggregation and formatting** — `aggregate_scores` and `compile_transcript` CALL tools combine all outputs deterministically into `@agg_scores` and `@transcript`.
6. **Final narrative** — one GENERATE to `overall_evaluation` produces `@evaluation_report`.
7. **Termination** — RETURN WITH `status='complete'` on success. If any GENERATE step raises `GenerationError`, the EXCEPTION handler immediately issues RETURN WITH `status='partial'`, returning whatever transcript was built before the failure.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 1 as text2spl input)
spl3 text2spl --description \
  "Generate a complete, scored technical interview transcript between a configurable \
   role/candidate pair, producing a structured evaluation report with per-answer scores \
   and an overall narrative assessment." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile interview_sim.spl --lang python/pocketflow
spl3 splc compile interview_sim.spl --lang python/langgraph
spl3 splc compile interview_sim.spl --lang go
```