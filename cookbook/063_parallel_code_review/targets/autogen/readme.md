# Parallel Code Review — AutoGen

AutoGen implementation of `parallel_code_review.spl` (Recipe 63).  
Runs three independent LLM agents concurrently (style review, security audit, test generation) then merges their outputs into a single prioritised report.

---

## Setup

```bash
# 1. Create/activate environment
conda activate spl123

# 2. Install dependencies
pip install pyautogen openai click

# 3. Ensure Ollama is running with your target model
ollama pull gemma3        # or gemma3, mistral, etc.
ollama serve              # if not already running as a service

# 4. (Optional) override the Ollama endpoint
export OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

## Run

```bash
# Minimal — review a one-liner
python code_review_autogen.py --code "def add(a, b): return a - b"

# Full flags
python code_review_autogen.py \
    --code code_review_autogen.py \
    --lang python \
    --review-model gemma3


```

---

## Expected output pattern

```
2026-04-20 12:00:00 [INFO] [parallel_code_review] starting 3-way parallel review | lang=python review_model=gemma4
2026-04-20 12:00:00 [INFO] [parallel_code_review] parallel checks complete — merging into report
2026-04-20 12:00:01 [INFO] [parallel_code_review] done | report_len=843

## Action Items
1. [CRITICAL] ...
2. [MODERATE] ...
...

## Test Coverage
```python
...
```

## Summary
...
```

The three parallel agents fire simultaneously; total wall-clock time ≈ max(style, security, test) rather than their sum.

---

## SPL → AutoGen construct mapping

| SPL construct | AutoGen equivalent | File location |
|---|---|---|
| `IMPORT '00_style_review'` | `async def style_review(...)` | lines 47–56 |
| `IMPORT '01_security_audit'` | `async def security_audit(...)` | lines 60–70 |
| `IMPORT '02_test_generator'` | `async def test_generator(...)` | lines 74–85 |
| `CREATE FUNCTION merge_reviews(...) AS $$ … $$` | `_MERGE_REVIEWS_TEMPLATE` string + `_merge_reviews()` | lines 89–120 |
| `WORKFLOW parallel_code_review` + `INPUT:` | `async def parallel_code_review(code, lang, review_model, log_dir)` | line 124 |
| `OUTPUT: @report TEXT` | function return type `-> str`, `report: str = ""` | line 138 |
| `LOGGING … LEVEL INFO` | `log.info(...)` | lines 143, 167, 173 |
| `CALL PARALLEL … END` | `asyncio.gather(style_review(...), security_audit(...), test_generator(...))` | lines 156–162 |
| `GENERATE merge_reviews(…) WITH OUTPUT BUDGET 1024 TOKENS USING MODEL @review_model INTO @report` | `_merge_reviews(..., max_tokens=1024)` | lines 164–170 |
| `COMMIT @report` | `return report` | line 174 |
| `EXCEPTION WHEN ModelUnavailable` | `except (openai.APIConnectionError, openai.AuthenticationError)` | line 177 |
| `RETURN '…' WITH status = 'failed'` | `return "[ERROR] Model unavailable."` | line 184 |
| `EXCEPTION WHEN BudgetExceeded` | `except openai.BadRequestError` (filtered on context/token message) | line 187 |
| `COMMIT @report WITH status = 'truncated'` | `return report` (partial result) | line 194 |
| Single LLM call (all sub-workflows + merge) | `AssistantAgent` + `a_generate_reply()` via `_single_turn()` | lines 32–44 |

---

## Architecture notes

- **`_single_turn()`** is a thin stateless wrapper over `AssistantAgent.a_generate_reply()`. Each sub-workflow and the merge step calls it independently so agents carry no cross-call state — matching SPL's pure-function semantics.
- **`asyncio.gather`** is the direct semantic equivalent of `CALL PARALLEL … END`: all three coroutines are submitted to the event loop simultaneously; results are collected in declaration order into `(style_fb, sec_fb, test_fb)`.
- **`max_tokens=1024`** in `_merge_reviews` enforces the `WITH OUTPUT BUDGET 1024 TOKENS` constraint at the Ollama/OpenAI API level.
- **Exception mapping**: SPL's `ModelUnavailable` maps to `openai.APIConnectionError` / `openai.AuthenticationError`; `BudgetExceeded` maps to `openai.BadRequestError` with a context/token keyword guard to avoid swallowing unrelated 400 errors.
- `--log-dir` is accepted for CLI parity with the SPL `INPUT:` signature but is not consumed by this adapter (AutoGen uses Python's `logging` module instead of file-based logs).