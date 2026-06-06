## Summary

This workflow converts a meeting transcript — supplied either as a file path or inline text — into a structured list of action items, decisions, and open questions, with owners and due dates extracted from the speaker dialogue. It exists to eliminate the manual work of post-meeting note processing, and produces output in JSON, Markdown, or email format suitable for direct distribution to teams. Project managers and engineering leads benefit most, gaining a reliable record of commitments without parsing raw transcripts themselves.

---

## Detailed Specification

### 1. Purpose

Transform a raw meeting transcript into a validated, structured action-item list with attributed owners, normalized due dates, and a choice of output format (JSON, Markdown, or email).

---

### 2. High-level Description

The workflow `meeting_to_actions` implements a **multi-step extraction pipeline** that combines deterministic tool calls with targeted LLM generation passes, using a schema-grounded approach to minimize hallucination. Two `CREATE FUNCTION` templates handle the core LLM work — `normalize_transcript` cleans and unifies potentially dual-source input (file and inline), while `extract_actions` performs structured information extraction grounded by a JSON Schema injected via the zero-cost `action_item_schema()` function and a pre-extracted speaker list. Downstream of the two GENERATE steps, three deterministic CALL tools enforce data quality without LLM cost: `normalize_dates` converts relative date phrases to ISO-8601, `validate_ownership` flags unowned high-priority items, and `write_file` persists intermediate artefacts for debugging. EVALUATE branches on `@output_format` to dispatch one of three terminal paths — `format_as_markdown`, `format_as_email`, or direct JSON pass-through — each concluding with a `RETURN` carrying a `status='complete'` token and a `format` label. A named EXCEPTION handler catches `ContextLengthExceeded` and re-routes through a `summarize_transcript` GENERATE call before repeating extraction, returning with `status='complete_chunked'` to signal the fallback path was taken.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Concept | SPL Equivalent | Notes |
|---|---|---|
| Named pipeline | `WORKFLOW meeting_to_actions` | Declares typed inputs (`@filename`, `@transcript`, `@output_format`, `@log_dir`) and output (`@output`) |
| Zero-cost schema injection | `CREATE FUNCTION action_item_schema()` | Returns a JSON Schema literal; no LLM call, used as a grounding argument |
| LLM transcript cleaning | `GENERATE normalize_transcript(...) INTO @clean_transcript` | Merges file + inline sources; uses speaker lists for speaker attribution |
| LLM structured extraction | `GENERATE extract_actions(...) INTO @structured_json` | Schema-grounded; speaker lists reduce owner hallucination |
| LLM fallback summarization | `GENERATE summarize_transcript(...) INTO @summary` | Only in exception path; produces a condensed transcript for re-extraction |
| LLM Markdown formatting | `GENERATE format_as_markdown(...) INTO @output` | Receives validated JSON + ownership notes |
| LLM email formatting | `GENERATE format_as_email(...) INTO @output` | Same inputs as Markdown path |
| Deterministic side effects | `CALL load_transcript / extract_speakers / normalize_dates / validate_ownership / write_file` | No LLM cost; enforce data quality and persist artefacts |
| Output branching | `EVALUATE @output_format WHEN = 'markdown' / 'email' ELSE` | Three-way branch on format string; each arm terminates with RETURN |
| Non-trivial return tokens | `RETURN @output WITH status='complete', format=...` / `status='complete_chunked'` | `complete_chunked` signals the exception fallback fired |
| Shared mutable state | SPL `@vars` (`@structured_json`, `@clean_transcript`, etc.) | Passed across CALL and GENERATE steps; `@structured_json` is mutated in-place by `normalize_dates` |
| Long-transcript fallback | `EXCEPTION WHEN ContextLengthExceeded THEN` | Intercepts context overflow; summarize → re-extract → normalize → return |

---

### 4. Logical Functions / Prompts

**`normalize_transcript`**
- **Role:** First LLM pass. Merges a file-sourced transcript and an optional inline transcript into a single clean document, standardises speaker attribution using the pre-extracted speaker lists, and removes formatting noise.
- **Key conventions:** Receives four arguments — raw file content, raw inline text, and two speaker arrays — so the model can resolve ambiguous speaker references deterministically against a known list.

**`extract_actions`**
- **Role:** Core extraction pass. Produces a JSON object conforming to `action_item_schema()` — including meeting title, date, attendees, summary, decisions, action items (with owner, due date, priority, context), open questions, and next meeting.
- **Key conventions:** Schema injected as a literal argument (zero-cost `CREATE FUNCTION`); speaker lists provided to constrain `owner` values to exact known names or empty string. Output is raw JSON consumed by downstream tool calls.

**`summarize_transcript`** *(exception path only)*
- **Role:** Condenses an oversized `@clean_transcript` to fit within context limits before re-running `extract_actions`.
- **Key conventions:** Used only when `ContextLengthExceeded` is raised; output replaces the original clean transcript for the re-extraction call.

**`format_as_markdown`**
- **Role:** Renders the validated `@structured_json` and `@validation_notes` as a human-readable Markdown document suitable for wikis or pull-request comments.
- **Key conventions:** Receives both the structured data and ownership validation notes so warnings about unowned high-priority items appear inline.

**`format_as_email`**
- **Role:** Formats the same validated data as a professional follow-up email, suitable for direct distribution to attendees.
- **Key conventions:** Same inputs as Markdown path; expected to produce a subject line and addressable body.

---

### 5. Control Flow

1. **Initialization** — LOGGING records format and filename; `load_transcript` and two `extract_speakers` calls populate file and inline speaker lists deterministically.
2. **Normalisation GENERATE** — `normalize_transcript` produces `@clean_transcript`; intermediate result written to disk via `write_file`.
3. **Extraction GENERATE** — `extract_actions` produces `@structured_json` grounded by schema and speakers; written to disk.
4. **Data quality CALLs** — `normalize_dates` mutates `@structured_json` in-place; `validate_ownership` produces `@validation_notes`.
5. **EVALUATE branch** — Three-way dispatch on `@output_format`:
   - `'markdown'` → GENERATE `format_as_markdown` → write file → `RETURN WITH status='complete', format='markdown'`
   - `'email'` → GENERATE `format_as_email` → write file → `RETURN WITH status='complete', format='email'`
   - *else* → `SET @output = @structured_json` → `RETURN WITH status='complete', format='json'`
6. **Exception path** — If `ContextLengthExceeded` fires at any GENERATE step: GENERATE `summarize_transcript` → GENERATE `extract_actions` → CALL `normalize_dates` → CALL `validate_ownership` → `RETURN WITH status='complete_chunked'` (JSON only; no format branch in fallback).

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile meeting_to_actions.spl --lang python/pocketflow
spl3 splc compile meeting_to_actions.spl --lang python/langgraph
spl3 splc compile meeting_to_actions.spl --lang go
```