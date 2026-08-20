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
blob), and `make_run_dir` / `save_pdf_copy` / `save_chunks` (the `out_dir`
debug-logging hierarchy — see "Debugging" below).

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
    "abstract": "... the paper's own abstract, verbatim from arXiv metadata — not LLM-summarized, and excluded from chunking (see tools.spl's semantic_chunk_plan) so it's never re-generated ...",
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

Params go through spl3's `-p`/`--param KEY=VALUE` flag — spl3 (unlike the
older `spl` CLI some sibling recipes were written against) does not accept
bare positional `key=value` args.

```bash
# Local run against Ollama
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --adapter ollama --model gemma3 \
    -p urls='["https://arxiv.org/abs/2501.12948","https://arxiv.org/abs/1706.03762"]'

# From a file
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --llm claude_cli:claude-sonnet-5 \
    -p urls="cookbook/89_arxiv_digest_eaai27/arxiv-papers.txt" \
    -p out_dir="cookbook/89_arxiv_digest_eaai27/output/"

# Workshop grid dispatch — the capstone demo path. The hub never runs SPL;
# a driver process (a person running spl3 by hand, or arxiv-digest-eaai27's
# thin FastAPI backend on the web form's behalf) does the orchestration and
# submits each individual GENERATE call to the hub as a single-prompt task.
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --adapter momagrid --hub https://hub.WORKSHOP_DOMAIN \
    -p urls='["https://arxiv.org/abs/2501.12948"]'
```

### Debugging: dumping intermediate output with `out_dir`

Both `arxiv_digest` and `summarize_arxiv_paper` take an optional `@out_dir TEXT
DEFAULT ''` input. When set, every stage's output is written to disk under a
per-run, per-paper directory hierarchy instead of only ever showing up buried
in the final `digest` string:

```
RUN_DIR   = <out_dir>/run-<timestamp>/     one per arxiv_digest batch
                                            (or per standalone unit-test run)
ARXIV_DIR = RUN_DIR/<arxiv-id>/            one per paper
```

| Path (relative to ARXIV_DIR unless noted) | Written by | Contents |
|---|---|---|
| `pdf/<name>.pdf` | `summarize_arxiv_paper` | the exact PDF `semantic_chunk_plan` read — copied out of the shared download cache so it's inspectable per-run |
| `chunk/NN_<slug>.md` | `summarize_arxiv_paper` | one file per section chunk — **the critical one for verifying the semantic chunking logic**: shows exactly how the PDF text got split, before any summarization touches it |
| `section_summary_raw.md` | `summarize_arxiv_paper` | the MAP step's per-section summaries — named "_raw" so `digest-<arxiv-id>.json` (the actual REDUCE-step output) is what draws the eye |
| `digest-<arxiv-id>.json` | `summarize_arxiv_paper` | the REDUCE step's digest and the final assembled card in one file — the card's `digest` field already carries the REDUCE output, so there's no separate `.md` copy |
| `RUN_DIR/results.json` | `arxiv_digest` | the final aggregated JSON array for the whole batch |

`RUN_DIR` is resolved **once** per batch in `arxiv_digest.spl` (via the
`make_run_dir` tool) and threaded down to every `summarize_arxiv_paper` call
via `@run_dir`, so all papers in one run land under the same timestamped
folder rather than each getting their own. Run `summarize_arxiv_paper.spl`
standalone (see below) and it makes its own `RUN_DIR` from `@out_dir`
directly.

```bash
spl3 run cookbook/89_arxiv_digest_eaai27/arxiv_digest.spl \
    --adapter echo \
    -p urls="cookbook/89_arxiv_digest_eaai27/arxiv-papers.txt" \
    -p out_dir="/tmp/arxiv_digest_debug"
```

```
/tmp/arxiv_digest_debug/
  run-20260819-061809/
    results.json
    2501.12948/
      pdf/2501.12948v2.pdf
      chunk/00_1_introduction.md
      chunk/01_5_deepseek.md
      ...
      section_summary_raw.md
      digest-2501.12948.json
```

Nothing is written when `out_dir` is left at its default (`''`) — this is
opt-in and has no effect on normal runs.

### Unit-testing `summarize_arxiv_paper` directly

`summarize_arxiv_paper.spl` is a standalone `WORKFLOW` — run it directly
against one paper URL to isolate the map-reduce pipeline (download → chunk →
summarize → reduce) from the outer loop and `parse_urls` normalization in
`arxiv_digest.spl`:

```bash
spl3 run cookbook/89_arxiv_digest_eaai27/summarize_arxiv_paper.spl \
    --adapter ollama --model gemma3 \
    -p url="https://arxiv.org/abs/1706.03762" \
    -p out_dir="$HOME/projects/digital-duck/SPL.py/cookbook/89_arxiv_digest_eaai27/output/"
```

Useful when a paper misbehaves inside the full batch and you want to isolate
whether the problem is in `parse_urls`/the per-item loop in `arxiv_digest.spl`,
or in the summarization pipeline itself.

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

## Fixed issues

- **Trailing sections silently dropped (2026-08-19).** `semantic_chunk_plan`'s
  `PDFExtractor(..., max_chars=40_000)` (inherited from recipe 47) truncated the
  extracted text before chunking ever ran. For a 54,945-char paper, the Conclusion
  section (starting at offset 48,484) was cut off entirely — not mis-chunked, just
  never seen by the header regex, so the digest silently ended at "Discussion" with
  no indication anything was missing. Raised to `max_chars=200_000`; verified fixed
  against the same paper (arXiv 2510.01230) — chunk count went from 6 to 9,
  correctly including Limitations, Conclusion, and References.

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
