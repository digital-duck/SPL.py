# 003 — Workflow  *(migrated from PocketFlow)*

**Source:** [pocketflow-workflow](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-workflow)
**Difficulty:** ☆☆☆
**Category:** basics

## What it does

Produces a polished, publication-ready article on any topic through a three-phase sequential pipeline: outline generation (YAML), section-by-section drafting (iterated with a WHILE loop), and final style rewriting. The YAML outline is parsed into a section list via a deterministic tool, and an early-exit pattern in the loop terminates when sections are exhausted. This is the canonical multi-step sequential workflow pattern in SPL — every step feeds the next.

## Real-world use cases

- **Content marketing teams**: Automate first-draft production for blog posts, product pages, and thought-leadership articles on any topic
- **Publishing platforms**: Generate structured long-form content at scale with consistent section coverage and narrative flow
- **Technical documentation**: Produce structured technical articles from a topic prompt, which writers then refine rather than write from scratch
- **Educational content creation**: Build course modules and lesson outlines programmatically across a curriculum topic list

## Key SPL constructs

- `CREATE TOOL_API parse_outline_sections(yaml_outline)` — parses YAML outline into a JSON section list; handles code-fenced and bare YAML
- `CREATE TOOL_API get_section_by_index(sections_json, idx)` — index-based section retrieval for the iteration loop
- `GENERATE generate_outline(@topic)` — LLM produces a 4–6 section YAML outline
- `GENERATE draft_section(@topic, @section_title, @yaml_outline)` — LLM writes each section with full outline context
- `GENERATE polish_article(@topic, @all_drafts)` — single rewrite pass for voice, transitions, and flow
- `WHILE @i < @max_sections DO` — iterates over sections; exits early when `get_section_by_index` returns blank
- `EVALUATE @is_blank WHEN contains("true")` — force-exits the section loop

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@topic` | TEXT | _(required)_ | Subject of the article to generate |
| `@max_sections` | INTEGER | 8 | Upper bound on number of sections to draft |

**Output:** `@article TEXT` — complete polished article text

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/003_workflow/article_writer.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Replace the sequential section loop with `CALL PARALLEL` to draft all sections simultaneously, then merge — saves significant wall-clock time on long articles
- Add a judge step after each section draft to retry sections that score below a quality threshold
- Use `IMPORT 'style_guide.spl'` to inject domain-specific style constraints into the polish prompt
- Parameterize `@section_count` and call this workflow from a batch runner to generate an entire content calendar

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-workflow-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-workflow-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-workflow-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-workflow-claude-sonnet-4-6.spl       # raw mmd2spl output (= article_writer.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.
