# 052 — Batch (Markdown Translator)  *(migrated from PocketFlow)*

**Source:** [pocketflow-batch](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-batch)
**Difficulty:** —
**Category:** basics

## What it does

Translates a Markdown document into multiple target languages in a batch, preserving all Markdown formatting (headings, code blocks, tables, lists, links) exactly. For each target language, the LLM translates the content and a second LLM format-check step verifies that all structural elements are intact — retrying up to a cap if formatting was lost. Output files are written to a language-named path in the output directory.

## Real-world use cases

- **Internationalized documentation**: Automatically produce translated versions of README files, API docs, or developer guides in all supported locales as part of a release pipeline
- **Content localization**: Translate marketing content, blog posts, or product pages while preserving Markdown structure for CMS ingestion
- **Multilingual knowledge bases**: Batch-translate an internal wiki or support knowledge base into team languages without manual formatting cleanup
- **Educational materials**: Distribute course content across language communities by translating lesson Markdown files with format-integrity checking

## Key SPL constructs

- `CREATE TOOL_API parse_target_languages(markdown_content)` — reads `target_languages` from the Markdown front matter YAML
- `CREATE TOOL_API build_output_path(output_dir, language)` — constructs a safe language-named output file path
- `CREATE FUNCTION translate_markdown(content, target_language)` — LLM translates prose while preserving all Markdown syntax elements
- `CREATE FUNCTION check_format_preserved(original, translation)` — LLM format verifier that returns "yes" or "no"
- `WHILE @i < @max_languages DO` — outer loop over target languages
- Inner `WHILE @iteration < @max_iterations DO` — retry loop on format check failure
- `CALL write_file(@output_path, @translation, "w")` — writes each translated file to disk

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@content` | TEXT | _(required)_ | Markdown content to translate (with front matter declaring `target_languages`) |
| `@output_dir` | TEXT | _(required)_ | Directory to write translated output files |
| `@max_iterations` | INTEGER | 3 | Maximum format-repair retries per language |

**Output:** `@result TEXT` — summary of translation outcomes per language

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/052_batch/batch_translator.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Use `CALL PARALLEL` to translate all target languages simultaneously instead of sequentially
- Add a `GENERATE review_translation(@original, @translation, @language)` step for a human-in-the-loop quality check before writing
- Replace front-matter language detection with a `--param target_languages=French,Spanish,Japanese` CLI override
- Chain with `031_invoice` to batch-translate extracted invoice summaries for multinational finance reporting

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-batch-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-batch-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-batch-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-batch-claude-sonnet-4-6.spl       # raw mmd2spl output (= batch_translator.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.
