## Summary

The Sentiment Pipeline is a batch sentiment analysis workflow that processes a list of text items — loaded from a file or passed inline — and returns a structured report containing per-item sentiment scores, aggregate trend statistics, and a narrative summary. It exists to give product, support, and social media teams a fast, repeatable way to extract emotional signals from large collections of short texts without writing custom analysis code.

---

## Detailed Specification

### 1. Purpose

Classify the sentiment of every item in a batch of text inputs, compute aggregate statistics, and assemble a human-readable trend report — all in a single declarative workflow execution.

---

### 2. High-level Description

The `sentiment_pipeline` WORKFLOW accepts four inputs: an optional file path (`@filename`), an optional inline pipe-delimited string (`@items`), a delimiter character (`@delimiter`), and a domain label (`@domain`). It begins with two deterministic CALL steps that load raw file content and split it into a clean JSON array (`@item_list`), incurring zero LLM cost. A single GENERATE call then invokes `batch_sentiment`, which uses a JSON Schema grounding context produced by the `sentiment_schema` CREATE FUNCTION to elicit one structured sentiment object per item — each carrying a label, numeric score, confidence, detected emotions, and key phrases. Two further deterministic CALL steps compute aggregate statistics (`compute_stats`) and identify the most extreme or notable items (`find_extremes`) before any additional LLM calls are made. A second GENERATE call invokes `summarize_sentiment_trends` to produce a narrative trend summary, and a final GENERATE call passes all accumulated state to `assemble_sentiment_report` to render the complete output. The EXCEPTION handler for `ContextLengthExceeded` gracefully degrades to a stats-and-trend-only report by re-running the deterministic CALL steps and the trend GENERATE, then returning with `status = 'stats_only'`; the happy path returns with `status = 'complete'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW sentiment_pipeline` | `WORKFLOW <name>` | Declares the orchestration entry point with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION sentiment_schema()` | `CREATE FUNCTION <name>` | A zero-LLM schema template injected as grounding context; uses `RETURN JSON … AS $$ … $$` literal body |
| `CREATE FUNCTION batch_sentiment(…)` | `CREATE FUNCTION <name>` | Prompt template with `{param}` slots for item list, schema, and domain |
| `CREATE FUNCTION summarize_sentiment_trends(…)` | `CREATE FUNCTION <name>` | Prompt template for narrative trend generation |
| `CREATE FUNCTION assemble_sentiment_report(…)` | `CREATE FUNCTION <name>` | Prompt template for final report assembly |
| `CALL load_items(…) INTO @file_content` | `CALL <tool>(…) INTO @<var>` | Deterministic file-load tool; no LLM |
| `CALL split_items(…) INTO @item_list` | `CALL <tool>(…) INTO @<var>` | Deterministic string-split tool; no LLM |
| `CALL compute_stats(…) INTO @stats_json` | `CALL <tool>(…) INTO @<var>` | Deterministic aggregation over LLM results |
| `CALL find_extremes(…) INTO @extremes` | `CALL <tool>(…) INTO @<var>` | Deterministic ranking/filtering tool |
| `GENERATE batch_sentiment(…) INTO @sentiment_results` | `GENERATE <fn>(…) INTO @<var>` | Single batched LLM call; structured JSON array output |
| `GENERATE summarize_sentiment_trends(…) INTO @trend_summary` | `GENERATE <fn>(…) INTO @<var>` | LLM narrative synthesis |
| `GENERATE assemble_sentiment_report(…) INTO @report` | `GENERATE <fn>(…) INTO @<var>` | Final LLM assembly call |
| `RETURN @report WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token signals successful full-detail run |
| `RETURN @report WITH status='stats_only'` | `RETURN @<var> WITH <k>=<v>` | Degraded path status token; drives different downstream handling |
| `EXCEPTION WHEN ContextLengthExceeded` | `EXCEPTION WHEN <Type> THEN …` | Named exception handler for oversized batches |
| `@filename`, `@items`, `@item_list`, `@stats_json`, etc. | SPL `@vars` | Shared mutable workflow state passed between CALL and GENERATE steps |
| `LOGGING … LEVEL INFO/DEBUG` | `LOGGING` | Structured observability at key pipeline stages |

---

### 4. Logical Functions / Prompts

**`sentiment_schema`**
- **Role:** Provides a static JSON Schema definition injected into the `batch_sentiment` prompt as grounding context. It costs no LLM tokens itself — it is a constant template.
- **Key conventions:** Returns a JSON array schema; each item requires `item`, `label` (enum: `positive | negative | neutral | mixed`), `score` (float –1 to +1), `confidence` (float 0 to 1); optionally includes `emotions` and `key_phrases` arrays.

**`batch_sentiment`**
- **Role:** The primary LLM call. Receives the full item list, the JSON schema for output grounding, and the domain label; produces one structured sentiment object per input item in the same order.
- **Key conventions:** Schema-grounded structured output; order preservation is an explicit schema contract (`"in the same order as the input list"`); domain context steers label calibration.

**`summarize_sentiment_trends`**
- **Role:** Consumes aggregate statistics (`@stats_json`) and extreme/notable items (`@extremes`) to generate a flowing prose narrative describing trends, patterns, and outliers.
- **Key conventions:** Input is structured JSON (not raw text); domain label provides framing for the narrative voice (e.g., "product reviews" vs. "support tickets").

**`assemble_sentiment_report`**
- **Role:** Final synthesis call. Combines the full per-item results, statistics, trend narrative, extremes, and domain into a complete, human-readable report.
- **Key conventions:** Receives all prior workflow state; responsible for formatting, section ordering, and overall report coherence.

---

### 5. Control Flow

The workflow is a **linear pipeline with a single exception branch** — there is no WHILE loop.

1. **Load → Split:** Two deterministic CALL steps convert the raw input (file or inline string) into a normalized `@item_list`.
2. **Batch sentiment:** A single GENERATE call processes all items at once, producing `@sentiment_results`.
3. **Aggregate → Identify extremes:** Two more deterministic CALL steps derive `@stats_json` and `@extremes` from the LLM results.
4. **Trend narrative:** A second GENERATE call produces `@trend_summary`.
5. **Report assembly:** A third GENERATE call produces `@report`.
6. **Termination (happy path):** `RETURN @report WITH status='complete'` signals a full-detail run.
7. **Exception branch (`ContextLengthExceeded`):** If the batch exceeds the model's context window during step 2, the handler re-executes the deterministic CALL steps and the trend GENERATE using whatever partial `@sentiment_results` are available, then terminates with `RETURN @report WITH status='stats_only', reason='context_length_exceeded'` — omitting per-item detail but preserving aggregate insight.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "The sentiment_pipeline WORKFLOW accepts four inputs: an optional file path, an optional inline pipe-delimited string, a delimiter character, and a domain label. It begins with two deterministic CALL steps that load raw file content and split it into a clean JSON array, incurring zero LLM cost. A single GENERATE call then invokes batch_sentiment, which uses a JSON Schema grounding context produced by the sentiment_schema CREATE FUNCTION to elicit one structured sentiment object per item — each carrying a label, numeric score, confidence, detected emotions, and key phrases. Two further deterministic CALL steps compute aggregate statistics and identify the most extreme or notable items before any additional LLM calls are made. A second GENERATE call invokes summarize_sentiment_trends to produce a narrative trend summary, and a final GENERATE call passes all accumulated state to assemble_sentiment_report to render the complete output. The EXCEPTION handler for ContextLengthExceeded gracefully degrades to a stats-and-trend-only report, returning with status = 'stats_only'; the happy path returns with status = 'complete'." --mode workflow

# Step 2 — compile to any target
spl3 splc compile sentiment.spl --lang python/pocketflow
spl3 splc compile sentiment.spl --lang python/langgraph
spl3 splc compile sentiment.spl --lang go
```