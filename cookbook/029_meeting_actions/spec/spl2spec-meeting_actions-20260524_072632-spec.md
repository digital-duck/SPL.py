## Summary

This workflow converts a meeting transcript — loaded from a file or provided inline — into a structured list of action items with owners, due dates, and priorities. It exists to eliminate the manual effort of reviewing meeting recordings or notes and producing follow-up task lists, reducing post-meeting overhead for teams. Project managers, engineering leads, and anyone who runs recurring meetings benefit directly.

---

## Detailed Specification

### 1. Purpose

Transform a raw meeting transcript into a validated, structured action-item document delivered in the caller's choice of JSON, Markdown, or email format.

---

### 2. High-level Description

The `meeting_to_actions` WORKFLOW accepts a transcript either as a file path (`@filename`) or as an inline string (`@transcript`), along with an `@output_format` selector (`json`, `markdown`, or `email`). Before any LLM call is made, three deterministic CALL tool steps establish grounding facts: `load_transcript` reads the file content, and two `extract_speakers` calls parse known speaker names from both the file and the inline source. A first GENERATE step (`normalize_transcript`) merges the two transcript sources, cleans formatting, and re-identifies speakers to produce a single canonical `@clean_transcript`. A second GENERATE step (`extract_actions`) uses that cleaned text together with a zero-cost `action_item_schema()` JSON schema and the extracted speaker lists to produce a fully-structured JSON object `@structured_json`. Two more deterministic CALL steps then post-process this JSON without LLM involvement: `normalize_dates` converts relative date phrases (e.g., "next Friday") to ISO-8601, and `validate_ownership` flags high-priority items that lack an assigned owner. Finally, an EVALUATE block branches on `@output_format`: the `markdown` branch fires a `format_as_markdown` GENERATE and RETURNs with `status='complete', format='markdown'`; the `email` branch fires `format_as_email` and RETURNs with `status='complete', format='email'`; the default JSON branch sets `@output` directly from `@structured_json` and RETURNs with `status='complete', format='json'`. An EXCEPTION handler for `ContextLengthExceeded` inserts a `summarize_transcript` GENERATE before the extraction step, yielding a condensed summary as input to `extract_actions`, and RETURNs with `status='complete_chunked'` to signal to the caller that the chunked recovery path was used.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW meeting_to_actions` | `WORKFLOW` | Entry point; declares `INPUT:` and `OUTPUT:` |
| `CREATE FUNCTION action_item_schema()` | `CREATE FUNCTION` | Zero-LLM-cost schema injected as grounding context into `extract_actions` |
| `CALL load_transcript(...)` | `CALL` (tool) | Deterministic file loader; no LLM |
| `CALL extract_speakers(...)` | `CALL` (tool) | Called twice — once per transcript source; deterministic |
| `GENERATE normalize_transcript(...)` | `GENERATE ... INTO @var` | First LLM call; merges and cleans raw transcript |
| `GENERATE extract_actions(...)` | `GENERATE ... INTO @var` | Second LLM call; schema-grounded structured extraction |
| `CALL normalize_dates(...)` | `CALL` (tool) | Deterministic ISO-8601 date normalization |
| `CALL validate_ownership(...)` | `CALL` (tool) | Deterministic ownership validation; produces `@validation_notes` |
| `EVALUATE @output_format WHEN = '...' THEN ... ELSE ... END` | `EVALUATE` | Three-branch dispatch on format selector; each branch carries a meaningful RETURN |
| `GENERATE format_as_markdown(...)` / `GENERATE format_as_email(...)` | `GENERATE ... INTO @var` | Formatting LLM calls inside EVALUATE branches |
| `CALL write_file(...)` | `CALL` (tool) | Persists intermediate and final outputs to `@log_dir` |
| `RETURN @output WITH status='complete', format='...'` | `RETURN ... WITH` | Non-trivial — carries both `status` and `format` metadata to caller |
| `RETURN @output WITH status='complete_chunked'` | `RETURN ... WITH` | Signals exception-path recovery to caller |
| `EXCEPTION WHEN ContextLengthExceeded THEN ... END` | `EXCEPTION WHEN` | Inserts `summarize_transcript` step before extraction on long transcripts |
| `@file_content`, `@clean_transcript`, `@structured_json`, `@output` | SPL `@vars` | Shared mutable state threaded through all steps |

---

### 4. Logical Functions / Prompts

**`action_item_schema()`**
- Role: Zero-LLM-cost grounding anchor. Returns a hardcoded JSON Schema object that constrains the output of `extract_actions`. Injected as a literal argument, not an LLM call.
- Key conventions: Defines required fields (`meeting_summary`, `action_items`); `owner` uses exact speaker names or empty string; `priority` is an enum (`high`/`medium`/`low`); `due_date` accepts relative phrases; `context` explains task motivation.

**`normalize_transcript`**
- Role: Merges the file-loaded and inline transcript sources into one canonical text, normalizes whitespace and formatting, and resolves speaker identities using pre-extracted speaker lists.
- Key conventions: Accepts four inputs (file content, inline text, two speaker lists); output is a clean, single-source transcript used by all downstream steps.

**`extract_actions`**
- Role: Core extraction LLM call — the primary deliverable generator. Produces a JSON object conforming to `action_item_schema()`.
- Key conventions: Grounded by both the schema definition and extracted speaker lists to prevent hallucinated owner names; outputs `meeting_title`, `attendees`, `decisions`, `action_items`, `open_questions`, and `next_meeting`.

**`format_as_markdown`**
- Role: Renders `@structured_json` and `@validation_notes` into a human-readable Markdown document.
- Key conventions: Receives both the structured data and ownership validation warnings so flagged items can be highlighted.

**`format_as_email`**
- Role: Renders `@structured_json` and `@validation_notes` into an email-ready plain-text body.
- Key conventions: Same dual-input pattern as `format_as_markdown`; output is formatted for direct copy-paste or SMTP dispatch.

**`summarize_transcript`**
- Role: Exception-path fallback. Compresses a long `@clean_transcript` that exceeded the model context window into a shorter summary suitable for re-running `extract_actions`.
- Key conventions: Used only inside `EXCEPTION WHEN ContextLengthExceeded`; output feeds directly into `extract_actions` as a substitute for `@clean_transcript`.

---

### 5. Control Flow

The workflow starts with two sequential deterministic CALL chains (file load → dual speaker extraction) before the first LLM call. The main path is then strictly linear: `normalize_transcript` → `extract_actions` → `normalize_dates` → `validate_ownership` → EVALUATE branch.

The EVALUATE on `@output_format` is the only branching construct on the happy path. All three branches (`markdown`, `email`, and the ELSE/JSON path) terminate with a RETURN carrying `status='complete'` and a `format=` tag, allowing the caller to inspect which output type was produced.

If `extract_actions` triggers `ContextLengthExceeded`, the EXCEPTION handler inserts `summarize_transcript` before re-running `extract_actions` on the summary, then resumes the deterministic post-processing (`normalize_dates`, `validate_ownership`) and exits with `status='complete_chunked'`. This status is non-trivial — it signals to the caller that the output was derived from a compressed summary rather than the full transcript, which may affect fidelity.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Transform a raw meeting transcript into a validated, \
  structured action-item document delivered in the caller's choice of JSON, Markdown, \
  or email format." --mode workflow

# Step 2 — compile to any target
spl3 splc compile meeting_to_actions.spl --lang python/pocketflow
spl3 splc compile meeting_to_actions.spl --lang python/langgraph
spl3 splc compile meeting_to_actions.spl --lang go
```