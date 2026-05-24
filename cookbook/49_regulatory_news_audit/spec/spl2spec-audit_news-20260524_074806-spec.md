## Summary

This workflow monitors a batch of financial news items for regulatory compliance risks, acting as an automated compliance officer for a G-SIB (Global Systemically Important Bank). It classifies each news item by risk level (low, medium, or high), persists structured audit records to disk, and fires real-time alerts for high-severity findings. Compliance teams and risk operations desks benefit by getting machine-speed triage of large news feeds without manual review.

---

## Detailed Specification

### 1. Purpose

Automatically audit a batch of financial news items for regulatory risk using an LLM-powered compliance persona, persist structured JSON results per item, and surface critical findings via alerts.

---

### 2. High-level Description

The workflow implements a **batch-audit loop** pattern: it reads a news feed file into a list, guards against empty input with an EVALUATE branch, then iterates over every item with a WHILE loop. For each item, a single GENERATE call invokes `audit_news`, a CREATE FUNCTION that injects a senior compliance officer persona and instructs the LLM to classify the item across four regulatory risk domains — Sanctions, AML, Market Manipulation, and AI Ethics — returning strictly valid JSON with a `risk_level` field, a `flags` list, and a one-sentence `summary`. After generation, two CALL side-effects handle persistence and control: `write_file` saves the raw JSON audit record to a per-batch log file, and `extract_json_field` deterministically parses the `risk_level` from the LLM output without a second LLM call. A second EVALUATE branches on that parsed value: items classified `"high"` log a critical alert and invoke `send_alert`, while all others are logged at INFO. The loop counter `@batch_id` doubles as the item index and the final batch count returned in RETURN WITH metadata when the scan completes normally; an early RETURN WITH `reason = 'feed_empty'` exits immediately if the feed contains no items.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW news_sentiment_monitor` | `WORKFLOW` | Top-level named orchestration unit with INPUT/OUTPUT declarations |
| `CREATE FUNCTION audit_news(news TEXT)` | `CREATE FUNCTION` | Prompt template with persona injection and `{news}` slot; returns strict JSON |
| `GENERATE audit_news(@news) INTO @audit_result` | `GENERATE ... INTO @var` | Single LLM call per news item; stores raw JSON string |
| `CALL read_news_feed(...)` / `write_file(...)` / `send_alert(...)` | `CALL ... INTO @var` / `CALL ... INTO NONE` | Side-effect tool calls; `INTO NONE` when return value is unused |
| `EVALUATE @batch_size WHEN = 0` | `EVALUATE` | Guard branch; triggers early exit on empty feed |
| `EVALUATE @current_risk WHEN 'high'` | `EVALUATE` | Risk-level branch; routes high-severity items to alert path |
| `WHILE @batch_id < @batch_size DO` | `WHILE ... DO ... END` | Iterates over all items in the loaded batch |
| `RETURN 'No data' WITH reason = 'feed_empty'` | `RETURN WITH status=` | Non-default early exit carrying a named reason; signals empty-feed condition to callers |
| `RETURN 'Scan Complete' WITH total_batches = @batch_id` | `RETURN WITH status=` | Normal termination with audit count metadata |
| `@news_batch`, `@batch_id`, `@audit_result`, `@current_risk` | SPL `@vars` | Shared mutable state threaded through the loop body |
| `LOGGING ... LEVEL INFO/DEBUG/ERROR` | `LOGGING` | Structured observability at multiple severity levels; ERROR on critical alerts |

---

### 4. Logical Functions / Prompts

#### `audit_news(news TEXT)`

- **Role:** The sole LLM call in the workflow; acts as the compliance analysis engine for each individual news item.
- **Persona:** Senior compliance officer at a G-SIB — establishes authoritative, risk-focused tone.
- **Risk domains:** Sanctions, AML, Market Manipulation, AI Ethics — exhaustive coverage of major regulatory exposure areas.
- **Output format:** Strict JSON sentinel enforced via `STRICTLY valid JSON` instruction. Schema: `{ "risk_level": "low|medium|high", "flags": ["..."], "summary": "one sentence" }`. The controlled vocabulary for `risk_level` enables downstream deterministic parsing via `extract_json_field` without a second LLM call.
- **Key convention:** The persona and the task instruction are co-located in one function (rather than a separate persona template) so the rendered string can be passed as a single argument to `GENERATE` without non-builtin function composition in the expression.

---

### 5. Control Flow

1. **Initialization** — load news feed from path, measure batch size.
2. **Guard EVALUATE** — if `@batch_size = 0`, RETURN early with `reason = 'feed_empty'`; no further processing.
3. **WHILE loop** — `@batch_id` starts at 0 and increments each iteration until `@batch_id < @batch_size` is false.
4. **Per-item body** — fetch item by index → GENERATE audit → write JSON to disk → extract `risk_level`.
5. **Risk EVALUATE** — if `risk_level = 'high'`: log CRITICAL + call `send_alert`; ELSE: log INFO and continue.
6. **Termination** — RETURN `'Scan Complete'` WITH `total_batches = @batch_id` once all items are processed.

The only non-trivial branches are the two EVALUATE blocks; the WHILE loop provides the only iteration construct. No exception handlers are declared; tool-call errors propagate to the runtime default handler.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Automatically audit a batch of financial news items \
  for regulatory risk using an LLM-powered compliance persona, persist structured \
  JSON results per item, and surface critical findings via alerts." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile audit_news.spl --lang python/pocketflow
spl3 splc compile audit_news.spl --lang python/langgraph
spl3 splc compile audit_news.spl --lang go
```