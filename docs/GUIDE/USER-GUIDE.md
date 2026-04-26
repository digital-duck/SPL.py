# SPL 3.0 User Guide

**SPL (Structured Prompt Language)** is a SQL-inspired declarative language for
orchestrating LLM workflows. You write a `.spl` file — the invariant *logical view* —
and the toolchain runs it, compiles it, describes it, or generates it from plain English.

---

## Table of Contents

1. [Quick-start](#1-quick-start)
2. [spl3 validate](#2-spl3-validate)
3. [spl3 run](#3-spl3-run)
4. [spl3 describe](#4-spl3-describe)
5. [spl3 text2spl](#5-spl3-text2spl)
6. [spl3 splc compile](#6-spl3-splc-compile)
7. [spl3 splc describe](#7-spl3-splc-describe)
8. [spl3 code-rag](#8-spl3-code-rag)
9. [Pipelines](#9-pipelines)
10. [Command reference](#10-command-reference)

---

## 1. Quick-start

```bash
# Validate a .spl file
spl3 validate cookbook/05_self_refine/self_refine.spl

# Run it
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama --model gemma3

# Generate a spec
spl3 describe cookbook/05_self_refine/self_refine.spl --adapter claude_cli

# Compile to Python/PocketFlow (deterministic — no LLM needed)
spl3 splc compile cookbook/05_self_refine/self_refine.spl --lang python/pocketflow
```

---

## 2. spl3 validate

Checks lexer → parser → semantic analyser. No LLM call.

```bash
spl3 validate <file.spl>
```

**Exit codes:** `0` = valid, `1` = error (with message).

```bash
spl3 validate cookbook/05_self_refine/self_refine.spl
# OK
```

---

## 3. spl3 run

Executes a `.spl` workflow against a live LLM adapter.

```bash
spl3 run <file.spl> [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--adapter` | `ollama` | LLM adapter: `ollama`, `claude_cli` |
| `--model` | adapter default | Model name override |
| `-p key=value` | — | Workflow `INPUT` parameter overrides |
| `--log-prompts DIR` | — | Write each assembled prompt to `DIR/` as `.md` |
| `--tools FILE` | — | Python module exposing `CALL`-able tool functions |

```bash
# Run with defaults
spl3 run cookbook/05_self_refine/self_refine.spl

# Override input params
spl3 run cookbook/05_self_refine/self_refine.spl \
  -p task="Explain quantum entanglement" \
  -p max_iterations=5 \
  --adapter ollama --model gemma3

# Save prompts for inspection
spl3 run self_refine.spl --log-prompts logs/prompts/
```

---

## 4. spl3 describe

Generates a plain-English functional specification from `.spl` source and writes it as
`<stem>-spec.md`.  The spec has **6 sections**:

| Section | Content |
|---------|---------|
| `## 0. High-level Description` | SPL-vocabulary prose — used as `text2spl` input for RAG seeding |
| `## 1. Purpose` | One-sentence summary |
| `## 2. Inputs` | Parameter table |
| `## 3. Process` | Numbered execution steps |
| `## 4. Error Handling` | EXCEPTION cases |
| `## 5. Output` | Return value and metadata |

### File input

```bash
spl3 describe <file.spl> [OPTIONS]
```

```bash
spl3 describe cookbook/05_self_refine/self_refine.spl --adapter claude_cli
# Writes: cookbook/05_self_refine/self_refine-spec.md
```

### Folder input — multi-file recipes

When a recipe spans multiple `.spl` files (e.g. a main orchestrator + sub-workflows),
pass the **folder**. All `*.spl` files in the folder are gathered and described together
as a single unit.

```bash
spl3 describe <folder/> [OPTIONS]
# Spec named after the folder: <folder>-spec.md
```

```bash
# Recipe 63 — main workflow + 3 parallel sub-workflows
spl3 describe cookbook/63_parallel_code_review/ --adapter claude_cli
# Collects: parallel_code_review.spl, 00_style_review.spl,
#           01_security_audit.spl, 02_test_generator.spl
# Writes:   cookbook/63_parallel_code_review/63_parallel_code_review-spec.md
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--adapter` | `ollama` | LLM adapter |
| `--model` | adapter default | Model override |
| `--spec-dir DIR` | same as input | Redirect spec output to a different directory |

```bash
spl3 describe my_workflow.spl --adapter ollama --model gemma3
spl3 describe cookbook/63_parallel_code_review/ --adapter claude_cli --spec-dir docs/specs
```

### Batch — describe all cookbook recipes

```bash
spl3 code-rag describe-all cookbook/ --adapter claude_cli
# Generates *-spec.md for every active recipe in cookbook_catalog.json
```

---

## 5. spl3 text2spl

Compiles a natural language description into valid SPL 3.0 source code.  Uses an LLM
adapter with a few-shot system prompt; optionally retrieves similar examples from the
Code-RAG store.

```bash
spl3 text2spl "<description>" [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--adapter` | `ollama` | LLM adapter |
| `-m / --model` | adapter default | Model override |
| `--mode` | `auto` | `auto` / `prompt` / `workflow` |
| `--validate / --no-validate` | validate | Run lexer+parser+analyser on output |
| `-o / --output FILE` | prints to stdout | Write generated SPL to file |

```bash
# One-shot generation
spl3 text2spl "summarise a document with a 2000 token budget"

# Explicit workflow mode, save to file
spl3 text2spl "build a review agent that refines text until quality > 0.8" \
  --mode workflow -o review.spl --adapter claude_cli

# Using Section 0 from a describe spec as input
spl3 text2spl "$(sed -n '/^## 0/,/^## 1/p' self_refine-spec.md | head -10)" \
  --mode workflow -o regenerated.spl
```

**Output:** always writes the file — even if validation fails — so you have a baseline
to inspect and fix.

---

## 6. spl3 splc compile

Deterministic (rule-based) or LLM-assisted compilation of a `.spl` logical view to a
physical target language.

```bash
spl3 splc compile <file.spl> --lang <target> [OPTIONS]
```

### Deterministic targets (no LLM needed)

These targets have a rule-based transpiler — fast, reproducible, no API cost:

| `--lang` | Output |
|----------|--------|
| `python/pocketflow` | Python — PocketFlow ETL nodes |
| `python/langgraph` | Python — LangGraph state machine |
| `go` | Go — stdlib + Ollama REST |
| `ts` | TypeScript — Node 18+ + Ollama REST |

### LLM-compiled targets

These use `claude_cli` to generate the implementation:

| `--lang` | Framework |
|----------|-----------|
| `python/crewai` | CrewAI |
| `python/autogen` | AutoGen |
| `python` | Plain Python |

### Examples

```bash
# Deterministic — Python/PocketFlow (1st-class target)
spl3 splc compile cookbook/05_self_refine/self_refine.spl \
  --lang python/pocketflow

# Overwrite existing output
spl3 splc compile cookbook/05_self_refine/self_refine.spl \
  --lang python/pocketflow --overwrite

# Custom output directory
spl3 splc compile self_refine.spl \
  --lang python/pocketflow --out-dir deploy/pocketflow/

# LLM-compiled target (requires claude_cli)
spl3 splc compile self_refine.spl \
  --lang python/crewai --model claude-sonnet-4-6

# Force LLM even for a deterministic target (for experimentation)
spl3 splc compile self_refine.spl --lang python/pocketflow --llm

# Dry-run: print the prompt, don't call the LLM
spl3 splc compile self_refine.spl --lang python/crewai --dry-run
```

### Output files

For a recipe `self_refine.spl` compiled with `--lang python/pocketflow`:

```
targets/python_pocketflow/
  self_refine_python_pocketflow.py   ← generated implementation
  readme.md                          ← ETL mapping table + run instructions
  splc_manifest.json                 ← provenance (source hash, model, timestamp)
```

### PocketFlow — ETL mapping

PocketFlow is the 1st-class `splc` target because it maps directly to ETL terminology
familiar to data professionals:

| PocketFlow | ETL role | SPL construct |
|------------|----------|---------------|
| `prep(shared)` | Extract | read `@variables` from shared store |
| `exec(prep_res)` | Transform | `GENERATE` / LLM call |
| `post(shared, prep_res, exec_res)` | Load | write results back + return action |
| `shared` dict | Staging area | SPL `@variable` scope |
| `Flow(start=...)` | Pipeline DAG | `WORKFLOW` + control flow |

---

## 7. spl3 splc describe

Generates a spec from a **compiled target implementation** (Python, TypeScript, Go).
This is the **reverse pipeline** — it lets you start from an existing implementation and
work back to a canonical SPL form.

```bash
spl3 splc describe <impl.py | folder/> [OPTIONS]
```

### Why use it

- You have an existing Python/PocketFlow or LangGraph agent and want to bring it into SPL
- You want a bilingual RAG entry: (implementation ↔ SPL description) pair
- You want to retarget an implementation to a different framework without rewriting

### Output spec sections

| Section | Content |
|---------|---------|
| `## 0. High-level Description` | SPL-vocab prose — paste directly into `text2spl` |
| `## 1. Purpose` | One-sentence summary |
| `## 2. SPL ↔ <Lang> Construct Mapping` | Table: SPL construct → target idiom |
| `## 3. Logical Functions / Prompts` | Each prompt template: name, role, conventions |
| `## 4. Control Flow` | Execution path in SPL terms |
| `## 5. How to Regenerate as SPL` | Ready-to-run `text2spl` + `splc compile` commands |

### Examples

```bash
# Describe a single generated file (lang auto-detected from filename)
spl3 splc describe \
  cookbook/05_self_refine/targets/python_pocketflow/self_refine_python_pocketflow.py \
  --adapter claude_cli
# Writes: targets/python_pocketflow/self_refine-splc-python_pocketflow-spec.md

# Describe all files in a targets directory
spl3 splc describe cookbook/05_self_refine/targets/python_pocketflow/ \
  --adapter claude_cli

# Describe a LangGraph implementation
spl3 splc describe cookbook/05_self_refine/langgraph/self_refine_langgraph.py \
  --adapter claude_cli

# Override auto-detected lang label
spl3 splc describe my_agent.py --lang "Python — PocketFlow" --adapter claude_cli

# Write spec to a shared docs directory
spl3 splc describe targets/python_pocketflow/ \
  --adapter claude_cli --spec-dir docs/specs/
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--lang LABEL` | auto-detected | Human-readable label, e.g. `Python — PocketFlow` |
| `--adapter` | `ollama` | LLM adapter |
| `--model` | adapter default | Model override |
| `--spec-dir DIR` | same as input | Redirect spec output |

---

## 8. spl3 code-rag

Manages the Code-RAG vector store that powers `text2spl` few-shot retrieval.
Store location: `.spl/code_rag/chroma.sqlite3`

### Seed the store

Three seeding modes in increasing description quality:

```bash
# Mode 1 — file header comments (fastest, lowest quality)
spl3 code-rag seed cookbook/

# Mode 2 — curated one-liners from cookbook_catalog.json
spl3 code-rag seed --catalog cookbook/cookbook_catalog.json

# Mode 3 — Section 0 from describe-generated specs (richest, recommended)
spl3 code-rag describe-all cookbook/ --adapter claude_cli   # generate specs first
spl3 code-rag seed cookbook/ --from-specs                   # seed from Section 0
```

### Inspect the store

```bash
# Statistics
spl3 code-rag stats

# Query — find similar recipes
spl3 code-rag query "self-refine loop with critique and approval token"
```

---

## 9. Pipelines

### Forward pipeline — SPL → target implementation

```
.spl file
  │
  ├── spl3 validate              (syntax check)
  ├── spl3 run                   (execute with LLM)
  ├── spl3 describe              (→ *-spec.md for humans and RAG)
  └── spl3 splc compile          (→ python/pocketflow, go, ts, langgraph, ...)
```

### Reverse pipeline — implementation → SPL

Use this to onboard existing code into SPL or to retarget to a different framework:

```
Existing implementation (Python/PocketFlow, LangGraph, etc.)
  │
  └── spl3 splc describe         (→ *-splc-<lang>-spec.md)
        │
        └── spl3 text2spl        (Section 0 → .spl source)
              │
              └── spl3 splc compile  (→ any new target)
```

### RAG bootstrapping pipeline

Seed the Code-RAG store so `text2spl` generates better SPL:

```
cookbook/*.spl
  │
  └── spl3 code-rag describe-all   (batch → *-spec.md for all active recipes)
        │
        └── spl3 code-rag seed --from-specs   (index Section 0 into ChromaDB)
              │
              └── spl3 text2spl "<description>"   (RAG retrieves similar examples)
```

### Multi-file recipe (parallel sub-workflows)

```bash
# Step 1 — describe the whole recipe as one unit
spl3 describe cookbook/63_parallel_code_review/ --adapter claude_cli

# Step 2 — compile main orchestrator
spl3 splc compile cookbook/63_parallel_code_review/parallel_code_review.spl \
  --lang python/pocketflow

# Step 3 — compile sub-workflows
for f in cookbook/63_parallel_code_review/0*.spl; do
  spl3 splc compile "$f" --lang python/pocketflow --overwrite
done
```

---

## 10. Command reference

```
spl3 validate <file.spl>
spl3 run <file.spl> [--adapter] [--model] [-p key=val] [--log-prompts DIR] [--tools FILE]
spl3 describe <file.spl | folder/> [--adapter] [--model] [--spec-dir DIR]
spl3 text2spl "<description>" [--adapter] [-m model] [--mode auto|prompt|workflow]
                               [--validate|--no-validate] [-o FILE]
spl3 explain <file.spl>

spl3 splc compile <file.spl> --lang <target>
               [--out-dir DIR] [--model] [--rag|--no-rag] [--rag-k N]
               [--references URL|PATH] [--overwrite] [--dry-run] [--llm] [-v]

spl3 splc describe <impl.py | folder/> [--lang LABEL] [--adapter] [--model] [--spec-dir DIR]

spl3 code-rag seed [cookbook/] [--catalog FILE] [--from-specs]
spl3 code-rag describe-all [cookbook/] [--adapter] [--model]
spl3 code-rag query "<text>"
spl3 code-rag stats

spl3 registry list
spl3 register <file.spl | dir/>
spl3 peers list
spl3 peers add <hub-url>
```

### Supported splc targets

| `--lang` | Transpiler | Notes |
|----------|-----------|-------|
| `python/pocketflow` | Deterministic | **1st-class target** — ETL-style, minimal deps |
| `python/langgraph` | Deterministic | LangGraph state machine |
| `go` | Deterministic | stdlib + Ollama REST |
| `ts` | Deterministic | TypeScript, Node 18+ |
| `python/crewai` | LLM | Requires `--model` |
| `python/autogen` | LLM | Requires `--model` |
| `python` | LLM | Plain Python, minimal deps |
