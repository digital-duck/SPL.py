# Evaluator-Optimizer Product Marketing Workflow

This project implements an iterative LLM orchestration pattern using a minimalist PocketFlow-style ETL architecture. It uses a **Generator** to create content and a **Judge** to evaluate it against quality standards, looping until the content passes or maximum attempts are reached.

### Requirements
- Python 3.8+
- `requests`
- `pyyaml`

```bash
pip install requests pyyaml
```

### Setup
Set your API key and preferred model as environment variables:
```bash
export OPENROUTER_API_KEY='your_api_key_here'
export LLM_MODEL='meta-llama/llama-3-70b-instruct' # Optional
```

### Usage
Run the script directly:
```bash
python your_file_name.py
```

### Workflow Logic
1. **Generator Node**: Takes the user `task` and any previous `feedback`. It generates a marketing description and wraps it in a YAML block.
2. **Judge Node**: Receives the draft and evaluates it. It assigns a score (1-10) and provides a verdict (`PASS`/`FAIL`) along with constructive feedback.
3. **Control Flow**: 
   - If the score is $\ge 7$ or the workflow has attempted 3 times, it terminates.
   - If the score is $< 7$ and attempts are $< 3$, it loops back to the **Generator** with the new feedback.
4. **Final Output**: The workflow returns the highest quality draft produced within the cycle.