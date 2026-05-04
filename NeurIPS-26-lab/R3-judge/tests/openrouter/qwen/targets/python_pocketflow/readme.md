# Setup & Run Instructions for `S4-judge-openrouter-qwen`

## Setup
1. Ensure Python 3.8+ is installed.
2. Set your OpenRouter API key to enable real LLM calls:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```
3. (Optional) Override the default model:
   ```bash
   export LLM_MODEL="qwen/qwen3.6-plus"
   ```

## Run Command
```bash
cd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/targets/python_pocketflow
DT=$(date +%Y%m%d_%H%M%S) && python S4-judge-openrouter-qwen.py \
  --initial-state "a minimalist LLM orchestration framework" \
  2>&1 | tee S4-judge-openrouter-qwen-run-${DT}.md
```

## Expected Output Pattern
If `OPENROUTER_API_KEY` is set, the script will hit OpenRouter with Qwen and return the refined description. If unset, it uses a built-in deterministic mock to guarantee successful execution:
```json
{
  "final_result": "This is a mock high-quality description generated for the provided state.",
  "status": "pass"
}
```

## SPL to Python/PocketFlow Mapping Table

| SPL Construct | Python / PocketFlow Equivalent | Notes |
|:---|:---|:---|
| `CREATE FUNCTION ... RETURNS TEXT AS $$ ... $$;` | `def func_name(...) -> str:` with formatted prompt string | Standard Python function acting as an ETL Extract/Transform node. |
| `WORKFLOW description_evaluation_loop` | `def S3_judge_openrouter_qwen(...) -> Dict[str, Any]:` | Top-level orchestrator function managing state and control flow. |
| `INPUT @initial_state STRING := "default"` | `initial_state: str = "default"` | Exact signature match with type hint and default. |
| `OUTPUT @final_result STRING` | `return {"final_result": ..., "status": ...}` | Structured dictionary return matching ETL payload conventions. |
| `@var := value;` | `context["var"] = value` / local assignment | State tracking via dictionary/local vars for mutability. |
| `WHILE @attempts <= 2 AND @status = "retry" DO` | `while attempts <= 2 and status == "retry":` | Direct Python loop translation preserving condition semantics. |
| `GENERATE ... INTO @var;` | `@var = function_call(...)` | Synchronous LLM invocation mapped to Python assignment. |
| `EVALUATE @verdict WHEN contains("pass") THEN` | `if "pass" in verdict.lower():` | Case-insensitive substring check matching `contains()` behavior. |
| `ELSE ... END;` | `else: ...` | Standard Python conditional branching. |
| `RETURN ... WITH ...;` | `return {"final_result": ..., "status": ...}` | Multi-value payload return typical in minimalist ETL frameworks. |
