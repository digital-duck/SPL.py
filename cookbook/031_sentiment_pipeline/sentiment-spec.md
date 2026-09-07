## 0. High-level Description

`sentiment_pipeline` implements a **batch sentiment analysis** workflow that combines deterministic tool calls with selective LLM generation to score, aggregate, and narrate sentiment trends across a collection of text items. The pipeline begins with two CALL side-effects — `load_items` to read an optional file and `split_items` to normalize the input into a clean JSON array — keeping all data-wrangling entirely outside the LLM. A single GENERATE step (`batch_sentiment`) then invokes the model against the full item list at once, grounded by a zero-cost JSON schema injected via `CREATE FUNCTION sentiment_schema()`, which enforces a four-label taxonomy (`positive`, `negative`, `neutral`, `mixed`), a float sentiment score on `[-1, 1]`, confidence, detected emotions, and key phrases. Two further deterministic CALL steps (`compute_stats`, `find_extremes`) extract aggregate statistics and notable outliers before two additional GENERATE calls (`summarize_sentiment_trends`, `assemble_sentiment_report`) produce a prose trend narrative and a full formatted report, respectively. LOGGING statements at INFO and DEBUG levels bracket every major stage, and a `ContextLengthExceeded` EXCEPTION handler gracefully degrades by bypassing per-item detail and returning only the stats-plus-trend summary, annotating the RETURN with `status = 'stats_only'` and a reason field.

---

## 1. Purpose

Performs batch sentiment classification over a list of text inputs and returns a structured report containing per-item labels and scores, aggregate trend statistics, and a natural-language narrative summary — all scoped to a configurable domain.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@filename` | `''` (empty) | Path to a text file containing input items to analyse; if empty, `@items` is used instead |
| `@items` | `''` (empty) | Pipe/delimiter-separated inline text items; used when no filename is supplied |
| `@delimiter` | `\n` | Character or string used to split `@items` into individual entries |
| `@domain` | `'general'` | Semantic domain label (e.g. `product_reviews`, `support_tickets`) passed as grounding context to each LLM prompt |

---

## 3. Process

1. **Log startup** — emit an INFO log recording `@domain` and `@filename` before any work begins.
2. **Load file content** — CALL `load_items(@filename)` to read the file into `@file_content`; if `@filename` is empty this returns an empty string (deterministic, no LLM).
3. **Split into item list** — CALL `split_items(@file_content, @items, @delimiter)` to merge file content and inline items, split on the delimiter, and store a clean JSON array in `@item_list`; log the result at DEBUG level (deterministic, no LLM).
4. **Batch sentiment classification** — GENERATE `batch_sentiment(@item_list, sentiment_schema(), @domain)` to send the full item list plus the embedded JSON schema to the LLM; results are stored in `@sentiment_results` as a JSON array with one entry per input item containing `label`, `score`, `confidence`, `emotions`, and `key_phrases`.
5. **Compute aggregate statistics** — CALL `compute_stats(@sentiment_results)` to calculate distribution counts, mean score, and other summary figures; store as `@stats_json` and log at DEBUG level (deterministic, no LLM).
6. **Identify extremes** — CALL `find_extremes(@sentiment_results)` to surface the most positive, most negative, highest-confidence, and other notable items into `@extremes` (deterministic, no LLM).
7. **Generate trend narrative** — GENERATE `summarize_sentiment_trends(@stats_json, @extremes, @domain)` to produce a prose summary of the overall sentiment trend; log completion at DEBUG level.
8. **Assemble final report** — GENERATE `assemble_sentiment_report(@sentiment_results, @stats_json, @trend_summary, @extremes, @domain)` to combine all artefacts into the complete formatted `@report`.
9. **Log completion and return** — emit an INFO log, then RETURN `@report` with metadata `status = 'complete'` and `domain = @domain`.

---

## 4. Error Handling

- **`ContextLengthExceeded`** — triggered when the full per-item results exceed the model's context window during report assembly. The handler re-runs `compute_stats` and `find_extremes` on whatever partial results are available, re-generates the trend narrative from those statistics alone (skipping per-item detail), sets `@report` to just the trend summary, and returns with `status = 'stats_only'` and `reason = 'context_length_exceeded'` to signal the degraded output to the caller.

---

## 5. Output

| Field | Value |
|---|---|
| Return variable | `@report` — a formatted text report |
| `status` (normal path) | `'complete'` |
| `status` (degraded path) | `'stats_only'` |
| `domain` | echoed from input `@domain` |
| `reason` | `'context_length_exceeded'` (degraded path only) |

On the normal path the report contains: per-item sentiment labels, scores, confidence values, detected emotions, and key phrases; aggregate distribution statistics; and a natural-language trend narrative. On the degraded path only aggregate statistics and the trend narrative are included; per-item detail is omitted.