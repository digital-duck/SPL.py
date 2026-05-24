## Summary

The Socratic Tutor is a pedagogical LLM workflow that simulates a guided tutoring session on any topic, asking probing questions rather than delivering answers directly. It models a three-turn dialogue between a Socratic tutor and a simulated student, then branches the third question based on a machine-assessed comprehension score. Non-technical stakeholders — educators, curriculum designers, and ed-tech teams — benefit by getting a reusable, level-adaptive dialogue scaffold that demonstrates question-driven learning at any subject and grade level.

---

## Detailed Specification

### 1. Purpose

Generate a structured, level-adaptive Socratic dialogue for a given topic and student level, branching the final question based on a 0–10 LLM-assessed comprehension score.

---

### 2. High-level Description

The `socratic_tutor` WORKFLOW opens by loading structured topic context and level-appropriate vocabulary guidance through two deterministic CALL steps (`load_topic`, `get_level_guidance`), incurring zero LLM cost before any generation begins. A reusable CREATE FUNCTION named `socratic_persona` encodes the tutor's strict behavioral rules — ask one question at a time, never state facts, build on student words — and is injected as inline system context into every GENERATE call that plays the tutor role. The workflow then executes a fixed three-question dialogue arc: GENERATE produces the opening question, followed by a simulated student response, a follow-up question, and a second simulated student response, all via separate GENERATE calls. After the second student turn, a dedicated GENERATE call to `assess_understanding` returns a numeric score (0–10); this score drives a single EVALUATE branch — scores above 7 route to a consolidation question that cements emerging understanding, while lower scores route to a scaffolded hint question that unblocks the student. A final GENERATE simulates the student's third response, and a deterministic CALL to `compile_dialogue` assembles the full exchange into formatted output. The WORKFLOW RETURNs with `status='complete'` and the `understanding_score` as metadata, making the comprehension signal available to any parent workflow or logging system.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| WORKFLOW | `socratic_tutor` | Top-level orchestration unit; accepts `@topic`, `@topic_id`, `@subject`, `@student_level`, `@max_questions` as INPUT |
| CREATE FUNCTION | `socratic_persona(student_level)` | Zero-LLM-cost persona template; injected inline as system context in every tutor-role GENERATE call |
| CALL | `load_topic`, `get_level_guidance`, `compile_dialogue` | Deterministic Python tools; no LLM involved; registered via `@spl_tool` in `tools.py` |
| GENERATE | `opening_question`, `simulate_student_response` (×3), `followup_question`, `assess_understanding`, `consolidation_question` / `hint_question` | Seven LLM calls total; each call stores result in a named `@var` |
| EVALUATE | `EVALUATE @understanding_score WHEN > 7 THEN ... ELSE ... END` | Single branch point; drives question type for turn 3 |
| RETURN WITH | `RETURN @dialogue WITH status='complete', understanding_score=@understanding_score` | Non-trivial: carries numeric comprehension metadata back to caller |
| Shared state (`@vars`) | `@question_1/2/3`, `@student_1/2/3`, `@understanding_score`, `@topic_context`, `@level_guide`, `@dialogue` | Bound sequentially; each step reads from previously-bound vars |

> **Note:** `@max_questions` is declared as an INPUT parameter but is not referenced in the workflow body — it is reserved for a future WHILE-loop extension.

---

### 4. Logical Functions / Prompts

**`socratic_persona(student_level)`**
- Role: Persona constraint template; defines the tutor's behavioral invariants.
- Key conventions: Injected inline (not a standalone LLM call); contains explicit negative rules ("Never say 'The answer is...'"); uses `{student_level}` slot to scale vocabulary and abstraction.

**`opening_question(topic, topic_context, persona, level_guide)`**
- Role: Produces the first Socratic question that opens the dialogue.
- Key conventions: Grounded by structured `@topic_context` from the catalog; persona injected as system context; question must be singular and open-ended.

**`simulate_student_response(question, topic, topic_context, student_level)`**
- Role: Simulates a plausible student reply at the declared level; called three times (after turns 1, 2, and 3).
- Key conventions: Must produce a response authentic to `@student_level` — partial understanding, common misconceptions, or tentative phrasing as appropriate.

**`followup_question(question_1, student_1, topic, topic_context, persona)`**
- Role: Generates the second tutor question, explicitly grounded in what the simulated student just said.
- Key conventions: Must reference `@student_1` to enforce the Socratic rule "build on the student's words"; persona injected as system context.

**`assess_understanding(student_1, student_2, topic, topic_context)`**
- Role: LLM judge that scores comprehension progress on a 0–10 numeric scale.
- Key conventions: Output must be a parseable integer or decimal; this value is consumed directly by the EVALUATE branch — no text wrapper.

**`consolidation_question(topic, topic_context, student_2, persona)`**
- Role: Third-turn question when understanding is strong (score > 7); prompts the student to generalize or apply their insight.
- Key conventions: Assumes partial mastery; asks for extension or connection to broader concepts.

**`hint_question(question_2, topic, topic_context, persona, level_guide)`**
- Role: Third-turn question when understanding is weak (score ≤ 7); provides a scaffold hint framed as a question.
- Key conventions: Must follow the "What if you considered...?" pattern from the persona; uses `@level_guide` to calibrate hint complexity.

---

### 5. Control Flow

```
load_topic  →  get_level_guidance
    ↓
opening_question  →  simulate_student_response(@student_1)
    ↓
followup_question  →  simulate_student_response(@student_2)
    ↓
assess_understanding  →  @understanding_score (0–10)
    ↓
EVALUATE @understanding_score
    WHEN > 7  →  consolidation_question  →  @question_3
    ELSE      →  hint_question           →  @question_3
    ↓
simulate_student_response(@student_3)
    ↓
compile_dialogue (deterministic)
    ↓
RETURN @dialogue WITH status='complete', understanding_score=@understanding_score
```

The workflow is a linear pipeline with exactly one branch point (EVALUATE on the comprehension score). There is no iterative loop despite the `@max_questions` parameter being declared — the dialogue is fixed at three tutor turns. The RETURN status `'complete'` is always reached; no error path is modeled in the current implementation.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 above as text2spl input)
spl3 text2spl --description "Generate a structured, level-adaptive Socratic dialogue \
  for a given topic and student level. Load structured topic context and level guidance \
  via deterministic tool calls (load_topic, get_level_guidance). Use a CREATE FUNCTION \
  socratic_persona to encode tutor behavioral rules injected as system context into every \
  tutor GENERATE call. Run a fixed three-question arc: GENERATE opening_question, \
  simulate_student_response, followup_question, simulate_student_response, then \
  assess_understanding returning a 0-10 score. EVALUATE the score — above 7 generates a \
  consolidation_question, else a hint_question. GENERATE a final student response, then \
  compile_dialogue via CALL. RETURN with status='complete' and understanding_score." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile socratic_tutor.spl --lang python/pocketflow
spl3 splc compile socratic_tutor.spl --lang python/langgraph
spl3 splc compile socratic_tutor.spl --lang go
```