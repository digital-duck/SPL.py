### Setup Instructions
1. Install Python 3.8+.
2. Install the `requests` library: `pip install requests`.
3. Obtain an OpenRouter API Key.
4. Set your environment variable: `export OPENROUTER_API_KEY='your_key_here'`.

### Run Command
```bash
python S3-judge-openrouter-gemini.py
```

### Expected Output Pattern
The script returns a dictionary containing the generated content, the completion status, and metadata regarding the number of attempts taken to pass the evaluation logic.

### SPL to PocketFlow Mapping

| SPL Construct | PocketFlow (Python) Implementation |
|:---|:---|
| `CREATE FUNCTION` | Class methods with LLM prompt templates and API calls. |
| `WORKFLOW` | A primary `run_workflow` method within the class. |
| `@variable := value` | Local variable assignment within the method scope. |
| `WHILE ... DO` | Standard Python `while` loop structure. |
| `GENERATE func()` | Method call to the LLM-wrapped function. |
| `EVALUATE ... WHEN` | Python `if/elif/else` conditional logic. |
| `RETURN ... WITH` | Returns a dictionary containing the payload and status. |
| `topic STRING` | Type-hinted method arguments. |