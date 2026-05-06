### Overview
This project implements a **Chain-of-Thought (CoT) reasoning workflow** using a minimalist PocketFlow-style ETL orchestration pattern. It externalizes planning, execution, and self-evaluation into a stateful iterative loop, enabling standard instruction-following LLMs to solve complex quantitative or logical problems without relying on proprietary extended-thinking endpoints.

### Requirements
```bash
pip install pyyaml
```
*(Note: The orchestration core and LLM client use only Python standard libraries. `pyyaml` is required for structured prompt parsing and state serialization.)*

### Setup
1. Set your LLM API key environment variable:
   ```bash
   export OPENROUTER_API_KEY="your_key_here"
   # OR
   export OPENAI_API_KEY="your_key_here"
   ```
2. Optionally configure the model and base URL:
   ```bash
   export LLM_MODEL="anthropic/claude-3-5-sonnet-20240620"
   export LLM_BASE_URL="https://openrouter.ai/api/v1/chat/completions"
   ```

### Usage
Run the script directly:
```bash
python cot_workflow.py
```
**Expected Output:**
```
🚀 Initializing Chain-of-Thought Workflow...
🔄 Entering node: ChainOfThought
📡 Calling LLM...

[Step 1] Executed: ...
  - [Done] Fill 5-gallon jug...
  - [Pending] Transfer water...
🔄 Entering node: ChainOfThought
📡 Calling LLM...

[Step 2] Executed: ...
  - [Done] Transfer 3 gallons...
  - [Done] Empty 3-gallon jug...
✅ EVALUATE: next_thought_needed is False. Terminating loop.
💾 Solution persisted to cot_solution.yaml
🏁 WORKFLOW COMPLETE
Status: solved
Iterations: 3
Final Solution:
[Final reasoning trace...]
==================================================
```

### Workflow Logic (Step-by-Step)
1. **State Initialization**: The `__main__` block seeds the `shared` dictionary with the problem statement, empty history, and metadata.
2. **PREP Phase**: `ChainOfThoughtNode.prep()` injects the problem, accumulated thoughts, and current plan status into strict YAML-enforced prompt templates.
3. **EXEC Phase**: `call_llm()` sends the prompt to the configured API endpoint and captures the raw string response.
4. **POST & EVALUATE**:
   - Parses the YAML block. An `EXCEPTION` handler catches parsing/schema failures, halts the loop safely, and marks status as `error`.
   - Appends the new thinking step to history and updates the hierarchical plan in `shared` state.
   - Streams progress to stdout.
   - Checks `next_thought_needed`. If `true`, returns `"continue"` to trigger the self-loop (`cot_node - "continue" >> cot_node`). If `false`, returns `"end"`.
5. **TERMINATION**: On `"end"`, the `Flow` breaks the loop, writes the complete state to `cot_solution.yaml` (if specified), and returns the final `solution` and `iterations` count.