## Summary

The arXiv Morning Brief workflow automates the daily task of reading new research papers: it downloads a list of arXiv PDFs, summarizes each paper section by section, reduces those summaries into a concise abstract, then assembles everything into a single formatted Markdown newsletter. Researchers and technical teams benefit by getting a digest of multiple papers in minutes rather than hours, without manually reading each PDF.

---

## Detailed Specification

### 1. Purpose

Automatically transform a list of arXiv paper URLs into a formatted Markdown morning brief by downloading each PDF, chunking and summarizing it via cascaded LLM calls, and assembling all abstracts into a single newsletter.

---

### 2. High-level Description

This workflow implements a **map-reduce summarization pipeline** using three `CREATE FUNCTION` prompt templates and two nested `WHILE` loops. The outer WHILE iterates over each paper URL; for each paper it calls tool functions to download the PDF and split it into structural chunks, then an inner WHILE drives a `GENERATE chunk_summarizer(...)` call per chunk, accumulating results into an `@summaries` list variable. Once all chunks are processed, a second `GENERATE paper_reducer(@summaries)` condenses the chunk summaries into a single 150-word abstract for that paper. After all papers are processed, a final `GENERATE brief_writer(@header, @paper_summaries, @brief_tokens)` formats the collected abstracts into a Markdown newsletter with section headings and a Key Themes section. `EXCEPTION WHEN ToolError` and `WHEN OTHERS` handlers at the paper level silently skip any paper that fails to download or parse, so one bad URL never aborts the entire run; a top-level `EXCEPTION WHEN OTHERS` catches catastrophic failures and returns a well-formed error status. Every `GENERATE` call carries a `WITH OUTPUT BUDGET ... TOKENS` clause to enforce length budgets, and `RETURN @brief WITH status='complete', papers=@n` delivers both the artifact and run metadata to the caller.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `arxiv_morning_brief` | Top-level named workflow; declares `INPUT:` / `OUTPUT:` contracts |
| `CREATE FUNCTION` | `chunk_summarizer`, `paper_reducer`, `brief_writer` | Reusable prompt templates with `{param}` slots; no LLM call happens at declaration |
| `GENERATE ... INTO @var` | Per-chunk summarization, per-paper reduction, final brief assembly | Three distinct LLM call sites; each uses `WITH OUTPUT BUDGET ... TOKENS` |
| `WHILE <cond> DO ... END` | Outer loop `@i < @n` (papers); inner loop `@j < @m` (chunks) | Nested; loop counters are `@i`/`@j`, incremented manually with `:=` |
| `CALL <tool>(...) INTO @var` | `parse_urls`, `build_brief_date_header`, `download_arxiv_pdf`, `semantic_chunk_plan`, `list_count`, `get_item`, `list_append` | Side-effect and utility tools; `list_append` returns the updated list into the same variable |
| `@var := expr` | `@paper_summaries := []`, `@i := 0`, `@j := @j + 1` | SPL mutable variable assignment; `[]` initializes an empty accumulator |
| `EXCEPTION WHEN ... THEN` | `ToolError` + `OTHERS` at paper scope; `OTHERS` at workflow scope | Paper-level handler skips the failing paper; workflow-level handler returns `status='error'` |
| `RETURN @var WITH k=v` | `RETURN @brief WITH status='complete', papers=@n` and `RETURN '...' WITH status='error'` | Non-trivial status tokens drive caller-side branching; `papers` provides run metadata |
| `LOGGING ... LEVEL` | INFO / DEBUG / WARN log lines throughout | Observability only; does not affect execution path |
| `WITH OUTPUT BUDGET @var TOKENS` | `@chunk_tokens`, `200`, `@brief_tokens` | Controls maximum token output for each `GENERATE`; prevents runaway responses |

> `EVALUATE` is not present — this workflow has no semantic branching; all control flow is counter-driven WHILE loops and exception handlers.

---

### 4. Logical Functions / Prompts

**`chunk_summarizer(chunk TEXT, max_tokens INT)`**
- **Role:** First-stage map — summarizes a single structural section of a PDF in isolation.
- **Prompt conventions:** Instructs the model to focus on *methods and findings* in plain English; `{max_tokens}` is injected as a soft word-count target (not a hard cut-off). No sentinel tokens; output is free-form prose.

**`paper_reducer(summaries TEXT)`**
- **Role:** First-stage reduce — merges all chunk summaries for one paper into a single ~150-word abstract.
- **Prompt conventions:** Instructs the model to act as a *research editor*; the `{summaries}` slot receives the full list of chunk summaries (likely newline-delimited). Hard output budget enforced externally via `WITH OUTPUT BUDGET 200 TOKENS`.

**`brief_writer(header TEXT, summaries TEXT, word_count INT)`**
- **Role:** Final-stage reduce — formats all per-paper abstracts into a publishable Markdown newsletter.
- **Prompt conventions:** Instructs the model as a *technical newsletter editor*; expects `### heading` per paper and a mandatory `## Key Themes` closing section listing 2–4 cross-paper themes. `{word_count}` provides a total length target; output budget enforced via `WITH OUTPUT BUDGET @brief_tokens TOKENS`.

---

### 5. Control Flow

```
START
  ├─ CALL parse_urls(@urls)                  → normalize input (JSON / CSV / file path)
  ├─ CALL build_brief_date_header(@date)     → format newsletter header
  ├─ @paper_summaries := [],  @i := 0
  ├─ CALL list_count(@urls) → @n
  │
  └─ WHILE @i < @n DO                        [outer loop: one iteration per paper]
       ├─ CALL get_item(@urls, @i) → @url
       │
       ├─ TRY
       │    ├─ CALL download_arxiv_pdf(@url)   → @pdf_path
       │    ├─ CALL semantic_chunk_plan(...)    → @chunks,  @m = list_count(@chunks)
       │    ├─ @summaries := [],  @j := 0
       │    │
       │    ├─ WHILE @j < @m DO               [inner loop: one LLM call per chunk]
       │    │    ├─ CALL get_item(@chunks, @j) → @chunk
       │    │    ├─ GENERATE chunk_summarizer(@chunk, @chunk_tokens) → @chunk_summary
       │    │    ├─ CALL list_append(@summaries, @chunk_summary)
       │    │    └─ @j := @j + 1
       │    │  END
       │    │
       │    ├─ GENERATE paper_reducer(@summaries) → @paper_summary
       │    └─ CALL list_append(@paper_summaries, @paper_summary)
       │
       ├─ EXCEPTION WHEN ToolError → LOGGING WARN, skip paper
       ├─ EXCEPTION WHEN OTHERS   → LOGGING WARN, skip paper
       │
       └─ @i := @i + 1
     END

  ├─ GENERATE brief_writer(@header, @paper_summaries, @brief_tokens) → @brief
  └─ RETURN @brief WITH status='complete', papers=@n

TOP-LEVEL EXCEPTION WHEN OTHERS:
  └─ RETURN 'Brief generation failed.' WITH status='error'
```

Termination is deterministic: both loops are counter-bounded (`@i < @n`, `@j < @m`). There is no quality gate or retry loop; the workflow processes every available paper exactly once.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (use Section 1 as the text2spl input)
spl3 text2spl --description \
  "Automatically transform a list of arXiv paper URLs into a formatted Markdown \
morning brief by downloading each PDF, chunking and summarizing it via cascaded \
LLM calls, and assembling all abstracts into a single newsletter. Use three \
CREATE FUNCTION templates (chunk_summarizer, paper_reducer, brief_writer), two \
nested WHILE loops for per-paper and per-chunk iteration, EXCEPTION WHEN ToolError \
and WHEN OTHERS to skip failing papers, WITH OUTPUT BUDGET TOKENS on every \
GENERATE, and RETURN WITH status='complete', papers=@n." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile arxiv_morning_brief.spl --lang python/pocketflow
spl3 splc compile arxiv_morning_brief.spl --lang python/langgraph
spl3 splc compile arxiv_morning_brief.spl --lang go
```