### Overview
This implementation defines a ReAct-style autonomous research agent using **PocketFlow**, a minimalist ETL-style LLM orchestration framework. The workflow iteratively decides between performing a web search to close knowledge gaps or synthesizing a final comprehensive answer. It features robust YAML parsing with automatic heuristic repair, shared state management across iterations, and clean CLI/file output.

### Requirements
```bash
pip install pocketflow openai duckduckgo-search pyyaml
```
* `pocketflow`: Core orchestration graph runner
* `openai`: LLM API client (compatible with OpenRouter & OpenAI)
* `duckduckgo-search`: External knowledge retrieval tool
* `pyyaml`: Structured prompt output parsing

### Setup (Environment Variables)
Export the following before running:
```bash
export OPENROUTER_API_KEY="your_openrouter_key_here"
# OR
export OPENAI_API_KEY="your_openai_key_here"

# Optional: Swap LLM provider/model
export LLM_MODEL="openai/gpt-4o-mini"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

### Usage
Run directly from the terminal:
```bash
python research_agent.py "How does quantum error correction work in topological qubits?"
```
**Expected Output:**
```
[INFO] Starting ReAct research agent for: 'How does quantum error correction work in topological qubits?'
[INFO] Routing: SEARCH -> topological qubits quantum error correction mechanisms 2024
[INFO] Executing web search for: 'topological qubits quantum error correction mechanisms 2024'
[INFO] Accumulated context updated. Looping back to decision phase.
...
[INFO] Routing: ANSWER
[INFO] Generating final synthesis.
[INFO] Workflow complete. Returning status: done

============================================================
✅ RESEARCH COMPLETE
============================================================
[Synthesized answer text appears here...]
============================================================

📄 Output persisted to research_output.txt
```

### Workflow Logic (Step-by-Step)
1. **Initialization**: Shared state dictionary is seeded with the user's question. `Flow` starts at `decide_action`.
2. **DECIDE (CREATE FUNCTION)**: The LLM receives a structured prompt containing the question and current context. It must output YAML with an `action` (`search` or `answer`).
3. **EVALUATE / EXCEPTION HANDLING**: `DecideAction.post()` parses the YAML. If malformed, `parse_yaml_safely()` applies regex-based block-scalar repairs and retries once before falling back to key extraction.
4. **BRANCH (IF search)**: Control routes to `SearchWeb`. The search query is extracted from the LLM response.
5. **CALL (External Tool)**: `SearchWeb.exec()` hits DuckDuckGo, fetches snippets, and returns them.
6. **CONTEXT UPDATE & WHILE LOOP**: `SearchWeb.post()` appends results to the shared `@context` and returns `"decide_action"`, forming an implicit `WHILE` loop.
7. **BRANCH (IF answer)**: Control routes to `AnswerQuestion`. The synthesis prompt injects the original question and accumulated context.
8. **RETURN**: `AnswerQuestion.post()` stores the final text in `@answer`, prints it to CLI, and returns `"done"`, halting the graph.
9. **Persistence**: The `__main__` block writes the final answer to `research_output.txt`.