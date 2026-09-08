## 0. High-level Description

`headline_news` implements a **generate-expand-evaluate-refine** pattern for producing a daily news digest on a user-supplied topic. The workflow begins with a GENERATE call to `generate_headlines`, which asks an LLM to produce a numbered list of bare headlines, followed immediately by a second GENERATE call to `expand_headlines`, which annotates each headline with a 2–3 sentence factual summary. A third GENERATE call to `evaluate_coverage` returns a single decimal score (0.0–1.0) representing how completely the major topic angles are represented. The workflow then uses an EVALUATE branch on that score: if coverage exceeds 0.75 the content is passed directly to `format_digest` and committed; otherwise a WARN-level LOGGING message is emitted and `fill_coverage_gaps` is called to append missing angles before formatting. Two scalar helper functions — `news_format_guide` and `perspective_guide` — are defined as CREATE FUNCTIONs that return style and framing instructions through SQL-style CASE expressions, and their output is injected into every prompt that requires it, making format (`style`) and analytical lens (`perspective`) fully parameterised. Every intermediate artifact is persisted via CALL `write_file` into a numbered log file under `@log_dir`, and the final digest is written to `final_digest.md` regardless of branch taken. Two EXCEPTION handlers guard resource limits: `ContextLengthExceeded` falls back to formatting the unexpanded headline list only, while `BudgetExceeded` returns whatever expanded content was last computed without further LLM calls.

## 1. Purpose

Automatically generates, expands, evaluates, and optionally refines a formatted daily news digest for a given topic, persisting all intermediate artifacts and returning a styled document ready for consumption.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | *(required)* | The subject area to generate news about (e.g. `"artificial intelligence"`). |
| `@date` | `'today'` | Reference date for the news generation prompt. |
| `@max_headlines` | `7` | Number of top headlines to generate in the first step. |
| `@style` | `'structured'` | Output format style; drives `news_format_guide`. Accepted values: `structured`, `executive brief`, `bullet points`, `narrative`. |
| `@perspective` | `'balanced'` | Analytical lens applied throughout; drives `perspective_guide`. Accepted values: `balanced`, `technical`, `business`, `global`, `policy`. |
| `@log_dir` | `'cookbook/37_headline_news/logs'` | Directory path where intermediate and final files are written. |

## 3. Process

1. **Initialise** — emit an INFO log recording `@topic`, `@max_headlines`, and `@perspective`.
2. **Generate headlines** — GENERATE `generate_headlines(@topic, @max_headlines, @date, perspective_guide(@perspective))` into `@headlines`, producing a numbered plain-text list of headlines with no summaries. Log at DEBUG, then CALL `write_file` → `01_headlines.md`.
3. **Expand headlines** — GENERATE `expand_headlines(@headlines, @topic, perspective_guide(@perspective))` into `@expanded`, replacing each bare headline with a 2–3 sentence factual block. Log at DEBUG, then CALL `write_file` → `02_expanded.md`.
4. **Evaluate coverage** — GENERATE `evaluate_coverage(@expanded, @topic, perspective_guide(@perspective))` into `@coverage_score`. The prompt instructs the model to reply with a single decimal only (0.0–1.0). Log the score at INFO, then CALL `write_file` → `03_coverage_score.txt`.
5. **Branch on score** — EVALUATE `@coverage_score`:
   - **> 0.75 (adequate coverage):** proceed directly to step 6.
   - **≤ 0.75 (coverage gaps):** log a WARN, then GENERATE `fill_coverage_gaps(@expanded, @topic, @coverage_score, perspective_guide(@perspective))` into `@expanded` (overwriting it with the full original-plus-additions list). CALL `write_file` → `04_expanded_refined.md`. Then proceed to step 6.
6. **Format digest** — GENERATE `format_digest(@expanded, @topic, @date, news_format_guide(@style))` into `@digest`, applying style and perspective framing and prepending a header. CALL `write_file` → `final_digest.md`.
7. **Return** — RETURN `@digest` with metadata `status` (`'complete'` or `'refined'`) and the raw `coverage` score.

## 4. Error Handling

- **`ContextLengthExceeded`** — The expanded content exceeded the model's context window. The workflow falls back to formatting the unexpanded `@headlines` (skipping the summaries entirely), writes the result to `final_digest_partial.md`, and returns with `status = 'partial'`. No refinement is attempted.
- **`BudgetExceeded`** — The token or cost budget was exhausted mid-run. The workflow immediately returns whatever state `@expanded` holds at that point (no further GENERATE or CALL steps), with `status = 'budget_limit'`. No file is written for the final digest.

## 5. Output

The workflow returns `@digest` (TEXT), a fully formatted news digest document. The RETURN statement carries two metadata fields:

| Field | Possible Values | Meaning |
|---|---|---|
| `status` | `complete` | Coverage was adequate (score > 0.75); no gap-filling was needed. |
| `status` | `refined` | Coverage gaps were detected; `fill_coverage_gaps` was run before formatting. |
| `status` | `partial` | `ContextLengthExceeded` triggered; digest is based on bare headlines only. |
| `status` | `budget_limit` | `BudgetExceeded` triggered; returns the last available `@expanded` content unformatted. |
| `coverage` | 0.0–1.0 decimal | The raw score from `evaluate_coverage` (absent on `partial` and `budget_limit` paths). |