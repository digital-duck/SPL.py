## Summary

This workflow analyzes sales data for a given period by delegating all arithmetic to deterministic Python tools and reserving the LLM solely for writing the natural-language narrative report. It exists to demonstrate the correct architectural boundary between tool-based computation and language generation, preventing the numeric hallucinations that arise when LLMs are asked to do math. Business analysts and developers building data-reporting pipelines benefit from this pattern.

---

## Detailed Specification

### 1. Purpose

Compute key sales metrics (total, average, min, max, period-over-period growth) using registered Python tools and then produce a formatted narrative report via a single LLM GENERATE call.

---

### 2. High-level Description

The `sales_analysis` WORKFLOW accepts three inputs — a comma-separated list of sales figures (`@sales`), the prior-period total (`@prev_total`), and a label for the reporting period (`@period`) — and produces a prose report in `@report`. The entire numeric pipeline is handled by seven sequential CALL statements that invoke registered Python tools: `sum_values`, `average_values`, `min_value`, `max_value`, `percentage_change`, and two `format_currency` calls for display formatting. No LLM tokens are consumed during this phase, making it deterministic and instantaneous. Once all metrics are bound to SPL variables (`@total`, `@avg`, `@low`, `@high`, `@growth`, `@total_fmt`, `@avg_fmt`), a single GENERATE call invokes the `sales_report` prompt template, passing all computed values so the LLM can write a fluent, data-grounded narrative. An EXCEPTION handler catches any failure (tool errors, generation errors, or bad input) and falls back to a GENERATE call on `error_summary` before returning with `status = 'error'`, ensuring the workflow always produces a usable output rather than a raw stack trace.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW sales_analysis` | `WORKFLOW` | Top-level named workflow with `INPUT:` / `OUTPUT:` declarations |
| `INPUT: @sales, @prev_total, @period` | SPL `@var` declarations | All three carry `DEFAULT` values for standalone testing |
| `CREATE FUNCTION sales_report(...)` | `CREATE FUNCTION` | Prompt template that accepts pre-computed metric variables |
| `CREATE FUNCTION error_summary(...)` | `CREATE FUNCTION` | Fallback prompt template used only in the exception path |
| `CALL sum_values(@sales) INTO @total` | `CALL` → Python tool | Dispatches to registered Python function; never falls through to LLM |
| `CALL percentage_change(...) INTO @growth` | `CALL` → Python tool | Same dispatch; deterministic arithmetic |
| `GENERATE sales_report(...) INTO @report` | `GENERATE` | Only LLM call in the happy path; all inputs are already computed |
| `RETURN @report WITH status = 'complete'` | `RETURN WITH status=` | Non-trivial status token signals successful completion to any caller |
| `EXCEPTION WHEN OTHERS THEN ... RETURN ... WITH status = 'error'` | `EXCEPTION WHEN` | Typed catch-all; `status = 'error'` is load-bearing for upstream EVALUATE |

---

### 4. Logical Functions / Prompts

**`sales_report`**
- **Role:** The sole narrative-generation prompt; receives fully computed, pre-formatted metrics as parameters and writes a human-readable period summary.
- **Key conventions:** All numeric inputs arrive as formatted strings (`@total_fmt`, `@avg_fmt`) or raw numbers (`@low`, `@high`, `@growth`), so the LLM never performs arithmetic. The prompt should instruct the model to produce concise business prose (e.g., 3–5 sentences) referencing the period label and growth figure.

**`error_summary`**
- **Role:** Graceful-degradation prompt invoked only in the EXCEPTION branch; produces a user-facing message acknowledging the failure.
- **Key conventions:** Receives only `@period` as context — by design, since metric variables may be undefined at the point of failure. Output should be brief and non-technical.

---

### 5. Control Flow

Execution is linear with one guarded exit:

1. **Computation phase** — seven sequential CALL statements bind metric variables; any tool failure immediately jumps to the EXCEPTION handler.
2. **Generation phase** — a single GENERATE call produces the narrative report using all bound variables.
3. **Happy-path exit** — `RETURN @report WITH status = 'complete'`.
4. **Exception path** — `EXCEPTION WHEN OTHERS` catches any error, runs `GENERATE error_summary(...)`, and exits with `status = 'error'`. This status token is meaningful: any parent WORKFLOW that CALLs `sales_analysis` can EVALUATE the returned status to decide whether to retry or escalate.

There is no WHILE loop and no EVALUATE branching in this workflow — control flow is entirely straight-line except for the exception guard.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Compute key sales metrics (total, average, min, \
  max, period-over-period growth) using registered Python tools and then \
  produce a formatted narrative report via a single LLM GENERATE call." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile sales_analysis.spl --lang python/pocketflow
spl3 splc compile sales_analysis.spl --lang python/langgraph
spl3 splc compile sales_analysis.spl --lang go
```