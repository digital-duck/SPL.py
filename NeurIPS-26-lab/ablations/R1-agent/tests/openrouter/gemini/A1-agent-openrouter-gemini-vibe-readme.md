### Setup Instructions
1. **Install Dependencies**:
   ```bash
   pip install requests duckduckgo-search pyyaml
   ```
2. **PocketFlow**: Ensure `pocketflow.py` (the 100-line framework) is in your python path or the same directory.
3. **Environment Variable**:
   ```bash
   export OPENROUTER_API_KEY='your_api_key_here'
   ```

### Run Command
```bash
python your_filename.py "What is the current stock price of Nvidia and recent news?"
```

### Expected Output Pattern
1. `[DECISION] Action: search` - The LLM decides it needs more info.
2. `[SEARCH] Query: ...` - The DuckDuckGo tool is invoked.
3. Repeats until `[DECISION] Action: answer`.
4. `FINAL ANSWER:` - A synthesized report followed by `Status: done`.

### Logic Mapping Table

| Requirement Step | PocketFlow Implementation |
| :--- | :--- |
| **WHILE-loop pattern** | `search >> decide` (Circular edge) |
| **`decide_action`** | `DecideActionNode` (LLM + YAML parsing) |
| **`search_web`** | `SearchWebNode` (Side-effect: DDGS tool) |
| **`answer_question`** | `AnswerQuestionNode` (Final synthesis) |
| **`@context`** | `shared["context"]` (Accumulated state) |
| **EVALUATE branch** | `decide - "search" >> search` vs `decide - "answer" >> answer` |
| **YAML Fallback** | `robust_yaml_parse` function with block scalar retry |
| **Termination** | `shared["status"] = "done"` in `AnswerQuestionNode.post` |