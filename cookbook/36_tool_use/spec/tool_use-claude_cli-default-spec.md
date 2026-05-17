## Summary

This workflow performs structured sales-period analysis by combining deterministic Python tools for all arithmetic with a single LLM call that produces the natural-language narrative. It exists to enforce a clean architectural boundary: math stays in code, prose stays in the model. Business analysts and reporting systems benefit by receiving accurate, consistently formatted sales summaries without the hallucination risk of asking an LLM to compute numbers.

---

## Detailed Specification

### 1. Purpose

Produce a narrative sales report for a given period by delegating all numeric computation to registered Python tools and using the LLM exclusively to generate the final human-readable summary.

---

### 2. High-level Description

The `sales_analysis` WORKFLOW accepts three inputs — a comma-separated list of sales figures (`@sales`), a previous-period total (`@prev_total`), and a period label (`@period`) — and produces a single `@report` text as output. Before any LLM token is consumed, six CALL statements dispatch all arithmetic to registered Python tools: `sum_values`, `average_values`, `min_value`, `max_value`, `percentage_change`, and `format_currency` (called twice), storing their results in intermediate `@vars`. Only after all numeric facts are resolved does a single GENERATE invoke the `sales_report` function, which receives the period label, raw sales series, formatted totals, average, low, high, and growth percentage, and synthesises them into a natural-language narrative stored in `@report`. The workflow concludes with `RETURN @report WITH status = 'complete'`. An EXCEPTION handler catches any runtime fault via `WHEN OTHERS`, falls back to a minimal `error_summary` GENERATE call, and returns `@report WITH status = 'error'`, ensuring the caller always receives a structured response. There are no loops or conditional branches in the happy path; control flow is entirely linear.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW sales_analysis` | `WORKFLOW <name>` | Declares the named orchestration entry point with typed `INPUT`/`OUTPUT` declarations |
| `CREATE FUNCTION sales_report` | `CREATE FUNCTION <name>` | Prompt template with `{param}` slots for period, sales, computed metrics |
| `CREATE FUNCTION error_summary` | `CREATE FUNCTION <name>` | Fallback prompt template used only in the exception path |
| `CALL sum_values(@sales) INTO @total` | `CALL <tool>(...) INTO @<var>` | Dispatches to a registered Python tool; result stored as `@var` for downstream use |
| `GENERATE sales_report(...) INTO @report` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; consumes all pre-computed `@vars` as prompt slots |
| `RETURN @report WITH status = 'complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'complete'` signals successful termination to the caller |
| `RETURN @report WITH status = 'error'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'error'` signals fault path to the caller |
| `EXCEPTION WHEN OTHERS THEN` | `EXCEPTION WHEN <Type> THEN` | Catch-all handler; triggers the error narrative path |
| Intermediate results | `@<var>` shared state | `@total`, `@avg`, `@low`, `@high`, `@growth`, `@total_fmt`, `@avg_fmt` thread computed data from CALL to GENERATE |

---

### 4. Logical Functions / Prompts

**`sales_report`**
- **Role:** Primary narrative generator; the only LLM call in the happy path.
- **Inputs:** `@period`, `@sales` (raw series), `@total_fmt`, `@avg_fmt`, `@low`, `@high`, `@growth`.
- **Key conventions:** All numeric slots are pre-computed and injected as formatted strings, so the model receives facts rather than raw numbers. The prompt is expected to produce a coherent business prose summary of the period's performance without performing any arithmetic itself.

**`error_summary`**
- **Role:** Minimal fallback narrative used exclusively inside the `EXCEPTION WHEN OTHERS` handler.
- **Inputs:** `@period`.
- **Key conventions:** Accepts only the period label (all computed `@vars` may be unavailable at fault time), producing a brief acknowledgement that the analysis for that period could not be completed.

---

### 5. Control Flow

Execution begins by sequentially issuing six CALL statements against registered Python tools to populate `@total`, `@avg`, `@low`, `@high`, `@growth`, `@total_fmt`, and `@avg_fmt`. Once all intermediate variables are resolved, a single GENERATE call produces `@report`. The workflow terminates with `RETURN @report WITH status = 'complete'`. There is no WHILE loop and no EVALUATE branch in the happy path — the flow is strictly linear. If any step raises a fault, control transfers to the `EXCEPTION WHEN OTHERS` handler, which issues a fallback GENERATE using only `@period` and terminates with `RETURN @report WITH status = 'error'`. The two distinct `status` values (`'complete'` vs `'error'`) are the only meaningful control-flow signals; callers can inspect them to decide how to handle the result.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a narrative sales report for a given period by delegating all numeric computation to registered Python tools and using the LLM exclusively to generate the final human-readable summary." --mode workflow

# Step 2 — compile to any target
spl3 splc compile sales_analysis.spl --lang python/pocketflow
spl3 splc compile sales_analysis.spl --lang python/langgraph
spl3 splc compile sales_analysis.spl --lang go
```