# SPL 3.0 User Guide

**SPL (Structured Prompt Language)** is a SQL-inspired declarative language for
orchestrating LLM workflows. You write a `.spl` file — the invariant *logical view* —
and the toolchain runs it, compiles it, describes it, or generates it from plain English.

> **End-to-end validated.** The ten-step pipeline documented in §15 (S1–S10) was
> designed for the NeurIPS 2026 paper *"Beyond Vibe Coding: Intent Invariance and
> Structured Prompt Language"* and executed across 5 real-world workflow recipes × 3
> model tiers (15 experiments). Every command in this guide was exercised in those
> experiments — making §15 both the research protocol and the most comprehensive
> integration test suite for SPL.py.

---

## Table of Contents

1. [Quick-start](#1-quick-start)
2. [LLM Adapters](#2-llm-adapters)
3. [spl3 validate](#3-spl3-validate)
4. [spl3 run](#4-spl3-run)
5. [spl3 describe](#5-spl3-describe)
6. [spl3 text2spl](#6-spl3-text2spl)
7. [spl3 text2mmd](#7-spl3-text2mmd)
8. [spl3 spl2mmd](#8-spl3-spl2mmd)
9. [spl3 mmd2spl](#9-spl3-mmd2spl)
10. [spl3 compare](#10-spl3-compare)
11. [spl3 splc compile](#11-spl3-splc-compile)
12. [spl3 splc describe](#12-spl3-splc-describe)
13. [spl3 vibe](#13-spl3-vibe)
14. [spl3 code-rag](#14-spl3-code-rag)
15. [Full Pipeline S1–S10: IR + Ablation](#15-full-pipeline-s1s10-ir--ablation)
16. [Debugging LLM Prompts](#16-debugging-llm-prompts)
17. [Command reference](#17-command-reference)

---

## 1. Quick-start

```bash
# Validate a .spl file
spl3 validate cookbook/05_self_refine/self_refine.spl

# Run it with different adapters
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama --model gemma3

# Visualise a .spl file as a Mermaid diagram (no LLM needed)
spl3 spl2mmd cookbook/05_self_refine/self_refine.spl --out-dir diagrams/

# Compare two Mermaid diagrams — auto-selects GED, emits DIVERGED/DEGRADED/etc.
spl3 compare orig.mmd roundtrip.mmd --adapter claude_cli --format html -o report.html

# Compile to Python/PocketFlow (deterministic — no LLM needed)
spl3 splc compile cookbook/05_self_refine/self_refine.spl --lang python/pocketflow

# Vibe-code directly from a description (bypass IR steps)
spl3 vibe "self-refine agent that iterates until quality > 0.8" \
  --adapter claude_cli -m claude-sonnet-4-6 -o out.py
```

---

## 2. LLM Adapters

SPL 3.0 supports multiple LLM adapters for different deployment scenarios and cost models:

### Available Adapters

| Adapter | Cost Model | Authentication | Models |
|---------|------------|----------------|--------|
| `claude_cli` | Subscription (flat rate) | Claude Code OAuth | `claude-sonnet-4-6` (default), any Claude model |
| `gemini_cli` | Free tier + subscription | Gemini CLI OAuth | `gemini-2.5-flash` (default), `gemini-3-flash-preview` |
| `ollama` | Local inference | None required | `gemma3` (default), `nomic-embed-text` (embedding) |
| `openrouter` | API usage | API Key | `google/gemini-3-flash-preview`, `qwen/qwen3.6-plus`, and many others |

---

## 3. spl3 validate

Checks lexer → parser → semantic analyser. No LLM call.

```bash
spl3 validate <file.spl>
```

---

## 4. spl3 run

Executes a `.spl` workflow against a live LLM adapter.

```bash
spl3 run <file.spl> [OPTIONS]
```

---

## 5. spl3 describe

Generates a plain-English functional specification from `.spl` source.

```bash
spl3 describe cookbook/05_self_refine/self_refine.spl --adapter claude_cli
```

---

## 6. spl3 text2spl

Compiles a natural language description into valid SPL 3.0 source code.

```bash
spl3 text2spl "build a review agent that refines text until quality > 0.8" \
  --mode workflow -o review.spl
```

---

## 7. spl3 text2mmd

Converts natural language workflow descriptions into Mermaid flowchart diagrams
using an LLM. The generated `.mmd` file can be reviewed and edited before
converting to SPL with `mmd2spl`.

```bash
spl3 text2mmd "user onboarding workflow with approval gates"
```

---

## 8. spl3 spl2mmd

Generates a Mermaid flowchart **directly from a `.spl` file's AST** — no LLM
required. Every workflow, procedure, loop, branch, and exception handler is
rendered deterministically from the parsed syntax tree, producing a diagram
that faithfully mirrors the actual script structure.

Use it to **visually review or validate** a `.spl` file at any point in the
pipeline: after `mmd2spl` (S3) to verify the generated SPL matches the original
diagram, when auditing a hand-written workflow, or to produce publication figures.

```bash
spl3 spl2mmd workflow.spl                             # defaults: .mmd + .html + .md + preview
spl3 spl2mmd *.spl --out-dir diagrams/                # batch convert, all outputs in one folder
spl3 spl2mmd workflow.spl --no-preview                # suppress browser auto-open
spl3 spl2mmd workflow.spl --save-pdf --out-dir diagrams/  # add PDF for publication
spl3 spl2mmd step1.spl step2.spl --save-pdf --save-png --out-dir diagrams/
```

### Node shapes by statement type

| Shape | Mermaid syntax | SPL statement |
|-------|----------------|---------------|
| Parallelogram | `[/…/]` | `GENERATE … INTO` (LLM call) |
| Subroutine | `[[…]]` | `CALL procedure()` |
| Diamond | `{…}` | `WHILE`, `EVALUATE`, exception handler |
| Cylinder | `[(…)]` | `STORE`, storage-assign |
| Stadium | `([…])` | Start, End, `RETURN`, `RAISE` |
| Flag | `>…]` | `LOGGING` |
| Rectangle | `[…]` | Assignment, `SELECT INTO`, generic |

Each workflow/procedure is wrapped in its own labelled subgraph. Nodes are
colour-coded by type: **blue** = LLM call, **amber** = procedure call,
**purple** = control flow, **green** = storage, **pink** = terminal, **grey** = log.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--out-dir DIR` | beside each input | All outputs written here; source `.spl` copied too |
| `--preview / --no-preview` | **on** | Open `.html` in the browser immediately |
| `--save-html / --no-save-html` | **on** | Write a browser-viewable `.html` |
| `--save-markdown / --no-save-markdown` | **on** | Write a `.md` with fenced mermaid block |
| `--save-spl / --no-save-spl` | **on** | Copy source `.spl` into `--out-dir` |
| `--save-png` | off | Write `.png` via headless Chrome/Chromium |
| `--save-pdf` | off | Write `.pdf` — tries `mmdc` first, then Chrome headless |

### Output files (example with `--out-dir diagrams/`)

```
diagrams/
  self_refine.mmd      ← raw Mermaid source (edit with any Mermaid tool)
  self_refine.md       ← Markdown with fenced diagram (VS Code / GitHub preview)
  self_refine.html     ← standalone browser page with live rendering
  self_refine.spl      ← copy of the source script
  self_refine.pdf      ← (--save-pdf) print-ready, A4 landscape, neutral theme
  self_refine.png      ← (--save-png) rasterised full-page screenshot
```

### mmdc setup (recommended for `--save-pdf`)

[`mmdc`](https://github.com/mermaid-js/mermaid-cli) is the official Mermaid CLI.
When present, it produces a **native vector PDF** — the highest-quality output for
paper figures, posters, and slides. If `mmdc` is not found, `spl2mmd` falls back
to Chrome headless `--print-to-pdf` (A4 landscape, neutral theme, no headers).

```bash
# Install mmdc globally (requires Node.js ≥ 18)
npm install -g @mermaid-js/mermaid-cli

# Verify installation
mmdc --version

# What spl2mmd calls internally for PDF
mmdc -i workflow.mmd -o workflow.pdf -t neutral -b white
```

> **Note:** `mmdc` downloads Chromium on first install (~200 MB via Puppeteer).
> On headless CI/CD servers, supply a `puppeteerConfigFile` pointing to an
> existing Chrome installation to avoid the download:
> ```bash
> mmdc -i workflow.mmd -o workflow.pdf \
>   --puppeteerConfigFile /etc/mmdc-puppeteer.json
> # /etc/mmdc-puppeteer.json: { "executablePath": "/usr/bin/google-chrome" }
> ```

### Multi-file projects

When workflows `CALL` each other across files, run `spl2mmd` on all files
together. Each produces its own diagram; cross-file calls appear as `CALL`
subroutine nodes labelled with the procedure name — the callee is not inlined,
keeping each diagram focused on a single file's logic.

```bash
spl3 spl2mmd step1.spl step2.spl step3.spl --out-dir diagrams/ --save-pdf
# or with glob
spl3 spl2mmd *.spl --out-dir diagrams/ --save-pdf
```

---

## 9. spl3 mmd2spl

Converts a Mermaid flowchart diagram into executable SPL workflow code.

```bash
spl3 mmd2spl workflow.mmd --adapter claude_cli -o workflow.spl
```

---

## 10. spl3 compare

A **multi-tier diff tool** that automatically selects the most appropriate comparison
algorithm for each file type, then synthesises all tier results into a single verdict:

> **EQUIVALENT** · **REFACTORED** · **DEGRADED** · **DIVERGED**

The synthesis layer is not a summary — it reasons *across* tiers: agreements confirm
confidence; contradictions expose subtler patterns (e.g. "same vocabulary, different
control flow" = REFACTORED even when character-level diff is large).

```bash
spl3 compare <file1> <file2> [OPTIONS]
```

### Six comparison tiers

| # | Tier | Mode | Auto-default for | What it measures |
|---|------|------|-----------------|-----------------|
| 1 | Topological | `ged` | `.mmd` | SPL-node-aware Graph Edit Distance |
| 2 | Semantic | `llm` / `vision` | `.md`, `.spl` / images | Intent, meaning, logical purpose |
| 3 | Syntactic | `ast-diff` | (manual) | AST-level inventory: GENERATE/CALL/workflow names |
| 4 | Structural | `structural` | (manual) | Document skeleton: headings, class/function names |
| 5 | Character | `git-diff` | `.py`, `.js`, `.ts` | Line-level text diff |
| 6 | Embedding | `vector` / `bert-score` | (manual) | Cosine similarity in embedding space |

**All modes are additive and composable.** The default tier is auto-selected from the
file extension; override or add tiers with `--mode`.

### File-type auto-dispatch

```bash
spl3 compare a.mmd b.mmd          # → ged  (no LLM needed)
spl3 compare a.spl b.spl          # → llm
spl3 compare a.md  b.md           # → llm
spl3 compare a.py  b.py           # → git-diff
spl3 compare a.png b.png          # → vision (PIL pixel-diff + LLM vision if available)
```

### Synthesis verdict

When `--synthesize` is on (default) and `--adapter` is set, a final LLM pass
integrates all tier results into a single structured verdict:

| Verdict | Meaning |
|---------|---------|
| `EQUIVALENT` | Functionally and semantically the same (surface noise allowed) |
| `REFACTORED` | Structure/intent preserved; presentation or style changed |
| `DEGRADED` | One file is a lossy version of the other — information was lost |
| `DIVERGED` | Genuinely different intent, logic, or purpose |

When no LLM adapter is available, a **rule-based fallback** drives the verdict
from GED normalized distance alone (0 → EQUIVALENT, < 0.10 → REFACTORED,
< 0.35 → DEGRADED, else → DIVERGED).

### LLM fallback for failed tiers

If a mode-specific tier fails (e.g. `networkx` not installed for `ged`, or
`dd-embed` not installed for `vector`) and `--adapter` is set, `compare`
automatically runs a targeted LLM analysis covering the failed tier's aspects
rather than leaving it blank.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode MODE` | auto (by ext) | Tier(s) to run. Repeatable. Choices: `llm git-diff vector bert-score ged vision ast-diff structural` |
| `--adapter NAME` | `ollama` | LLM adapter for all analysis: semantic, vision, synthesis, fallback |
| `--model MODEL` | adapter default | Model override |
| `--adapter-embed NAME` | same as `--adapter` | Adapter for embedding modes (vector, bert-score) |
| `--adapter-synthesis NAME` | same as `--adapter` | Adapter for synthesis pass |
| `--format` | `markdown` | Output format: `markdown` · `json` · `text` · `html` |
| `--focus` | `all` | LLM focus: `all` · `structure` · `logic` · `quality` · `syntax` · `spl` |
| `--diff-style` | `unified` | git-diff style: `unified` · `context` · `side-by-side` |
| `--synthesize / --no-synthesize` | on | Run synthesis LLM pass to produce verdict |
| `--output / -o FILE` | stdout | Write report to file |
| `--prompt` | off | Print LLM prompt and exit (mode=llm) |

> **`--focus spl`** activates a domain-aware prompt that treats `GENERATE` function
> signatures as the semantic heart, `EXCEPTION` handlers as safety contracts, and
> `CALL` dependencies as primary evidence — rather than treating `.spl` as generic text.

### Output formats

**`--format markdown`** (default) — renders a structured report with the synthesis
verdict banner at the top, followed by collapsible tier sections. Suitable for saving
as `S6-*.md` or `S10-*.md` pipeline artifacts.

**`--format html`** — renders a **3-panel side-by-side report**:
- Top-left panel: File 1 (Mermaid diagrams rendered live via Mermaid JS; images embedded; code shown as-is)
- Top-right panel: File 2 (same)
- Bottom panel: synthesis verdict (colour-coded banner) + collapsible tier details

**`--format json`** — machine-readable, includes all tier results and metadata.
Useful for programmatic processing or aggregating results across experiments.

**`--format text`** — compact terminal output, verdict first.

### Examples

```bash
# .mmd round-trip check — GED auto-selected, HTML report with live diagrams
spl3 compare orig.mmd roundtrip.mmd \
  --adapter claude_cli --format html -o roundtrip.html

# .spl semantic comparison with SPL-domain prompt
spl3 compare v1.spl v2.spl \
  --adapter claude_cli --focus spl

# Multi-tier: topology + semantics + syntax (for deep SPL diff)
spl3 compare a.spl b.spl \
  --mode llm --mode ast-diff --mode git-diff \
  --adapter claude_cli --focus spl --format html -o diff.html

# Spec round-trip fidelity — S6 in the NDD pipeline
spl3 compare S1-spec.md S5-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o S6-spec-diff.md

# Compare two Python files with LLM-assisted logical diff (upgrade from git-diff)
spl3 compare old.py new.py --mode llm --mode git-diff --adapter claude_cli

# Image comparison (PNG Mermaid diagrams)
spl3 compare orig.png roundtrip.png --mode vision --adapter claude_cli

# No LLM — pure GED with rule-based verdict
spl3 compare a.mmd b.mmd --adapter "" --format text

# Full ablation comparison — S10 in the NDD pipeline
spl3 compare S6-ir-diff.md S9-vibe-diff.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o S10-ablation.md
```

### Round-trip consistency workflow

`spl3 compare` is the natural quality gate for the `spl2mmd → mmd2spl → spl2mmd`
round-trip. Compare the original `.mmd` against the re-generated `.mmd` to detect
what `mmd2spl` lost:

```bash
# Generate original diagram (deterministic)
spl3 spl2mmd workflow.spl --out-dir diagrams/ --no-preview

# Round-trip: Mermaid → SPL → Mermaid
spl3 mmd2spl diagrams/workflow.mmd --adapter claude_cli -o roundtrip.spl
spl3 spl2mmd roundtrip.spl --out-dir roundtrip/ --no-preview

# Semantic diff: topology (GED) + synthesis verdict
spl3 compare diagrams/workflow.mmd roundtrip/roundtrip.mmd \
  --adapter claude_cli --format html -o roundtrip-report.html
```

A `DEGRADED` verdict identifies specific lost nodes; `EQUIVALENT` confirms
lossless round-trip. The HTML report renders both diagrams side-by-side for
direct visual comparison.

---

## 11. spl3 splc compile

Deterministic or LLM-assisted compilation of a `.spl` logical view to a physical target.

```bash
# Deterministic — Python/PocketFlow (no LLM needed)
spl3 splc compile agent.spl --lang python/pocketflow

# LLM-assisted — any target
spl3 splc compile agent.spl --lang go --llm --adapter claude_cli
spl3 splc compile agent.spl --lang python/crewai --llm --adapter openrouter -m qwen/qwen3.6-plus
```

### Supported targets

| `--lang` | Transpiler | Notes |
|----------|-----------|-------|
| `python/pocketflow` | Deterministic | Default for NDD experiments |
| `python/langgraph` | Deterministic | |
| `go` | Deterministic | |
| `ts` | Deterministic | |
| `python/crewai` | LLM only | Requires `--llm` |
| `python/autogen` | LLM only | Requires `--llm` |
| `python` | LLM only | Plain Python, requires `--llm` |

---

## 12. spl3 splc describe

Reverse-engineers a specification from a **compiled target implementation**. Used in step S5 of the NDD round-trip pipeline.

```bash
spl3 splc describe targets/python_pocketflow/agent.py --adapter claude_cli
spl3 splc describe targets/python_pocketflow/ --adapter openrouter -m qwen/qwen3.6-plus
```

The generated spec feeds back into the reverse pipeline:
```
splc describe → spec.md → text2spl → .spl → splc compile → new target
```

---

## 13. spl3 vibe

One-shot prototype generator: **NL description → working code + README + test data**,
in a single LLM call. No `.mmd` or `.spl` IR steps required.

Works with any model available via `ollama` (local), `claude_cli`, or `openrouter`
(400+ cloud models). The `--out-dir` mode is recommended — it writes all three
outputs to a folder so `spl3 splc describe` can process them as a unit in step S8.

```bash
spl3 vibe "<description>" [OPTIONS]
# or
spl3 vibe --description <TEXT_OR_FILE> [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `DESCRIPTION` | (required) | Natural language requirement or path to a `.md` spec file |
| `--description / -d` | — | Same as positional arg; takes precedence if both given |
| `--target / -t` | `python/pocketflow` | Target language/framework |
| `--adapter` | `ollama` | LLM adapter |
| `--model / -m` | adapter default | Model override |
| `--out-dir DIR` | — | **Recommended.** Write code + `README.md` + `test_data.py` to `DIR` |
| `--output / -o` | stdout | Single-file mode: write code to `FILE` (also writes `<stem>-readme.md`) |
| `--rag / --no-rag` | `--rag` | Include RAG few-shot examples from the SPL recipe store |
| `--rag-k` | `3` | Number of RAG examples (1–10) |
| `--references` | — | Reference codebase(s): GitHub URL or local path (repeatable) |
| `--no-readme` | off | Skip generating readme and test data |
| `--verbose / -v` | off | Print progress and token counts |
| `--prompt` | off | Print the assembled LLM prompt and exit (no API call) |

### Examples

```bash
# Recommended: folder mode — all outputs in one place
spl3 vibe "ReAct research agent" \
  --out-dir ./out --adapter ollama -m gemma3

# From a spec file, via openrouter (multi-model comparison)
spl3 vibe --description S1-agent-spec.md \
  --out-dir ./out/qwen --adapter openrouter -m qwen/qwen3.6-plus
spl3 vibe --description S1-agent-spec.md \
  --out-dir ./out/gemini --adapter openrouter -m google/gemini-3-flash-preview

# Different target framework
spl3 vibe "RAG pipeline with re-ranking" \
  --target python/langgraph \
  --out-dir ./out --adapter claude_cli

# Preview prompt without calling the LLM
spl3 vibe "judge agent" --adapter claude_cli --prompt
```

### Output files

| Mode | File | Contents |
|------|------|----------|
| `--out-dir DIR` | `DIR/vibe_output.py` | Complete implementation |
| | `DIR/README.md` | Setup, usage, expected output |
| | `DIR/test_data.py` | 2–3 realistic test inputs |
| `--output FILE` | `FILE` | Implementation |
| | `<stem>-readme.md` | Setup and usage |
| | `<stem>-test_data.py` | Test inputs |

### Notes

- **Context window matters**: models with larger context windows (Qwen, Gemini) tend
  to follow the mandatory 3-section output structure more reliably than models with
  shorter effective windows. If README or test data are missing, try a larger model.
- **RAG query**: `vibe` passes the raw description directly to the RAG store (unlike
  `splc compile` which extracts the query from SPL syntax).
- **No manifest**: `vibe` does not write `splc_manifest.json`. Use filename convention
  (`S7-<recipe>-<adapter>-<model>.py`) to track provenance in experiments.
- **`--no-rag`**: useful when the description is very domain-specific or when isolating
  the LLM's pretrained knowledge from recipe store examples.

---

## 14. spl3 code-rag

Manages the Code-RAG vector store that powers `text2spl` and `vibe` few-shot retrieval.

```bash
spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```

---

## 15. Full Pipeline S1–S10: IR + Ablation

The ten-step pipeline combines the full IR path (S1–S6) with an ablation baseline
(S7–S10) to measure whether the Mermaid + SPL intermediate representations add
measurable value over direct vibe coding.

### Background: NeurIPS 2026 validation

These steps were designed for the NeurIPS 2026 paper *"Beyond Vibe Coding: Intent
Invariance and Structured Prompt Language"* and executed as 15 experiments (5 recipes
× 3 model tiers). In doing so, every SPL.py command was exercised end-to-end on real
PocketFlow workflows — making these experiments the most comprehensive integration
validation of the toolchain to date. **The steps are not just a research protocol;
each one is a useful standalone feature.**

### The ten steps at a glance

| Step | Command | Output | Standalone value |
|------|---------|--------|-----------------|
| S1 | `spl3 splc describe --include-docs` | `S1-*-1-spec.md` | Reverse-engineer any codebase into a spec |
| S2 | `spl3 text2mmd` | `S2-*.mmd` | Visualise workflow topology from a spec |
| S3 | `spl3 mmd2spl` | `S3-*.spl` | Convert a diagram to executable SPL |
| S3✓ | `spl3 spl2mmd` | `S3-*.mmd` | **Visual validation:** re-render S3 SPL as diagram, compare with S2 |
| S4 | `spl3 splc compile --llm` | `S4-*.py` | Compile SPL to a target framework |
| S5 | `spl3 splc describe` | `S5-*-2-spec.md` | Spec the compiled artifact |
| S6 | `spl3 compare S1 S5` | `S6-*-spec-diff.md` | Measure round-trip intent fidelity (ΔS) |
| S7 | `spl3 vibe --out-dir` | `vibe/` folder | One-shot prototype from spec (bypass IR) |
| S8 | `spl3 splc describe` | `S8-*-3-spec.md` | Spec the vibe-generated artifact |
| S9 | `spl3 compare S1 S8` | `S9-*-vibe-diff.md` | Measure vibe round-trip fidelity |
| S10 | `spl3 compare S6 S9` | `S10-*-ablation.md` | **ΔIR = S6 − S9** (IR value-add) |

### Human Checkpoint Protocol

Every `[Human Checkpoint]` in S1–S10 follows the same three-step protocol:

```
1. REVIEW   — inspect the generated artifact
2. RUN      — execute/test with real inputs; work with AI assistant to fix all issues
3. DOCUMENT — record issues and fixes in notes.md before proceeding
```

Checkpoints occur after S1 (spec quality), S2 (diagram topology), S3 (SPL validation
+ run), S3✓ (visual diff of re-rendered diagram vs. S2), S4 (compiled code test),
S6 (review score), S7 (vibe output run), S10 (ablation verdict).
Steps S5, S8, S9 are fully automated.

### Phase 1 — Full IR pipeline (S1→S6)

```
existing code / README
    → S1: spl3 splc describe --include-docs    spec (ground truth)
    → S2: spl3 text2mmd                        Mermaid diagram
          ⚠️  [Human] verify topology
    → S3: spl3 mmd2spl                         SPL workflow
          spl3 spl2mmd S3-*.spl                re-render as diagram for visual diff vs S2
          ⚠️  [Human] spl3 validate + spl3 run
    → S4: spl3 splc compile --llm              compiled code
          ⚠️  [Human] run with test inputs
    → S5: spl3 splc describe                   round-trip spec
    → S6: spl3 compare S1 S5                   ΔS score
          ⚠️  [Human] review score; trace drift to S2 or S3
```

### Phase 2 — Ablation baseline (S7→S10)

```
    → S7: spl3 vibe --out-dir                  vibe-coded folder
          ⚠️  [Human] run with same test inputs as S4
    → S8: spl3 splc describe <vibe-folder>     vibe spec
    → S9: spl3 compare S1 S8                   vibe ΔS score
    → S10: spl3 compare S6 S9                  ΔIR = S6 − S9
           ⚠️  [Human] review ablation report; aggregate across runs
```

### Canonical command sequence (R1-agent / claude example)

```bash
export RECIPE=agent  ADAPTER=claude_cli  MODEL_ID=claude-sonnet-4-6  MODEL=sonnet
export OUT=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-$RECIPE/tests/$ADAPTER/$MODEL
export SRC=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-$RECIPE/src/pocketflow-$RECIPE

# S1 — describe original code
spl3 splc describe $SRC --include-docs --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md

# S2 — Mermaid diagram  *** HUMAN CHECKPOINT: verify topology ***
spl3 text2mmd $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --adapter $ADAPTER --model $MODEL_ID -o $OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd

# S3 — SPL workflow
spl3 mmd2spl $OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd \
  --adapter $ADAPTER --model $MODEL_ID -o $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl
spl3 validate $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl

# S3✓ — visual validation: re-render S3 SPL as diagram, compare with S2
spl3 spl2mmd $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --out-dir $OUT/S3-check/ --no-preview --save-pdf

# S4 — compile to Python/PocketFlow
spl3 splc compile $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --lang python/pocketflow --llm --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/targets/python_pocketflow --overwrite

# S5 — describe compiled code
spl3 splc describe $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL.py \
  --adapter $ADAPTER --model $MODEL_ID -o $OUT/S5-$RECIPE-$ADAPTER-$MODEL-2-spec.md

# S6 — round-trip score (judge fixed at claude-opus-4-6)
spl3 compare $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S5-$RECIPE-$ADAPTER-$MODEL-2-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff.md

# S7 — vibe-coded baseline  *** HUMAN CHECKPOINT: run generated code ***
mkdir -p $OUT/vibe/python_pocketflow
spl3 vibe --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow

# S8 — describe vibe output
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9 — vibe round-trip score
spl3 compare $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 — ablation: IR value-add = S6 score − S9 score
spl3 compare $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff.md \
  $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S10-$RECIPE-$ADAPTER-$MODEL-ablation.md
```

### When to use each path

| Situation | Recommendation |
|-----------|----------------|
| Rapid prototype — explore a new framework or idea | S7 (`spl3 vibe`) |
| Multi-model comparison — same spec, different models | S7 × N models |
| Need traceable, validated, auditable artifacts | S1→S6 (full IR) |
| Quantify IR value-add for a specific workflow | S1→S10 (both paths) |
| Already have a `.spl` file, new target | S4 only (`splc compile`) |
| Already have compiled code, need spec | S5 only (`splc describe`) |
| Visual audit of any `.spl` file (no LLM) | `spl3 spl2mmd` |
| Publication-quality diagram from `.spl` | `spl3 spl2mmd --save-pdf` |

---

## 16. Debugging LLM Prompts

All LLM-powered commands support the `--prompt` flag. It prints the full assembled
prompt — including RAG hits and reference context — then exits without calling the API.

```bash
# Preview the vibe prompt
spl3 vibe "my workflow" --adapter claude_cli --prompt

# Preview the splc compile prompt
spl3 splc compile agent.spl --lang go --llm --prompt

# Preview the Mermaid generation prompt
spl3 text2mmd "my workflow" --prompt

# Preview the mmd2spl prompt (requires --adapter)
spl3 mmd2spl workflow.mmd --adapter claude_cli --prompt
```

The output includes prompt length in characters and approximate token count.

---

## 17. Command reference

```
spl3 validate <file.spl> [file.spl ...]
spl3 run <file.spl> [--adapter] [--model] [-p key=val] [--log-prompts DIR]
spl3 describe <file.spl | folder/> [--adapter] [--model] [--prompt]
spl3 text2spl "<description>" [--adapter] [--mode auto|prompt|workflow] [--prompt]
spl3 text2mmd "<description>" [--adapter] [--style flowchart|graph|sequence] [--prompt]
spl3 spl2mmd <file.spl> [file.spl ...]
              [--out-dir DIR]
              [--preview/--no-preview]      # default: on
              [--save-html/--no-save-html]  # default: on
              [--save-markdown/--no-save-markdown]  # default: on
              [--save-spl/--no-save-spl]    # default: on
              [--save-png]                  # default: off
              [--save-pdf]                  # default: off; needs mmdc or Chrome
spl3 mmd2spl <file.mmd> [--adapter] [--template workflow|function] [--prompt]
spl3 compare <f1> <f2>
              [--mode llm|git-diff|vector|bert-score|ged|vision|ast-diff|structural]
              [--adapter NAME] [--model MODEL]
              [--adapter-embed NAME] [--adapter-synthesis NAME]
              [--format markdown|json|text|html] [-o FILE]
              [--focus all|structure|logic|quality|syntax|spl]
              [--diff-style unified|context|side-by-side]
              [--synthesize/--no-synthesize]
              [--prompt]
spl3 vibe "<description>" [--target LANG] [--adapter] [--model]
          [--out-dir DIR] [-o FILE]
          [--rag/--no-rag] [--rag-k N] [--references URL] [--verbose] [--prompt]

spl3 splc compile <file.spl> --lang <target> [--llm] [--adapter] [--rag-k N]
                  [--references URL] [--out-dir DIR] [--overwrite] [--prompt]
spl3 splc describe <impl.py | folder/> [--lang LABEL] [--adapter] [--spec-dir DIR]
                   [-o FILE] [--include-docs] [--prompt]

spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```
