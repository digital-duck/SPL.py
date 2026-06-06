## 0. High-level Description

This workflow implements a **two-persona interview simulation** pattern in which three distinct LLM roles — interviewer, candidate, and evaluator — collaborate across a structured Q&A pipeline. Three `CREATE FUNCTION` constructs establish the persona scaffolding: `interviewer_persona` injects a professional, probing interviewer character parameterized by role, focus area, and difficulty; `candidate_persona` injects a realistic job-seeker character parameterized by role and years of experience; and `evaluation_rubric` defines a strict four-dimension scoring schema (accuracy, depth, communication, experience, each 0–10, total max 40) that mandates the LLM return **valid JSON only** with no prose outside the object. The control flow is fully linear — no `WHILE` loop or `EVALUATE` branch — instead alternating between deterministic `CALL` side-effects (role loading, candidate loading, question extraction, score aggregation, transcript compilation) and LLM `GENERATE` calls (question set generation, per-question answering, per-answer scoring, overall narrative), a deliberate design that minimises LLM non-determinism by offloading all parsing and arithmetic to tool functions. `LOGGING` statements at `INFO` level bracket the major milestones (session start, aggregate scores, completion) and at `DEBUG` level trace data-loading and scoring phases. A single `EXCEPTION WHEN GenerationError` guard catches LLM failures in the evaluation phase and falls back to `RETURN`ing the already-compiled transcript with `status = 'partial'`, while a successful run `RETURN`s the full evaluation report with `status = 'complete'` and role/focus/difficulty metadata.

## 1. Purpose

Generate a fully scored mock technical interview — questions, candidate answers, per-question rubric scores, and an overall narrative evaluation — for a given role, focus area, and candidate profile.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@role_key` | `''` | Catalog key identifying a predefined role (e.g. `senior_swe`). Pass `list` to enumerate available roles. |
| `@candidate_id` | `''` | Catalog key identifying a predefined candidate profile (e.g. `alice_senior_swe`). Pass `list` to enumerate candidates. |
| `@role` | `''` | Free-form role title (used when not drawing from catalog, e.g. `"ML Engineer"`). |
| `@focus` | `''` | Topic area to focus interview questions on (e.g. `system_design`, `kubernetes`). |
| `@difficulty` | `'medium'` | Question difficulty level: `easy`, `medium`, or `hard`. |
| `@num_questions` | `3` | Number of interview questions to generate and evaluate. |
| `@experience` | `'5 years'` | Candidate's years of relevant experience, injected into the candidate persona. |

## 3. Process

1. **Log session start** — emit an `INFO` log recording role, focus, and difficulty.
2. **Load role context** — `CALL load_role(@role_key, @focus)` deterministically fetches the role definition and focus-area context into `@role_context` (no LLM).
3. **Load candidate profile** — `CALL load_candidate(@candidate_id)` fetches the candidate's background data into `@candidate_profile` (no LLM); emit a `DEBUG` log confirming both loads.
4. **Generate question set** — `GENERATE generate_question_set(...)` calls the LLM once, grounded by `@role_context` and the `interviewer_persona` function, producing a JSON block of `@num_questions` questions in `@questions_json`.
5. **Extract individual questions** — three sequential `CALL extract_question(@questions_json, N)` calls parse questions 1, 2, and 3 out of the JSON deterministically into `@q1`, `@q2`, `@q3` (no LLM).
6. **Generate candidate answers** — three sequential `GENERATE answer_question(...)` calls, each grounded by the relevant question, role context, candidate profile, and the `candidate_persona` function, producing `@a1`, `@a2`, `@a3`.
7. **Score each answer** — emit a `DEBUG` log (`'Scoring answers ...'`), then three sequential `GENERATE score_answer(...)` calls, each receiving a question/answer pair plus `@role_context` and the `evaluation_rubric` function; each returns a JSON object with per-dimension scores and one-sentence feedback into `@score1`, `@score2`, `@score3`.
8. **Aggregate scores** — `CALL aggregate_scores(@score1, @score2, @score3)` combines the three JSON score objects deterministically into `@agg_scores` (no LLM); emit an `INFO` log of the aggregate.
9. **Compile transcript** — `CALL compile_transcript(...)` formats all questions, answers, and scores into a structured `@transcript` (no LLM).
10. **Write overall evaluation** — `GENERATE overall_evaluation(@transcript, @agg_scores, @role, @focus, @candidate_profile)` asks the LLM for a narrative evaluation report grounded in the deterministically computed aggregate scores, producing `@evaluation_report`.
11. **Log completion** — emit an `INFO` log, then `RETURN @evaluation_report` with metadata.

## 4. Error Handling

- **`GenerationError`** — if any LLM `GENERATE` call fails (most likely during the final `overall_evaluation` step, since that is where the exception is guarded), the workflow catches the error and `RETURN`s `@transcript` with `status = 'partial'` and `reason = 'evaluation_failed'`. The per-question transcript is preserved even when the narrative evaluation cannot be produced.

## 5. Output

The primary output is `@evaluation_report` (TEXT), an LLM-written narrative evaluation grounded in the aggregated rubric scores and full interview transcript.

On success, the `RETURN` includes the following metadata:

| Field | Value |
|---|---|
| `status` | `'complete'` |
| `role` | value of `@role` |
| `focus` | value of `@focus` |
| `difficulty` | value of `@difficulty` |

On partial failure (LLM generation error), `@transcript` is returned instead with:

| Field | Value |
|---|---|
| `status` | `'partial'` |
| `reason` | `'evaluation_failed'` |