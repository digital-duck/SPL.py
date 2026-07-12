# 006 — Map Reduce  *(migrated from PocketFlow)*

**Source:** [pocketflow-map-reduce](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-map-reduce)
**Difficulty:** ☆☆☆
**Category:** basics

## What it does

Screens a directory of resumes against a set of criteria by mapping an LLM scoring function over each resume in parallel batches of three, then reducing the scored results into a ranked, filtered executive summary report. The map phase uses `CALL PARALLEL` to process three resumes concurrently per loop iteration; the reduce phase aggregates scores, ranks candidates, partitions them into qualified/rejected lists, and generates an executive-ready report.

## Real-world use cases

- **High-volume recruiting**: Process hundreds of applicant resumes against a job's evaluation criteria within minutes, producing a ranked shortlist with scoring rationale
- **Grant program management**: Score applications against funding criteria at scale, surfacing the highest-fit candidates for human review
- **Vendor selection**: Evaluate RFP responses from multiple suppliers against weighted criteria and produce a comparative ranking report
- **Academic admissions**: Screen applicant portfolios against program requirements and generate a triage report for admissions committees

## Key SPL constructs

- `CREATE TOOL_API list_resume_files(directory)` — scans a directory for resume files (.txt, .pdf, .docx, .md, .rtf)
- `CREATE TOOL_API aggregate_scores(all_evaluations)` — extracts numeric scores and computes summary statistics
- `CREATE TOOL_API rank_candidates(all_evaluations)` — sorts candidates by score descending
- `CREATE TOOL_API filter_candidates(ranked, threshold, filter_type)` — partitions into qualified/rejected
- `CALL PARALLEL evaluate_single_resume(@path1, @criteria) INTO @eval1, ... END` — 3 concurrent LLM evaluations per loop
- `WHILE @i < @max_iterations DO` — outer loop over resume batches
- `GENERATE generate_summary_report(...)` — executive-level synthesis of all results

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@resume_dir` | TEXT | `"./resumes"` | Directory containing resume files |
| `@criteria` | TEXT | `"relevant work experience, technical skills, educational background, communication clarity"` | Comma-separated evaluation criteria |
| `@threshold` | TEXT | `"7"` | Minimum score (0–10) to classify as qualified |
| `@max_iterations` | INTEGER | 20 | Maximum batch iterations (covers up to 60 resumes) |

**Output:** `@report TEXT` — executive summary with ranked candidates, score statistics, and recommended next steps

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/006_map_reduce/map_reduce.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Deploy to Momagrid with `--adapter momagrid` to distribute each `evaluate_single_resume` call across different worker nodes for true parallel execution
- Increase batch size from 3 to larger values by extending the `CALL PARALLEL` block
- Add `EXCEPTION WHEN` handling to skip corrupt or unreadable resume files without aborting the pipeline
- Pipe the output JSONL into a downstream `033_text2sql` workflow to query results via natural language

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-map_reduce-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-map_reduce-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-map_reduce-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-map_reduce-claude-sonnet-4-6.spl       # raw mmd2spl output (= map_reduce.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.
