## Summary

This is an autonomous coding agent that takes a failing test suite and iteratively implements the missing code until all tests pass. It operates in a tight tool-loop — inspect, read, patch, run, repeat — driven entirely by an LLM that reads its own action history and decides what to do next. Engineers and teams with skeleton codebases benefit most: the agent handles mechanical implementation work so humans can focus on design.

---

## Detailed Specification

### 1. Purpose

Autonomously implement skeleton functions in a Python codebase by iteratively using file inspection, code patching, and test execution tools until a given test suite fully passes.

---

### 2. High-level Description

The workflow is a single WORKFLOW named `CodingAgent` that runs a bounded WHILE loop (up to 50 iterations) driven by an LLM decision function. At the top of each iteration, a `CompactHistory` step uses GENERATE to summarize overly long action histories so the LLM's context window never overflows — old entries beyond a rolling window are replaced with a bullet-point summary. The core of the loop is a `DecideAction` step that uses GENERATE to send the full task description, compacted action history, persistent memory from past sessions, and optional project-specific rules (`AGENTS.md` skills file) to the LLM, which responds with a structured JSON object naming exactly one tool and its arguments.

EVALUATE on the returned tool name routes execution to one of five dedicated tool branches (`list_files`, `grep_search`, `read_file`, `run_command`, `patch_file`) or, if the tool name is unrecognized, appends an error message to history and issues a `retry` action that skips tool execution and loops immediately. When the LLM selects `patch_file`, control enters a three-node sub-WORKFLOW (the Flow-IS-Node pattern): `PatchRead` loads the file, `PatchValidate` checks that the target string exists exactly once (using fuzzy matching to suggest corrections on failure), and `PatchApply` writes the replacement; a validation failure triggers an early RETURN with status `error`, surfacing the mismatch message as the tool result rather than corrupting the file. Every tool node appends its result to shared history before looping back to `CompactHistory`. RETURN with status `done` terminates the loop when the LLM explicitly selects the `done` tool or the step counter reaches the limit; at that point, a CALL to `save_memory` persists a two-to-three-bullet LLM-generated summary of the session's key learnings to `.memory.md` for future runs.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW CodingAgent` | `create_coding_agent_flow()` + `Flow(start=compact)` | Top-level orchestration unit |
| `WHILE step < MAX_STEPS DO ... END` | `compact >> decide >> [tool] >> compact` cycle | Loop is implicit in PocketFlow graph edges; `DecideAction.post` increments step counter |
| `GENERATE DecideAction(...) INTO @tool_call` | `DecideAction.exec(prompt) → call_llm(prompt)` | Core LLM call; prompt assembled in `prep` from task, history, memory, skills |
| `GENERATE CompactHistory(...) INTO @history` | `CompactHistory.exec(inputs) → call_llm(summary_prompt)` | Conditional LLM call; only fires when `len(history) > COMPACT_AFTER` |
| `EVALUATE @tool_call WHEN tool = 'X' THEN ... END` | `DecideAction.post` returning a named action string | PocketFlow routes on the string: `decide - "list_files" >> ListFiles()` etc. |
| `CALL patch_subflow(...) INTO @patch_result` | `PatchFile(Flow)` as a node inside the outer `Flow` | Flow-IS-Node pattern; sub-workflow executes atomically and writes result to `shared["_patch_result"]` |
| `RETURN @result WITH status='done'` | `DecideAction.post` returning `"done"` | Triggers loop exit; saves memory before returning |
| `RETURN @error WITH status='error'` | `PatchValidate.post` returning `"error"` | Exits patch sub-workflow early; error message surfaced as tool result |
| `RETURN @result WITH status='retry'` | `DecideAction.post` returning `"retry"` | Unknown tool — appends error to history and skips tool execution |
| `@shared` (SPL variables) | `shared` dict passed through all nodes | Holds `task`, `workdir`, `history`, `step`, `tool_call`, `result`, `_patch_content`, `_patch_result` |
| `EXCEPTION WHEN MaxStepsError` | `if step >= MAX_STEPS: return "done"` | Hard ceiling enforced inside `DecideAction.post` |
| `IMPORT 'memory.md'` / `IMPORT 'AGENTS.md'` | `load_memory(workdir)` / `load_skills(workdir)` | File-based context injection into each `DecideAction` prompt |

---

### 4. Logical Functions / Prompts

**DecideAction**
- Role: The agent's reasoning core — given the full task, history, memory, and available tools, pick the single best next action.
- Prompt conventions: System role is "coding agent fixing failing tests". Context sections are assembled in order: skills (if present), memory (if present), tool descriptions, task, history. Output format is enforced with a JSON sentinel: ` ```json\n{"tool": "...", "args": {...}, "reason": "..."}\n``` `. Parsing extracts between ` ```json ` and ` ``` ` delimiters; malformed JSON raises an assertion that triggers a retry via `max_retries=3`.

**CompactHistory**
- Role: Context-window guardian — periodically replaces old history with a dense summary so the `DecideAction` prompt stays within LLM token limits.
- Prompt conventions: Plain text instruction: "Summarize these past actions briefly". Input is a bullet list of `tool: result` lines for history entries older than the rolling window. Output is free-form prose and inserted as a synthetic `{"tool": "summary", ...}` history entry.

**SaveMemory** (called at termination)
- Role: Distills session learnings into a persistent artifact for future runs.
- Prompt conventions: Instruction: "Summarize key learnings from this coding session in 2-3 bullets". Input is the last 5 history entries formatted as `tool: result` lines. Output is written verbatim to `.memory.md`.

---

### 5. Control Flow

```
CompactHistory
    → (always) DecideAction
        → "list_files"   → ListFiles   → CompactHistory
        → "grep_search"  → GrepSearch  → CompactHistory
        → "read_file"    → ReadFile    → CompactHistory
        → "run_command"  → RunCommand  → CompactHistory
        → "patch_file"   → PatchFile SubFlow:
                              PatchRead → PatchValidate
                                  → (ok)    PatchApply → (exit subflow)
                                  → "error" (exit subflow, error in _patch_result)
                          → CompactHistory
        → "retry"        → CompactHistory   (unknown tool, no execution)
        → "done"         → save_memory → END
```

Termination conditions (both inside `DecideAction.post`):
- LLM selects the `done` tool — RETURN with `status='done'`.
- Step counter reaches `MAX_STEPS = 50` — forced RETURN with `status='done'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Autonomously implement skeleton functions in a Python codebase by iteratively using file inspection, code patching, and test execution tools until a given test suite fully passes." --mode workflow

# Step 2 — compile to any target
spl3 splc compile coding_web_search_agent.spl --lang python/pocketflow
spl3 splc compile coding_web_search_agent.spl --lang python/langgraph
spl3 splc compile coding_web_search_agent.spl --lang go
```