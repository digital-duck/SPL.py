## Summary

This implementation demonstrates the Shared Store communication pattern in PocketFlow by building a stateful word-counting loop. A user enters text repeatedly, and a shared dictionary accumulates running statistics (text count, word count, average) across iterations. It exists as a pedagogical example showing how nodes pass state through a shared object rather than through direct return values.

---

## Detailed Specification

### 1. Purpose

Collect text input from a user in a continuous loop, count the words in each submission, and display cumulative statistics (total texts processed, total words, average words per text) until the user signals exit.

### 2. High-level Description

The workflow follows a three-phase WHILE loop that continues until the user types `q`. In the input phase, the workflow reads a line of text and initializes a shared statistics record (`@stats`) on first execution, incrementing `total_texts` on every subsequent pass. The EVALUATE construct checks whether the input equals the sentinel value `q`; if so, RETURN WITH `status="exit"` terminates the loop. Otherwise, a word-count tool call splits the input string on whitespace and accumulates the result into `@stats.total_words`. A display step then reads `@stats` and prints the running totals and average before cycling back to the input phase. There are no LLM generation steps — all computation is deterministic Python logic invoked via CALL; the workflow is purely a shared-state communication skeleton with no probabilistic branching.

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW WordCounter` | `create_flow()` + `flow.run(shared)` | Top-level orchestration entry point |
| `@shared` / `@stats` | `shared` dict passed to every node | Mutable state threaded through all nodes |
| `CALL initialize_stats() INTO @stats` | `TextInput.post()` initializing `shared["stats"]` | First-run guard (`if "stats" not in shared`) |
| `CALL count_words(@text) INTO @word_count` | `WordCounter.exec(text)` via `len(text.split())` | Pure deterministic tool, no LLM |
| `CALL update_stats(@word_count)` | `WordCounter.post()` updating `shared["stats"]["total_words"]` | Side-effect write to shared store |
| `CALL display_stats(@stats)` | `ShowStats.post()` printing formatted output | Side-effect print, no return value |
| `EVALUATE @input WHEN equals('q') THEN ... ELSE ...` | `if prep_res == 'q': return "exit"` in `TextInput.post()` | Only real branch in the workflow |
| `WHILE input != 'q' DO ... END` | `show_stats - "continue" >> text_input` back-edge in `flow.py` | Loop body = count + display |
| `RETURN @result WITH status="exit"` | `return "exit"` in `TextInput.post()` | Terminates the WHILE loop |

### 4. Logical Functions / Prompts

**No LLM prompt templates exist in this implementation.** All functions are deterministic tool calls:

| Name | Role | Key Conventions |
|---|---|---|
| `read_input` | Captures a line of text from stdin; doubles as loop sentinel check | Returns raw string; sentinel value is literal `'q'` |
| `count_words` | Splits input on whitespace, returns integer word count | `len(str.split())` — no tokenizer, no normalization |
| `update_stats` | Accumulates `total_texts` and `total_words` into `@stats` | Mutates shared store in-place; average is derived, not stored |
| `display_stats` | Formats and prints running totals plus average | Average computed as `total_words / total_texts` at display time |

### 5. Control Flow

```
[START]
  │
  ▼
read_input(@text)
  │
  ├─ EVALUATE: @text == 'q' ──► RETURN WITH status="exit" ──► [END]
  │
  └─ (else, initialize @stats on first pass)
       │
       ▼
  count_words(@text) → @word_count
       │
       ▼
  update_stats(@word_count) into @stats
       │
       ▼
  display_stats(@stats)
       │
       └──────────────────────────────────► back to read_input  [WHILE loop]
```

Termination is the only non-trivial control-flow event. Everything else is a linear chain.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Collect text input from a user in a continuous loop,
count the words in each submission using a deterministic split tool, and display
cumulative statistics (total texts processed, total words, average words per text)
until the user types q to exit. Use a WHILE loop with EVALUATE on the sentinel value,
CALL tool functions for counting and display, and maintain running totals in shared
@stats variables across iterations." --mode workflow

# Step 2 — compile to any target
spl3 splc compile word_counter.spl --lang python/pocketflow
spl3 splc compile word_counter.spl --lang python/langgraph
spl3 splc compile word_counter.spl --lang go
```