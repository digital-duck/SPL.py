### Setup Instructions
1. **Python Environment**: Requires Python 3.8+.
2. **Dependencies**: Install the required packages:
   ```bash
   pip install pocketflow duckduckgo-search requests pyyaml
   ```
3. **API Key**: Export your OpenRouter API key in your environment:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

### Run Command
```bash
python research_agent.py "What are the latest breakthroughs in room-temperature superconductors?"
```
*(Optional)*: Add `--model anthropic/claude-3-5-sonnet-20241022` to change the LLM backend.

### Expected Output Pattern
```
2024-01-01 12:00:00 | INFO     | 🔍 Starting research for: 'What are the latest breakthroughs...'
2024-01-01 12:00:02 | INFO     | DecideNode -> Action: search | Query: latest room-temperature superconductor research
2024-01-01 12:00:03 | INFO     | Searching web for: 'latest room-temperature superconductor research'
2024-01-01 12:00:05 | INFO     | SearchNode -> Context updated (1240 chars). Looping back to Decide.
2024-01-01 12:00:08 | INFO     | DecideNode -> Action: answer | Query: N/A
2024-01-01 12:00:12 | INFO     | AnswerNode -> Synthesis complete. Workflow terminating.

============================================================
✅ RESEARCH COMPLETE
📊 Status: done
📝 Answer:
Recent studies indicate...
============================================================
```

### Logical Step to Target Mapping

| Logical Step                     | Target Implementation (PocketFlow)                          |
|----------------------------------|-------------------------------------------------------------|
| `decide_action` chain-of-thought | `DecideNode.exec()` calls `call_llm()` with reasoning prompt |
| YAML parsing + block-scalar retry| `parse_yaml()` with `try/except` and `|` string manipulation |
| `search_web` tool invocation     | `SearchNode.exec()` wraps `duckduckgo_search.DDGS`          |
| Accumulate results in `@context` | `SearchNode.post()` appends to `shared["context"]`          |
| WHILE loop pattern               | `search >> decide` (default back-edge) + `decide - "search"`|
| Conditional branch               | `decide - "search" >> search`, `decide - "answer" >> answer`|
| `answer_question` synthesis      | `AnswerNode.exec()` prompts LLM to synthesize `shared["context"]` |
| Termination & RETURN status      | `AnswerNode.post()` sets `shared["status"]="done"`, returns `"done"` |
| CLI entry & config               | `argparse` in `__main__` block, `shared["model"]` injection |
| Shared state management          | `shared` dict passed implicitly via `prep()`/`post()` hooks |