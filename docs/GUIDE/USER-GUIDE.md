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
12. [spl3 vibe](#12-spl3-vibe)
13. [spl3 code-rag](#13-spl3-code-rag)
14. [Full IR Pipeline vs Vibe (Ablation)](#14-full-ir-pipeline-vs-vibe-ablation)
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

Generates target code **directly from a natural language description**, bypassing the
`.mmd` and `.spl` intermediate representation (IR) steps. This is the "vibe coding"
path — fast, one-shot, no structured intermediate artifacts.

Under the hood, `vibe` reuses all of `splc`'s compilation infrastructure: the same
RAG few-shot store, reference fetcher, and LLM caller. The only difference is the
input: a human description instead of a structured `.spl` file.

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
| `--output / -o` | stdout | Write generated code to `FILE` |
| `--rag / --no-rag` | `--rag` | Include RAG few-shot examples from the SPL recipe store |
| `--rag-k` | `3` | Number of RAG examples (1–10) |
| `--references` | — | Reference codebase(s): GitHub URL or local path (repeatable) |
| `--no-readme` | off | Skip generating the `<stem>-readme.md` alongside the code |
| `--verbose / -v` | off | Print progress and token counts |
| `--prompt` | off | Print the assembled LLM prompt and exit (no API call) |

### Examples

```bash
# Quickest path — description on the command line
spl3 vibe "self-refine agent: generate a draft, critique it, refine until score > 0.8" \
  --adapter claude_cli -m claude-sonnet-4-6 -o out/self_refine.py

# Read description from a spec file (e.g. Section 0 of a splc describe output)
spl3 vibe --description S1-agent-sonnet-spec.md \
  --adapter openrouter -m qwen/qwen3.6-plus \
  --target python/pocketflow \
  -o tests/openrouter/qwen/A1-agent-qwen.py

# Different target framework
spl3 vibe "RAG pipeline with re-ranking" \
  --target python/langgraph \
  --adapter openrouter -m google/gemini-3-flash-preview \
  -o out/rag_langgraph.py

# Inspect the prompt without calling the LLM
spl3 vibe "judge agent" --adapter claude_cli --prompt

# With a reference codebase for grounding
spl3 vibe "research agent" \
  --references https://github.com/langchain-ai/langgraph \
  --target python/langgraph \
  --adapter claude_cli -o out/research.py
```

### Output files

When `--output FILE` is given, `vibe` writes two files:

| File | Contents |
|------|----------|
| `FILE` | The generated implementation (e.g. `agent.py`) |
| `<stem>-readme.md` | Setup instructions, run command, and logical-step mapping table |

### Notes

- **RAG query**: unlike `splc compile` (which extracts the query from SPL comment syntax),
  `vibe` passes the raw description directly to the RAG store, ensuring semantically
  relevant few-shot examples are retrieved.
- **No manifest**: `vibe` does not write a `splc_manifest.json`. Use the output filename
  convention (`A1-<recipe>-<model>.py`) to track provenance in experiments.
- **`--no-rag`**: useful when the description is very domain-specific or when you want
  to isolate the LLM's pretrained knowledge from recipe store examples.

---

## 13. spl3 code-rag

Manages the Code-RAG vector store that powers `text2spl` and `vibe` few-shot retrieval.

```bash
spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```

---

## 14. Full IR Pipeline vs Vibe (Ablation)

SPL provides two distinct paths from a human description to runnable code.
Comparing their outputs is the core of the NDD ablation study.

```
Full IR Pipeline (S1–S6):
  description
    → spl3 splc describe   (S1: spec.md)
    → spl3 text2mmd        (S2: .mmd)   ← Human review
    → spl3 mmd2spl         (S3: .spl)   ← Human validate/run
    → spl3 splc compile    (S4: .py)    ← Human test
    → spl3 splc describe   (S5: spec.md)
    → spl3 compare S1 S5   (S6: round-trip diff)

Vibe / Bypass IR (A1–A3):
  description
    → spl3 vibe            (A1: .py)    ← Human test (same test cases as S4)
    → spl3 splc describe   (A2: spec.md)
    → spl3 compare S1 A2   (A3: ablation diff)
```

**Interpreting results:** Compare the S6 diff (full IR) against the A3 diff (bypass IR).
If S6 consistently shows higher semantic similarity, the `.mmd` + `.spl` IR steps
add measurable value to round-trip fidelity.

### When to use `vibe` vs the full pipeline

| Situation | Recommendation |
|-----------|----------------|
| Rapid prototyping, exploring a new framework | `vibe` |
| NDD experiment — need traceable, validated artifacts | Full IR pipeline |
| Ablation study — quantifying IR value-add | Both paths, then `spl3 compare` |
| Existing `.spl` file, new deployment target | `splc compile` (not vibe) |

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
spl3 vibe "<description>" [--target LANG] [--adapter] [--model] [-o FILE]
          [--rag/--no-rag] [--rag-k N] [--references URL] [--verbose] [--prompt]

spl3 splc compile <file.spl> --lang <target> [--llm] [--adapter] [--rag-k N]
                  [--references URL] [--out-dir DIR] [--overwrite] [--prompt]
spl3 splc describe <impl.py | folder/> [--lang LABEL] [--adapter] [--spec-dir DIR]
                   [-o FILE] [--include-docs] [--prompt]

spl3 code-rag seed [cookbook/] [--from-specs]
spl3 code-rag stats
```
