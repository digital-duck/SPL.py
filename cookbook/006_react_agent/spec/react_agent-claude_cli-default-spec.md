## Summary

This workflow retrieves a country's population for two consecutive years using web search, computes the year-over-year growth rate via a deterministic Python tool, and produces a concise prose narrative report. It exists to demonstrate the ReAct agent pattern — separating factual data retrieval (LLM + WebSearch) from arithmetic (Python tool, no LLM) from synthesis (LLM narrative generation). Data analysts and business stakeholders benefit from an accurate, cost-efficient population report without manual data lookup or error-prone LLM arithmetic.

---

## Detailed Specification

### 1. Purpose

Automatically fetch a country's population for two consecutive years, compute the year-over-year growth rate using a deterministic Python tool, and deliver a concise prose report to the end user.

---

### 2. High-level Description

This implementation follows the ReAct agent pattern using a WORKFLOW named `population_growth` that separates retrieval, computation, and synthesis into three distinct stages. Two CALL invocations of the `search_population` PROCEDURE drive WebSearch-backed LLM calls, each using the `search_population` CREATE FUNCTION template to return a bare integer population figure for a specified country and year — the tight prompt enforces no narration, no commas, and no markdown so downstream parsing is reliable. A second CALL routes to the Python tool `calc_growth_rate` registered via `--tools`, performing deterministic arithmetic with zero LLM cost, ensuring the growth rate is always numerically correct. A final GENERATE call uses the `growth_report` CREATE FUNCTION to synthesize a 2–3 sentence plain-prose narrative from the collected data points, explicitly prohibiting markdown headers, file creation, and tool use to keep output clean. Structured LOGGING statements at INFO and DEBUG level bracket each stage for observability. An EXCEPTION handler for `SearchFailed` falls back to a `search_error_report` LLM call and RETURN WITH `status='error'`, while the happy path ends with RETURN WITH `status='complete'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW population_growth` | `WORKFLOW <name>` | Declares the top-level orchestration entry point with typed INPUT/OUTPUT |
| `CREATE FUNCTION search_population` | `CREATE FUNCTION <name>` | Prompt template with `{country}` and `{year}` slots; enforces bare-integer output |
| `CREATE FUNCTION growth_report` | `CREATE FUNCTION <name>` | Prompt template with five data slots; enforces plain-prose output |
| `PROCEDURE search_population` | `PROCEDURE <name>` | Wraps a GENERATE call as a reusable callable unit |
| `CALL search_population(...) INTO @pop_prev/curr` | `CALL <tool>(...) INTO @<var>` | Routes to the PROCEDURE (which calls WebSearch-backed LLM); result stored in variable |
| `CALL calc_growth_rate(...) INTO @growth_rate` | `CALL <tool>(...) INTO @<var>` | Routes directly to Python tool from `tools.py`; deterministic, no LLM |
| `GENERATE growth_report(...) INTO @report` | `GENERATE <fn>(...) INTO @<var>` | LLM call using the `growth_report` function template |
| `@country`, `@year_curr`, `@pop_prev`, etc. | Shared state `@<var>` | Typed workflow-scoped variables passed between all stages |
| `LOGGING ... LEVEL INFO/DEBUG` | `LOGGING` | Observability statements; not a control-flow construct |
| `RETURN @report WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token signals successful completion |
| `RETURN @report WITH status='error'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token signals retrieval failure |
| `EXCEPTION WHEN SearchFailed THEN` | `EXCEPTION WHEN <Type> THEN` | Named handler for web search failures; produces fallback report |

---

### 4. Logical Functions / Prompts

**`search_population(country TEXT, year INT)`**
- **Role:** Data retrieval — instructs the LLM to invoke WebSearch and return a single population integer for the given country and year.
- **Key conventions:** Sentinel constraint — output must be a plain integer, no commas, no spaces, no text, no markdown. An example of valid output (`1409670000`) is embedded in the prompt to anchor format compliance. Narration is explicitly prohibited.

**`growth_report(country, year_prev, pop_prev, year_curr, pop_curr, growth_rate)`**
- **Role:** Synthesis — takes five pre-computed data values and produces a 2–3 sentence human-readable narrative report.
- **Key conventions:** Plain prose only; markdown headers, file creation, and tool use are explicitly forbidden in the prompt. All arithmetic inputs are passed as resolved variables — the LLM performs no computation, only language generation.

---

### 5. Control Flow

1. **Initialization:** `@year_prev` is computed as `@year_curr - 1` via scalar assignment. A LOGGING INFO statement records the run parameters.
2. **Retrieval (parallel by intent, sequential in spec):** CALL `search_population` twice — once for `@year_prev`, once for `@year_curr` — storing results in `@pop_prev` and `@pop_curr`. A LOGGING DEBUG statement records the fetched values.
3. **Computation:** CALL `calc_growth_rate(@pop_prev, @pop_curr)` routes to the Python tool; result stored in `@growth_rate`. A LOGGING INFO statement records the computed rate.
4. **Synthesis:** GENERATE `growth_report(...)` produces `@report` via LLM.
5. **Termination (happy path):** RETURN `@report` WITH `status='complete'`.
6. **Exception path:** If `SearchFailed` is raised at any retrieval stage, GENERATE `search_error_report(@country)` into `@report` and RETURN WITH `status='error'`. No retry loop is defined — the workflow terminates immediately on this exception.

There is no WHILE loop and no EVALUATE branch in this workflow; control flow is strictly linear on the happy path with a single named exception exit.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Automatically fetch a country's population for two consecutive years, compute the year-over-year growth rate using a deterministic Python tool, and deliver a concise prose report to the end user." --mode workflow

# Step 2 — compile to any target
spl3 splc compile population_growth.spl --lang python/pocketflow
spl3 splc compile population_growth.spl --lang python/langgraph
spl3 splc compile population_growth.spl --lang go
```