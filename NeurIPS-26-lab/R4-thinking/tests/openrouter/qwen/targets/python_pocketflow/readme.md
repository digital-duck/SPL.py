# S4-thinking-openrouter-qwen

A minimalist ETL-style LLM orchestration workflow implementing a Chain-of-Thought reasoning loop using OpenRouter's Qwen model.

## Setup Instructions
1. Ensure Python 3.9+ is installed.
2. Set your OpenRouter API key as an environment variable:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```
3. (Optional) Override the default model:
   ```bash
   export LLM_MODEL="qwen/qwen3.6-plus"
   ```
4. No additional Python packages are required (uses only standard library `urllib`, `json`, `os`).

## Run Command
```bash
cd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/targets/python_pocketflow
DT=$(date +%Y%m%d_%H%M%S) && python S4-thinking-openrouter-qwen.py \
  --problem "How can we reduce latency in transformer-based NLP models?" \
  2>&1 | tee S4-thinking-openrouter-qwen-run-${DT}.md
```

## Expected Output Pattern
The script will:
1. Initialize the prompt state.
2. Loop up to 3 times, sending the context to the Qwen model via OpenRouter.
3. Evaluate responses for `YAML_ERROR`, `CONTINUE: true`, or a final solution.
4. Save the extracted result to `chain_of_thought.md`.
5. Print the final extracted solution to stdout.

Example stdout:
```
Extract Final Solution: step_1: profile_model
step_2: apply_quantization
FINAL: true
```

## SPL to Python/PocketFlow Mapping Table

| SPL Construct | Python / PocketFlow Equivalent | Notes |
|---------------|--------------------------------|-------|
| `CREATE FUNCTION assemble_prompt(...) RETURNS TEXT` | `def assemble_prompt(state, plan): return f"..."` | Standard Python function returning formatted prompt string. |
| `WORKFLOW ChainOfThoughtLoop` | `class S3ThinkingOpenrouterQwen: def run(...)` | Class encapsulates the workflow state and execution steps. |
| `INPUT @problem STRING, @plan STRING := "default_plan"` | `def run(self, problem: str, plan: str = "default_plan")` | Python type hints and default values match SPL exactly. |
| `OUTPUT @final_result STRING` | `-> str` return type + explicit `return final_result` | Matches SPL output contract. |
| `@var := "value";` | `var = value` | Direct Python variable assignment. |
| `WHILE @cond = "true" AND @iteration < 3 DO` | `while next_thought_needed == "true" and iteration < 3:` | Direct Python `while` loop preserving termination conditions. |
| `GENERATE assemble_prompt(...) INTO @llm_output` | `llm_output = self._call_llm(assemble_prompt(...))` | HTTP POST to OpenRouter API, parses JSON response. |
| `EVALUATE @llm_output WHEN contains("X") THEN ... ELSE ... END` | `if "X" in llm_output: ... else: ...` | Native Python string containment check with `if/elif/else`. |
| `CALL write_file("chain_of_thought.md", @final_result)` | `with open(...) as f: f.write(...)` | Standard Python file I/O context manager. |
| `RETURN @final_result WITH status = "complete"` | `return final_result` | Python return statement. Status is implicit in successful execution. |
