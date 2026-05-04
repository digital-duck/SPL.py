## 0. High-level Description

This workflow implements iterative chain-of-thought reasoning with two nested loops. One `CREATE FUNCTION` prompt is defined: `ChainOfThoughtStep` instructs the LLM to reason step-by-step and emit **plain YAML** (no code fences) with three required keys — `current_thinking`, `next_action_plan`, and `next_thought_needed` (boolean). The compiled PocketFlow uses three nodes: `S3ThinkingInitNode` seeds all shared variables; `S3ThinkingThinkNode` handles both the outer WHILE and the inner YAML-retry loop — the outer WHILE runs as a PocketFlow self-loop (`think - "continue" >> think`) where the exit condition is checked in `prep()` (returning `None` to break), while the inner YAML-retry loop runs as plain Python inside `exec()` (up to 3 retries); `S3ThinkingFinalizeNode` assigns `@solution := @current_thinking` and sets `status="complete"`. Each outer iteration writes two blocks to a trace file: the raw YAML response with a validity flag, then the extracted fields. The `EXCEPTION WHEN BudgetExceeded` SPL block maps to `except subprocess.CalledProcessError` around `Flow.run()`, which sets `status="budget_limit"` and returns the last `@current_thinking`. Helpers (`_format_thoughts_to_text`, `_extract_last_plan`, `_validate_yaml_fields`, `_append_thought`, `_extract_yaml_field`, `_print_thought_progress`) are pure Python functions corresponding to SPL CALL tools.

---

## 1. Purpose

Solves a problem through iterative chain-of-thought reasoning: the LLM reasons step-by-step, producing a structured thought at each iteration, until it signals completion or a maximum iteration cap is reached.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW ChainOfThought` | `_build_flow() → Flow(start=init)` | Three-node graph; outer WHILE is a self-loop on `S3ThinkingThinkNode` |
| `INPUT @problem TEXT, @max_iterations INT := 5, @trace_file TEXT := "..."` | `run_s3_thinking_chain_of_thought(problem, max_iterations=5, trace_file=..., model=...)` | Stored in `shared` before `Flow.run()` |
| `OUTPUT @solution TEXT` | `shared["solution"]` written by `S3ThinkingFinalizeNode.post()` | Returned as `result["solution"]` by public API |
| Variable init block (`@thoughts:="[]"` etc.) | `S3ThinkingInitNode.exec()` returns init dict; `.post()` calls `shared.update(...)` | `@thoughts` stored as Python `list`, not string `"[]"` |
| `WHILE @next_thought_needed = "true" AND @iteration < @max_iterations DO` | `S3ThinkingThinkNode.prep()` — returns `None` (break) or data dict (continue) | De Morgan: `not (a and b)` = `a != "true" or iteration >= max_iterations` |
| `@thought_number += 1; @iteration += 1` | Computed as `p["thought_number"] + 1` and `p["iteration"] + 1` inside `exec()` | Updated in `shared` via `shared.update(exec_res)` in `post()` |
| `CALL format_thoughts_to_text(@thoughts)` | `_format_thoughts_to_text(thoughts)` — join list as `"Thought N: ..."` | Pure Python |
| `CALL extract_last_plan(@thoughts)` | `_extract_last_plan(thoughts)` — `thoughts[-1].get("next_action_plan", ...)` | Pure Python |
| Inner WHILE: `@yaml_valid="false" AND @retry_count<3` | `while yaml_valid == "false" and retry_count < _MAX_YAML_RETRIES:` inside `exec()` | Python loop — no PocketFlow node; tight retry doesn't need shared state transitions |
| `GENERATE ChainOfThoughtStep(...) INTO @thought_data` | `_call_llm(_cot_prompt(...), model)` — `subprocess.run(["claude", "--model", ..., "-p", ...])` | Asks for PLAIN YAML, no fences |
| `CALL validate_yaml_fields(@thought_data)` | `_validate_yaml_fields(text)` — `yaml.safe_load` + required-keys check; returns `"true"/"false"` | Python `bool` values lowercased to match SPL string convention |
| `CALL write_file(@trace_file, ..., "a")` | `_write_file(path, content, mode)` — `open(path, mode).write(content)` | Appends; no `makedirs` (flat filename default) |
| `CALL append_thought(@thoughts, @thought_data)` | `_append_thought(thoughts, yaml_text)` — `yaml.safe_load` + list append | Mutates shallow copy; result returned and pushed back to `shared` |
| `CALL extract_yaml_field(@thought_data, "field")` | `_extract_yaml_field(text, field)` — `yaml.safe_load`; `bool` → lowercase string | Handles Python `True/False` → `"true"/"false"` |
| `CALL print_thought_progress(...)` | `_print_thought_progress(thinking, plan)` — `print(...)` first 200 chars | Returns `"ok"` |
| `@solution := @current_thinking` | `S3ThinkingFinalizeNode.prep()` reads `shared["current_thinking"]` | Assigned to `shared["solution"]` in `post()` |
| `RETURN @solution WITH status="complete"` | `shared["status"] = "complete"` + `"end"` terminal action | `"end"` has no successor → flow ends |
| `EXCEPTION WHEN BudgetExceeded THEN RETURN ... WITH status="budget_limit"` | `except subprocess.CalledProcessError` around `_build_flow().run(shared)` | Maps Claude CLI non-zero exit to `budget_limit` status |
| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "--model", model, "-p", prompt, "--output-format", "text"])` | `_MODEL = "claude-sonnet-4-6"` default constant |

---

## 3. Logical Functions / Prompts

### `ChainOfThoughtStep`
- **Role:** Core reasoning step. Given the problem, previous thoughts (as formatted text), last plan, and current thought number, produces one step of analysis.
- **Output:** **Plain YAML** (no fences) with three mandatory keys: `current_thinking` (detailed analysis), `next_action_plan` (updated plan), `next_thought_needed` (`true`/`false`).
- **Retry:** If the response fails `yaml.safe_load` or is missing required keys, the same prompt is retried up to `_MAX_YAML_RETRIES = 3` times within a single outer iteration.

### Tool calls (deterministic, no LLM)
- `_format_thoughts_to_text(thoughts)` — formats the thoughts list as `"Thought N: <current_thinking>"` lines; returns `"(no previous thoughts)"` when empty.
- `_extract_last_plan(thoughts)` — returns `thoughts[-1]["next_action_plan"]` or `"(no plan yet)"`.
- `_validate_yaml_fields(text)` — returns `"true"` iff `yaml.safe_load` succeeds and all three required keys are present.
- `_append_thought(thoughts, yaml_text)` — parses YAML and appends dict (or `{"raw": text}` on failure) to the list.
- `_extract_yaml_field(text, field)` — returns `str(val).lower()` for bool values, `str(val)` otherwise; `""` on parse error.
- `_print_thought_progress(thinking, plan)` — prints first 200 chars of each field to stdout.

---

## 4. Control Flow

```
INPUT @problem TEXT, @max_iterations INT := 5, @trace_file TEXT

@thoughts ← []; @thought_number ← 0; @iteration ← 0
@next_thought_needed ← "true"; @current_thinking ← ""; @updated_plan ← ""

── WHILE @next_thought_needed = "true" AND @iteration < @max_iterations ───
│  (PocketFlow: S3ThinkingThinkNode self-loop; prep() checks condition)
│
│  @thought_number += 1; @iteration += 1
│  @thoughts_text ← format_thoughts_to_text(@thoughts)
│  @last_plan_text ← extract_last_plan(@thoughts)
│
│  ── YAML-retry WHILE @yaml_valid = "false" AND @retry_count < 3 ─────
│  │  GENERATE ChainOfThoughtStep(@problem, @thoughts_text,         [LLM]
│  │                               @last_plan_text, @thought_number)
│  │  → @thought_data
│  │  validate_yaml_fields(@thought_data) → @yaml_valid
│  │  @retry_count += 1
│  └─────────────────────────────────────────────────────────────────────
│
│  write_file(@trace_file, "--- Thought N (yaml_valid=...) ---\n...", "a")
│  @thoughts ← append_thought(@thoughts, @thought_data)
│  @next_thought_needed ← extract_yaml_field(@thought_data, "next_thought_needed")
│  @current_thinking ← extract_yaml_field(@thought_data, "current_thinking")
│  @updated_plan ← extract_yaml_field(@thought_data, "next_action_plan")
│  write_file(@trace_file, "next_thought_needed=...\ncurrent_thinking=...\n\n", "a")
│  print_thought_progress(@current_thinking, @updated_plan)
│
└──────────────────────────────────────────────────────────────────────────

@solution := @current_thinking
RETURN @solution WITH status="complete"

EXCEPTION: subprocess.CalledProcessError → RETURN @current_thinking WITH status="budget_limit"
```

**Observed run (2026-05-04):** Problem `"Why is fibonacci sequence important?"`, max-iterations=5 → `status=complete`. One outer iteration (thought 1) with `next_thought_needed=false` after a comprehensive single-step analysis covering biology, mathematics, computer science, and finance.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — regenerate SPL from this spec
spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-thinking-claude_cli-sonnet-2-spec.md)" \
    --mode workflow --adapter claude_cli

# Step 2 — run (requires tools.py with CoT helper implementations)
spl3 run ChainOfThought.spl --adapter claude_cli \
    --param problem="Why is the fibonacci sequence important?" \
    --param max_iterations=5

# Step 3 — recompile to any target
spl3 splc compile ChainOfThought.spl --lang python/pocketflow --llm \
    --adapter claude_cli --model sonnet
spl3 splc compile ChainOfThought.spl --lang python/langgraph
spl3 splc compile ChainOfThought.spl --lang go
```
