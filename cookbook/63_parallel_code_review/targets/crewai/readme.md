## Recipe 63 — Parallel Code Review (CrewAI)

Compiled from `parallel_code_review.spl` by `splc`.  
Three independent LLM agents (style, security, tests) run concurrently via CrewAI's `async_execution` mechanism, then a fourth merge agent consolidates their outputs into a single prioritised report.

---

### Setup

```bash
# 1. Install dependencies
pip install crewai "crewai[tools]"

# 2. Ensure Ollama is running with your chosen model
ollama pull gemma4          # or gemma3, llama3.2, etc.

# 3. (Optional) Override the Ollama base URL
export OLLAMA_BASE_URL=http://192.168.0.184:11434
```

---

### Run

```bash
# Inline snippet
python parallel_code_review.py \
    --code "def add(a, b): return a - b" \
    --lang python \
    --review-model gemma4

# From a file
python parallel_code_review.py \
    --file my_module.py \
    --lang python \
    --review-model gemma3

# Minimal (uses all defaults)
python parallel_code_review.py --code "print('hello')"
```

Equivalent SPL invocation for cross-reference:

```
spl3 run parallel_code_review.spl \
    code="def add(a, b): return a - b" \
    lang=python review_model=gemma4
```

---

### Expected output pattern

```
2026-04-20 12:00:00 [INFO] [parallel_code_review] starting 3-way parallel review | lang=python review_model=gemma4
2026-04-20 12:00:08 [INFO] [parallel_code_review] parallel checks complete — merging into report
2026-04-20 12:00:11 [INFO] [parallel_code_review] done | report_len=843

========================================================================
CONSOLIDATED CODE REVIEW REPORT
========================================================================

## Action Items
1. [CRITICAL] Function `add` subtracts instead of adding — change `a - b` to `a + b`
...

## Test Coverage
```python
def test_add_positive(): ...
```

## Summary
The code contains a critical logic bug and is not production-ready...
```

---

### SPL → CrewAI construct map

| SPL construct | CrewAI equivalent | Location in file |
|---|---|---|
| `IMPORT '00_style_review'` | `_build_style_review()` — returns `(Agent, Task)` | `_build_style_review` |
| `IMPORT '01_security_audit'` | `_build_security_audit()` — returns `(Agent, Task)` | `_build_security_audit` |
| `IMPORT '02_test_generator'` | `_build_test_generator()` — returns `(Agent, Task)` | `_build_test_generator` |
| `CREATE FUNCTION merge_reviews(...)` | `_build_merge()` — encodes prompt as `Task.description` | `_build_merge` |
| `WORKFLOW parallel_code_review INPUT:/OUTPUT:` | `parallel_code_review(code, lang, review_model, log_dir) -> str` | `parallel_code_review` |
| `CALL PARALLEL ... END` | Three `Task` instances with `async_execution=True` | `_build_*` builders |
| Fan-in after `CALL PARALLEL` | `Task(context=[style_task, security_task, test_task])` | `_build_merge` |
| `GENERATE ... WITH OUTPUT BUDGET 1024 TOKENS USING MODEL @review_model` | `LLM(max_tokens=1024)` on the merge agent's dedicated LLM | `parallel_code_review` → `merge_llm` |
| `LOGGING ... LEVEL INFO/ERROR/WARN` | `logger.info / logger.error / logger.warning` | throughout `parallel_code_review` |
| `COMMIT @report` | `return report` | `parallel_code_review` |
| `EXCEPTION WHEN ModelUnavailable` | `except (ConnectionError, OSError)` | `parallel_code_review` |
| `EXCEPTION WHEN BudgetExceeded` | `except Exception` + token-keyword check on message | `parallel_code_review` |
| `RETURN '...' WITH status = 'failed'` | `return "[ERROR] Model unavailable."` | `parallel_code_review` |
| `COMMIT @report WITH status = 'truncated'` | `return report or "[TRUNCATED] ..."` | `parallel_code_review` |