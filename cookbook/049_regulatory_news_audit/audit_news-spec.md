## 0. High-level Description

This workflow implements a **regulatory news monitoring** pipeline using an iterative batch-processing pattern. A single `CREATE FUNCTION` named `audit_news` inlines a compliance-officer persona directly into the prompt template, instructing the LLM to analyze a financial news item and return **strictly valid JSON** containing a `risk_level` field (`low|medium|high`), a `flags` array, and a one-sentence `summary`; the focus areas are Sanctions, AML, Market Manipulation, and AI Ethics. The control flow uses a `WHILE @batch_id < @batch_size` loop to iterate over every item in the loaded news feed, calling `GENERATE audit_news(...)` on each one, then using `CALL` side-effects to persist the raw JSON result to a per-batch log file via `write_file` and, for high-risk items, dispatch an alert via `send_alert`. An `EVALUATE @current_risk` branch inside the loop distinguishes `'high'`-risk items — triggering an `ERROR`-level log and an alert call — from all other risk levels, which receive an `INFO`-level clearance log. A guard `EVALUATE @batch_size WHEN = 0` short-circuits the workflow with an early `RETURN` if the feed is empty. The workflow uses structured `LOGGING` at `INFO`, `DEBUG`, and `ERROR` levels throughout to record feed loading, per-item content, risk decisions, and critical alerts, and `RETURN`s a completion status with a `total_batches` metadata field.

---

## 1. Purpose

Automatically audit a batch of financial news items for regulatory risk, log the results, and immediately alert on any high-risk findings.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@news_batch_path` | `cookbook/49_regulatory_news_audit/data/news_feed.txt` | Path to the flat-file news feed to be audited |
| `@log_dir` | `cookbook/49_regulatory_news_audit/logs-spl` | Directory where per-batch JSON audit results are written |

---

## 3. Process

1. Log an `INFO` message announcing the start of the compliance scan and the source path.
2. `CALL read_news_feed(@news_batch_path)` to load all news items into `@news_batch`.
3. `CALL get_list_length(@news_batch)` to obtain `@batch_size`; log the count at `INFO`.
4. `EVALUATE @batch_size`: if it equals `0`, log an `ERROR` and `RETURN 'No data'` with `reason = 'feed_empty'`, terminating the workflow early.
5. Initialize loop counter `@batch_id := 0`.
6. Enter `WHILE @batch_id < @batch_size` loop:
   - a. Log `INFO` that the current batch index is being processed.
   - b. `CALL get_item(@news_batch, @batch_id)` to retrieve the individual news text into `@news`; log the raw text at `DEBUG`.
   - c. `GENERATE audit_news(@news)` — invoke the LLM with the inlined compliance-officer prompt — storing the JSON response in `@audit_result`.
   - d. `CALL write_file(f'{@log_dir}/batch_{@batch_id}.json', @audit_result)` to persist the raw audit JSON to disk.
   - e. `CALL extract_json_field(@audit_result, 'risk_level')` to deterministically parse `@current_risk` from the JSON.
   - f. `EVALUATE @current_risk`: if `'high'`, log a `CRITICAL ALERT` at `ERROR` level and `CALL send_alert(@audit_result)`; otherwise log clearance at `INFO`.
   - g. Increment `@batch_id := @batch_id + 1`.
7. Exit loop; `RETURN 'Scan Complete'` with metadata `total_batches = @batch_id`.

---

## 4. Error Handling

- **Empty feed (`EVALUATE @batch_size = 0`)**: Not a formal `EXCEPTION` block but an explicit early-exit guard — logs an `ERROR` and returns `'No data'` with `reason = 'feed_empty'` before any LLM calls are made.

> **Note:** The script declares no `EXCEPTION WHEN` blocks. It does not explicitly handle `MaxIterationsReached`, `BudgetExceeded`, `ContextLengthExceeded`, `ModelOverloaded`, or other SPL exception types — if any of these occur at runtime they will propagate unhandled to the caller.

---

## 5. Output

| Condition | Return value | Metadata |
|---|---|---|
| Feed was empty | `'No data'` | `reason = 'feed_empty'` |
| All items processed | `'Scan Complete'` | `total_batches = <count of items processed>` |

The `@compliance_report` OUTPUT variable receives the return value string. Side-effect outputs are also produced: one JSON file per news item written to `@log_dir/batch_<N>.json`, and an out-of-band alert payload sent via `send_alert` for every item whose `risk_level` is `high`.