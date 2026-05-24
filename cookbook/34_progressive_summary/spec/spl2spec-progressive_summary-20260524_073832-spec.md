## Summary

The Progressive Summarizer takes a body of text and produces a structured, audience-aware set of summaries at three increasing levels of detail — one sentence, one paragraph, and one page. Each layer builds on the previous one to preserve coherence rather than re-summarizing from scratch. Content teams, researchers, and executives who need the same material compressed to different depths are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Given an arbitrary body of text, produce a layered summary package at sentence, paragraph, and page granularity — with a fidelity quality score — tailored to a specified audience.

### 2. High-level Description

The workflow opens with `LOGGING` of the run parameters, then executes a fixed linear sequence of `GENERATE` calls that implement a progressive compression strategy. The first `GENERATE` call invokes `summarize` to produce a single sentence (≤ 25 words) capturing the text's central idea; the constraint string itself comes from `summary_constraints`, a deterministic `CREATE FUNCTION` that maps a layer name to a formatting rule, keeping prompt logic out of the workflow body. A second `GENERATE` call invokes `expand_summary` with both the original text and the sentence summary, producing a 3-5 sentence paragraph-level summary that remains anchored to the source rather than drifting from the prior layer alone. An `EVALUATE` block then branches on the integer value of `@layers`: when `@layers >= 3`, a third `GENERATE expand_summary` call produces a 2-3 paragraph page-length summary; otherwise `@page_summary` is set to an empty string. After all layers are generated, `verify_summary_fidelity` makes an LLM-judged quality pass over the original text and both core summaries, returning a fidelity score stored in `@fidelity_score`. Finally, `assemble_summary_package` collects all layers, the fidelity score, and the audience tag into a single structured output, and the workflow `RETURN`s it with `status = 'complete'`. An `EXCEPTION WHEN ContextLengthExceeded` handler provides a graceful fallback: `chunk_and_summarize` splits oversized input into segments, merges them at paragraph level, then `summarize` compresses that to a sentence, and `assemble_summary_package` produces an abbreviated package returned with `status = 'complete_chunked'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION summary_constraints(layer)` | `CREATE FUNCTION` | Deterministic SQL CASE expression; returns a length/format constraint string per layer name. Not an LLM call. |
| `WORKFLOW progressive_summarizer` | `WORKFLOW` | Named workflow with `INPUT:` (`@text`, `@audience`, `@layers`) and `OUTPUT:` (`@summary_package`) declarations. |
| `GENERATE summarize(...) INTO @sentence_summary` | `GENERATE ... INTO @var` | Layer 1 LLM call — one-sentence compression of full input text. |
| `GENERATE expand_summary(...) INTO @paragraph_summary` | `GENERATE ... INTO @var` | Layer 2 LLM call — paragraph built from original text + sentence summary. |
| `EVALUATE @layers WHEN >= 3 THEN ... ELSE ... END` | `EVALUATE` | Branches on an integer threshold to conditionally execute Layer 3; only non-trivial branch in the workflow. |
| `GENERATE expand_summary(...) INTO @page_summary` | `GENERATE ... INTO @var` | Layer 3 LLM call — page built from original text + paragraph summary; inside the `EVALUATE` true branch. |
| `GENERATE verify_summary_fidelity(...) INTO @fidelity_score` | `GENERATE ... INTO @var` | LLM-judged quality gate; scores faithfulness of layers 1 and 2 against the source. |
| `GENERATE assemble_summary_package(...) INTO @summary_package` | `GENERATE ... INTO @var` | Final aggregation step on both the normal and exception paths. |
| `RETURN @summary_package WITH status = 'complete'` | `RETURN @var WITH` | Non-default terminal status on the happy path; signals fully layered output to callers. |
| `RETURN @summary_package WITH status = 'complete_chunked'` | `RETURN @var WITH` | Alternate terminal status from the exception handler; signals that chunking was applied. |
| `EXCEPTION WHEN ContextLengthExceeded THEN ... END` | `EXCEPTION WHEN` | Typed recovery for oversized input; re-routes the summarization through `chunk_and_summarize`. |
| `@sentence_summary`, `@paragraph_summary`, `@page_summary`, `@fidelity_score` | SPL `@vars` | Shared mutable state threaded across `GENERATE` calls; each is an input to the next stage. |

---

### 4. Logical Functions / Prompts

**`summary_constraints(layer TEXT)`**
- **Role:** Deterministic constraint provider, not an LLM prompt. A SQL `CASE` expression that maps `'sentence'` → 25-word one-idea rule, `'paragraph'` → 3-5 sentence coverage rule, `'page'` → 2-3 paragraph full-argument rule, and a default for any other value. Its output string is passed as a parameter into LLM prompt templates to enforce output length and format without embedding constraints directly in the workflow body.

**`summarize(text, constraints, audience)`**
- **Role:** Layer 1 compression. Reduces the full source text to a single sentence capturing the single most important idea.
- **Key conventions:** Receives the `summary_constraints('sentence')` string as an explicit constraint parameter; audience-aware framing is expected to adjust register and vocabulary.

**`expand_summary(text, prior_summary, constraints, audience)`**
- **Role:** Layers 2 and 3 expansion. Takes the original source text plus the previous layer's summary and expands to the next level of detail. Used twice: once at paragraph level (Layer 2, seeded from `@sentence_summary`) and once at page level (Layer 3, seeded from `@paragraph_summary`).
- **Key conventions:** Receiving both the original text and the prior layer prevents semantic drift; the `constraints` parameter (from `summary_constraints`) controls target length and structure; audience-aware.

**`verify_summary_fidelity(text, sentence_summary, paragraph_summary)`**
- **Role:** Quality gate. Scores how faithfully the sentence and paragraph summaries represent the source material.
- **Key conventions:** Returns a fidelity score stored in `@fidelity_score`; this value is passed through to the final package and surfaced in `RETURN` metadata, giving downstream callers a signal-quality indicator without blocking execution.

**`chunk_and_summarize(text, constraints)`**
- **Role:** Exception-path preprocessor only. Splits an oversized input into manageable segments, summarizes each, and merges them into a single paragraph-level summary.
- **Key conventions:** Invoked exclusively inside `EXCEPTION WHEN ContextLengthExceeded`; its output substitutes for `@paragraph_summary` in the abbreviated recovery path.

**`assemble_summary_package(sentence_summary, paragraph_summary, page_summary, fidelity_score, audience)`**
- **Role:** Final aggregation on both paths. Collects all layer outputs and metadata into a single structured document returned as `@summary_package`.
- **Key conventions:** Accepts an empty string for `@page_summary` (when `@layers < 3` or on the exception path) and `'n/a'` for `fidelity_score` on the exception path, so the template must handle absent-layer gracefully.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING (run parameters)
  │
  ├─ GENERATE summarize → @sentence_summary          [Layer 1]
  │
  ├─ GENERATE expand_summary → @paragraph_summary    [Layer 2]
  │
  ├─ EVALUATE @layers >= 3
  │     ├─ TRUE  → GENERATE expand_summary → @page_summary   [Layer 3]
  │     └─ FALSE → @page_summary := ''
  │
  ├─ GENERATE verify_summary_fidelity → @fidelity_score
  │
  ├─ GENERATE assemble_summary_package → @summary_package
  │
  └─ RETURN @summary_package WITH status='complete'

EXCEPTION WHEN ContextLengthExceeded
  │
  ├─ GENERATE chunk_and_summarize → @paragraph_summary
  ├─ GENERATE summarize → @sentence_summary
  ├─ GENERATE assemble_summary_package → @summary_package
  └─ RETURN @summary_package WITH status='complete_chunked'
```

There is no `WHILE` loop. The only branching is a single `EVALUATE` on the integer `@layers` value to gate Layer 3. Both `status = 'complete'` and `status = 'complete_chunked'` are non-trivial tokens — callers can inspect them to know whether chunking was applied and whether a full three-layer package is available.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl \
  --description "Given an arbitrary body of text, produce a layered summary package at \
sentence, paragraph, and page granularity — with a fidelity quality score — tailored \
to a specified audience. Use CREATE FUNCTION for deterministic layer constraints, \
GENERATE calls for each summarization layer where each layer is seeded from the prior \
one for coherence, EVALUATE on an integer layers parameter to conditionally generate \
the page-level layer, a fidelity GENERATE call as a quality gate, a final assembly \
GENERATE call, and EXCEPTION WHEN ContextLengthExceeded to fall back to \
chunk-and-summarize. RETURN with status='complete' on the happy path and \
status='complete_chunked' on the exception path." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile progressive_summarizer.spl --lang python/pocketflow
spl3 splc compile progressive_summarizer.spl --lang python/langgraph
spl3 splc compile progressive_summarizer.spl --lang go
```