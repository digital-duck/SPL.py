## Summary

Text Converter is an interactive command-line tool that repeatedly accepts user text, applies a chosen string transformation (uppercase, lowercase, reverse, or whitespace collapse), and loops until the user exits. It exists to demonstrate PocketFlow's branching and loop patterns using pure deterministic logic — no LLM calls are made. Developers learning PocketFlow benefit from seeing how `prep`/`exec`/`post` hooks and named action tokens compose into a stateful interactive pipeline.

---

## Detailed Specification

### 1. Purpose

Convert a user-supplied string via one of four deterministic transformations (uppercase, lowercase, reverse, whitespace-collapse) in a repeating interactive loop until the user chooses to exit.

### 2. High-level Description

The workflow is a two-node interactive loop with two exit paths. A `TextInput` step collects a string from stdin, presents a numbered menu, and branches on the user's menu choice: selecting option 5 terminates the workflow immediately via an `exit` action, while any other choice advances to the `TextTransform` step. `TextTransform` applies the selected operation — using deterministic string functions rather than an LLM — displays the result, then asks whether to process another string. If the user confirms, it clears the cached input in shared state and returns an `input` action that routes back to `TextInput`, forming a WHILE-style loop. If the user declines, it returns `exit` and the workflow terminates at an `EndNode`. Shared state (`@text`, `@choice`) threads context between nodes across iterations. There are no LLM calls, no prompt templates, and no exception handlers in the current implementation; all branching is driven by raw user keystrokes evaluated as string equality.

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW TextConverter` | `Flow(start=text_input)` + `flow.run({})` | Top-level orchestration unit |
| `CREATE FUNCTION` | *(absent)* | No LLM prompt templates; all logic is deterministic |
| `GENERATE` | *(absent)* | No LLM calls; transformations are pure Python string ops |
| `CALL transform_text(@text, @choice) INTO @result` | `TextTransform.exec((text, choice))` | Side-effect-free deterministic tool call |
| `CALL get_input() INTO @text` | `input(...)` inside `TextInput.prep` / `post` | Console I/O side effect |
| `WHILE user_wants_to_continue DO ... END` | `TextTransform → "input" → TextInput` cycle | Loop terminates when `exit` action fires |
| `EVALUATE @choice WHEN == '5' THEN exit ELSE transform` | `if choice == "5": return "exit"` in `TextInput.post` | Branch on raw menu selection |
| `EVALUATE @continue WHEN == 'y' THEN input ELSE exit` | `if input(...).lower() == 'y': return "input"` | Branch on continuation prompt |
| `RETURN WITH status='exit'` | `return "exit"` from `post()` | Non-trivial termination token; drives routing to `EndNode` |
| `@text`, `@choice` (shared vars) | `shared["text"]`, `shared["choice"]` | Cross-node mutable state dictionary |
| `EXCEPTION WHEN ...` | *(absent)* | No error handling in current implementation |

### 4. Logical Functions / Prompts

**`get_user_text`**
- Role: Collects the raw string to transform; skips re-prompting if text is already cached in shared state (supports loop-back without re-entry).
- Key conventions: Prompt is `"\nEnter text to convert: "`; result stored in `@text`.

**`get_menu_choice`**
- Role: Displays a numbered menu (1–5) and reads the user's selection; drives the primary branch between transform and exit.
- Key conventions: Input is a single character `"1"`–`"5"`; choice `"5"` is the exit sentinel; any other value passes to the transform step.

**`apply_transformation`**
- Role: Pure deterministic string operation dispatched by `@choice`; no LLM involvement.
- Key conventions: `"1"` → `.upper()`, `"2"` → `.lower()`, `"3"` → `[::-1]`, `"4"` → `" ".join(text.split())`; unrecognised choice returns the literal string `"Invalid option!"`.

**`ask_continue`**
- Role: After displaying the result, prompts the user for loop continuation; clears `@text` from shared state before looping so fresh input is requested next iteration.
- Key conventions: Checks `.lower() == 'y'`; any other input exits.

### 5. Control Flow

```
START
  └─► TextInput.prep   — populate @text (skip if already set)
      TextInput.post   — display menu, read @choice
          ├─ choice == "5"  → RETURN status="exit" → EndNode  (terminate)
          └─ otherwise      → advance to TextTransform

      TextTransform.prep  — read (@text, @choice) from shared state
      TextTransform.exec  — apply deterministic transform → @result
      TextTransform.post  — print @result, prompt continuation
          ├─ user says "y"  → clear @text, RETURN status="input" → TextInput  (loop)
          └─ user says other → RETURN status="exit" → EndNode  (terminate)
END
```

The WHILE loop is implicit in the `TextTransform → "input" → TextInput` back-edge. Both `exit` actions lead to the same `EndNode`, which is a no-op terminal.

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Build an interactive CLI workflow called TextConverter. \
  It loops between two steps: first collect a string from the user and a menu choice \
  (uppercase/lowercase/reverse/remove-extra-spaces/exit); if the user picks exit, \
  terminate immediately. Otherwise apply the chosen deterministic string transformation \
  using CALL, display the result, then ask whether to process another string. \
  If yes, clear the cached input and loop back to the input step (WHILE pattern). \
  If no, exit. Use @text and @choice as shared variables. No LLM calls are needed." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_converter.spl --lang python/pocketflow
spl3 splc compile text_converter.spl --lang python/langgraph
spl3 splc compile text_converter.spl --lang go
```