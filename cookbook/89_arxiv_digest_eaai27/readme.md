# Recipe 89: arXiv Digest (EAAI-27 workshop capstone)

Given a list of arXiv paper URLs, produces one structured digest per paper: each
section summarized independently (map), then reduced into a paragraph-per-section
plus a 3-bullet "Key Contributions" block (reduce). Built for the EAAI-27 Model AI
Assignment workshop's live capstone demo — see
`docs/conference/EAAI-2027/submission/Gong-DistributedInferenceGrid/handout.md`,
"Capstone Demo: arXiv Paper Summarization."

## Pattern

```
parse_urls(urls) → N papers
  └─► per paper: lookup_arxiv → download_arxiv_pdf → semantic_chunk_plan → M sections
        └─► MAP: section_summarizer(section_i) for i in 0..M
              └─► REDUCE: paper_digest_writer(all section summaries) → one digest
        └─► assemble_paper_digest → one JSON object
  └─► append_json_array → final JSON array, one object per paper
```

## Why this recipe, not a new build from scratch

Assembled from two existing cookbook recipes rather than written fresh — see
attribution comments in `tools.spl`:

- **`cookbook/47_arxiv_morning_brief`** — the download/chunk/map/reduce shape
  (`download_arxiv_pdf`, `semantic_chunk_plan`, `parse_urls`, `list_count` reused
  near-verbatim).
- **`cookbook/72_verify_arxiv_references`** — ground-truth paper metadata via the
  arXiv Atom API (`extract_arxiv_id`, `lookup_arxiv`, `json_field` reused
  near-verbatim), and the per-item `DO ... EXCEPTION ... END` error-isolation
  pattern inside the loop (one bad paper doesn't kill the whole batch).
- **`cookbook/13_map_reduce`** — the general map-reduce shape this recipe is an
  arXiv-specific instance of.

New in this recipe: `get_chunk_field` (pulls one field out of a chunked section
without relying on native LIST↔TOOL_API serialization), `append_json_array` /
`assemble_paper_digest` (deterministic JSON assembly so the output is a clean
array of objects a frontend can render directly, rather than a single Markdown
blob).

## Files

| File | Purpose |
|---|---|
| `arxiv_digest.spl` | Top-level orchestrator — loops over the submitted paper list |
| `summarize_arxiv_paper.spl` | Sub-workflow — one paper's full map-reduce, called once per paper |
| `functions.spl` | LLM function defs (`section_summarizer`, `paper_digest_writer`) |
| `tools.spl` | TOOL_API defs (download, chunk, metadata lookup, JSON assembly) |
| `arxiv-papers.txt` | Sample paper list for local testing |

## Output shape

`arxiv_digest.spl` returns a JSON array, one object per paper:

```json
[
  {
    "arxiv_id": "2501.12948",
    "title": "...",
    "authors": "...",
    "url": "https://arxiv.org/abs/2501.12948",
    "section_count": 7,
    "digest": "**Introduction:** ...\n\n**Key Contributions:**\n- ...\n- ...\n- ..."
  },
  ...
]
```

A paper that fails to download/lookup still produces an object (`title:
"Unavailable"`, `digest` explaining the failure) rather than breaking the batch —
matches the per-item error isolation in recipe 72.

## Usage

`tools.spl`'s `CREATE TOOL_API` defs load automatically via `IMPORT 'tools'` inside
the `.spl` files themselves — no `--tools` flag needed. (That flag is for a
different mechanism: external `@spl_tool`-decorated Python modules, as in
`cookbook/13_map_reduce/tools.py`.)

```bash
# Local run against Ollama
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --adapter ollama --model gemma3 \
    urls='["https://arxiv.org/abs/2501.12948","https://arxiv.org/abs/1706.03762"]'

# From a file
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    urls="cookbook/89_arxiv_digest_eaai27/arxiv-papers.txt"

# Workshop grid dispatch — the actual capstone demo path. The hub IS the SPL
# execution engine, so a thin frontend submits `urls` to the hub's task API
# directly; no separate backend service shells out to `spl3 run` on its behalf.
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --adapter momagrid --hub https://hub.WORKSHOP_DOMAIN \
    urls='["https://arxiv.org/abs/2501.12948"]'
```

## Validated

```
spl3 validate cookbook/89_arxiv_digest_eaai27/*.spl
```

All four files parse clean (0 errors). The `CALL target not found` / `WHILE loop
... no RETURN` warnings are cross-file IMPORT-resolution artifacts of validating
files individually — the known-good recipe 47 produces the identical class of
warnings under the same check (confirmed 2026-08-18), so these are not real
issues in this recipe.

## Parallelism note

Today's SPL (3.0) dispatches sub-workflow `CALL`s sequentially within one script
run — `CALL PARALLEL` fan-out is flagged for a future SPL version (see
`cookbook/47_arxiv_morning_brief/readme.md`). The "several papers' worth of jobs
in flight simultaneously" the EAAI-27 capstone describes comes from **concurrent
attendee submissions**, each becoming its own script run against the shared hub —
not from a single run's internal per-paper loop running in parallel. Worth being
precise about this when describing the demo live.

## Not yet done

- Not run end-to-end against a real Ollama/Momagrid backend in this session —
  only `spl3 validate` (syntax/semantics, `spl123` conda env) was checked, not
  actual execution. Run the local-Ollama usage example above before relying on
  it for the live demo.
- `dd_extract.pdf.PDFExtractor` (used by `semantic_chunk_plan`) is an external
  dependency assumed present per recipe 47/72's conventions — not verified
  installed in this session.
- No automated tests (recipe 47 has `tests/test_tools.py` +
  `tests/test_workflow.py` as a model to follow if this recipe needs the same
  level of pre-demo confidence).
