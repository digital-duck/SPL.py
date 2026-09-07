## Summary

This workflow implements a three-stage chain-of-thought reasoning pipeline that takes a topic as input and produces an executive-level summary through progressive refinement. It works by first gathering research on a topic, then analyzing that research for trends and implications, and finally distilling the analysis into a concise brief. Knowledge workers and analysts benefit by getting structured, multi-step LLM reasoning rather than a single-shot answer.

## Detailed Specification

### 1. Purpose

Execute a sequential three-stage LLM reasoning chain — research, analyze, summarize — that transforms a raw topic into a polished executive brief through structured chain-of-thought prompting.

### 2. High-level Description

The WORKFLOW `chain_of_thought` accepts a single TEXT input `@topic` (defaulting to `'distributed AI inference'`) and produces a TEXT output `@summary`. It follows a linear chain-of-thought pattern where each GENERATE call feeds its output as input to the next stage, building a progressive reasoning context. The first CREATE FUNCTION `research` prompts the LLM to produce key facts about the given topic. The second CREATE FUNCTION `analyze` takes the research output and prompts the LLM to identify key trends and implications within those findings. The third CREATE FUNCTION `summarize_analysis` takes the analysis and prompts the LLM to condense it into a concise executive brief. All three stages execute sequentially via GENERATE, storing intermediate results in shared workflow variables `@research`, `@analysis`, and `@summary`. The workflow terminates with RETURN carrying `status = 'complete'`.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| WORKFLOW | `WORKFLOW chain_of_thought` | Single workflow, linear execution, no branches |
| CREATE FUNCTION | `research`, `analyze`, `summarize_analysis` | Three prompt templates with single `{param}` slot each |
| GENERATE | Three sequential GENERATE calls | Each LLM call stores result in a workflow variable |
| Shared state | `@topic`, `@research`, `@analysis`, `@summary` | Variables thread context through all three stages |
| RETURN | `RETURN @summary WITH status = 'complete'` | Terminal status token signals successful completion |

### 4. Logical Functions / Prompts

**`research(topic TEXT)`**
- Role: Stage 1 — grounding. Prompts the LLM to gather and state key facts about the topic.
- Key conventions: Open-ended retrieval prompt; no output format constraint; result stored in `@research`.

**`analyze(research TEXT)`**
- Role: Stage 2 — reasoning. Injects the full research text and prompts the LLM to extract trends and implications.
- Key conventions: Passes prior stage output verbatim via `{research}` slot; no scoring or sentinel tokens; result stored in `@analysis`.

**`summarize_analysis(analysis TEXT)`**
- Role: Stage 3 — distillation. Injects the full analysis and prompts the LLM to produce a concise executive brief.
- Key conventions: Explicitly named `summarize_analysis` to avoid collision with the SPL built-in `summarize()`; passes prior stage output via `{analysis}` slot; result stored in `@summary`.

### 5. Control Flow

Execution enters `chain_of_thought` with `@topic` bound. Stage 1 runs `GENERATE research(@topic)`, producing `@research`. Stage 2 runs `GENERATE analyze(@research)`, producing `@analysis`. Stage 3 runs `GENERATE summarize_analysis(@analysis)`, producing `@summary`. There are no loops, no WHILE, and no EVALUATE branches — the path is strictly linear. The workflow terminates with `RETURN @summary WITH status = 'complete'`.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Execute a sequential three-stage LLM reasoning chain — research, analyze, summarize — that transforms a raw topic into a polished executive brief through structured chain-of-thought prompting." --mode workflow

# Step 2 — compile to any target
spl3 splc compile chain_of_thought.spl --lang python/pocketflow
spl3 splc compile chain_of_thought.spl --lang python/langgraph
spl3 splc compile chain_of_thought.spl --lang go
```