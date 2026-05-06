# SPL 3.0 User Guide

**SPL (Structured Prompt Language)** is a SQL-inspired declarative language for
orchestrating LLM workflows. You write a `.spl` file — the invariant *logical view* —
and the toolchain runs it, compiles it, describes it, or generates it from plain English.

> **End-to-end validated.** The ten-step pipeline documented in §14 (S1–S10) was
> designed for the NeurIPS 2026 paper *"Beyond Vibe Coding: Intent Invariance and
> Structured Prompt Language"* and executed across 5 real-world workflow recipes × 3
> model tiers (15 experiments). Every command in this guide was exercised in those
> experiments — making §14 both the research protocol and the most comprehensive
> integration test suite for SPL.py.

---

## Table of Contents

1. [Quick-start](#1-quick-start)
2. [LLM Adapters](#2-llm-adapters)
3. [spl3 validate](#3-spl3-validate)
4. [spl3 run](#4-spl3-run)
5. [spl3 describe](#5-spl3-describe)
6. [spl3 text2spl](#6-spl3-text2spl)
7. [spl3 text2mermaid](#7-spl3-text2mermaid)
8. [spl3 mermaid2spl](#8-spl3-mermaid2spl)
9. [spl3 compare](#9-spl3-compare)
10. [spl3 splc compile](#10-spl3-splc-compile)
11. [spl3 splc describe](#11-spl3-splc-describe)
12. [spl3 vibe](#12-spl3-vibe)
13. [spl3 code-rag](#13-spl3-code-rag)
14. [Full Pipeline S1–S10: IR + Ablation](#14-full-pipeline-s1s10-ir--ablation)
15. [Debugging LLM Prompts](#15-debugging-llm-prompts)
16. [Command reference](#16-command-reference)

---

## 1. Quick-start

```bash
# Validate a .spl file
spl3 validate cookbook/05_self_refine/self_refine.spl

# Run it with different adapters
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama --model gemma3

# Compare two specs using the "Physics Lens"
spl3 compare spec1.md spec2.md --mode vector --mode llm

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

## 7. spl3 text2mermaid

Converts natural language workflow descriptions into Mermaid flowchart diagrams.

```bash
spl3 text2mmd "user onboarding workflow with approval gates"
```

---

## 8. spl3 mermaid2spl

Converts a Mermaid flowchart diagram into executable SPL workflow code.

```bash
spl3 mmd2spl workflow.mmd --adapter claude_cli -o workflow.spl
```

---

## 9. spl3 compare

Performs semantic and/or mechanical comparison between two files. This is the primary tool for measuring **Intent Invariance** in NDD round-trip experiments.

```bash
spl3 compare <file1> <file2> [OPTIONS]
```

### Comparison Modes (`--mode`)

You can specify multiple modes to generate a comprehensive "Physics Lens" report:

| Mode | Description | Metric | Best for |
|------|-------------|--------|----------|
| `llm` | LLM-powered semantic analysis (default) | 1-10 scores | `.md` spec files |
| `vector` | Embedding-based cosine similarity | 0.0–1.0 | Any text files |
| `bert-score` | Contextual alignment via BERTScore | F1 Score | Any text files |
| `ged` | Graph Edit Distance | Topological distance | `.mmd` files only |
| `git-diff` | Line-by-line difference | Unified/side-by-side diff | `.spl` files |

### Examples

```bash
# Full scientific comparison
spl3 compare spec1.md spec2.md --mode llm --mode vector --mode bert-score

# Compare topologies of two Mermaid charts
spl3 compare chart1.mmd chart2.mmd --mode ged

# Mechanical diff with side-by-side view (markdown output)
spl3 compare file1.spl file2.spl --mode git-diff --diff-style side-by-side
```

---

## 10. spl3 splc compile

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

## 11. spl3 splc describe

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

## 12. spl3 vibe

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

## 13. spl3 code-rag

Manages the Code-RAG vector store that powers `text2spl` and `vibe` few-shot retrieval.

```bash
spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```

---

## 14. Full Pipeline S1–S10: IR + Ablation

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
+ run), S4 (compiled code test), S6 (review score), S7 (vibe output run), S10
(ablation verdict). Steps S5, S8, S9 are fully automated.

### Phase 1 — Full IR pipeline (S1→S6)

```
existing code / README
    → S1: spl3 splc describe --include-docs    spec (ground truth)
    → S2: spl3 text2mmd                        Mermaid diagram
          ⚠️  [Human] verify topology
    → S3: spl3 mmd2spl                         SPL workflow
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

---

## 15. Debugging LLM Prompts

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

## 16. Command reference

```
spl3 validate <file.spl>
spl3 run <file.spl> [--adapter] [--model] [-p key=val] [--log-prompts DIR]
spl3 describe <file.spl | folder/> [--adapter] [--model] [--prompt]
spl3 text2spl "<description>" [--adapter] [--mode auto|prompt|workflow] [--prompt]
spl3 text2mmd "<description>" [--adapter] [--style flowchart|graph|sequence] [--prompt]
spl3 mmd2spl <file.mmd> [--adapter] [--template workflow|function] [--prompt]
spl3 compare <f1> <f2> [--mode MODE] [--adapter] [--format markdown|json|text] [--prompt]
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
