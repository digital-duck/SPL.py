## 0. High-level Description

This workflow implements a **tool-use / function-call** pattern where all deterministic computation is deliberately offloaded to registered Python tools via CALL, reserving GENERATE exclusively for natural-language narrative output. The architectural principle is explicit: LLMs handle language, not arithmetic. Six CALL side-effects perform the full statistical suite — `sum_values`, `average_values`, `min_value`, `max_value`, `percentage_change`, `format_currency` — each storing results INTO dedicated output variables before a single GENERATE is ever invoked. The lone `sales_report` CREATE FUNCTION then receives all pre-computed values as parameters, ensuring the LLM never touches raw numbers. A catch-all EXCEPTION WHEN OTHERS branch handles any failure gracefully by invoking an `error_summary` GENERATE and returning with `status = 'error'`, while the happy path RETURNs with `status = 'complete'`. No WHILE loop or EVALUATE branch is present; the control flow is strictly linear, reflecting the stateless, single-pass nature of a deterministic data-pipeline pattern.

## 1. Purpose

Produces a formatted natural-language sales performance report for a given period by computing all statistics via deterministic Python tools and handing only the narrative task to an LLM.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@sales` | `'1200,1450,1380,1600,1750,1900'` | Comma-separated list of individual sales figures for the period |
| `@prev_total` | `'7800'` | Total sales figure from the prior comparable period, used to compute growth |
| `@period` | `'H1 2025'` | Human-readable label for the reporting period, passed through to narrative output |

## 3. Process

1. **Sum** — CALL `sum_values(@sales)` to compute the period total; store in `@total`.
2. **Average** — CALL `average_values(@sales)` to compute the mean sale; store in `@avg`.
3. **Minimum** — CALL `min_value(@sales)` to find the lowest individual figure; store in `@low`.
4. **Maximum** — CALL `max_value(@sales)` to find the highest individual figure; store in `@high`.
5. **Growth** — CALL `percentage_change(@prev_total, @total)` to compute period-over-period change; store in `@growth`.
6. **Format total** — CALL `format_currency(@total)` to produce a display-ready string; store in `@total_fmt`.
7. **Format average** — CALL `format_currency(@avg)` to produce a display-ready string; store in `@avg_fmt`.
8. **Narrative** — GENERATE `sales_report(...)` passing `@period`, `@sales`, `@total_fmt`, `@avg_fmt`, `@low`, `@high`, and `@growth` to the LLM; store the resulting prose in `@report`.
9. **Return** — RETURN `@report` with metadata `status = 'complete'`.

## 4. Error Handling

- **WHEN OTHERS** — catches any exception raised during tool calls or generation; invokes GENERATE `error_summary(@period)` to produce a fallback message, then RETURNs `@report` with `status = 'error'`. No exception type is re-raised; the workflow always terminates with a usable return value.

## 5. Output

| Field | Value | Notes |
|---|---|---|
| `@report` | `TEXT` | Natural-language sales narrative (happy path) or error summary (failure path) |
| `status` | `'complete'` / `'error'` | Indicates whether the workflow completed successfully or fell through to the exception handler |