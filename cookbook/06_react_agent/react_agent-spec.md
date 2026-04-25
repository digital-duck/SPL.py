## 0. High-level Description

This workflow implements a **ReAct-style agent** (Reason + Act) that combines deterministic tool execution with LLM-driven narrative generation to produce a population growth report for a given country. Two CREATE FUNCTIONs are defined: `search_population`, a tightly-constrained prompt that instructs the model to invoke `WebSearch` and return a bare integer with no surrounding text or markdown, and `growth_report`, a narrative-only prompt that explicitly forbids tool use and file creation, accepting five pre-computed parameters to produce a 2–3 sentence prose summary. The control flow is strictly linear — no WHILE loop is needed because the data retrieval and computation are fixed-step: two CALL invocations route through the `search_population` PROCEDURE (which wraps a GENERATE) to fetch prior- and current-year populations via WebSearch, followed by a CALL to `calc_growth_rate`, a Python tool registered externally via `--tools`, which performs the arithmetic deterministically at zero LLM cost. A final GENERATE invokes `growth_report` to compose the human-readable narrative. LOGGING is used at INFO level to bracket the overall operation (country and year range) and the computed growth rate, and at DEBUG level to record the raw population figures fetched. The single EXCEPTION handler catches `SearchFailed`, falling back to a `search_error_report` GENERATE and returning with `status = 'error'`, keeping the workflow non-fatal when web retrieval is unavailable.

---

## 1. Purpose

Fetch a country's population for two consecutive years via live web search, compute the year-over-year growth rate using a deterministic Python tool, and return a concise prose report summarising the result.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@country` | `'China'` | Name of the country whose population growth is being analysed |
| `@year_curr` | `2023` | The "current" year of interest; the prior year is derived as `@year_curr - 1` |

---

## 3. Process

1. **Derive prior year** — compute `@year_prev := @year_curr - 1` (e.g. 2022 when default is used).
2. **Log start** — emit an INFO-level log recording the country and the two-year window.
3. **Fetch prior-year population** — CALL the `search_population` PROCEDURE with `(@country, @year_prev)`, which internally GENERATEs the `search_population` prompt to drive a `WebSearch` tool call; the model is constrained to return only a plain integer. Result stored in `@pop_prev`.
4. **Fetch current-year population** — repeat the same CALL with `@year_curr`; result stored in `@pop_curr`.
5. **Log raw figures** — emit a DEBUG-level log with both population values.
6. **Compute growth rate** — CALL the external Python tool `calc_growth_rate(@pop_prev, @pop_curr)` directly (no LLM involvement); result stored in `@growth_rate`.
7. **Log growth rate** — emit an INFO-level log with the computed percentage.
8. **Generate narrative report** — GENERATE `growth_report(...)` passing all five data points (`@country`, both years, both populations, `@growth_rate`) to produce a 2–3 sentence plain-prose summary; result stored in `@report`.
9. **Return** — RETURN `@report` with metadata `status = 'complete'`.

---

## 4. Error Handling

- **`SearchFailed`** — triggered when the web search cannot retrieve population data; the workflow GENERATEs a `search_error_report` (passing `@country`) into `@report` and RETURNs with `status = 'error'`, allowing the caller to detect the failure gracefully without an unhandled exception.

---

## 5. Output

| Field | Value |
|---|---|
| `@report` | Plain-prose TEXT: a 2–3 sentence population growth narrative (or an error description on failure) |
| `status` | `'complete'` on success; `'error'` if `SearchFailed` was caught |

No additional metadata fields are attached to the RETURN statement beyond `status`.