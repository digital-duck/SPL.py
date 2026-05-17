## Summary

The Socratic Tutor workflow simulates a one-on-one tutoring session in which an LLM-powered tutor never gives direct answers — it only asks questions that guide a student toward self-discovery. A second LLM role plays the student, producing a realistic simulated dialogue grounded in any topic from a catalog or entered freeform. The workflow benefits educators, curriculum designers, and self-learners who want to model or experience Socratic pedagogy across science, math, and programming subjects at configurable grade levels.

---

## Detailed Specification

### 1. Purpose

Generates a three-exchange Socratic dialogue between a persona-constrained tutor and a simulated student, adapting the final question based on an LLM-assessed understanding score, and returns the compiled transcript with a completion status and that score.

---

### 2. High-level Description

The `socratic_tutor` WORKFLOW begins by invoking two deterministic CALL tools — `load_topic` to retrieve structured topic context from a catalog (or accept freeform input) and `get_level_guidance` to fetch vocabulary and scaffolding parameters for the student's grade level — neither of which consumes LLM tokens. A CREATE FUNCTION named `socratic_persona` acts as a reusable system-prompt template, injecting strict Socratic rules and student-level calibration into every tutor-role GENERATE call. The workflow then runs a fixed sequence of five GENERATE calls in alternating tutor/student roles: `opening_question` poses the first question, `simulate_student_response` produces a plausible student answer, `followup_question` builds on that answer, and a second `simulate_student_response` advances the student's reasoning. A sixth GENERATE call to `assess_understanding` produces a numeric score (0–10) reflecting how close the student is to grasping the concept. An EVALUATE branch on that score selects either `consolidation_question` (score > 7, to cement emerging understanding) or `hint_question` (score ≤ 7, to unblock a struggling student) as the third tutor turn, followed by a final `simulate_student_response`. A deterministic CALL to `compile_dialogue` assembles the six turns into a formatted transcript, and the workflow terminates with RETURN WITH `status='complete'` and `understanding_score` attached as output metadata.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW socratic_tutor` | `WORKFLOW <name>` | Declares the top-level orchestration with typed INPUT/OUTPUT variables |
| `CREATE FUNCTION socratic_persona` | `CREATE FUNCTION <name>` | Reusable prompt template with `{student_level}` slot; zero LLM cost — injected as system context |
| `CALL load_topic(...) INTO @topic_context` | `CALL <tool>(...) INTO @<var>` | Deterministic tool; no LLM; retrieves catalog entry or freeform topic |
| `CALL get_level_guidance(...) INTO @level_guide` | `CALL <tool>(...) INTO @<var>` | Deterministic tool; returns vocabulary and scaffolding guidance |
| `GENERATE opening_question(...) INTO @question_1` | `GENERATE <fn>(...) INTO @<var>` | LLM call; tutor role; uses `socratic_persona` as system context |
| `GENERATE simulate_student_response(...) INTO @student_N` | `GENERATE <fn>(...) INTO @<var>` | LLM call; student role; invoked three times across the dialogue |
| `GENERATE assess_understanding(...) INTO @understanding_score` | `GENERATE <fn>(...) INTO @<var>` | LLM call; evaluator role; returns a 0–10 numeric score |
| `EVALUATE @understanding_score WHEN > 7 THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Branches on numeric threshold; drives selection of consolidation vs. hint question |
| `CALL compile_dialogue(...) INTO @dialogue` | `CALL <tool>(...) INTO @<var>` | Deterministic formatter; assembles all six turns into final transcript |
| `RETURN @dialogue WITH status='complete', understanding_score=...` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial return: carries understanding_score as structured output metadata |
| `@topic_context`, `@level_guide`, `@question_N`, `@student_N`, `@understanding_score`, `@dialogue` | Shared state via SPL `@vars` | Pipeline state passed between CALL and GENERATE steps |
| `LOGGING ... LEVEL INFO/DEBUG` | `LOGGING` | Observability hooks; no control-flow effect |

---

### 4. Logical Functions / Prompts

**`socratic_persona`**
- Role: System-prompt factory; defines the tutor's persona and hard constraints for every tutor-role GENERATE call.
- Key conventions: Six numbered rules enforced as "NEVER break these"; prohibits fact-stating and direct answers; requires exactly one question per turn; instructs level-adaptive vocabulary via the `{student_level}` slot. Zero LLM cost — rendered once and injected.

**`opening_question`**
- Role: Generates the first tutor question that opens the dialogue.
- Key conventions: Grounded by `@topic_context` and `@level_guide`; `socratic_persona` sets the system role; output is a single question string.

**`simulate_student_response`**
- Role: Simulates a plausible student reply at the configured grade level; invoked three times (`@student_1`, `@student_2`, `@student_3`).
- Key conventions: Receives the preceding tutor question, topic, topic context, and student level; produces a natural-language student utterance reflecting partial understanding appropriate to the level.

**`followup_question`**
- Role: Generates the second tutor question, explicitly building on the student's first response.
- Key conventions: Takes `@question_1` and `@student_1` as prior context alongside topic and `socratic_persona`; output must reference the student's actual words, not a pre-scripted script.

**`assess_understanding`**
- Role: Evaluator; scores how well the student's responses reflect emerging comprehension.
- Key conventions: Consumes both `@student_1` and `@student_2` plus topic context; returns a numeric 0–10 value used directly in the EVALUATE branch condition.

**`consolidation_question`**
- Role: Third tutor question for students who are close to understanding (score > 7); cements and extends the insight.
- Key conventions: Receives `@student_2` (latest response), topic context, and `socratic_persona`; tone is celebratory and deepening.

**`hint_question`**
- Role: Third tutor question for students who remain stuck (score ≤ 7); provides a scaffolded hint as a question.
- Key conventions: Receives the prior `@question_2`, topic context, `socratic_persona`, and `@level_guide`; must frame the hint as "What if you considered...?" per persona rules.

**`compile_dialogue`** *(deterministic tool)*
- Role: Formats all six turns (three tutor questions, three student responses) into a readable transcript.
- Key conventions: Deterministic CALL; also embeds `@topic` label and `@understanding_score` in the output; no LLM involved.

---

### 5. Control Flow

Execution is linear through steps 1–7: two deterministic CALL tools load topic and level context, then five alternating GENERATE calls produce `@question_1 → @student_1 → @question_2 → @student_2 → @understanding_score`. At step 8 an EVALUATE branch inspects `@understanding_score`: when the score exceeds 7 the workflow takes the consolidation path (GENERATE `consolidation_question`); otherwise it takes the hint path (GENERATE `hint_question`). Either branch assigns the result to `@question_3`. Execution then converges and continues linearly: a final GENERATE produces `@student_3`, a deterministic CALL to `compile_dialogue` assembles the transcript into `@dialogue`, and the workflow terminates with RETURN WITH `status='complete'` and `understanding_score=@understanding_score`. There is no WHILE loop; the dialogue is a fixed three-exchange structure with a single adaptive branch at the midpoint.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generates a three-exchange Socratic dialogue between a \
persona-constrained tutor and a simulated student, adapting the final question based \
on an LLM-assessed understanding score, and returns the compiled transcript with a \
completion status and that score." --mode workflow

# Step 2 — compile to any target
spl3 splc compile socratic_tutor.spl --lang python/pocketflow
spl3 splc compile socratic_tutor.spl --lang python/langgraph
spl3 splc compile socratic_tutor.spl --lang go
```