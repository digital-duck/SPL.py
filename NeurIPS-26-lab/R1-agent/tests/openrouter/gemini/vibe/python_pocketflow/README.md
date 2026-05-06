# PocketFlow Research Agent

This is a minimalist ETL-style LLM orchestration agent that uses a recursive research pattern. It autonomously decides whether to search the web for more information or synthesize a final answer based on the current context.

## Requirements
- Python 3.8+
- `requests`
- `pyyaml`
- `duckduckgo-search`

```bash
pip install requests pyyaml duckduckgo-search
```

## Setup
Set the following environment variables:
- `OPENROUTER_API_KEY`: Your API key for OpenRouter (or OpenAI).
- `LLM_MODEL`: (Optional) The model to use. Defaults to `meta-llama/llama-3.1-8b-instruct`.
- `LLM_BASE_URL`: (Optional) Custom API endpoint. Defaults to OpenRouter.

## Usage
Run the script directly:
```bash
python flow.py
```

## Workflow Logic
1. **Initialize State**: Sets up the question and an empty context.
2. **DecideAction**: The LLM evaluates the question against gathered context and outputs a YAML decision (either `search` or `answer`).
3. **Branching (Evaluate)**:
    - If **search**: The `SearchWeb` node executes a DuckDuckGo search, appends the results to the context, and the loop repeats.
    - If **answer**: The loop terminates.
4. **AnswerQuestion**: The LLM synthesizes all gathered research into a final polished response.
5. **Termination**: The workflow returns the final answer.