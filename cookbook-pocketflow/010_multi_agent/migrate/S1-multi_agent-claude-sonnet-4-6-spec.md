## Summary

This workflow implements a two-player Taboo word-guessing game where two LLM agents — a Hinter and a Guesser — exchange messages asynchronously until the target word is identified or a turn limit is reached. The Hinter must describe the target word without using a list of forbidden terms, while the Guesser narrows its answer based on accumulated hints and prior wrong guesses. It demonstrates how SPL can coordinate concurrent, stateful agent loops through message-passing rather than a single linear call chain.

---

## Detailed Specification

### 1. Purpose

Orchestrate two concurrently running LLM agents in a turn-based guessing game where the Hinter generates forbidden-word-safe clues and the Guesser converges on the target word, terminating on a correct guess or a configurable turn ceiling.

---

### 2. High-level Description

This workflow uses the **CALL PARALLEL** pattern to run two independent WHILE loops simultaneously: one for the Hinter agent and one for the Guesser agent, synchronized through bidirectional message queues (analogous to SPL shared `@vars` with channel semantics). The workflow begins by injecting an empty bootstrap message into the hinter channel to start the first turn.

The Hinter's loop is driven by a `generate_hint` function: on each iteration it reads the latest guess from the shared hinter queue, then calls GENERATE with a prompt that includes the `@target_word`, the `@forbidden_words` list, and `@past_guesses` accumulated so far, producing a concise natural-language clue (at most five words). The generated hint is forwarded to the guesser queue and the loop continues via RETURN WITH `status="continue"`.

The Guesser's loop is driven by a `generate_guess` function: it reads the latest hint from the shared guesser queue, calls GENERATE with the hint and the history of wrong guesses, and produces a single-word answer. An EVALUATE block then checks whether the guess matches `@target_word` (case-insensitive); on a match it broadcasts a sentinel `GAME_OVER` token into the hinter queue and exits with RETURN WITH `status="done"`. If the turn counter reaches `@max_turns` without a match, the same sentinel is sent and the loop exits with RETURN WITH `status="max_turns_reached"`. Otherwise, the wrong guess is appended to `@past_guesses`, the turn counter is incremented, and the guess is forwarded to the hinter queue to drive the next Hinter iteration.

The Hinter's loop detects the `GAME_OVER` sentinel and exits with RETURN WITH `status="done"`, cleanly terminating both concurrent branches. No exception handling is explicitly required because the sentinel protocol guarantees both loops reach a terminal state; however an EXCEPTION WHEN `TimeoutError` handler would be appropriate to guard against queue deadlocks in production.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW taboo_game` | `async def run_game(word, forbidden, max_turns)` | Top-level orchestrator; initializes all shared state |
| `CREATE FUNCTION generate_hint` | `AsyncHinter.exec_async` + inline prompt string | Builds hint prompt from target, forbidden list, past guesses |
| `CREATE FUNCTION generate_guess` | `AsyncGuesser.exec_async` + inline prompt string | Builds guess prompt from hint and past guesses |
| `GENERATE generate_hint(...) INTO @hint` | `hint = call_llm(prompt)` in `AsyncHinter.exec_async` | Single LLM call; result forwarded to guesser queue |
| `GENERATE generate_guess(...) INTO @guess` | `guess = call_llm(prompt)` in `AsyncGuesser.exec_async` | Single LLM call; result checked against target |
| `CALL PARALLEL ... END` | `asyncio.gather(hinter_flow.run_async(shared), guesser_flow.run_async(shared))` | Both agent loops run concurrently |
| `WHILE status = "continue" DO ... END` (Hinter) | `hinter - "continue" >> hinter` self-loop in `AsyncFlow` | Loop continues while hinter receives non-sentinel input |
| `WHILE status = "continue" DO ... END` (Guesser) | `guesser - "continue" >> guesser` self-loop in `AsyncFlow` | Loop continues while guess is wrong and turns < max |
| `EVALUATE @guess WHEN matches(@target_word)` | `if exec_res.lower() == shared["target_word"].lower()` in `AsyncGuesser.post_async` | Exact match check; drives "done" vs "continue" branch |
| `RETURN WITH status="done"` | `return "end"` from `post_async` (correct guess) | Signals both flows to terminate |
| `RETURN WITH status="max_turns_reached"` | `return "end"` from `post_async` (turns ≥ max_turns) | Alternative termination branch |
| `@target_word`, `@forbidden_words`, `@past_guesses`, `@turns` | `shared["target_word"]`, `shared["forbidden_words"]`, `shared["past_guesses"]`, `shared["turns"]` | Mutable shared state dict; SPL `@vars` are the equivalent |
| Hinter↔Guesser channel | `asyncio.Queue` (hinter_queue, guesser_queue) | SPL models this as `@hinter_channel` / `@guesser_channel` INPUT/OUTPUT vars |
| `EXCEPTION WHEN TimeoutError THEN ...` | *(absent — implicit in asyncio)* | Should be added; queue deadlock guard |

---

### 4. Logical Functions / Prompts

**`generate_hint`**
- **Role:** Produces a short, forbidden-word-safe clue about the target word each turn.
- **Key conventions:**
  - Always includes `@target_word` and `@forbidden_words` in the prompt.
  - Appends `@past_guesses` when non-empty, with the instruction "Make hint more specific" — a progressive refinement nudge.
  - Hard length constraint: "Use at most 5 words." Forces brevity without a structured output format.
  - No sentinel or scoring token; raw string output is forwarded directly.

**`generate_guess`**
- **Role:** Produces a single-word candidate answer based on the current hint and wrong-guess history.
- **Key conventions:**
  - Includes the full `@past_guesses` list to discourage repeating prior answers.
  - Explicit output format instruction: "Directly reply a single word:" — no punctuation, no explanation.
  - Output is consumed by the EVALUATE block for an exact (case-insensitive) match against `@target_word`.

---

### 5. Control Flow

```
INIT: push "" → hinter_queue   (bootstrap first Hinter turn)

CALL PARALLEL:
  ┌─ HINTER LOOP ─────────────────────────────────────────────────────┐
  │  WHILE true:                                                       │
  │    read @guess ← hinter_queue                                     │
  │    IF @guess == "GAME_OVER" → RETURN WITH status="done"  (exit)  │
  │    GENERATE generate_hint(@target_word, @forbidden_words,         │
  │                            @past_guesses) INTO @hint              │
  │    push @hint → guesser_queue                                     │
  │    → continue (loop)                                              │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ GUESSER LOOP ─────────────────────────────────────────────────────┐
  │  WHILE true:                                                        │
  │    read @hint ← guesser_queue                                      │
  │    GENERATE generate_guess(@hint, @past_guesses) INTO @guess       │
  │    EVALUATE @guess:                                                 │
  │      WHEN matches(@target_word) →                                  │
  │        push "GAME_OVER" → hinter_queue                            │
  │        RETURN WITH status="done"                   (correct)       │
  │      WHEN @turns >= @max_turns →                                   │
  │        push "GAME_OVER" → hinter_queue                            │
  │        RETURN WITH status="max_turns_reached"      (timeout)       │
  │      ELSE →                                                         │
  │        append @guess → @past_guesses                               │
  │        increment @turns                                            │
  │        push @guess → hinter_queue                                  │
  │        → continue (loop)                                           │
  └─────────────────────────────────────────────────────────────────────┘

Both parallel branches terminate when their respective flows receive "end".
```

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "Orchestrate two concurrently running LLM agents in a \
turn-based Taboo guessing game where the Hinter generates forbidden-word-safe clues \
and the Guesser converges on the target word, terminating on a correct guess or a \
configurable turn ceiling. Use CALL PARALLEL for two independent WHILE loops \
synchronized through shared @hinter_channel and @guesser_channel variables. \
The Hinter loop calls GENERATE generate_hint(@target_word, @forbidden_words, \
@past_guesses) INTO @hint each turn. The Guesser loop calls GENERATE \
generate_guess(@hint, @past_guesses) INTO @guess and uses EVALUATE to check \
for a match; RETURN WITH status='done' on correct guess or status='max_turns_reached' \
when @turns >= @max_turns; otherwise append @guess to @past_guesses and continue." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile taboo_game.spl --lang python/pocketflow
spl3 splc compile taboo_game.spl --lang python/langgraph
spl3 splc compile taboo_game.spl --lang go
```