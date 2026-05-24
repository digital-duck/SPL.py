## Summary

The Headline News Aggregator is a daily news digest generator that takes a topic and produces a polished, formatted briefing by generating headlines, expanding them with factual summaries, and evaluating coverage completeness before committing. It detects and fills coverage gaps in a single-pass quality gate, then styles the result to a requested format (executive brief, bullet points, narrative, or structured digest). News editors, analysts, and executives who need a reliable, perspective-aware daily briefing on a moving topic area are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Generate a polished, format-styled daily news digest for a user-specified topic by synthesizing headlines, expanding them into factual summaries, evaluating coverage completeness, and filling detected gaps before final formatting.

---

### 2. High-level Description

The `headline_news` WORKFLOW implements a **generate–expand–evaluate–refine–format** pipeline for LLM-powered news synthesis. Two pure helper functions, `news_format_guide` and `perspective_guide`, act as SQL-style CASE lookup tables that inject style and perspective instructions into downstream prompts without making LLM calls themselves. The pipeline opens with a GENERATE call to `generate_headlines`, which produces a numbered list of raw headlines for the topic, followed immediately by a second GENERATE call to `expand_headlines` that annotates each headline with a 2–3 sentence factual summary. A third GENERATE call to `evaluate_coverage` acts as an LLM judge, returning a decimal score between 0.0 and 1.0 representing how completely the summaries cover the topic's major angles. An EVALUATE branch on the score then routes execution: scores above 0.75 proceed directly to a GENERATE call to `format_digest`, which applies the requested style guide and commits the result with `status = 'complete'`; scores at or below 0.75 trigger a GENERATE call to `fill_coverage_gaps`, which appends missing angles to the expanded list before the same `format_digest` step commits with `status = 'refined'`. Every intermediate artifact is persisted to disk via CALL `write_file` side-effects for auditability. Two typed exception handlers guard the outer boundary: `ContextLengthExceeded` falls back to formatting the raw headlines directly with `status = 'partial'`, and `BudgetExceeded` returns the expanded (unformatted) content immediately with `status = 'budget_limit'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW headline_news` | `WORKFLOW` | Top-level orchestration unit; declares typed `INPUT:` / `OUTPUT:` |
| `CREATE FUNCTION news_format_guide` | `CREATE FUNCTION` (data lookup) | No LLM call; pure CASE expression mapping style names to instruction strings |
| `CREATE FUNCTION perspective_guide` | `CREATE FUNCTION` (data lookup) | No LLM call; pure CASE expression mapping perspective names to instruction strings |
| `CREATE FUNCTION generate_headlines` | `CREATE FUNCTION` (prompt template) | LLM call; produces a numbered list of raw headlines |
| `CREATE FUNCTION expand_headlines` | `CREATE FUNCTION` (prompt template) | LLM call; annotates each headline with a factual 2–3 sentence summary |
| `CREATE FUNCTION evaluate_coverage` | `CREATE FUNCTION` (prompt template / judge) | LLM call; returns a bare decimal score 0.0–1.0; sentinel: score-only output with no explanation |
| `CREATE FUNCTION fill_coverage_gaps` | `CREATE FUNCTION` (prompt template) | LLM call; returns full list (original + additions) to patch underrepresented angles |
| `CREATE FUNCTION format_digest` | `CREATE FUNCTION` (prompt template) | LLM call; applies style guide and renders the final output with header |
| `GENERATE ... INTO @var` | `GENERATE` | Five LLM calls storing results in `@headlines`, `@expanded`, `@coverage_score`, `@expanded` (overwrite), `@digest` |
| `CALL write_file(...) INTO NONE` | `CALL` (side-effect) | Persists intermediate artifacts to `@log_dir`; result discarded |
| `EVALUATE @coverage_score WHEN > 0.75` | `EVALUATE` | Single-pass numeric branch; threshold 0.75 routes to `complete` vs. gap-fill path |
| `RETURN @digest WITH status = 'complete'` | `RETURN WITH status=` | Non-trivial: signals clean coverage path to caller |
| `RETURN @digest WITH status = 'refined'` | `RETURN WITH status=` | Non-trivial: signals gap-fill path was taken |
| `RETURN @digest WITH status = 'partial'` | `RETURN WITH status=` | Non-trivial: exception fallback, headlines-only formatting |
| `RETURN @expanded WITH status = 'budget_limit'` | `RETURN WITH status=` | Non-trivial: budget guard, returns unexpanded summaries |
| `EXCEPTION WHEN ContextLengthExceeded` | `EXCEPTION` | Fallback: format raw headlines only |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION` | Fallback: return `@expanded` as-is without final formatting |
| `@headlines`, `@expanded`, `@coverage_score`, `@digest` | `@vars` (shared state) | Passed between GENERATE calls as the workflow's mutable pipeline state |
| `LOGGING ... LEVEL INFO/DEBUG/WARN` | `LOGGING` | Observability hooks; not control flow |

---

### 4. Logical Functions / Prompts

**`news_format_guide(style)`**
- **Role:** Pure style-instruction lookup; output is injected verbatim as `{format_guide}` in `format_digest`. No LLM call.
- **Key conventions:** CASE on four values (`executive brief`, `bullet points`, `narrative`, default `structured`); each branch is a self-contained formatting instruction string.

**`perspective_guide(perspective)`**
- **Role:** Pure perspective-instruction lookup; output is injected as `{perspective}` in the three LLM prompt functions that need it. No LLM call.
- **Key conventions:** CASE on four named perspectives (`technical`, `business`, `global`, `policy`) plus a balanced default.

**`generate_headlines(topic, max_headlines, date, perspective)`**
- **Role:** Seeds the pipeline with a numbered list of headlines; no summaries yet.
- **Key conventions:** Strict output format — numbered list only, no inline summaries; `{perspective}` is pre-resolved by `perspective_guide` at call site.

**`expand_headlines(headlines, topic, perspective)`**
- **Role:** Transforms raw headlines into an annotated list. Each item gets a 2–3 sentence factual summary.
- **Key conventions:** Output format mirrors the numbered input with a `Summary:` sub-label per item; preserves original headlines verbatim.

**`evaluate_coverage(expanded, topic, perspective)`**
- **Role:** Acts as an LLM judge that scores coverage completeness.
- **Key conventions:** Sentinel token — **score only, no explanation**; decimal 0.0–1.0 with four anchor descriptions (1.0, 0.75, 0.5, 0.25). This bare-number output is what makes the `EVALUATE @coverage_score WHEN > 0.75` branch parseable.

**`fill_coverage_gaps(expanded, topic, coverage_score, perspective)`**
- **Role:** Patches the expanded list by adding 2–3 headlines+summaries for underrepresented angles.
- **Key conventions:** Must return the **full** list (original + additions) in the same style as `expand_headlines` output so `format_digest` receives a coherent input.

**`format_digest(expanded, topic, date, format_guide)`**
- **Role:** Final rendering step; applies the style guide and adds a topic+date header.
- **Key conventions:** `{format_guide}` is a pre-resolved instruction string from `news_format_guide`; output is the final user-visible artifact.

---

### 5. Control Flow

**Entry:** WORKFLOW receives `@topic`, `@date`, `@max_headlines`, `@style`, `@perspective`, and `@log_dir`.

**Step 1 — Headline generation:** GENERATE `generate_headlines` → `@headlines`. Side-effect: log file written.

**Step 2 — Expansion:** GENERATE `expand_headlines` → `@expanded`. Side-effect: log file written.

**Step 3 — Coverage judgment:** GENERATE `evaluate_coverage` → `@coverage_score` (bare decimal string). Side-effect: log file written.

**Step 4 — Single-pass quality branch (EVALUATE):**
- `@coverage_score > 0.75` → GENERATE `format_digest` → `@digest` → RETURN WITH `status = 'complete'`.
- ELSE (coverage gaps detected) → GENERATE `fill_coverage_gaps` → `@expanded` (overwritten in-place) → GENERATE `format_digest` → `@digest` → RETURN WITH `status = 'refined'`.

There is **no WHILE loop**; the gap-fill step executes at most once. The EVALUATE is a single conditional fork, not an iterative refinement gate.

**Exception paths:**
- `ContextLengthExceeded` (context window overflow, typically on large `@expanded`): falls back to formatting the shorter `@headlines` directly → RETURN WITH `status = 'partial'`.
- `BudgetExceeded` (token budget hit before formatting): returns `@expanded` without final styling → RETURN WITH `status = 'budget_limit'`.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 "High-level Description" as text2spl input)
spl3 text2spl --description "Generate a polished, format-styled daily news digest for a user-specified topic by synthesizing headlines, expanding them into factual summaries, evaluating coverage completeness with an LLM judge that returns a decimal score, filling detected gaps in a single pass when the score is at or below 0.75, and applying a user-selected style guide before committing. Use typed exception handlers for ContextLengthExceeded (fallback to raw headlines) and BudgetExceeded (return unexpanded summaries). Persist all intermediate artifacts via write_file side-effects." --mode workflow

# Step 2 — compile to any target
spl3 splc compile headline_news.spl --lang python/langgraph
spl3 splc compile headline_news.spl --lang python/pocketflow
spl3 splc compile headline_news.spl --lang go

# Step 3 — run directly
spl3 run headline_news.spl --adapter claude_cli --model claude-opus-4-6 \
    topic="renewable energy" style="executive brief" perspective="policy" max_headlines=5
```