# Research Agent — PocketFlow Implementation

## Overview

An iterative research agent that answers a user-supplied question by repeatedly deciding whether to search the web (DuckDuckGo) or synthesize a final prose answer. Accumulated search results are stored in a shared `context` buffer that grows across iterations. The agent terminates as soon as it decides it has enough information, or after `MAX_ITERATIONS` rounds (safety cap).

```
DecideAction ─"search"→ SearchWeb ─"decide"→ DecideAction   ← loop
             ─"answer"→ AnswerQuestion                        ← terminal
```

## Requirements

```bash
pip install pocketflow openai duckduckgo-search pyyaml
```

| Package | Role |
|---|---|
| `pocketflow` | Minimalist ETL-style LLM orchestration |
| `openai` | OpenRouter / OpenAI API client |
| `duckduckgo-search` | Free, no-key web search |
| `pyyaml` | YAML parsing of structured LLM output |

## Setup — Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | one of the two | — | OpenRouter key (preferred) |
| `OPENAI_API_KEY` | one of the two | — | OpenAI key (fallback) |
| `LLM_MODEL` | no | `openai/gpt-4o-mini` | Model ID (OpenRouter format: `provider/model`) |
| `MAX_ITERATIONS` | no | `8` | Maximum search-decide rounds before forcing an answer |

```bash
export OPENROUTER_API_KEY="sk-or-..."
export LLM_MODEL="openai/gpt-4o-mini"   # or "anthropic/claude-3-5-sonnet", etc.
```

## Usage

```bash
# Default question (baked into __main__)
python research_agent.py

# Custom question
python research_agent.py "How does RLHF differ from DPO for LLM alignment?"

# Swap model without editing code
LLM_MODEL=anthropic/claude-3-5-haiku python research_agent.py "What is CRISPR-Cas9?"
```

### Expected output (abbreviated)

```
======================================================================
Research Agent  |  model=openai/gpt-4o-mini  |  max_iter=8
Question: What are the key differences between transformer and mamba ...
======================================================================
[DecideAction] iter=1 — reasoning...
[DecideAction] → action='search'  query='transformer vs mamba architecture differences'
[SearchWeb] Querying DuckDuckGo: 'transformer vs mamba architecture differences'
[DecideAction] iter=2 — reasoning...
[DecideAction] → action='search'  query='mamba state space model long sequence efficiency'
[SearchWeb] Querying DuckDuckGo: 'mamba state space model long sequence efficiency'
[DecideAction] iter=3 — reasoning...
[DecideAction] → action='answer'  query=''
[AnswerQuestion] Synthesizing final answer...

======================================================================
FINAL ANSWER
======================================================================
Transformers and Mamba (a selective state-space model) differ primarily in ...
```

## Workflow Logic — Step by Step

1. **Initialization**: `shared` dict is created with the user's `question`, an empty `context` (`"No previous search"`), and `iteration=0`. The `DecideAction` node is the entry point.

2. **DecideAction (WHILE-loop body)**:
   - Builds a two-section prompt: `### CONTEXT` (question + all previous search results) and `### ACTION SPACE` (enumerate `search`/`answer` with parameter schemas).
   - Calls the LLM; expects a fenced ` ```yaml ``` ` block with fields `thinking | action | reason | search_query | answer`.
   - YAML parsing has a two-attempt safety net: if `yaml.safe_load` fails, all `thinking`/`reason`/`answer` keys are rewritten to use `|` block-scalar notation and parsing is retried. A second failure raises `ValueError`.
   - `post()` inspects `decision["action"]`:
     - `"search"` → writes `search_query` to shared, returns `"search"` (route to `SearchWeb`).
     - `"answer"` → returns `"answer"` (route to `AnswerQuestion`).

3. **SearchWeb (loop-back side-effect)**:
   - Reads `shared["search_query"]`.
   - Calls `duckduckgo_search.DDGS().text()` for up to 5 results.
   - Formats results as `Title / URL / Snippet` blocks.
   - Appends a `SEARCH: <query>\nRESULTS: <...>` block to `shared["context"]`.
   - Returns `"decide"` → loops back to `DecideAction`.

4. **AnswerQuestion (terminal)**:
   - Builds a synthesis prompt with `### CONTEXT` (full accumulated research).
   - Calls the LLM; stores the free-form prose response in `shared["answer"]`.
   - Returns `"done"` — no successor node; flow terminates.

5. **Safety cap**: If `iteration >= MAX_ITERATIONS` inside `DecideAction.exec()`, a synthetic `action: answer` dict is returned immediately, skipping further searches and routing directly to `AnswerQuestion`.