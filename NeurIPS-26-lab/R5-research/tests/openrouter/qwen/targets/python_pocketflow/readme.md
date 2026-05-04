# S4-research-openrouter-qwen Workflow

A Python PocketFlow (minimalist ETL-style LLM orchestration) implementation compiled from `S3-research-openrouter-qwen.spl`.

## Setup Instructions
1. Ensure Python 3.8+ is installed.
2. Install web search dependency:
   ```bash
   pip install ddgs duckduckgo_search
   ```
3. Set your OpenRouter API key for real LLM responses:
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```
4. (Optional) Override the default model:
   ```bash
   export LLM_MODEL="qwen/qwen3.6-plus"
   ```

## Run Command
```bash
cd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/targets/python_pocketflow
DT=$(date +%Y%m%d_%H%M%S) && python S4-research-openrouter-qwen.py \
  --topic "PocketFlow LLM orchestration framework" \
  2>&1 | tee S4-research-openrouter-qwen-run-${DT}.md
```

## Expected Output Pattern
The script will:
1. Log each ETL step (EXTRACT -> TRANSFORM -> GENERATE -> LOAD).
2. Execute 2 iterations of query generation, web search, and fact extraction.
3. Synthesize aggregated notes into a final report.
4. Save the report to `report.txt` in the working directory.
5. Print the final report to stdout.

## SPL to Python/PocketFlow Mapping Table

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---------------|--------------------------------|-------|
| `CREATE FUNCTION ... RETURNS TEXT AS $$ ... $$` | Python function returning formatted prompt strings (`_plan_queries_prompt`, etc.) | Prompts are isolated for maintainability and ETL pipeline clarity. |
| `WORKFLOW research_workflow` | Class `S3ResearchOpenrouterQwenFlow` with `run()` method | Acts as the orchestrator, maintaining state dictionary as shared memory. |
| `INPUT @topic STRING := "default_topic"` | `def run(self, topic: str = "default_topic") -> str:` | Exact name, type, and default preserved. Type hinting used for clarity. |
| `OUTPUT @report STRING` | Return type annotation `-> str` + `return self.state["report"]` | Matches SPL output contract. |
| `@var := value;` | `self.state["var"] = value` | State dictionary replaces SPL variable scope for ETL data passing. |
| `WHILE <cond> DO ... END` | `while <cond>:` standard Python loop | Exact boolean logic preserved (`loop_count < 2 and iteration < 3`). |
| `GENERATE <func>(@arg) INTO @out` | `self.state["out"] = _llm_generate(prompt)` | Maps to ETL "Transform" step using OpenRouter/Qwen API. |
| `CALL search_web(...) INTO ...` | `self.state["web_results"] = _search_web(...)` | Maps to ETL "Extract" step via ddgs DuckDuckGo search. |
| `@notes := @notes + @extracted_facts;` | `self.state["notes"] += ...` | Standard string concatenation in Python. |
| `CALL write_file("report.txt", @report);` | `_write_file("report.txt", self.state["report"])` | Maps to ETL "Load" step using standard file I/O. |
| `RETURN @report WITH status = "complete"` | `logging.info(...); return self.state["report"]` | Status logged, final value returned to caller. |
