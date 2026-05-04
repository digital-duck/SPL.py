# S3-agent-openrouter-qwen Implementation Guide

## Setup Instructions
1. Ensure Python 3.8+ is installed.
2. Set your OpenRouter API key in the environment:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```
3. (Optional) Override the default model:
   ```bash
   export LLM_MODEL="qwen/qwen-2.5-coder-32b-instruct"
   ```

## Run Command
```bash
python S3_agent_openrouter_qwen.py
```

## Expected Output Pattern
The script will output a JSON object containing the workflow status and the synthesized final response:
```json
{
  "status": "complete",
  "final_response": "[LLM-generated answer based on accumulated search context...]"
}
```
*Note: If `OPENROUTER_API_KEY` is unset, the pipeline runs in mock mode and returns `[MOCK_LLM_RESPONSE]` to demonstrate structural correctness.*

## SPL to Python/PocketFlow Mapping Table

| SPL Construct | Python/PocketFlow Equivalent |
| :--- | :--- |
| `CREATE FUNCTION ... RETURNS TEXT AS $$ ... $$;` | Python functions returning prompt strings (e.g., `prompt_decide_action`) |
| `WORKFLOW DecisionAgent INPUT ... OUTPUT ...` | Class `S3AgentOpenRouterQwen` with `run(user_query: str) -> Dict` |
| `@variable := value;` | Dictionary context assignment: `ctx["@variable"] = value` |
| `GENERATE func(...) INTO @var;` | `ctx["@var"] = generate(prompt_func(...))` (LLM invocation layer) |
| `WHILE condition DO ... END;` | Standard Python `while condition:` loop |
| `EVALUATE var WHEN contains("x") THEN ... ELSE ... END;` | Python `if "x" in ctx["@var"].lower(): ... else: ...` |
| `CALL sub_workflow(...) INTO @var;` | Direct function invocation: `ctx["@var"] = web_search(...)` |
| `RETURN @var WITH status = "...";` | `return {"status": "...", "final_response": ctx["@var"]}` |