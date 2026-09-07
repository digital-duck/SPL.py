## 0. High-level Description

This workflow implements a **persona-constrained iterative dialogue simulation** pattern in which a Socratic tutor LLM persona guides a student to self-discover answers through carefully sequenced questions. A single `CREATE FUNCTION` — `socratic_persona` — defines a strict system-context persona injected into every LLM call that touches the tutor role; it enforces six hard rules (one question at a time, no direct answers, build on student words, hint-as-question when stuck, celebrate partial insight, forbidden phrases) and is parameterised by `student_level` to calibrate vocabulary and abstraction. The workflow begins with two deterministic `CALL` side-effects — `load_topic` and `get_level_guidance` — that fetch structured topic context and level scaffolding from an external catalog with zero LLM cost, before handing off to a fixed three-turn dialogue loop of alternating `GENERATE` calls for tutor questions (`opening_question`, `followup_question`) and simulated student responses (`simulate_student_response`). After two turns an `EVALUATE` branch forks on a 0–10 understanding score produced by `assess_understanding`: scores above 7 route to a consolidation question that cements emerging understanding, while lower scores route to a `hint_question` that unblocks a struggling student. A final deterministic `CALL` to `compile_dialogue` assembles the full exchange into structured output, and the workflow `RETURN`s the dialogue with `status = 'complete'` and the `understanding_score` as metadata. `LOGGING` statements at `INFO` and `DEBUG` levels bracket each major phase — topic loading, score emission, and dialogue completion — providing an observability trail without adding LLM cost.

## 1. Purpose

Guide a student to discover an answer themselves through three adaptive Socratic questions, simulating both tutor and student turns and returning the complete formatted dialogue together with an understanding score.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | `''` | Freeform topic text when no catalog entry is used |
| `@topic_id` | `''` | Catalog key for a pre-authored topic (e.g. `sky_blue`, `recursion`) |
| `@subject` | `''` | Subject domain used to resolve `@topic_id` in the catalog (e.g. `science`, `math`, `programming`) |
| `@student_level` | `'high school'` | Describes the target student's educational level; drives persona vocabulary and question complexity |
| `@max_questions` | `5` | Maximum number of questions (declared for resource-limit signalling; the current script issues exactly 3) |

## 3. Process

1. **Log startup** — emit an `INFO` log recording `student_level`, `topic`, and `topic_id`.
2. **Load topic context** — `CALL load_topic(@topic_id, @subject)` retrieves structured topic metadata from the catalog into `@topic_context` (deterministic, no LLM).
3. **Load level guidance** — `CALL get_level_guidance(@student_level)` retrieves vocabulary and scaffolding recommendations into `@level_guide` (deterministic, no LLM); emit a `DEBUG` log confirming both are loaded.
4. **Generate opening question** — `GENERATE opening_question(...)` calls the LLM with the topic, topic context, `socratic_persona(@student_level)` as system persona, and level guidance; result stored in `@question_1`.
5. **Simulate first student response** — `GENERATE simulate_student_response(@question_1, ...)` produces a plausible student reply at the given level into `@student_1`.
6. **Generate follow-up question** — `GENERATE followup_question(...)` calls the LLM grounded on the tutor's first question, the student's actual response, topic context, and the Socratic persona; result stored in `@question_2`.
7. **Simulate second student response** — `GENERATE simulate_student_response(@question_2, ...)` produces a further student reply into `@student_2`.
8. **Assess understanding** — `GENERATE assess_understanding(@student_1, @student_2, @topic, @topic_context)` asks the LLM to score emerging understanding on a 0–10 scale into `@understanding_score`; emit an `INFO` log with the score.
9. **Adaptive third question (EVALUATE branch)**:
   - If `@understanding_score > 7` → `GENERATE consolidation_question(...)` using topic context, the student's second response, and the Socratic persona to cement understanding into `@question_3`.
   - Otherwise → `GENERATE hint_question(...)` using the second question, topic context, Socratic persona, and level guidance to unblock the student into `@question_3`.
10. **Simulate third student response** — `GENERATE simulate_student_response(@question_3, ...)` produces the final student reply into `@student_3`.
11. **Compile dialogue** — `CALL compile_dialogue(...)` assembles all three question–response pairs, the topic, and the understanding score into the formatted `@dialogue` string (deterministic, no LLM).
12. **Log completion** — emit an `INFO` log with the final `understanding_score`.
13. **Return** — `RETURN @dialogue WITH status = 'complete', understanding_score = @understanding_score`.

## 4. Error Handling

No `EXCEPTION` blocks are declared in this script. The following SPL exception types are implicitly available but not explicitly handled here:

- `MaxIterationsReached` — not wired; `@max_questions` is declared but the loop is unrolled as fixed sequential steps rather than a `WHILE` construct.
- `BudgetExceeded`, `HallucinationDetected`, `QualityBelowThreshold`, `ContextLengthExceeded`, `ModelOverloaded` — none are caught; any such condition would surface as an unhandled runtime exception and halt the workflow.

## 5. Output

| Field | Type | Description |
|---|---|---|
| `@dialogue` | `TEXT` | The fully formatted three-turn tutor–student exchange produced by `compile_dialogue` |
| `status` | metadata `STRING` | Always `'complete'` on successful execution |
| `understanding_score` | metadata value | The 0–10 integer score from `assess_understanding`, indicating how much the simulated student demonstrated emerging understanding by the end of the dialogue |