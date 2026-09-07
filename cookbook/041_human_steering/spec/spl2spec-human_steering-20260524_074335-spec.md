## Summary

This workflow demonstrates the "Pause for Approval" pattern, where an LLM drafts a short article and then halts to collect a human reviewer's feedback before deciding whether to refine or ship the result. It separates the automated generation steps from a deterministic human-gate step, ensuring a person can redirect the output before it is finalized. Editors, content teams, or any workflow that requires a human sign-off before publication will benefit from this pattern.

---

## Detailed Specification

### 1. Purpose

Generate a concise tech article on a given topic, pause for optional human reviewer feedback, conditionally refine the article based on that feedback, and persist each artifact to disk.

---

### 2. High-level Description

The `human_steering` WORKFLOW accepts a topic string and a log directory path, then executes a three-phase pipeline. In the first phase it invokes a `draft` GENERATE call that instructs an LLM tech writer to produce a structured 3-sentence article (opening claim, supporting example, forward-looking conclusion). The draft is immediately persisted via a `write_file` CALL side-effect and then a second deterministic CALL to `wait_for_human_feedback` pauses execution and surfaces the draft to a human reviewer, collecting their free-text notes without incurring any additional LLM cost. In the third phase, an EVALUATE branch inspects the returned feedback string: if it is non-empty the workflow issues a `refine` GENERATE call that sends both the original draft and the reviewer notes to a senior-editor persona, which revises the text while preserving the original structure unless explicitly told otherwise; if the feedback is empty the initial draft is promoted directly to `@final_article` unchanged. All three artifacts — draft, feedback, and final article — are written to disk via CALL side-effects, and the workflow terminates with `RETURN @final_article WITH status = 'complete'`. A `GenerationError` EXCEPTION handler provides a graceful fallback that returns the raw draft with `status = 'draft_only'` so callers can distinguish a partial result from a full one.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW human_steering` | `WORKFLOW` | Top-level named orchestration unit with `INPUT:` / `OUTPUT:` declarations |
| `CREATE FUNCTION draft(...)` | `CREATE FUNCTION` | Prompt template for initial article generation; parameterized by `{topic}` |
| `CREATE FUNCTION refine(...)` | `CREATE FUNCTION` | Prompt template for editorial revision; parameterized by `{draft}` and `{feedback}` |
| `GENERATE draft(@topic) INTO @draft` | `GENERATE … INTO @var` | LLM call; result bound to `@draft` |
| `GENERATE refine(@draft, @feedback) INTO @final_article` | `GENERATE … INTO @var` | Conditional LLM call; result bound to `@final_article` |
| `CALL write_file(...) INTO NONE` | `CALL … INTO NONE` | Deterministic side-effect (file I/O); no return value consumed |
| `CALL wait_for_human_feedback(...) INTO @feedback` | `CALL … INTO @var` | Deterministic human-gate; blocks execution until feedback is captured, result bound to `@feedback` |
| `EVALUATE @feedback WHEN != '' THEN … ELSE … END` | `EVALUATE` | Branch on feedback presence; drives the refine-vs-passthrough decision |
| `RETURN @final_article WITH status = 'complete'` | `RETURN … WITH status=` | Non-trivial terminal status signals successful full pipeline to callers |
| `EXCEPTION WHEN GenerationError THEN` | `EXCEPTION WHEN <Type>` | Typed error handler; returns partial result with `status = 'draft_only'` |
| `@draft`, `@feedback`, `@final_article` | Shared `@var` state | Pipeline variables passed between GENERATE, CALL, and EVALUATE steps |

---

### 4. Logical Functions / Prompts

**`draft(topic TEXT)`**
- **Role:** Produces the first-pass article that will be shown to the human reviewer.
- **Persona:** "professional tech writer"
- **Output format:** Exactly 3 sentences following a fixed rhetorical structure — opening claim, supporting example, forward-looking conclusion. No sentinel tokens or scores; raw prose is expected.

**`refine(draft TEXT, feedback TEXT)`**
- **Role:** Incorporates human reviewer notes into the existing draft without discarding its structure.
- **Persona:** "senior editor"
- **Key convention:** The prompt explicitly instructs the model to preserve the three-sentence structure unless the feedback directly overrides it, preventing over-correction. Both the full draft and the verbatim feedback are injected into the prompt, making the revision traceable.

---

### 5. Control Flow

1. **Initial step** — `GENERATE draft(@topic) INTO @draft` produces the first artifact; the draft is written to disk immediately.
2. **Human gate** — `CALL wait_for_human_feedback(...)` blocks the pipeline synchronously until a human submits feedback (or dismisses with an empty string); the feedback is written to disk.
3. **Branch** — `EVALUATE @feedback WHEN != ''` forks into two paths:
   - **Feedback present:** `GENERATE refine(@draft, @feedback) INTO @final_article` produces a revised article.
   - **No feedback:** `@final_article := @draft` — the draft is promoted as-is; no LLM call is made.
4. **Termination** — The final article is written to disk and the workflow exits via `RETURN @final_article WITH status = 'complete'`.
5. **Error path** — Any `GenerationError` in the pipeline is caught by the EXCEPTION handler, which returns `@draft` (whatever was generated before the failure) with `status = 'draft_only'`, allowing callers to distinguish a graceful partial result from an unhandled crash.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a concise tech article on a given topic, \
pause for optional human reviewer feedback, conditionally refine the article based \
on that feedback, and persist each artifact to disk." --mode workflow

# Step 2 — compile to any target
spl3 splc compile human_steering.spl --lang python/pocketflow
spl3 splc compile human_steering.spl --lang python/langgraph
spl3 splc compile human_steering.spl --lang go
```