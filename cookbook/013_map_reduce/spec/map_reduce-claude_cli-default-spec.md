## Summary

The Map-Reduce Summarizer splits a large document into manageable chunks, summarizes each chunk independently (map phase), then combines all chunk summaries into a single cohesive final summary (reduce phase). It exists to handle documents that exceed an LLM's context window without losing coverage. Content teams, researchers, and document-processing pipelines benefit by getting high-quality summaries of arbitrarily long texts.

---

## Detailed Specification

### 1. Purpose

Produce a styled final summary of any document — regardless of length — by splitting it into chunks, summarizing each chunk via LLM, and reducing all summaries into one quality-checked result.

### 2. High-level Description

This implementation applies the classic map-reduce pattern to LLM-based document summarization. The WORKFLOW `map_reduce_summarizer` accepts a raw document, an optional style directive, and a log directory, and returns a `@final_summary` text variable along with metadata. Two deterministic CALL tools — `chunk_plan()` and `extract_chunk()` — handle splitting without consuming LLM tokens: `chunk_plan()` computes how many chunks to produce, and `extract_chunk()` retrieves each chunk by index. The MAP phase runs a WHILE loop over `@chunk_index < @chunk_count`, calling GENERATE `summarize_chunk()` for each chunk and accumulating results into a `@summaries` list; raw chunks and per-chunk summaries are written to disk via CALL `write_file()` after each iteration. After the loop, the REDUCE phase joins all summaries with GENERATE `reduce_summaries()` to produce `@final_summary`, then GENERATE `quality_score()` evaluates it against the original document. An EVALUATE branch on the score emits `RETURN WITH status='complete'` when the score exceeds 0.7, or triggers GENERATE `improve_summary()` and returns `WITH status='refined'` otherwise. Two EXCEPTION handlers — `ContextLengthExceeded` and `BudgetExceeded` — perform a graceful partial reduce over whatever summaries were collected before the error, writing the result and returning `WITH status='partial'` or `WITH status='budget_limit'` respectively.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW map_reduce_summarizer` | `WORKFLOW <name>` | Top-level orchestration; declares INPUT/OUTPUT variables |
| `chunk_plan()`, `extract_chunk()`, `write_file()` | `CALL <tool>(...) INTO @<var>` | Deterministic, zero LLM tokens; `write_file` is a SPL built-in |
| `summarize_chunk()`, `reduce_summaries()`, `quality_score()`, `improve_summary()` | `GENERATE <fn>(...) INTO @<var>` | Each is a CREATE FUNCTION prompt template backed by an LLM call |
| `WHILE @chunk_index < @chunk_count DO ... END` | `WHILE <cond> DO ... END` | Drives the map phase; `@chunk_index` incremented manually each iteration |
| `EVALUATE @score WHEN > 0.7 THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Branches on numeric quality score to determine refinement |
| `RETURN @final_summary WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial: status token `'complete'` vs `'refined'` drives output metadata |
| `RETURN @final_summary WITH status='refined'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial: triggers after `improve_summary()` refinement path |
| `EXCEPTION WHEN ContextLengthExceeded` | `EXCEPTION WHEN <Type> THEN ...` | Graceful partial reduce; returns `status='partial'` |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type> THEN ...` | Budget guard; returns `status='budget_limit'` |
| `@summaries := []` / `list_append()` / `list_concat()` | Shared state via SPL `@vars` | Mutable list accumulates per-chunk summaries across WHILE iterations |

### 4. Logical Functions / Prompts

**`summarize_chunk(@chunk, @chunk_index)`**
- **Role:** MAP step — condenses one chunk into a self-contained summary.
- **Prompt conventions:** Receives raw chunk text and its positional index; expected to produce a standalone prose summary that preserves key facts without reference to surrounding chunks.

**`reduce_summaries(@summaries_text, @style)`**
- **Role:** REDUCE step — synthesizes all per-chunk summaries into one coherent final summary.
- **Prompt conventions:** Receives newline-joined chunk summaries and a style directive (e.g., `"bullet points"`, `"executive brief"`); the style parameter steers output format and register.

**`quality_score(@final_summary, @document)`**
- **Role:** Quality gate — scores the final summary against the original document.
- **Prompt conventions:** Expected to return a numeric value in [0, 1]; the EVALUATE branch uses `> 0.7` as the pass threshold. No sentinel tokens; numeric output only.

**`improve_summary(@final_summary, @summaries_text)`**
- **Role:** Refinement — rewrites a low-scoring final summary using the raw chunk summaries as a reference.
- **Prompt conventions:** Receives both the draft summary and the full summaries text; returns an improved version that better covers the source material.

### 5. Control Flow

1. **Initialization:** `@chunk_index := 0`, `@summaries := []`.
2. **Chunk planning:** CALL `chunk_plan(@document)` → `@chunk_count`.
3. **MAP loop:** WHILE `@chunk_index < @chunk_count` — extract chunk, write raw chunk to disk, GENERATE `summarize_chunk()`, write summary to disk, append to `@summaries`, increment index.
4. **REDUCE:** Concatenate `@summaries` → `@summaries_text`, GENERATE `reduce_summaries()` → `@final_summary`.
5. **Quality gate:** GENERATE `quality_score()` → `@score`.
6. **EVALUATE branch:**
   - `@score > 0.7` → write final summary, `RETURN WITH status='complete', chunks=@chunk_count`.
   - ELSE → GENERATE `improve_summary()`, write improved summary, `RETURN WITH status='refined', chunks=@chunk_count`.
7. **Exception paths:**
   - `ContextLengthExceeded`: partial reduce over collected `@summaries`, `RETURN WITH status='partial'`.
   - `BudgetExceeded`: same partial reduce, `RETURN WITH status='budget_limit'`.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a styled final summary of any document —
  regardless of length — by splitting it into chunks, summarizing each chunk
  via LLM, and reducing all summaries into one quality-checked result." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile map_reduce_summarizer.spl --lang python/pocketflow
spl3 splc compile map_reduce_summarizer.spl --lang python/langgraph
spl3 splc compile map_reduce_summarizer.spl --lang go
```