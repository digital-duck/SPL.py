## 0. High-level Description

This workflow implements a **progressive summarization** (layered compression) pattern that condenses a long input text into three increasingly detailed summary layers: sentence, paragraph, and page. A `CREATE FUNCTION summary_constraints` acts as a lookup table driven by a `layer` sentinel argument, returning tightly scoped formatting instructions (word limits, structure rules) for each tier — these constraints are injected directly into every `GENERATE` call to enforce output shape. The `summarize` function produces the sentence-level summary directly from the source text, while the `expand_summary` function builds each subsequent layer on top of the previous one (not the raw text alone), preserving coherence through the hierarchy. An `EVALUATE @layers` branch gates the third `GENERATE` call so that a `layers=2` invocation safely skips page-length generation and assigns an empty string instead. After all layers are produced, a dedicated `verify_summary_fidelity` `GENERATE` call performs a quality check against the original text, and `assemble_summary_package` renders all layers and the fidelity score into a single structured output. `LOGGING` statements at `INFO` level bookend the workflow and report the fidelity score, while `DEBUG`-level entries confirm each layer's completion; the sole `EXCEPTION WHEN ContextLengthExceeded` handler recovers gracefully by switching to a `chunk_and_summarize` strategy, rebuilding the minimal two-layer package and flagging the result with `status = 'complete_chunked'`.

---

## 1. Purpose

Produce a structured, audience-targeted summary package containing one-sentence, paragraph, and (optionally) page-length summaries of a long text, each layer building on the previous for coherence, along with a fidelity score validating accuracy against the source.

---

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `@text` | *(required)* | The source text to be summarized |
| `@audience` | `'general'` | Target audience tone/framing (e.g. `'executive'`, `'technical'`) |
| `@layers` | `3` | Number of summary layers to generate (2 skips the page-length layer) |

---

## 3. Process

1. Log workflow start at `INFO` level, recording `audience` and `layers` values.
2. Call `GENERATE summarize(...)` with the full source text, `sentence`-tier constraints from `summary_constraints('sentence')`, and the audience parameter — stores the result in `@sentence_summary`.
3. Log layer 1 completion at `DEBUG` level.
4. Call `GENERATE expand_summary(...)` with the full text, `@sentence_summary` as the prior layer, `paragraph`-tier constraints, and the audience — stores result in `@paragraph_summary`.
5. Log layer 2 completion at `DEBUG` level.
6. `EVALUATE @layers`: if `>= 3`, call `GENERATE expand_summary(...)` with the full text, `@paragraph_summary` as the prior layer, and `page`-tier constraints — stores result in `@page_summary`; otherwise assign `@page_summary := ''` (no LLM call).
7. Log layer 3 completion at `DEBUG` level (only if generated).
8. Call `GENERATE verify_summary_fidelity(...)` passing the original text, `@sentence_summary`, and `@paragraph_summary` — stores a quality score in `@fidelity_score`.
9. Log the fidelity score at `INFO` level.
10. Call `GENERATE assemble_summary_package(...)` combining all three layer outputs, the fidelity score, and the audience into a single structured document — stores in `@summary_package`.
11. `RETURN @summary_package` with metadata: `status = 'complete'`, `layers_generated`, `audience`, and `fidelity`.

---

## 4. Error Handling

- **`ContextLengthExceeded`** — the source text exceeds the model's context window: fall back to `GENERATE chunk_and_summarize(...)` using paragraph-tier constraints to produce `@paragraph_summary` from chunked input, then derive `@sentence_summary` from that condensed text; assemble a two-layer package (page layer is empty string, fidelity is `'n/a'`), and return with `status = 'complete_chunked'` to signal the degraded path was taken.

---

## 5. Output

`@summary_package` — a structured text document assembled by `assemble_summary_package`, containing all generated summary layers and the fidelity score, formatted for the specified audience.

**Metadata returned with `RETURN`:**

| Field | Value | Notes |
|-------|-------|-------|
| `status` | `'complete'` or `'complete_chunked'` | `'complete_chunked'` indicates the fallback chunking path was used |
| `layers_generated` | integer (value of `@layers`) | Not present in the chunked fallback return |
| `audience` | string | Reflects the `@audience` input; not present in chunked fallback |
| `fidelity` | score string from `@fidelity_score` | Set to `'n/a'` in the chunked fallback |