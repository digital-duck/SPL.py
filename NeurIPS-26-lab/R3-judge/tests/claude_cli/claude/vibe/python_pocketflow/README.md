## LLM-as-a-Judge — PocketFlow Workflow

### Overview

A minimalist PocketFlow pipeline that evaluates any question/response pair using an LLM judge. The judge scores the response on five calibrated criteria (correctness, completeness, clarity, conciseness, helpfulness) and returns a structured JSON report with per-criterion scores (1–5), an overall score, a pass/borderline/fail verdict, and a prose summary.

```
ValidateInput → JudgeEval → ParseScores → ComputeVerdict → FormatOutput
      │                           │
      └── [error] → ErrorNode     └── [retry] ──┐
                                                 │ (up to 1 retry on bad JSON)
                                                 └── ParseScores
```

### Requirements

```bash
pip install pocketflow        # minimalist LLM orchestration
# The inline fallback means pocketflow is optional; the workflow runs either way.
```

For the `claude_cli` adapter, the `claude` CLI must be installed and authenticated:
```bash
pip install claude-code        # or: npm install -g @anthropic-ai/claude-code
claude login
```

For the `openrouter` adapter:
```bash
export OPENROUTER_API_KEY=sk-or-...
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_ADAPTER` | `claude_cli` | `claude_cli` or `openrouter` |
| `LLM_MODEL` | `claude-opus-4-7` | Any model supported by the adapter |
| `LLM_MAX_TOKENS` | `2048` | Max tokens for judge output |
| `OPENROUTER_API_KEY` | *(required for openrouter)* | OpenRouter API key |

### Usage

```bash
# Default example (runs inline demo question)
python flow.py

# Custom question and response (positional args)
python flow.py "What is a race condition?" "A race condition occurs when ..."

# Use OpenRouter with Gemini
LLM_ADAPTER=openrouter LLM_MODEL=google/gemini-2.5-pro python flow.py
```

### Expected Output

```
============================================================
  LLM JUDGE EVALUATION REPORT
============================================================
  CORRECTNESS     5/5   Response is factually accurate...
  COMPLETENESS    4/5   Covers both concepts well but...
  CLARITY         5/5   Explanation is well-structured...
  CONCISENESS     4/5   Appropriately concise...
  HELPFULNESS     5/5   Would genuinely help a student...
------------------------------------------------------------
  OVERALL (LLM)    : 4.60/5.0
  OVERALL (COMPUTED): 4.60/5.0
  VERDICT          : PASS
============================================================
  SUMMARY:
  A strong, accurate response that correctly ...
============================================================

JSON output saved to shared['output']
```

### Workflow Step-by-Step

1. **ValidateInputNode** — Strips whitespace, checks both `question` and `response` are non-empty. Routes to `ErrorNode` on failure.
2. **JudgeEvalNode** — Constructs the full rubric prompt (5 criteria × scoring instructions) and calls `call_llm()` with a strict system prompt enforcing calibrated scoring. Stores raw output in `shared["raw_judge_output"]`.
3. **ParseScoresNode** — Strips markdown fences, extracts the first JSON block with a regex, and `json.loads()` it. On failure, calls the LLM once more with a JSON-repair instruction and retries. After two failures, routes to `ErrorNode`.
4. **ComputeFinalVerdictNode** — Independently recomputes the arithmetic mean from per-criterion scores (audit trail), normalises the verdict string, and stores `result` in shared state.
5. **FormatOutputNode** — Pretty-prints the report to stdout and serialises the complete result to `shared["output"]` as a JSON string.
6. **ErrorNode** — Logs the error and writes `{"error": "..."}` to `shared["output"]` so callers always get valid JSON.