## Setup Instructions
1. **Environment**: Ensure you have Python 3.9+ installed.
2. **Dependencies**:
   ```bash
   pip install requests PyYAML
   ```
3. **API Key**: 
   - Set an environment variable `OPENROUTER_API_KEY`.
   - The script uses `google/gemini-2.0-flash-lite-preview-02-05:free` via OpenRouter.
4. **Execution**:
   ```bash
   python your_file_name.py
   ```

## Mapping Table

| SPL Construct | Python Equivalent | Implementation Detail |
| :--- | :--- | :--- |
| **WORKFLOW** | `create_research_flow()` | Orchestrates node instances and their loop connections. |
| **CREATE FUNCTION** | `DecideAction.exec` | Encapsulates the prompt logic for decision making. |
| **GENERATE** | `call_llm(prompt)` | Sends context to Gemini and returns text. |
| **CALL** | `search_web_duckduckgo` | A side-effect function simulating external tool access. |
| **EVALUATE** | `if decision.get("action") == "search"` | Python conditional logic inside the node's `exec`. |
| **WHILE** | `search.decide_node = decide` | Functional loop created by nodes referencing each other. |
| **RETURN** | `final_state["answer"]` | The extraction of the final synthesized string from state. |
| **@vars** | `shared` dictionary | Dictionary passed through every `exec` call to persist state. |
```