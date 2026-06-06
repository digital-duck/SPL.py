# PocketFlow Deep Research Orchestrator

## Overview
A minimalist, ETL-style LLM orchestration workflow that autonomously researches a user-specified topic. It iteratively generates targeted web queries, gathers factual snippets in parallel, extracts key insights, and evaluates research completeness. The flow loops up to 2 times to fill knowledge gaps before synthesizing and saving a comprehensive Markdown report.

## Requirements
- Python 3.9+
- Standard library only (`urllib`, `concurrent.futures`, `pathlib`, `logging`, `re`, `json`)
- Valid LLM API key (OpenAI or OpenRouter)

## Setup
1. Clone or download the script: `pocketflow_research.py`
2. Set environment variables:
   ```bash
   export OPENAI_API_KEY="sk-..."  # Or OPENROUTER_API_KEY="..."
   export LLM_MODEL="gpt-4o-mini"  # Optional: defaults to gpt-4o-mini
   ```

## Usage
```bash
python pocketflow_research.py
```
**Expected Output:**
```
🚀 Starting Deep Research Workflow for: 'Impact of microplastics on marine ecosystems'

2024-01-01 12:00:00 [INFO] ▶ Executing: planner (step 1)
2024-01-01 12:00:02 [INFO] Planner generated 3 queries.
2024-01-01 12:00:02 [INFO] ▶ Executing: searcher (step 2)
2024-01-01 12:00:03 [INFO] Searching: query 1...
2024-01-01 12:00:05 [INFO] Extracted 3 fact blocks into @notes buffer.
2024-01-01 12:00:05 [INFO] ▶ Executing: synthesizer (step 3)
2024-01-01 12:00:07 [INFO] Synthesis action: finalize
2024-01-01 12:00:07 [INFO] ▶ Executing: reporter (step 4)
2024-01-01 12:00:10 [INFO] Final report saved to research_Impact_of_microplastics_on_m.md

✅ Workflow Finished. Status: complete, Iterations: 0
📄 Report preview (first 300 chars): ...
```

## Workflow Logic (Step-by-Step)
1. **Initialization**: `PocketFlow` creates a shared context dictionary (`@notes`, `@loop_count`, `@topic`, etc.).
2. **PlannerNode**: Calls LLM with `plan_queries` prompt. Parses strict YAML to populate `@current_queries` (3 queries).
3. **SearcherNode (Map)**: Iterates over `@current_queries` in parallel (`ThreadPoolExecutor`). Calls `search_web` (DuckDuckGo API) then `extract_facts` (LLM) for each. Results appended to `@notes` buffer.
4. **SynthesizerNode (Reduce/Assess)**: Calls LLM with `assess_and_report` prompt. Evaluates `@notes` for gaps. Outputs YAML with `action: research` or `action: finalize`. Bypasses LLM if `@loop_count >= 2`.
5. **Routing & Loop**: `SynthesizerNode.post()` checks action. If `"research"` and iterations < 2, increments `@loop_count`, stores `@feedback`, and routes back to `planner`. If `"finalize"`, routes to `reporter`.
6. **ReporterNode**: Generates final Markdown if missing, writes to disk (`research_<topic>.md`), sets `@status=complete`, and halts the flow.
7. **Error Handling**: Network/LLM failures raise exceptions immediately, halting the workflow and logging the error. No silent failures.