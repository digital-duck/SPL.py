## 0. High-level Description

`meeting_to_actions` implements a **multi-step extraction pipeline** that transforms a meeting transcript into a structured TODO list with owners, due dates, and priorities. The workflow accepts input either as a raw inline transcript string or a path to a file on disk, merging both sources before any LLM work begins. Four `CREATE FUNCTION` prompt templates drive the LLM phases: `normalize_transcript` cleans and de-duplicates the merged text; `extract_actions` uses a zero-cost schema anchor (`action_item_schema()`, itself a `CREATE FUNCTION` returning a static JSON Schema object) together with deterministically extracted speaker names to ground ownership attribution; `format_as_markdown` and `format_as_email` render the validated JSON into human-readable output formats. Between and around the LLM `GENERATE` steps, five deterministic `CALL` tool invocations handle file loading (`load_transcript`), speaker extraction (`extract_speakers`), date normalisation to ISO-8601 (`normalize_dates`), ownership validation (`validate_ownership`), and log file persistence (`write_file`); this deliberate separation of deterministic and non-deterministic work minimises unnecessary model calls. A terminal `EVALUATE @output_format` branch routes the validated JSON through one of three paths — `markdown`, `email`, or a passthrough `json` default — each issuing a `RETURN` with `status = 'complete'` and a `format` metadata field. The single `EXCEPTION` handler catches `ContextLengthExceeded` by inserting a `summarize_transcript` `GENERATE` step before re-running the extraction path, allowing the workflow to gracefully handle very long transcripts with a `status = 'complete_chunked'` signal.

---

## 1. Purpose

Converts a meeting transcript (from a file or inline text) into a validated, structured list of action items with owners, due dates, and priorities, returned in the user's choice of JSON, Markdown, or email format.

---

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `@filename` | `''` (empty) | Path to a transcript file on disk; if empty, file loading is a no-op |
| `@transcript` | `''` (empty) | Inline transcript text passed directly on the command line |
| `@output_format` | `'json'` | Desired output format: `json`, `markdown`, or `email` |
| `@log_dir` | `'cookbook/04_model_showdown/logs-spl'` | Directory where intermediate and final artifacts are written by `write_file` calls |

---

## 3. Process

1. **Log startup.** Emit an `INFO`-level log recording `@output_format` and `@filename`.

2. **Load file transcript.** `CALL load_transcript(@filename)` — reads the file if `@filename` is non-empty; stores content in `@file_content` (deterministic, no LLM).

3. **Extract speakers from both sources.** `CALL extract_speakers(@file_content)` → `@speakers_from_file`; `CALL extract_speakers(@transcript)` → `@speakers_from_inline`. Speaker lists are used later to ground ownership attribution. Log `@speakers_from_file` at `DEBUG`.

4. **Normalise transcript (LLM).** `GENERATE normalize_transcript(...)` merges `@file_content` and `@transcript`, cleans formatting, and resolves speaker names into `@clean_transcript`. Write the result to `{@log_dir}/clean_transcript.md`. Log completion at `DEBUG`.

5. **Extract structured action items (LLM).** `GENERATE extract_actions(@clean_transcript, action_item_schema(), @speakers_from_file, @speakers_from_inline)` — the static JSON Schema and known speaker lists are injected as grounding context to constrain ownership and schema conformance. Result stored in `@structured_json`. Write to `{@log_dir}/structured_json.md`. Log at `INFO`.

6. **Normalise due dates.** `CALL normalize_dates(@structured_json)` converts relative phrases (e.g. "Friday", "end of sprint") to ISO-8601 dates in-place; result overwrites `@structured_json` (deterministic, no LLM).

7. **Validate ownership.** `CALL validate_ownership(@structured_json)` flags high-priority action items that have no assigned owner; findings stored in `@validation_notes` (deterministic, no LLM).

8. **Format and return output.** Branch on `@output_format`:
   - **`markdown`** — `GENERATE format_as_markdown(@structured_json, @validation_notes)` → `@output`; write to `{@log_dir}/output.md`; `RETURN` with `status='complete', format='markdown'`.
   - **`email`** — `GENERATE format_as_email(@structured_json, @validation_notes)` → `@output`; write to `{@log_dir}/output-email.md`; `RETURN` with `status='complete', format='email'`.
   - **`json` (default / else)** — `SET @output = @structured_json` (no additional LLM call); `RETURN` with `status='complete', format='json'`.

---

## 4. Error Handling

- **`ContextLengthExceeded`** — Triggered when the cleaned transcript is too long for the model's context window during the `extract_actions` step. The handler inserts a compression step: `GENERATE summarize_transcript(@clean_transcript)` produces `@summary`, then re-runs `extract_actions`, `normalize_dates`, and `validate_ownership` against the summary. The raw JSON is returned directly (no reformatting step) with `status = 'complete_chunked'` to signal to the caller that the output was derived from a summary rather than the full transcript.

---

## 5. Output

The workflow returns `@output TEXT` via a `RETURN` statement that always includes a `status` field and a `format` field:

| `status` | `format` | Content |
|----------|----------|---------|
| `complete` | `markdown` | LLM-rendered Markdown report including validation notes |
| `complete` | `email` | LLM-rendered email body including validation notes |
| `complete` | `json` | Raw JSON conforming to `action_item_schema()` with normalised dates |
| `complete_chunked` | *(absent)* | Raw JSON derived from a summarised transcript (context-overflow fallback) |

The JSON payload, regardless of format, conforms to the schema declared in `action_item_schema()` and includes: `meeting_title`, `meeting_date`, `attendees`, `meeting_summary`, `decisions[]`, `action_items[]` (each with `task`, `owner`, `due_date` in ISO-8601, `priority` enum, and `context`), `open_questions[]`, and `next_meeting`. Fields `meeting_summary` and `action_items` are required; all others are optional.