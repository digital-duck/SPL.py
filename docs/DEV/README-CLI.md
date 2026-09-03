# SPL3 CLI — Command Taxonomy and Design Notes

## Overview

`spl3` is the main entry point for the SPL 3.0 runtime. It is built with
[Click](https://click.palletsprojects.com/) and registered via the `spl3`
console script in `pyproject.toml`. The implementation lives in
`spl3/cli.py`.

The CLI exposes roughly 30 commands. To keep `spl3 --help` scannable, helper
and conversion tools are grouped under `spl3 util`, and Hub management items
are grouped under `spl3 hub`.

---

## Command taxonomy

### Top-level (core operations)

| Command | Purpose |
|---|---|
| `run` | Execute a `.spl` workflow |
| `validate` | Check `.spl` syntax and semantics |
| `test` | Pipeline-level test runner |
| `vibe` | NL description → working code + README |
| `text2spl` | NL description → `.spl` source |
| `splc` | Compile `.spl` to LangGraph / Go / TypeScript |
| `migrate` | Migrate a codebase via DODA pipeline |
| `configure` | Read/write persistent SPL configuration |
| `code-rag` | Manage the Code-RAG index |
| `experiment` | Batch ablation study runner |
| `tool-api` | Manage CREATE TOOL_API library registry |
| `compare` | Multi-tier file diff with verdict synthesis |
| `compare-bom` | BOM/manifest batch compare |
| `judge` | LLM-based rubric evaluation |
| `show` | List adapters, models, stdlib tools |
| `cache` | Layer 2 content cache management |
| `help` | Show help |

### `spl3 util` — format conversion and one-off helpers

| Sub-command | Purpose |
|---|---|
| `img2mmd` | Extract Mermaid flowchart from an image (multimodal LLM) |
| `img2text` | Extract text / pseudo-code from an image (OCR via LLM) |
| `spl2mmd` | Generate Mermaid diagram for a `.spl` file |
| `text2mmd` | Generate Mermaid diagram from natural language |
| `mmd2spl` | Convert Mermaid diagram to `.spl` workflow |
| `explain` | Show execution plan for a `.spl` file (dry-run, no LLM) |
| `describe` | Generate plain-English spec for a `.spl` file/folder |
| `install-skill` | Install the `/spl3` Claude Code skill |
| `md2pdf` | Convert Markdown to PDF via pandoc + XeLaTeX |

### `spl3 hub` — Hub registry, peering, workflow management

| Sub-command | Purpose |
|---|---|
| `hub workflow list` | List durable workflow runs |
| `hub workflow status` | Show step-by-step status of a run |
| `hub workflow resume` | Resume a crashed/interrupted run from checkpoint |
| `hub workflow send-event` | Send HITL event to a waiting workflow |
| `hub registry list` | List workflows registered on the Hub |
| `hub register` | Register `.spl` workflows to a Hub |
| `hub peers list` | List peer Hubs |
| `hub peers add` | Add a peer Hub (peering handshake) |

---

## Rationale for the grouping

Before this refactor, `spl3 --help` listed ~28 commands at the same level,
making it hard to find the relevant command at a glance. The grouping follows
two principles:

1. **Core operations stay top-level** — commands a user runs daily (`run`,
   `validate`, `vibe`, `splc`, `text2spl`) should require the fewest keystrokes.

2. **Helper and infra commands move into groups** — format converters
   (`img2mmd`, `mmd2spl`, …), document tools (`explain`, `describe`,
   `md2pdf`), and Hub management (`workflow`, `registry`, `peers`) are
   secondary workflows that benefit from a namespace.

---

## Implementation pattern

The `cmd_util` and `cmd_hub` groups are defined in `spl3/cli.py` and
registered on `main` with `@main.group(...)`.

```python
@main.group("util", short_help="...")
def cmd_util():
    """..."""

@cmd_util.command("img2mmd", ...)
def cmd_img2mmd(...):
    ...
```

For `hub`, the four sub-items (`workflow`, `registry`, `register`, `peers`)
are defined as standalone Click groups/commands (using `@click.group()` /
`@click.command()` rather than `@main.group()`) and then attached with
`cmd_hub.add_command(...)` after their definitions. This keeps the internal
sub-command registrations (e.g. `@workflow.command("list")`) unchanged.

```python
@click.group()
def workflow():
    """Manage durable workflow runs."""

@workflow.command("list")
def workflow_list():
    ...

cmd_hub.add_command(workflow)
```

---

## `spl3 util md2pdf`

Wraps `pandoc --pdf-engine=xelatex` with sane defaults for technical documents:

- Body font: DejaVu Serif; mono font: DejaVu Sans Mono
- `--resource-path=.` + `cwd` set to the file's directory so relative image
  paths (e.g. `review-feedback/*.png`) resolve correctly
- Unicode-safe: box-drawing and subscript characters handled by DejaVu;
  emoji must be replaced with plain text before conversion

Equivalent shell script: `docs/research/solver/md2pdf.sh` in the dd-research
repo.

---

## Migration from pre-group CLI

Commands moved under `spl3 util`:

| Old | New |
|---|---|
| `spl3 img2mmd` | `spl3 util img2mmd` |
| `spl3 img2text` | `spl3 util img2text` |
| `spl3 spl2mmd` | `spl3 util spl2mmd` |
| `spl3 text2mmd` | `spl3 util text2mmd` |
| `spl3 mmd2spl` | `spl3 util mmd2spl` |
| `spl3 explain` | `spl3 util explain` |
| `spl3 describe` | `spl3 util describe` |
| `spl3 install-skill` | `spl3 util install-skill` |

Commands moved under `spl3 hub`:

| Old | New |
|---|---|
| `spl3 workflow list` | `spl3 hub workflow list` |
| `spl3 registry list` | `spl3 hub registry list` |
| `spl3 register` | `spl3 hub register` |
| `spl3 peers list` | `spl3 hub peers list` |
| `spl3 peers add` | `spl3 hub peers add` |
