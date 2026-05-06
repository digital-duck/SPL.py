## Overview
This implementation realizes an evaluator-optimizer pattern using a minimalist PocketFlow-style orchestrator. It automatically generates a product description, evaluates it against clarity/persuasiveness metrics, and iteratively refines the draft using LLM feedback until a quality threshold is met or a maximum attempt limit is reached.

## Requirements
```bash
pip install pyyaml httpx
```
*(Uses `httpx` for lightweight, provider-agnostic HTTP calls to OpenAI-compatible endpoints. `pyyaml` handles structured response parsing.)*

## Setup
Set the following environment variables before execution:
```bash
export OPENROUTER_API_KEY="your-key-here"  # or OPENAI_API_KEY
export LLM_MODEL="anthropic/claude-3-haiku-20240307" # or any OpenAI-compatible model
export OPENAI_BASE_URL="https://openrouter.ai/api/v1" # Optional: custom base URL
export SCORE_THRESHOLD="7" # Optional: default 7
export MAX_ATTEMPTS="3"    # Optional: default 3
```

## Usage
Run the script directly:
```bash
python workflow.py
```

### Expected Output
```
Starting workflow for: An ergonomic bamboo standing desk converter with smooth dual-monitor lifting mechanism.

=== WORKFLOW OUTPUT ===
Final Score : 8
Attempts    : 2
Description : Elevate your workspace with our ergonomic bamboo standing desk converter, engineered for effortless height adjustment and dual-monitor stability. Crafted from sustainable bamboo, its whisper-quiet lifting mechanism transforms sitting into standing in seconds. Boost your posture, energy, and productivity without compromising office aesthetics.
Saved to    : result.yaml
```

## Workflow Logic
1. **Initialization**: Shared state is seeded with the input `@task`. `@attempts` and `@feedback` default to 0 and empty.
2. **GENERATE (Generator)**: Calls `call_llm` with a prompt enforcing a 2-3 sentence limit and YAML output. If `@feedback` exists from a prior cycle, it's appended to guide revision. Result is stored in `@draft`.
3. **EVALUATE (Judge)**: Sends `@draft` to the LLM with a strict YAML schema requesting `score` (1-10), `verdict` (PASS/FAIL), and `feedback`. Increments `@attempts`.
4. **BRANCHING**:
   - If `score >= threshold` or `verdict == PASS`: Saves `@draft` to `@final_description`, returns `pass`, and terminates.
   - If threshold not met AND `@attempts < MAX_ATTEMPTS`: Returns `fail`.
5. **WHILE LOOP**: The `PocketFlow` orchestrator routes `fail` back to the Generator node. The cycle repeats.
6. **TERMINATION**: If `@attempts` reaches the limit, the current draft is accepted as final, `pass` is returned, and state is persisted to `result.yaml`. Network/parsing errors trigger implicit fallbacks to prevent pipeline crashes.