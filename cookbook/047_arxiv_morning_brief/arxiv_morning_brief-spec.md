## 0. High-level Description

This workflow implements a **map-reduce** pattern to produce a Markdown "morning brief" from a collection of arXiv PDF papers. Three CREATE FUNCTIONs drive the LLM work: `chunk_summarizer` takes a raw text section and a token budget and returns a plain-English summary focused on methods and findings; `paper_reducer` acts as a research editor that collapses a list of section summaries into a ~150-word abstract capturing contribution, method, and results; and `brief_writer` acts as a newsletter editor that formats all paper abstracts under `###` headings and appends a `## Key Themes` section listing 2–4 cross-paper themes. Control flow is expressed with two nested WHILE loops — the outer loop iterates over papers (`@i < @n`), and the inner loop iterates over structural chunks of each paper (`@j < @m`) — followed by a final GENERATE that assembles the complete brief. Each GENERATE call uses `WITH OUTPUT BUDGET … TOKENS` to cap LLM output size. Two CALL side-effects handle input normalisation (`parse_urls`, `build_brief_date_header`) and list utilities (`list_count`, `get_item`, `list_append`), while `download_arxiv_pdf` and `semantic_chunk_plan` perform cached/rate-limited I/O. LOGGING statements at INFO, DEBUG, and WARN levels trace paper count, download paths, chunk counts, and per-paper abstracts. Per-paper errors are caught by an inner EXCEPTION block (`ToolError` and `OTHERS`) that logs a warning and skips the offending paper, while an outer EXCEPTION `WHEN OTHERS` catches any catastrophic failure and returns a minimal error payload.

---

## 1. Purpose

Given one or more arXiv PDF URLs (or a file containing them), the workflow downloads, chunks, and summarises each paper, then assembles and returns a formatted Markdown morning brief with per-paper summaries and a cross-paper themes section.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@urls` | *(required)* | Paper sources — accepts a JSON array, space/comma-delimited string, or a file path containing URLs |
| `@date` | `''` | Date string used to build the brief header; empty string triggers auto-detection inside `build_brief_date_header` |
| `@brief_tokens` | `1024` | Maximum output token budget for the final `brief_writer` GENERATE call (controls brief length) |
| `@chunk_tokens` | `512` | Maximum output token budget per `chunk_summarizer` GENERATE call (controls per-chunk summary verbosity) |

---

## 3. Process

1. **Log start** — emit an INFO message signalling the workflow has begun.
2. **Normalise URLs** — CALL `parse_urls(@urls)` to accept any of JSON array, space-delimited, comma-delimited, or file-path input formats; result overwrites `@urls`.
3. **Build date header** — CALL `build_brief_date_header(@date)` to produce a formatted header string stored in `@header`.
4. **Initialise accumulators** — set `@paper_summaries` to an empty list and counter `@i` to 0; CALL `list_count(@urls)` to get total paper count `@n`; log `@n` at INFO.
5. **Outer loop — iterate over papers** (`WHILE @i < @n`):
   - a. CALL `get_item(@urls, @i)` to retrieve the current URL; log it at INFO.
   - b. **Download** — CALL `download_arxiv_pdf(@url)` into `@pdf_path` (cached, rate-limited); log path at DEBUG.
   - c. **Chunk** — CALL `semantic_chunk_plan(@pdf_path)` to produce structural (header/paragraph-based) chunks in `@chunks`; CALL `list_count(@chunks)` to get chunk count `@m`; log at DEBUG.
   - d. **Inner loop — summarise each chunk** (`WHILE @j < @m`): CALL `get_item(@chunks, @j)`, GENERATE `chunk_summarizer(@chunk, @chunk_tokens)` with an output budget of `@chunk_tokens` tokens into `@chunk_summary`, CALL `list_append(@summaries, @chunk_summary)`, increment `@j`.
   - e. **Reduce** — GENERATE `paper_reducer(@summaries)` with a 200-token output budget into `@paper_summary`; log the abstract at DEBUG.
   - f. CALL `list_append(@paper_summaries, @paper_summary)` to accumulate the abstract.
   - g. **Per-paper error handling** — if a `ToolError` or any other exception is raised during steps b–f, log a WARN and skip to the next paper (continue outer loop).
   - h. Increment `@i`.
6. **Log completion** — emit an INFO message that all `@n` papers have been processed.
7. **Assemble brief** — GENERATE `brief_writer(@header, @paper_summaries, @brief_tokens)` with an output budget of `@brief_tokens` tokens into `@brief`.
8. **Log and return** — emit INFO "Brief complete", then RETURN `@brief` with metadata `status = 'complete'` and `papers = @n`.

---

## 4. Error Handling

- **`ToolError` (inner, per-paper)** — raised when a CALL tool fails (e.g. download failure, chunking error); the paper is silently skipped with a WARN log and the outer loop continues to the next URL.
- **`OTHERS` (inner, per-paper)** — any unexpected exception during processing of a single paper; same behaviour as `ToolError` — log WARN and skip.
- **`OTHERS` (outer, workflow-level)** — a catastrophic failure that escapes all per-paper handling (e.g. failure in the final `brief_writer` GENERATE or in pre-loop setup); logs WARN "Brief generation failed" and returns the string `'Brief generation failed.'` with `status = 'error'`.

---

## 5. Output

| Field | Type | Description |
|---|---|---|
| *(return value)* `@brief` | `TEXT` | A Markdown document with `###`-headed per-paper summaries and a `## Key Themes` section |
| `status` | metadata string | `'complete'` on success; `'error'` on workflow-level failure |
| `papers` | metadata int | Total number of URLs that were attempted (`@n`); present only on success |