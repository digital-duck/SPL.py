# SPL 3.0 User Guide

**SPL (Structured Prompt Language)** is a SQL-inspired declarative language for
orchestrating LLM workflows. You write a `.spl` file — the invariant *logical view* —
and the toolchain runs it, compiles it, describes it, or generates it from plain English.

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
12. [spl3 code-rag](#12-spl3-code-rag)
13. [Visual Workflow Pipeline](#13-visual-workflow-pipeline)
14. [Debugging LLM Prompts](#14-debugging-llm-prompts)
15. [Pipelines](#15-pipelines)
16. [Standard Library Tools](#16-standard-library-tools)
17. [Command reference](#17-command-reference)

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
```

---

## 2. LLM Adapters

SPL 3.0 supports multiple LLM adapters for different deployment scenarios and cost models:

### Available Adapters

| Adapter | Cost Model | Authentication | Models |
|---------|------------|---------------|---------|
| `claude_cli` | Subscription (flat rate) | Claude Code OAuth | `claude-sonnet-4-6` (default), any Claude model |
| `gemini_cli` | Free tier + subscription | Gemini CLI OAuth | `gemini-2.5-flash` (default), `gemini-3-flash-preview` |
| `ollama` | Local inference | None required | `gemma3` (default), `nomic-embed-text` (embedding) |
| `openrouter` | API Usage | API Key | `google/gemini-3-flash-preview`, `deepseek/deepseek-v4-flash` |

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
spl3 text2mermaid "user onboarding workflow with approval gates"
```

---

## 8. spl3 mmd2spl

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

| Mode | Description | Metric |
|------|-------------|--------|
| `llm` | LLM-powered semantic analysis (default) | 1-10 scores |
| `vector` | Embedding-based cosine similarity | 0.0 - 1.0 similarity |
| `bert-score` | Contextual alignment via BERTScore | F1 Score |
| `ged` | Graph Edit Distance (for Mermaid files) | Topological distance |
| `git-diff` | Traditional line-by-line difference | Unified/Side-by-side diff |

### Examples

```bash
# Full scientific comparison
spl3 compare spec1.md spec2.md --mode llm --mode vector --mode bert-score

# Compare topologies of two Mermaid charts
spl3 compare chart1.mmd chart2.mmd --mode ged

# Mechanical diff only
spl3 compare file1.spl file2.spl --mode git-diff --diff-style side-by-side
```

---

## 10. spl3 splc compile

Deterministic or LLM-assisted compilation of a `.spl` logical view to a physical target.

```bash
# Deterministic — Python/PocketFlow
spl3 splc compile agent.spl --lang python/pocketflow

# LLM-assisted — Go
spl3 splc compile agent.spl --lang go --llm
```

---

## 11. spl3 splc describe

Reverse-engineers a specification from a **compiled target implementation**.

```bash
spl3 splc describe targets/python_pocketflow/agent.py --adapter claude_cli
```

---

## 12. spl3 code-rag

Manages the Code-RAG vector store that powers `text2spl` few-shot retrieval.

---

## 13. Visual Workflow Pipeline

Design visually, execute logically:
1. `text2mmd` → Visual topology
2. Human Review → Correct topology
3. `mmd2spl` → Declarative logic
4. `splc compile` → Physical implementation

---

## 14. Debugging LLM Prompts

All LLM-powered commands (`text2spl`, `mmd2spl`, `vibe`, `compare`, etc.) support the `--prompt` flag. This allows you to inspect the full assembled prompt (including RAG hits and references) before the API call is made.

```bash
# Preview the prompt for Mermaid generation
spl3 text2mmd "my workflow" --prompt

# Preview the prompt for SPL compilation
spl3 splc compile agent.spl --lang go --llm --prompt
```

---

## 17. Command reference

```
spl3 validate <file.spl>
spl3 run <file.spl> [--adapter] [--model] [-p key=val] [--log-prompts DIR]
spl3 describe <file.spl | folder/> [--adapter] [--model] [--prompt]
spl3 text2spl "<description>" [--adapter] [--mode auto|prompt|workflow] [--prompt]
spl3 text2mmd "<description>" [--adapter] [--style flowchart|graph|sequence] [--prompt]
spl3 mmd2spl <file.mmd> [--adapter] [--template workflow|function] [--prompt]
spl3 compare <f1> <f2> [--mode Mode] [--adapter] [--adapter-embed] [--prompt]
spl3 vibe -d "<req>" --target <lang> [--references URL] [--prompt]

spl3 splc compile <file.spl> --lang <target> [--llm] [--prompt]
spl3 splc describe <impl.py | folder/> [--lang LABEL] [--prompt]

spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```
