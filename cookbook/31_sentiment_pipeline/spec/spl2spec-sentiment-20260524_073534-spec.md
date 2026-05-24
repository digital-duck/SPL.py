## Summary

The Sentiment Pipeline workflow performs batch sentiment analysis over a list of text inputs — from a file or inline — and produces a structured JSON result per item alongside an aggregated trend narrative and a full report. It exists to give teams a repeatable, domain-aware way to process collections of reviews, support tickets, or social posts without writing bespoke analysis code. Product managers, support leads, and data analysts benefit directly from the generated trend summaries and extreme-item highlights.

---

## Detailed Specification

### 1. Purpose

Run structured batch sentiment analysis over an ordered list of text inputs and return a full domain-contextualized report containing per-item labels, scores, emotions, key phrases, aggregate statistics, and a narrative trend summary.

---

### 2. High-level Description

The `sentiment_pipeline` WORKFLOW accepts either a file path (`@filename`) or an inline pipe-delimited string (`@items`), plus an optional `@domain` tag (e.g. `product_reviews`) that grounds all LLM calls. A `CREATE FUNCTION sentiment_schema()` provides a zero-cost JSON schema injected as grounding context — it is never sent to an LLM as a generation target. The pipeline opens with two deterministic CALL steps: `load_items` reads the file (or passes through when empty), and `split_items` normalises the result into a clean JSON array `@item_list`. A single GENERATE call (`batch_sentiment`) then sends the entire item list plus the schema and domain to the LLM, producing one structured object per item — label, score (-1 to +1), confidence, detected emotions, and key phrases — stored in `@sentiment_results`. Two more deterministic CALL steps (`compute_stats`, `find_extremes`) extract aggregate statistics and identify outlier items without any LLM involvement. Two final GENERATE calls then synthesise the analytical output: `summarize_sentiment_trends` writes a prose trend narrative, and `assemble_sentiment_report` composes the complete deliverable. The workflow terminates with `RETURN @report WITH status = 'complete'`. An `EXCEPTION WHEN ContextLengthExceeded` handler catches oversized batches gracefully: it re-runs the stats/extremes CALL steps on whatever partial results exist, generates a condensed trend summary, and returns with `status = 'stats_only'` to signal a degraded-but-valid result to the caller.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `PocketFlow Node` | `WORKFLOW sentiment_pipeline` | Top-level named orchestration unit with INPUT/OUTPUT declarations |
| Schema definition node | `CREATE FUNCTION sentiment_schema()` | Pure data template; zero LLM cost; injected as context into `batch_sentiment` |
| Deterministic processing step | `CALL <tool>(...) INTO @var` | Used for `load_items`, `split_items`, `compute_stats`, `find_extremes` — no LLM |
| LLM generation step | `GENERATE <fn>(...) INTO @var` | Used for `batch_sentiment`, `summarize_sentiment_trends`, `assemble_sentiment_report` |
| Graceful degradation on oversized input | `EXCEPTION WHEN ContextLengthExceeded THEN ... END` | Re-runs stats/extremes CALLs, emits condensed summary, RETURN with `status = 'stats_only'` |
| Non-trivial termination signal | `RETURN @report WITH status = 'complete'` | `'complete'` vs `'stats_only'` lets callers distinguish full vs degraded output |
| Intermediate pipeline state | `@filename`, `@file_content`, `@item_list`, `@sentiment_results`, `@stats_json`, `@extremes`, `@trend_summary`, `@report` | SPL `@vars` thread state across all CALL/GENERATE steps |
| Domain parameterisation | `@domain TEXT DEFAULT 'general'` | Passed into every LLM GENERATE call as grounding context; no EVALUATE branch needed |

> No `WHILE` loop or `EVALUATE` branch exists in this workflow — the pipeline is strictly linear with a single exception path.

---

### 4. Logical Functions / Prompts

**`sentiment_schema()`**
- **Role:** Provides the JSON output schema injected into `batch_sentiment` as a grounding constraint. Not a prompt template — returns a static JSON object.
- **Key conventions:** Defines a typed array where each item has required fields (`item`, `label`, `score`, `confidence`) and optional enrichment fields (`emotions`, `key_phrases`). The `label` field is constrained to an enum (`positive`, `negative`, `neutral`, `mixed`). Score range is -1 to +1; confidence range is 0 to 1.

**`batch_sentiment(@item_list, schema, @domain)`**
- **Role:** The core LLM call. Receives the full item list, the JSON schema, and the domain label; returns one structured sentiment object per input item in the same order.
- **Key conventions:** Schema-grounded structured output. Domain tag steers the LLM's interpretation of sentiment (e.g. what "negative" means in support tickets vs. social posts). Output must be a JSON array matching the schema.

**`summarize_sentiment_trends(@stats_json, @extremes, @domain)`**
- **Role:** Synthesises aggregate statistics and notable outliers into a prose trend narrative. Also used as the sole output in the exception (degraded) path.
- **Key conventions:** Input is structured JSON (stats + extremes); output is human-readable prose. Domain is passed to contextualise the narrative voice.

**`assemble_sentiment_report(@sentiment_results, @stats_json, @trend_summary, @extremes, @domain)`**
- **Role:** Final composition step. Merges per-item detail, statistics, trend narrative, and extreme examples into a single polished report.
- **Key conventions:** Acts as an aggregator prompt — no new analysis, only assembly and formatting. Domain steers section headings or framing.

---

### 5. Control Flow

The pipeline is a strictly linear seven-step sequence with no iteration or branching in the happy path:

1. **Load** — `CALL load_items(@filename)` reads the file if `@filename` is set; otherwise returns an empty string.
2. **Split** — `CALL split_items(@file_content, @items, @delimiter)` normalises whichever source is populated into a JSON array `@item_list`.
3. **Batch sentiment** — `GENERATE batch_sentiment(...)` produces `@sentiment_results`, a structured JSON array with one entry per item.
4. **Stats** — `CALL compute_stats(@sentiment_results)` produces `@stats_json` (label distributions, mean score, etc.).
5. **Extremes** — `CALL find_extremes(@sentiment_results)` identifies the highest-scoring, lowest-scoring, and most-notable items.
6. **Trend narrative** — `GENERATE summarize_sentiment_trends(...)` produces `@trend_summary` from stats and extremes.
7. **Report assembly** — `GENERATE assemble_sentiment_report(...)` merges everything into `@report`.

`RETURN @report WITH status = 'complete'` terminates the happy path.

**Exception path:** If `ContextLengthExceeded` is raised (typically during `batch_sentiment` on very large batches), the handler re-runs steps 4–6 on whatever partial `@sentiment_results` exist, sets `@report = @trend_summary`, and terminates with `RETURN @report WITH status = 'stats_only'`. The caller can inspect `status` to know the report omits per-item detail.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 1 + Section 2 as text2spl input)
spl3 text2spl \
  --description "Run structured batch sentiment analysis over an ordered list of text inputs \
and return a full domain-contextualized report containing per-item labels, scores, emotions, \
key phrases, aggregate statistics, and a narrative trend summary. The workflow accepts either \
a file path or an inline delimited string plus an optional domain tag. Two deterministic tool \
calls load and split the inputs; a single LLM GENERATE call produces structured per-item \
results against a JSON schema; two more deterministic tool calls compute aggregate stats and \
identify extreme items; two final LLM GENERATE calls produce a trend narrative and a full \
assembled report. An EXCEPTION WHEN ContextLengthExceeded handler falls back to a stats-only \
summary and returns with status='stats_only'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile sentiment_pipeline.spl --lang python/pocketflow
spl3 splc compile sentiment_pipeline.spl --lang python/langgraph
spl3 splc compile sentiment_pipeline.spl --lang go
```