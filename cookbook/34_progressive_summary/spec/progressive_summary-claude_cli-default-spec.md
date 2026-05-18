## Summary

The Progressive Summarizer condenses any long text into a structured three-layer summary package — a one-sentence distillation, a paragraph-length overview, and a page-length treatment — each layer building coherently on the one before it. It exists because readers at different levels of detail (an executive scanning headlines versus an analyst needing context) need the same content at different resolutions. Any organisation that produces or consumes long-form documents benefits directly.

---

## Detailed Specification

### 1. Purpose

Produce a quality-verified, audience-tailored summary package at three granularity levels (sentence, paragraph, page) from any input text, with a graceful fallback for texts that exceed model context limits.

---

### 2. High-level Description

The `progressive_summarizer` WORKFLOW accepts a raw text, an optional audience label (default `general`), and an optional layer count (default `3`). It uses a SQL-style CREATE FUNCTION called `summary_constraints` as a pure-text helper that returns layer-specific length and focus constraints for each of the three layers: sentence, paragraph, and page. The workflow calls GENERATE `summarize` to produce a one-sentence distillation of the original text, then calls GENERATE `expand_summary` twice — first to expand that sentence into a paragraph using the original text as ground truth, and again to expand the paragraph into a page-length treatment. The second GENERATE `expand_summary` call is guarded by an EVALUATE on `@layers >= 3`, so when the caller requests fewer than three layers the page summary is skipped and `@page_summary` is set to an empty string. After all layers are produced, GENERATE `verify_summary_fidelity` scores how faithfully the sentence and paragraph summaries represent the source, and GENERATE `assemble_summary_package` bundles all layers and the fidelity score into a single structured output. The workflow RETURNs `@summary_package` WITH `status='complete'`, the layer count, audience, and fidelity score as metadata. An EXCEPTION handler for `ContextLengthExceeded` catches oversized inputs, chunks and summarises them directly at paragraph level, then assembles a reduced two-layer package and RETURNs WITH `status='complete_chunked'` to signal the degraded path.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW progressive_summarizer` | `WORKFLOW <name>` | Declares the named orchestration with INPUT / OUTPUT / DO / EXCEPTION blocks |
| `CREATE FUNCTION summary_constraints(layer)` | `CREATE FUNCTION <name>` | SQL-style pure-text helper; returns layer-specific constraint strings; no LLM call involved |
| `GENERATE summarize(...)` | `GENERATE <fn>(...) INTO @<var>` | LLM call for Layer 1; result stored in `@sentence_summary` |
| `GENERATE expand_summary(...)` (×2) | `GENERATE <fn>(...) INTO @<var>` | LLM calls for Layers 2 and 3; each uses the prior layer plus the original text |
| `GENERATE verify_summary_fidelity(...)` | `GENERATE <fn>(...) INTO @<var>` | Quality-gate LLM call; result stored in `@fidelity_score` |
| `GENERATE assemble_summary_package(...)` | `GENERATE <fn>(...) INTO @<var>` | Final assembly LLM call; produces `@summary_package` |
| `EVALUATE @layers WHEN >= 3 THEN ... ELSE ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Conditionally executes Layer 3 generation; sets `@page_summary := ''` on the false branch |
| `RETURN @summary_package WITH status='complete'` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial: `'complete'` vs `'complete_chunked'` distinguishes normal from chunked execution |
| `RETURN @summary_package WITH status='complete_chunked'` | `RETURN @<var> WITH <k>=<v>, ...` | Signals degraded path to the caller; drives downstream decision-making |
| `EXCEPTION WHEN ContextLengthExceeded` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for oversized input; bypasses normal layer progression |
| `@sentence_summary`, `@paragraph_summary`, `@page_summary`, `@fidelity_score`, `@summary_package` | Shared state `@<var>` | Intermediate variables passed between GENERATE calls; `@page_summary` may be empty |

---

### 4. Logical Functions / Prompts

**`summary_constraints(layer)`**
- Role: Configuration helper, not an LLM call. Returns a constraint string injected into summarization prompts to enforce length and focus per layer.
- Conventions: CASE expression over the literals `'sentence'` / `'paragraph'` / `'page'`; falls back to a "comprehensive" instruction for any other value. Used as an argument to `summarize` and `expand_summary`.

**`summarize(text, constraints, audience)`**
- Role: Layer 1 producer. Compresses the full source text into a single sentence.
- Key conventions: Receives the raw text, the sentence-level constraint string (max 25 words, one idea), and the audience label to calibrate register and vocabulary.

**`expand_summary(text, prior_summary, constraints, audience)`**
- Role: Layer 2 and Layer 3 producer. Expands a prior-layer summary while keeping the original text as an accuracy anchor.
- Key conventions: The `prior_summary` argument enforces coherent layering (each layer inherits the framing of the previous one rather than re-reading the raw text independently). Constraints and audience are passed through identically to `summarize`.

**`verify_summary_fidelity(text, sentence_summary, paragraph_summary)`**
- Role: Quality gate. Scores how faithfully the produced summaries represent the source.
- Key conventions: Returns `@fidelity_score`, a value (likely a numeric score or descriptive label) that is logged at INFO level and included in the final package metadata. No threshold-based loop is applied — the score is advisory, surfaced to the caller via RETURN metadata.

**`assemble_summary_package(sentence_summary, paragraph_summary, page_summary, fidelity_score, audience)`**
- Role: Formatter and packager. Combines all layer outputs and the fidelity score into a single structured text artifact.
- Key conventions: `page_summary` may be an empty string (when `@layers < 3` or in the chunked exception path); `fidelity_score` is `'n/a'` in the exception path. Output format is a structured text block suitable for downstream consumption.

**`chunk_and_summarize(text, constraints)`** *(exception path only)*
- Role: Fallback chunker. Splits oversized input and summarises each chunk at paragraph level, producing a condensed text that fits within context limits.
- Key conventions: Used exclusively inside the `ContextLengthExceeded` handler; its output feeds a reduced two-layer assembly.

---

### 5. Control Flow

Execution begins by calling GENERATE `summarize` on the full input text to produce `@sentence_summary` (Layer 1). GENERATE `expand_summary` is then called with the sentence summary to produce `@paragraph_summary` (Layer 2). An EVALUATE on `@layers >= 3` branches: when true, a second GENERATE `expand_summary` produces `@page_summary` (Layer 3); when false, `@page_summary` is set to the empty string. Control then flows unconditionally to GENERATE `verify_summary_fidelity`, followed by GENERATE `assemble_summary_package`. The workflow terminates with RETURN WITH `status='complete'`.

If a `ContextLengthExceeded` exception is raised at any point, execution transfers to the EXCEPTION handler. GENERATE `chunk_and_summarize` reduces the text to a manageable paragraph, GENERATE `summarize` derives a sentence summary from that, and GENERATE `assemble_summary_package` produces a two-layer package. The handler terminates with RETURN WITH `status='complete_chunked'`, allowing the caller to detect and flag the degraded result.

There is no WHILE loop; the workflow is a linear conditional pipeline with a single named exception branch.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a quality-verified, audience-tailored summary \
  package at three granularity levels (sentence, paragraph, page) from any input \
  text, with a graceful fallback for texts that exceed model context limits." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile progressive_summarizer.spl --lang python/pocketflow
spl3 splc compile progressive_summarizer.spl --lang python/langgraph
spl3 splc compile progressive_summarizer.spl --lang go
```