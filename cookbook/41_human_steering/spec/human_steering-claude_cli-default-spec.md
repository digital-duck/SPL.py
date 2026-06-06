## Summary

This workflow generates a short tech article on a given topic, then pauses so a human reviewer can read it and optionally provide feedback before the final version is produced. If the reviewer supplies feedback, a second LLM call refines the draft; if they skip, the original draft is used unchanged. It benefits editorial teams and AI-assisted publishing pipelines that need a human approval gate without abandoning automation entirely.

---

## Detailed Specification

### 1. Purpose

Generate a draft article on a user-supplied topic, collect optional human feedback via a blocking pause, and conditionally refine the draft into a final article — writing all artifacts to disk.

---

### 2. High-level Description

The workflow `human_steering` implements the "Pause for Approval" pattern: an LLM draft is produced, a human is invited to review it, and the workflow branches based on whether feedback was given. It defines two CREATE FUNCTIONs: `draft`, which prompts a professional tech writer persona to produce a concise three-sentence article (opening claim, supporting example, forward-looking conclusion), and `refine`, which prompts a senior editor persona to revise the draft while preserving that same three-part structure unless the feedback explicitly overrides it. After the initial GENERATE call produces `@draft`, a deterministic CALL to `wait_for_human_feedback` blocks execution — incurring no LLM cost — until the reviewer responds or skips. An EVALUATE on `@feedback` branches the flow: a non-empty string triggers a second GENERATE call through `refine`, while an empty string short-circuits to the original draft. All intermediate artifacts (`draft.md`, `feedback.md`, `final_article.md`) are persisted via CALL to `write_file`. A RETURN WITH `status='complete'` signals successful termination; an EXCEPTION handler for `GenerationError` returns whatever draft is available with `status='draft_only'` and a diagnostic reason, enabling callers to distinguish partial from full completion.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW human_steering` | `WORKFLOW <name>` | Declares the named orchestration entry point with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION draft(...)` | `CREATE FUNCTION <name>` | Prompt template with `{topic}` slot; tech-writer persona |
| `CREATE FUNCTION refine(...)` | `CREATE FUNCTION <name>` | Prompt template with `{draft}` and `{feedback}` slots; editor persona |
| `GENERATE draft(@topic) INTO @draft` | `GENERATE <fn>(...) INTO @<var>` | First LLM call; result stored in `@draft` |
| `GENERATE refine(@draft, @feedback) INTO @final_article` | `GENERATE <fn>(...) INTO @<var>` | Conditional second LLM call; only runs when feedback is non-empty |
| `CALL wait_for_human_feedback(...) INTO @feedback` | `CALL <tool>(...) INTO @<var>` | Blocking deterministic side-effect; human steering gate; no LLM cost |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO @<var>` | Non-LLM side-effect; persists artifacts to disk; result discarded |
| `EVALUATE @feedback WHEN != '' THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Branches on whether the human provided feedback |
| `@final_article := @draft` | Shared state `@<var>` assignment | Direct variable assignment in the ELSE branch; no LLM call |
| `RETURN @final_article WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial terminal status signals full success to caller |
| `EXCEPTION WHEN GenerationError THEN RETURN @draft WITH status='draft_only'` | `EXCEPTION WHEN <Type> THEN ...` | Partial-success fallback; `draft_only` status distinguishes it from `complete` |

---

### 4. Logical Functions / Prompts

**`draft(topic TEXT)`**
- **Role:** Produces the initial article from scratch based solely on the user-supplied topic.
- **Persona:** Professional tech writer.
- **Output conventions:** Exactly three sentences following a fixed structure — (1) opening claim, (2) supporting example, (3) forward-looking conclusion. No sentinel tokens; result is raw prose.

**`refine(draft TEXT, feedback TEXT)`**
- **Role:** Revises the draft to satisfy reviewer feedback while preserving the three-sentence structure.
- **Persona:** Senior editor.
- **Output conventions:** Structured same as `draft` output unless the feedback explicitly requests restructuring. Both `{draft}` and `{feedback}` are injected verbatim with clear labels to prevent context confusion. No sentinel tokens; result is raw prose.

---

### 5. Control Flow

1. **Initial step:** `GENERATE draft(@topic)` produces `@draft`; it is written to `draft.md`.
2. **Human gate:** `CALL wait_for_human_feedback(...)` blocks until the reviewer acts; result stored in `@feedback` and written to `feedback.md`.
3. **Branch:** `EVALUATE @feedback` — if non-empty, a second `GENERATE refine(...)` produces `@final_article`; if empty, `@final_article` is assigned directly from `@draft` (no LLM call).
4. **Termination:** `@final_article` is written to `final_article.md`; `RETURN @final_article WITH status='complete'` ends the workflow.
5. **Exception path:** If `GenerationError` is raised at any point, the handler returns `@draft WITH status='draft_only', reason='generation_error'`, allowing the caller to distinguish a fully refined article from a bare draft.

There is no WHILE loop; this is a linear flow with a single EVALUATE branch and a single exception path.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a draft article on a user-supplied topic, collect optional human feedback via a blocking pause, and conditionally refine the draft into a final article — writing all artifacts to disk." --mode workflow

# Step 2 — compile to any target
spl3 splc compile human_steering.spl --lang python/pocketflow
spl3 splc compile human_steering.spl --lang python/langgraph
spl3 splc compile human_steering.spl --lang go
```