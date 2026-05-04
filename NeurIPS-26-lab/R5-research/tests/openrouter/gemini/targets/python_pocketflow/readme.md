### Setup Instructions
1. Install Python 3.9+.
2. Install `requests` library: `pip install requests`.
3. Set your OpenRouter API Key in the environment:
   `export OPENROUTER_API_KEY='your_key_here'`

### Run Command
```bash
python S3-research-openrouter-gemini.py
```

### Expected Output Pattern
The script will iterate twice through the research loop, querying the Gemini model via OpenRouter. It will generate search queries, simulate web results, extract notes, and finally write a file named `report.txt` containing a Markdown-formatted research paper.

### SPL to PocketFlow Mapping Table

| SPL Construct | PocketFlow / Python Implementation |
|:---|:---|
| `CREATE FUNCTION` | Python function with f-string prompt templates |
| `WORKFLOW` | Class inheriting from `Workflow` (or standard Python class) |
| `GENERATE func() INTO @var` | `var = func_fn(...)` |
| `CALL tool() INTO @var` | `var = tool_fn(...)` |
| `WHILE @cond DO` | `while loop_cond:` |
| `EVALUATE ... WHEN` | `if ... in status:` |
| `INPUT / OUTPUT` | `__init__` arguments and `run()` return dictionary |
| `@var := value` | Standard Python variable assignment |