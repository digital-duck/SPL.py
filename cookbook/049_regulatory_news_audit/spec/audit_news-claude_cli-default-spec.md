## Summary

The Regulatory News Monitor is an automated compliance screening workflow that reads a batch of financial news items, uses an LLM acting as a senior compliance officer to classify each item's regulatory risk, and persists the results to disk while triggering real-time alerts for high-severity findings. It exists to give compliance teams at large financial institutions continuous, auditable visibility into emerging regulatory risks without requiring manual review of every news feed item. Operations staff and compliance officers benefit directly from automated triage and instant escalation when critical risk is detected.

---

## Detailed Specification

### 1. Purpose

Process a batch of financial news items through an LLM-based compliance audit, persist structured JSON risk assessments per item, and immediately alert stakeholders when any item is classified as high risk.

---

### 2. High-level Description

This workflow, named `news_sentiment_monitor`, implements a batch-iteration pattern using a WHILE loop to drive a single LLM audit function across an arbitrarily sized news feed. The workflow begins by loading the news feed from disk via CALL and checking its length; if the feed is empty an EVALUATE branch fires immediately, returning with `reason = 'feed_empty'` and terminating execution early. For every item that passes this gate, a GENERATE call invokes the `audit_news` CREATE FUNCTION, which injects a senior compliance officer persona and instructs the model to produce strictly valid JSON containing a risk level (`low`, `medium`, or `high`), a list of regulatory flags (Sanctions, AML, Market Manipulation, AI Ethics), and a one-sentence summary. After each GENERATE, two CALL side-effects run: one writes the raw JSON to a per-batch log file under `@log_dir`, and a deterministic JSON field extraction retrieves the `risk_level` without a second LLM call. A nested EVALUATE on `@current_risk` branches on the value `'high'` to fire a CALL to `send_alert`, while all other risk levels are logged at INFO level only. The WHILE counter `@batch_id` increments each iteration, and after the loop exhausts all items the workflow concludes with RETURN `'Scan Complete'` carrying `total_batches = @batch_id` as metadata.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW news_sentiment_monitor` | `WORKFLOW <name>` | Top-level orchestration entry point with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION audit_news(news TEXT)` | `CREATE FUNCTION <name>` | Reusable prompt template; inlines the compliance persona to avoid non-builtin function calls in GENERATE expressions |
| `GENERATE audit_news(@news) INTO @audit_result` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call per news item; result is raw JSON text stored in a variable |
| `CALL read_news_feed(...)`, `CALL write_file(...)`, `CALL send_alert(...)`, `CALL extract_json_field(...)`, etc. | `CALL <tool>(...) INTO @<var>` | Side-effect tool calls for I/O and deterministic extraction; `INTO NONE` used when return value is discarded |
| `WHILE @batch_id < @batch_size DO ... END` | `WHILE <cond> DO ... END` | Iterates over the full news batch; `@batch_id` is the loop counter managed with `:=` assignment |
| `EVALUATE @batch_size WHEN = 0 THEN ...` | `EVALUATE @<var> WHEN ... THEN ...` | Guard clause; fires early RETURN if feed is empty |
| `EVALUATE @current_risk WHEN 'high' THEN ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ...` | Branches within the loop to escalate high-risk findings via alert |
| `RETURN 'No data' WITH reason = 'feed_empty'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial early exit with structured metadata; terminates the workflow before the loop |
| `RETURN 'Scan Complete' WITH total_batches = @batch_id` | `RETURN @<var> WITH <k>=<v>` | Normal termination; carries audit count as output metadata |
| `@news_batch`, `@batch_id`, `@audit_result`, `@current_risk` | SPL `@<var>` (shared state) | All workflow-scoped variables; passed between CALL, GENERATE, and EVALUATE steps |
| `LOGGING f'...' LEVEL INFO/DEBUG/ERROR` | Structured logging | Diagnostic instrumentation at each major step; no SPL branching dependency |

---

### 4. Logical Functions / Prompts

#### `audit_news(news TEXT)`

- **Role:** The sole LLM prompt in the workflow; called once per news item inside the WHILE loop.
- **Key prompt conventions:**
  - Persona injection: the prompt opens with "You are a senior compliance officer at a G-SIB," establishing expert regulatory framing directly in the template body rather than as a separate function call.
  - Domain scope: explicitly restricts attention to four risk categories — Sanctions, AML, Market Manipulation, and AI Ethics — preventing model drift into unrelated topics.
  - Sentinel output format: the word `STRICTLY` combined with an inline JSON schema (`{ "risk_level": "low|medium|high", "flags": [...], "summary": "..." }`) acts as the output sentinel, making downstream deterministic parsing via `extract_json_field` reliable without a second LLM call.
  - Single `{news}` parameter slot receives the raw news text verbatim.

---

### 5. Control Flow

1. **Initialisation** — CALL `read_news_feed` loads the full batch into `@news_batch`; CALL `get_list_length` stores the count in `@batch_size`.
2. **Empty-feed guard** — EVALUATE `@batch_size` against `= 0`; if true, logs an ERROR and executes RETURN with `reason = 'feed_empty'`, halting the workflow entirely.
3. **Batch iteration** — `@batch_id` is initialised to `0`; WHILE `@batch_id < @batch_size` drives the main processing loop.
4. **Per-item processing** — Inside each iteration: CALL `get_item` fetches the current news string; GENERATE `audit_news` produces a JSON audit; CALL `write_file` persists the result; CALL `extract_json_field` extracts `risk_level` deterministically.
5. **Risk branch** — EVALUATE `@current_risk`: if `'high'`, CALL `send_alert` fires and an ERROR log is emitted; all other values fall through the ELSE branch with an INFO log.
6. **Counter advance** — `@batch_id` increments by 1; WHILE condition is re-evaluated.
7. **Termination** — When `@batch_id` reaches `@batch_size`, WHILE exits and RETURN `'Scan Complete'` carries `total_batches = @batch_id` as metadata.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Process a batch of financial news items through an LLM-based compliance audit, persist structured JSON risk assessments per item, and immediately alert stakeholders when any item is classified as high risk." --mode workflow

# Step 2 — compile to any target
spl3 splc compile news_sentiment_monitor.spl --lang python/pocketflow
spl3 splc compile news_sentiment_monitor.spl --lang python/langgraph
spl3 splc compile news_sentiment_monitor.spl --lang go
```