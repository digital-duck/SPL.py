## Summary

The arXiv Morning Brief workflow automatically downloads a set of arXiv research PDFs, breaks each into structural chunks, summarizes every chunk with an LLM, reduces those summaries into a per-paper abstract, and finally assembles all abstracts into a polished Markdown newsletter complete with a "Key Themes" section. It exists to give researchers or teams a daily digest of preprints without manual reading. Any reader who wants to stay current with a curated list of papers in minutes rather than hours is the intended beneficiary.

---

## Detailed Specification

### 1. Purpose

Produce a formatted Markdown morning brief from a list of arXiv PDF URLs by downloading, chunking, and LLM-summarizing each paper, then synthesizing all per-paper abstracts into a single newsletter with recurring themes.

---

### 2. High-level Description

The `arxiv_morning_brief` WORKFLOW implements a **map-reduce summarization pipeline** over a variable-length list of arXiv PDFs. It begins by normalizing the incoming URL list (accepting JSON arrays, space/comma-delimited strings, or a file path) and building a dated header via side-effect CALL tools, then iterates over each URL with an outer WHILE loop. Inside the outer loop, a nested WHILE loop drives per-chunk LLM calls: each structural chunk of the PDF is passed to the `chunk_summarizer` CREATE FUNCTION, which produces a concise plain-English summary bounded by an explicit `WITH OUTPUT BUDGET` token cap. Once all chunks are summarized, a single GENERATE call to the `paper_reducer` CREATE FUNCTION collapses the list of chunk summaries into a ~150-word paper abstract. A per-paper EXCEPTION handler catches both `ToolError` (download or tool failures) and `OTHERS` (unexpected errors), logging a warning and skipping the offending paper rather than aborting the run. After all papers are processed, a final GENERATE call to the `brief_writer` CREATE FUNCTION formats all collected abstracts into a Markdown newsletter with per-paper `###` headings and a `## Key Themes` closing section. The WORKFLOW RETURNS the brief with `status='complete'` and a paper count on success, or `status='error'` via an outer EXCEPTION WHEN OTHERS handler on fatal failure.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW arxiv_morning_brief` | `WORKFLOW <name>` | Declares the top-level orchestration with typed INPUT/OUTPUT |
| `CREATE FUNCTION chunk_summarizer` | `CREATE FUNCTION <name>({params})` | Prompt template for per-chunk summarization; uses `{chunk}` and `{max_tokens}` slots |
| `CREATE FUNCTION paper_reducer` | `CREATE FUNCTION <name>({params})` | Prompt template for collapsing chunk summaries into one abstract |
| `CREATE FUNCTION brief_writer` | `CREATE FUNCTION <name>({params})` | Prompt template for final newsletter formatting |
| `GENERATE chunk_summarizer(...) WITH OUTPUT BUDGET @chunk_tokens TOKENS INTO @chunk_summary` | `GENERATE <fn>(...) INTO @<var>` | Token-budgeted LLM call per chunk |
| `GENERATE paper_reducer(...) WITH OUTPUT BUDGET 200 TOKENS INTO @paper_summary` | `GENERATE <fn>(...) INTO @<var>` | Fixed 200-token budget for abstract reduction |
| `GENERATE brief_writer(...) WITH OUTPUT BUDGET @brief_tokens TOKENS INTO @brief` | `GENERATE <fn>(...) INTO @<var>` | Final newsletter generation |
| `CALL parse_urls / download_arxiv_pdf / semantic_chunk_plan / list_* INTO @var` | `CALL <tool>(...) INTO @<var>` | Side-effect tool calls: URL normalization, PDF download, chunking, list operations |
| `WHILE @i < @n DO ... END` | `WHILE <cond> DO ... END` | Outer loop over all papers |
| `WHILE @j < @m DO ... END` | `WHILE <cond> DO ... END` | Inner loop over chunks of a single paper (inlined sub-workflow) |
| `EXCEPTION WHEN ToolError THEN` | `EXCEPTION WHEN <Type> THEN` | Per-paper handler: skip on download/tool failure |
| `EXCEPTION WHEN OTHERS THEN` (inner) | `EXCEPTION WHEN <Type> THEN` | Per-paper handler: skip on any unexpected error |
| `EXCEPTION WHEN OTHERS THEN` (outer) | `EXCEPTION WHEN <Type> THEN` | Workflow-level fatal handler |
| `@paper_summaries, @i, @j, @summaries, @brief` | Shared state `@<var>` | Mutable list and counter variables threaded through the loop body |
| `RETURN @brief WITH status='complete', papers=@n` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial: signals successful completion with paper count |
| `RETURN 'Brief generation failed.' WITH status='error'` | `RETURN @<var> WITH status='error'` | Non-trivial: signals fatal failure to the caller |

---

### 4. Logical Functions / Prompts

**`chunk_summarizer(chunk TEXT, max_tokens INT)`**
- **Role:** First-stage LLM call in the inner per-chunk loop. Produces a short plain-English summary of a single structural section of a paper.
- **Key conventions:** Instructs the model to focus on methods and findings. The `{max_tokens}` slot sets a soft word-count target aligned to the `WITH OUTPUT BUDGET` hard token cap. No sentinel tokens; output is free-form prose.

**`paper_reducer(summaries TEXT)`**
- **Role:** Mid-stage reduction call applied once per paper after all chunks are summarized. Collapses the list of chunk summaries into a single ~150-word abstract.
- **Key conventions:** Targets ~150 words covering core contribution, method, and key results. Hard output budget of 200 tokens enforced by SPL. Input is the concatenated list of chunk summaries as a single TEXT value.

**`brief_writer(header TEXT, summaries TEXT, word_count INT)`**
- **Role:** Final assembly call invoked once after all papers are processed. Formats the collection of per-paper abstracts into a complete Markdown newsletter.
- **Key conventions:** Mandates `###` headings per paper and a closing `## Key Themes` section listing 2–4 recurring themes. `{word_count}` sets the approximate total length target. Output budget is the configurable `@brief_tokens` parameter (default 1024 tokens). Output is valid Markdown.

---

### 5. Control Flow

1. **Initialization** — CALL `parse_urls` normalizes `@urls` into an indexable list; CALL `build_brief_date_header` produces `@header`; `@paper_summaries` and counter `@i` are initialized.
2. **Outer WHILE `@i < @n`** — iterates once per paper URL.
   - CALL `get_item(@urls, @i)` retrieves the current URL.
   - A per-paper exception guard wraps Steps A–D:
     - **Step A** — CALL `download_arxiv_pdf` fetches and caches the PDF.
     - **Step B** — CALL `semantic_chunk_plan` splits the PDF into structural chunks; CALL `list_count` sets `@m`.
     - **Step C** — Inner **WHILE `@j < @m`**: GENERATE `chunk_summarizer` for each chunk with a token budget; results are appended to `@summaries` via CALL `list_append`; `@j` increments.
     - **Step D** — GENERATE `paper_reducer` reduces `@summaries` to `@paper_summary`; CALL `list_append` adds it to `@paper_summaries`.
   - EXCEPTION WHEN `ToolError` or `OTHERS`: logs a WARN and skips; `@i` still increments (no retry).
3. **Final assembly** — GENERATE `brief_writer(@header, @paper_summaries, @brief_tokens)` produces the Markdown newsletter.
4. **Termination** — RETURN `@brief` WITH `status='complete', papers=@n` on success. The outer EXCEPTION WHEN OTHERS handler catches any fatal error and RETURNS WITH `status='error'`, terminating the workflow.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile arxiv_morning_brief.spl --lang python/pocketflow
spl3 splc compile arxiv_morning_brief.spl --lang python/langgraph
spl3 splc compile arxiv_morning_brief.spl --lang go
```