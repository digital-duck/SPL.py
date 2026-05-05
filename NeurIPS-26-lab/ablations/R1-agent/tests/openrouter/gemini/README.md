# Gemini Research Agent (PocketFlow + OpenRouter)

This folder contains an iterative research agent using the PocketFlow framework and Gemini models via OpenRouter.

## Overview

The agent uses a loop to gather information:
1.  **Decide**: Uses Gemini to decide whether to search or answer.
2.  **Search**: Performs DuckDuckGo searches to accumulate context.
3.  **Answer**: Synthesizes the final answer once enough information is gathered.

## Files

- `A1-agent-openrouter-gemini-vibe.py`: The main Python script.

## Setup

1.  Install dependencies:
    ```bash
    pip install pocketflow duckduckgo-search requests pyyaml
    ```
2.  Set OpenRouter API key:
    ```bash
    export OPENROUTER_API_KEY='your_api_key'
    ```

## Usage

```bash
python A1-agent-openrouter-gemini-vibe.py "Your research question"
```

Default question: "What are the latest breakthroughs in room-temperature superconductivity as of 2024?"
