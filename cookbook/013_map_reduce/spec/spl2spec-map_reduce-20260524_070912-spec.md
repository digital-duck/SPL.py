## Summary

The Map-Reduce Summarizer workflow processes documents that are too long to fit in a single LLM context window by splitting the text into manageable chunks, summarizing each chunk independently, then merging all chunk summaries into one coherent final summary. A quality gate scores the final result and triggers an automatic refinement pass if the score falls below threshold. This is useful for researchers, analysts, and developers who need reliable summaries of large corpora, reports, or codebases without hitting model context limits.

---

## Detailed Specification

### 1. Purpose

Summarize arbitrarily large text documents by applying a map-reduce pattern: split → summarize each piece → merge → score → optionally refine.

---

### 2. High-level Description

`map_reduce_summarizer` is a WORKFLOW that accepts a raw document, an output style preference, and an optional log directory. It begins by invoking the deterministic tool `chunk_plan` (via CALL, consuming zero LLM tokens) to decide how many chunks the document should be divided into. A WHILE loop then iterates over each chunk index: for every iteration, `extract_chunk` (CALL, zero tokens) slices out the chunk, `write_file` persists it to disk, and `summarize_chunk` (GENERATE) produces an LLM summary that is appended to the `@summaries` list and also written to disk. After the loop, the list is concatenated into `@summaries_text` and `reduce_summaries` (GENERATE) combines all chunk summaries into a single `@final_summary` respecting the requested style. A second GENERATE call to `quality_score` returns a numeric confidence score; an EVALUATE branch accepts the summary as-is with `status='complete'` when the score exceeds 0.7, or fires `improve_summary` (GENERATE) for a single refinement pass and returns with `status='refined'`. Two EXCEPTION handlers — for `ContextLengthExceeded` and `BudgetExceeded` — perform a best-effort reduce on whatever partial summaries have accumulated and return with `status='partial'` or `status='budget_limit'` respectively, ensuring the workflow never exits empty-handed.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `map_reduce_summarizer` node class | `WORKFLOW map_reduce_summarizer` | Top-level named orchestration unit with INPUT/OUTPUT declarations |
| Python chunking utility | `CALL chunk_plan(@document) INTO @chunk_count` | Deterministic; zero LLM tokens; returns integer chunk count |
| Python slice utility | `CALL extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk` | Deterministic; zero LLM tokens; called once per WHILE iteration |
| File persistence | `CALL write_file(path, content) INTO NONE` | SPL built-in side-effect; used to log chunks, summaries, and final output |
| Per-chunk summarization prompt | `GENERATE summarize_chunk(@chunk, @chunk_index) INTO @chunk_summary` | One LLM call per chunk; result appended to `@summaries` list |
| Merge prompt | `GENERATE reduce_summaries(@summaries_text, @style) INTO @final_summary` | Single LLM call after loop; style parameter shapes output format |
| Quality scoring prompt | `GENERATE quality_score(@final_summary, @document) INTO @score` | LLM returns a numeric score in (0, 1] |
| Refinement prompt | `GENERATE improve_summary(@final_summary, @summaries_text) INTO @final_summary` | Conditional single LLM call; only runs when score ≤ 0.7 |
| Score threshold branch | `EVALUATE @score WHEN > 0.7 THEN ... ELSE ...END` | Non-trivial branch: drives accept vs. refine path |
| Loop over chunks | `WHILE @chunk_index < @chunk_count DO ... END` | Standard map phase; counter incremented manually |
| Shared accumulator | `@summaries` (LIST), `@summaries_text` (TEXT), `@chunk_index` (INT) | SPL `@var` shared state across iterations |
| Accept path exit | `RETURN @final_summary WITH status='complete', chunks=@chunk_count` | Signals no refinement was needed |
| Refine path exit | `RETURN @final_summary WITH status='refined', chunks=@chunk_count` | Signals one improvement pass was applied |
| Context overflow recovery | `EXCEPTION WHEN ContextLengthExceeded THEN ... RETURN WITH status='partial'` | Reduces partial summaries collected so far |
| Budget overflow recovery | `EXCEPTION WHEN BudgetExceeded THEN ... RETURN WITH status='budget_limit'` | Same rescue logic; different status token for caller routing |

---

### 4. Logical Functions / Prompts

**`summarize_chunk`**
- **Role:** Map phase — independently condenses one document fragment into a self-contained summary.
- **Key conventions:** Receives the raw chunk text plus its ordinal index so the LLM can contextualize position (e.g., "chunk 2 of 5"). Output is free-form prose; no sentinel tokens required. Called once per loop iteration; results accumulate in `@summaries`.

**`reduce_summaries`**
- **Role:** Reduce phase — merges all per-chunk summaries into a single coherent final summary.
- **Key conventions:** Receives the newline-joined summaries and a caller-supplied `@style` parameter (e.g., `"bullet points"`, `"executive brief"`). The style parameter is the primary knob for controlling output shape without changing the prompt template.

**`quality_score`**
- **Role:** Quality gate — judges how well the final summary covers the source document.
- **Key conventions:** Must return a floating-point score between 0 and 1. The EVALUATE branch uses `> 0.7` as the acceptance threshold. The prompt should instruct the model to reply with only the numeric value (or a parseable format) to avoid branch misfires.

**`improve_summary`**
- **Role:** Refinement — rewrites the summary when the quality gate rejects it.
- **Key conventions:** Receives both the low-scoring draft and the full `@summaries_text` so the model can cross-reference source material. Runs at most once (no loop); the refined result overwrites `@final_summary` in place.

---

### 5. Control Flow

```
START
  │
  ├─ CALL chunk_plan  →  @chunk_count
  │
  ├─ WHILE @chunk_index < @chunk_count
  │     │
  │     ├─ CALL extract_chunk  →  @chunk
  │     ├─ CALL write_file (raw chunk)
  │     ├─ GENERATE summarize_chunk  →  @chunk_summary
  │     ├─ CALL write_file (chunk summary)
  │     ├─ list_append @summaries
  │     └─ @chunk_index + 1
  │
  ├─ list_concat @summaries  →  @summaries_text
  ├─ GENERATE reduce_summaries  →  @final_summary
  ├─ GENERATE quality_score  →  @score
  │
  └─ EVALUATE @score
        WHEN > 0.7  →  write_file  →  RETURN status='complete'
        ELSE        →  GENERATE improve_summary  →  write_file  →  RETURN status='refined'

EXCEPTION ContextLengthExceeded  →  reduce partial @summaries  →  RETURN status='partial'
EXCEPTION BudgetExceeded         →  reduce partial @summaries  →  RETURN status='budget_limit'
```

The only non-linear control flow is the single EVALUATE branch after the reduce step and the two EXCEPTION handlers. The WHILE loop is strictly linear (no early exit). Status tokens `'complete'`, `'refined'`, `'partial'`, and `'budget_limit'` are all meaningful — callers can route on them to decide whether to re-run, log a warning, or surface the result as-is.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as the text2spl input)
spl3 text2spl --description "map_reduce_summarizer is a WORKFLOW that accepts a raw document, \
an output style preference, and an optional log directory. It begins by invoking the deterministic \
tool chunk_plan (via CALL, zero LLM tokens) to decide how many chunks the document should be \
divided into. A WHILE loop iterates over each chunk index: extract_chunk (CALL, zero tokens) \
slices out the chunk, write_file persists it, and summarize_chunk (GENERATE) produces a summary \
appended to the @summaries list. After the loop, reduce_summaries (GENERATE) combines all chunk \
summaries into a final summary respecting the requested style. A quality_score (GENERATE) returns \
a numeric score; an EVALUATE branch returns status='complete' when score > 0.7, or fires \
improve_summary (GENERATE) for one refinement pass and returns status='refined'. EXCEPTION handlers \
for ContextLengthExceeded and BudgetExceeded perform a best-effort reduce on partial summaries and \
return status='partial' or status='budget_limit'." \
--mode workflow --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile map_reduce_summarizer.spl --lang python/pocketflow
spl3 splc compile map_reduce_summarizer.spl --lang python/langgraph
spl3 splc compile map_reduce_summarizer.spl --lang go
```