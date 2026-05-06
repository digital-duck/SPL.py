# PocketFlow Chain-of-Thought (CoT) Orchestrator

This project implements a structured Chain-of-Thought reasoning workflow using a minimalist ETL-style orchestration pattern (PocketFlow). It forces an LLM to maintain an externalized plan, evaluate its own previous steps, and iterate until a complex problem is solved.

### Requirements
- Python 3.8+
- `pip install PyYAML requests`

### Setup
Set your API keys and preferred model as environment variables:
```bash
export OPENROUTER_API_KEY='your_key_here'
# Optional settings:
export LLM_MODEL='meta-llama/llama-3-70b-instruct'
export LLM_BASE_URL='https://openrouter.ai/api/v1'
```

### Usage
Run the script directly:
```bash
python main.py
```

### Workflow Logic
1. **Initialize**: The `shared` state is populated with the `problem` and an initial `planning` list.
2. **Execution Node (`ChainOfThoughtNode`)**:
   - **Prep**: Increments the thought counter.
   - **Exec**: Constructs a prompt containing the problem, full history of thoughts, and the current plan. It calls the LLM and expects a YAML response.
   - **YAML Parsing**: Extracts `current_thinking`, the updated `planning` list, and the `next_thought_needed` flag.
   - **Post**: Checks the `next_thought_needed` flag. If `True`, it returns `"continue"`; otherwise, it returns `"done"`.
3. **Looping**: The Flow controller uses the `"continue"` transition to route back to the same node, creating a `WHILE` loop.
4. **Termination**: When the LLM decides the task is complete (usually after a "Conclusion" step), the loop breaks and the final answer is displayed.