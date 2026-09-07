## 0. High-level Description

This workflow implements a **map-reduce** pattern for summarizing documents that may exceed a single LLM context window. The map phase uses a WHILE loop driven by `@chunk_index < @chunk_count` to iterate over document segments: each iteration CALLs the deterministic (zero-token) tools `chunk_plan` and `extract_chunk` to slice the document, then GENERATEs a per-chunk summary via `summarize_chunk`, writing both the raw chunk and its summary to disk via `write_file` CALL side-effects. The reduce phase concatenates all accumulated summaries and GENERATEs a combined result through `reduce_summaries`, whose output style is governed by the `@style` INPUT parameter. A second GENERATE call invokes `quality_score` to evaluate the final summary against the original document; an EVALUATE branch then either accepts the result (`> 0.7`) or triggers a further GENERATE through `improve_summary` — a lightweight single-pass self-refine step — before writing `final_summary.md` and returning. LOGGING statements emit progress at document ingestion, after chunk planning, after each chunk summary, and on final save. Two EXCEPTION handlers — `ContextLengthExceeded` and `BudgetExceeded` — both perform a best-effort reduce over whatever summaries have accumulated so far and return with a degraded status code rather than failing hard.

## 1. Purpose

Summarize an arbitrarily large document by splitting it into manageable chunks, summarizing each independently, and combining the results into a single quality-checked final summary.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@document` | *(required)* | Full text of the document to summarize |
| `@style` | *(required)* | Desired output style for the final summary (e.g. `"bullet points"`, `"executive brief"`) |
| `@log_dir` | `cookbook/13_map_reduce/logs-spl` | Directory path where chunk files, per-chunk summaries, and the final summary are written |

## 3. Process

1. Initialize `@chunk_index` to `0` and `@summaries` to an empty list.
2. Log the start of the workflow along with the document length.
3. **Plan** — CALL `chunk_plan(@document)` to compute `@chunk_count`, the number of segments the document will be split into (deterministic, consumes no LLM tokens).
4. Log the number of chunks determined.
5. **Map loop** — repeat while `@chunk_index < @chunk_count`:
   - CALL `extract_chunk(@document, @chunk_index, @chunk_count)` to extract the current segment into `@chunk` (deterministic, zero tokens).
   - CALL `write_file` to persist the raw chunk to `<log_dir>/chunk_<N>.md`.
   - GENERATE `summarize_chunk(@chunk, @chunk_index)` into `@chunk_summary` via the LLM.
   - CALL `write_file` to persist the summary to `<log_dir>/summary_<N>.md`.
   - Log progress for this chunk index.
   - Append `@chunk_summary` to `@summaries` and increment `@chunk_index`.
6. **Reduce** — concatenate all entries in `@summaries` with newline separators into `@summaries_text`, then GENERATE `reduce_summaries(@summaries_text, @style)` into `@final_summary`.
7. **Quality check** — GENERATE `quality_score(@final_summary, @document)` into `@score`.
8. **Evaluate score**:
   - If `@score > 0.7`: CALL `write_file` to save `final_summary.md`, log the score, and RETURN with `status = 'complete'`.
   - Otherwise: GENERATE `improve_summary(@final_summary, @summaries_text)` into `@final_summary` (self-refine pass), CALL `write_file` to save `final_summary.md`, log the score, and RETURN with `status = 'refined'`.

## 4. Error Handling

- **`ContextLengthExceeded`** — triggered if any GENERATE call overflows the model's context window. The handler concatenates whatever partial summaries have been collected so far, runs a final `reduce_summaries` GENERATE, writes `final_summary.md`, and returns with `status = 'partial'`.
- **`BudgetExceeded`** — triggered if token or cost limits are hit mid-run. Identical recovery path to `ContextLengthExceeded`: reduce over accumulated summaries, write file, and return with `status = 'budget_limit'`.

## 5. Output

The workflow RETURNs `@final_summary` (TEXT) along with the following metadata fields:

| Field | Possible Values | Meaning |
|---|---|---|
| `status` | `complete` | Summary passed quality threshold (`score > 0.7`) on first attempt |
| `status` | `refined` | Summary required a self-refine pass before saving |
| `status` | `partial` | Run was cut short by `ContextLengthExceeded`; summary covers only processed chunks |
| `status` | `budget_limit` | Run was cut short by `BudgetExceeded`; summary covers only processed chunks |
| `chunks` | integer | Total number of chunks the document was split into (omitted on exception paths) |

The final summary text is also written to `<log_dir>/final_summary.md` in all code paths.