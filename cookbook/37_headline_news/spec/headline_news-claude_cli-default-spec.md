## Summary

The Headline News Aggregator is an LLM workflow that produces a polished, topic-focused daily news digest by generating headlines, expanding them into factual summaries, and self-evaluating coverage quality before committing the final output. If the model detects significant gaps in topic coverage, it automatically fills in missing angles before styling the digest. News professionals, analysts, and teams who need a reliable daily briefing on a fast-moving topic area—without manual curation—are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Generate a structured, coverage-validated daily news digest for any given topic by orchestrating headline generation, summary expansion, quality evaluation, and conditional gap-filling into a single end-to-end LLM workflow.

---

### 2. High-level Description

The `headline_news` WORKFLOW executes a four-stage pipeline: headline generation, expansion, coverage evaluation, and conditional refinement. Two SQL-style helper functions—`news_format_guide` and `perspective_guide`—are not LLM calls; they are pure lookup tables that translate user-facing style and perspective tokens into inline prompt instructions injected at call sites. The first GENERATE call invokes `generate_headlines` to produce a numbered list of raw headlines capped at `@max_headlines`; the second GENERATE call invokes `expand_headlines` to annotate each headline with a 2–3 sentence factual summary. A third GENERATE call invokes `evaluate_coverage`, which returns a single decimal score between 0.0 and 1.0 reflecting how completely the major angles for the topic are represented. An EVALUATE branch on that score drives the only meaningful control-flow decision in the workflow: if the score exceeds 0.75, `format_digest` is called immediately and the workflow RETURNs with `status='complete'`; otherwise, `fill_coverage_gaps` is called to append missing-angle summaries to the expanded content before a final `format_digest` pass, yielding `status='refined'`. Every intermediate result is persisted to a log directory via CALL `write_file` side effects. Two EXCEPTION handlers provide graceful degradation: `ContextLengthExceeded` produces a partial digest from raw headlines with `status='partial'`, and `BudgetExceeded` returns the last expanded content with `status='budget_limit'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW headline_news` | `WORKFLOW headline_news` | Declares the named orchestration workflow with typed INPUT/OUTPUT |
| `CREATE FUNCTION news_format_guide` | `CREATE FUNCTION news_format_guide` | SQL CASE helper; returns a plain-text style guide string, not an LLM prompt |
| `CREATE FUNCTION perspective_guide` | `CREATE FUNCTION perspective_guide` | SQL CASE helper; returns a plain-text perspective lens string, not an LLM prompt |
| `CREATE FUNCTION generate_headlines` | `CREATE FUNCTION generate_headlines` | LLM prompt template; `{perspective}` slot receives the output of `perspective_guide(...)` |
| `CREATE FUNCTION expand_headlines` | `CREATE FUNCTION expand_headlines` | LLM prompt template; consumes `@headlines` output of the prior GENERATE |
| `CREATE FUNCTION evaluate_coverage` | `CREATE FUNCTION evaluate_coverage` | LLM prompt template; instructs the model to return a bare decimal score with a sentinel format |
| `CREATE FUNCTION fill_coverage_gaps` | `CREATE FUNCTION fill_coverage_gaps` | LLM prompt template; returns the FULL updated list (original + additions) |
| `CREATE FUNCTION format_digest` | `CREATE FUNCTION format_digest` | LLM prompt template; receives `news_format_guide(...)` output as `{format_guide}` slot |
| `GENERATE ... INTO @var` | `GENERATE ... INTO @var` | Five LLM calls: headlines, expanded, coverage\_score, (conditionally) expanded (refined), digest |
| `CALL write_file(...) INTO NONE` | `CALL write_file(...) INTO NONE` | Side-effect tool call; used for audit logging at every major stage |
| `EVALUATE @coverage_score WHEN > 0.75` | `EVALUATE @coverage_score WHEN > 0.75 THEN ... ELSE ... END` | Numeric threshold branch; the sole non-linear control-flow decision |
| `RETURN @digest WITH status='complete'` | `RETURN @digest WITH status='complete'` | Non-default token; signals clean completion on the high-coverage path |
| `RETURN @digest WITH status='refined'` | `RETURN @digest WITH status='refined'` | Non-default token; signals that gap-filling was required |
| `EXCEPTION WHEN ContextLengthExceeded` | `EXCEPTION WHEN ContextLengthExceeded THEN ... END` | Fallback: format from raw headlines, `status='partial'` |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN BudgetExceeded THEN ... END` | Fallback: return expanded content as-is, `status='budget_limit'` |
| Shared state `@headlines`, `@expanded`, `@coverage_score`, `@digest` | SPL `@vars` | Mutable workflow-scoped variables threaded through all stages |

---

### 4. Logical Functions / Prompts

**`news_format_guide(style)`**
- **Role:** Pure lookup helper; translates the `style` parameter into a formatting instruction block injected into `format_digest`. Not an LLM call.
- **Key conventions:** Four-way CASE: `'executive brief'`, `'bullet points'`, `'narrative'`, default `'structured'`. Returns a compact imperative instruction string.

**`perspective_guide(perspective)`**
- **Role:** Pure lookup helper; translates the `perspective` parameter into a scope-and-framing instruction injected into all three LLM prompt templates that take a perspective slot.
- **Key conventions:** Five-way CASE: `'technical'`, `'business'`, `'global'`, `'policy'`, default `'balanced'`. Returns a single-sentence framing directive.

**`generate_headlines(topic, max_headlines, date, perspective)`**
- **Role:** First-stage prompt; generates a numbered list of raw headlines (no summaries). Sets the topic scope for all downstream steps.
- **Key conventions:** Output format is a strict numbered list (`1. ...`, `2. ...`); no prose. The `{perspective}` slot receives the pre-computed `perspective_guide(...)` string.

**`expand_headlines(headlines, topic, perspective)`**
- **Role:** Second-stage prompt; annotates each headline with a 2–3 sentence factual summary using `[N]. [headline] / Summary: [...]` structure.
- **Key conventions:** Preserves headline numbering; explicitly instructs facts + context + significance per item.

**`evaluate_coverage(expanded, topic, perspective)`**
- **Role:** Quality-gate prompt; returns a single bare decimal score (0.0–1.0) as a sentinel token. Drives the EVALUATE branch.
- **Key conventions:** Score-only output enforced by prompt ("Score only, no explanation"). Rubric anchors: 1.0 = complete, 0.75 = minor gaps, 0.5 = significant gaps, 0.25 = very incomplete.

**`fill_coverage_gaps(expanded, topic, coverage_score, perspective)`**
- **Role:** Refinement prompt; adds 2–3 supplementary headlines + summaries for underrepresented angles, then returns the full merged list.
- **Key conventions:** Output must include the original content plus additions; same style as `expand_headlines` output. Receives the numeric `{coverage_score}` for self-awareness.

**`format_digest(expanded, topic, date, format_guide)`**
- **Role:** Final styling prompt; applies the user-selected format to the expanded (and optionally refined) content and adds a header.
- **Key conventions:** `{format_guide}` slot injects the `news_format_guide(...)` instruction block verbatim. Output must include a header with topic and date.

---

### 5. Control Flow

The workflow executes linearly until the EVALUATE branch:

1. **Init:** Log workflow parameters.
2. **Stage 1 — GENERATE `generate_headlines`** → `@headlines`; log + write `01_headlines.md`.
3. **Stage 2 — GENERATE `expand_headlines`** → `@expanded`; log + write `02_expanded.md`.
4. **Stage 3 — GENERATE `evaluate_coverage`** → `@coverage_score`; log + write `03_coverage_score.txt`.
5. **EVALUATE `@coverage_score`:**
   - **`> 0.75` (high coverage):** GENERATE `format_digest` → `@digest`; write `final_digest.md`; RETURN `status='complete'`.
   - **ELSE (coverage gaps):** GENERATE `fill_coverage_gaps` → `@expanded` (overwrites); write `04_expanded_refined.md`; GENERATE `format_digest` → `@digest`; write `final_digest.md`; RETURN `status='refined'`.
6. **EXCEPTION `ContextLengthExceeded`:** GENERATE `format_digest` from raw `@headlines` (skipping expansion); write `final_digest_partial.md`; RETURN `status='partial'`.
7. **EXCEPTION `BudgetExceeded`:** RETURN `@expanded` (last known good state) with `status='budget_limit'`.

There is no WHILE loop; this is a single-pass workflow with one conditional branch and two exception escape hatches.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a structured, coverage-validated daily news digest \
for any given topic by orchestrating headline generation, summary expansion, quality \
evaluation, and conditional gap-filling into a single end-to-end LLM workflow." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile headline_news.spl --lang python/pocketflow
spl3 splc compile headline_news.spl --lang python/langgraph
spl3 splc compile headline_news.spl --lang go
```