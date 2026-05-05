# Iterative Research Agent (PocketFlow + OpenRouter)

This folder contains an implementation of an iterative research agent using the PocketFlow framework and OpenRouter LLMs.

## Overview

The agent follows a WHILE-loop pattern:
1. **Decide**: Analyze the question and accumulated context. Decide whether to search for more information or generate the final answer.
2. **Search**: If "search" is chosen, perform a DuckDuckGo search and update the context.
3. **Answer**: If "answer" is chosen (or max iterations reached), synthesize the final response.

## Files

- `A1-agent-openrouter-claude-vibe.py`: The main Python script implementing the agent.

## Requirements

Ensure you have the following installed:
- `pocketflow`
- `duckduckgo_search`
- `requests`
- `pyyaml`

You can install them via:
```bash
pip install pocketflow duckduckgo-search requests pyyaml
```

## Setup

Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your_api_key_here'
```

## Usage

Run the agent with a question:
```bash
python A1-agent-openrouter-claude-vibe.py "What are the latest breakthroughs in fusion energy?"
```

Options:
- `--model`: Specify the OpenRouter model (default: `google/gemini-3-flash-preview`).
- `--max-iterations`: Set maximum search loops (default: 3).
- `--verbose`: Enable debug logging.

Example:
```bash
python A1-agent-openrouter-claude-vibe.py "Latest AI news from NeurIPS 2026" --model anthropic/claude-3-opus --max-iterations 5
```
