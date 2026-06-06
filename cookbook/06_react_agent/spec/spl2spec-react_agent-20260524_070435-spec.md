## Summary

This workflow fetches a country's population for two consecutive years using web search, computes the year-over-year growth rate via a deterministic Python tool, and synthesizes a plain-prose narrative report. It exists to demonstrate the ReAct agent pattern in SPL: grounding factual data retrieval in real web search rather than LLM memory. Data analysts, educators, and developers building population analytics pipelines benefit most.

---

## Detailed Specification

### 1. Purpose

Retrieve real-time population figures for a given country across two consecutive years, compute the growth rate without relying on LLM arithmetic, and return a concise narrative report.

---

### 2. High-level Description

The `population_growth` WORKFLOW accepts a country name and a reference year, then derives the prior year by arithmetic (`@year_prev := @year_curr - 1`). It invokes the `search_population` PROCEDURE twice via CALL — once per year — each of which issues a tight GENERATE call using the `search_population` CREATE FUNCTION, whose prompt instructs the LLM to use WebSearch and return only a bare integer, suppressing all narration. Once both population figures are in hand, a second CALL routes to `calc_growth_rate`, a Python tool registered from `tools.py`; this step is entirely deterministic and incurs zero LLM cost. The resulting growth rate and both population values are passed to a final GENERATE using the `growth_report` CREATE FUNCTION, which is explicitly forbidden from tool use or markdown — it produces plain narrative prose only. EXCEPTION handling catches `SearchFailed` and routes to a `search_error_report` GENERATE, returning with `status = 'error'` to signal failure to any caller; the happy path returns with `status = 'complete'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW population_growth` | `WORKFLOW` | Top-level entry point; declares `INPUT:` and `OUTPUT:` |
| `PROCEDURE search_population` | `PROCEDURE` | Named sub-unit wrapping a single GENERATE; called twice, once per year |
| `CREATE FUNCTION search_population` | `CREATE FUNCTION` | Prompt template with `{country}` and `{year}` slots; enforces bare-integer output |
| `CREATE FUNCTION growth_report` | `CREATE FUNCTION` | Prompt template with six slots; enforces plain prose, no tool use |
| `GENERATE search_population(...) INTO @result` | `GENERATE ... INTO @var` | LLM call with WebSearch enabled; result bound to `@result` |
| `GENERATE growth_report(...) INTO @report` | `GENERATE ... INTO @var` | LLM call for narrative synthesis; no tools permitted |
| `CALL search_population(...) INTO @pop_prev/curr` | `CALL ... INTO @var` | Invokes the named PROCEDURE; binds OUTPUT to caller variable |
| `CALL calc_growth_rate(...) INTO @growth_rate` | `CALL ... INTO @var` | Routes to Python tool (`tools.py`); deterministic, no LLM |
| `@year_prev := @year_curr - 1` | shared `@var` arithmetic | Inline scalar computation; no LLM involved |
| `RETURN @report WITH status = 'complete'` | `RETURN ... WITH status=` | Non-trivial: signals success to callers and exception handler |
| `EXCEPTION WHEN SearchFailed THEN` | `EXCEPTION WHEN <Type>` | Named typed handler; catches web-search failure, returns `status = 'error'` |
| `LOGGING ... LEVEL INFO/DEBUG` | `LOGGING` | Observability side-effects; INFO for milestones, DEBUG for intermediate values |

---

### 4. Logical Functions / Prompts

**`search_population`**
- **Role:** Retrieves a single population figure for one (country, year) pair via WebSearch.
- **Key conventions:** Instructs the LLM to use WebSearch as a tool. Output must be a bare integer — no commas, no units, no explanation. A concrete valid-output example (`1409670000`) is included in the prompt to eliminate formatting drift. The tight constraint is intentional: the result feeds directly into a Python arithmetic function where any non-numeric string would raise an error.

**`growth_report`**
- **Role:** Synthesizes a human-readable 2–3 sentence population growth narrative from pre-computed data.
- **Key conventions:** All six values (`country`, `year_prev`, `pop_prev`, `year_curr`, `pop_curr`, `growth_rate`) are injected as prompt slots. The prompt explicitly prohibits markdown headers, file creation, and tool use — this step is pure text generation, no side-effects. Output is plain prose only.

---

### 5. Control Flow

1. **Entry:** `population_growth` WORKFLOW receives `@country` and `@year_curr`; computes `@year_prev` by inline arithmetic.
2. **Data retrieval (linear):** CALL `search_population(@country, @year_prev)` → binds `@pop_prev`. CALL `search_population(@country, @year_curr)` → binds `@pop_curr`. Each CALL descends into the PROCEDURE, which issues a GENERATE with WebSearch.
3. **Computation:** CALL `calc_growth_rate(@pop_prev, @pop_curr)` → binds `@growth_rate`. This is a Python-side tool call; the executor never sends this to an LLM.
4. **Synthesis:** GENERATE `growth_report(...)` → binds `@report`. Single LLM call, no tools.
5. **Termination (happy path):** RETURN `@report` WITH `status = 'complete'`.
6. **Exception path:** If `SearchFailed` is raised at any point during steps 2–3, the handler issues a GENERATE `search_error_report(@country)` and returns WITH `status = 'error'`, allowing a caller WORKFLOW to detect failure via the status field.

There is no WHILE loop and no EVALUATE branch; the control flow is entirely linear except for the typed exception handler.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Retrieve real-time population figures for a given \
country across two consecutive years, compute the growth rate without relying on \
LLM arithmetic, and return a concise narrative report." --mode workflow

# Step 2 — compile to any target
spl3 splc compile population_growth.spl --lang python/pocketflow
spl3 splc compile population_growth.spl --lang python/langgraph
spl3 splc compile population_growth.spl --lang go
```