## Summary

Debate Arena orchestrates a structured debate between two LLM personas—one arguing for a motion, one against—across multiple rebuttal rounds, then calls a third LLM persona to judge the winner. It exists to demonstrate multi-perspective adversarial reasoning, where forcing opposing viewpoints produces richer analysis than a single balanced response. Product teams, researchers, and educators benefit from this pattern when they need to stress-test ideas or surface the strongest arguments on both sides of a question.

---

## Detailed Specification

### 1. Purpose

Run a multi-round structured debate between two opposing LLM personas on any motion, then produce a judged verdict with a declared winner.

---

### 2. High-level Description

The `debate_arena` WORKFLOW accepts a debate motion, a round count, and a log directory as inputs. It begins by invoking two CREATE FUNCTIONs—`pro_argument` and `con_argument`—via GENERATE to produce opening statements from each side, then persists both to disk using CALL `write_file`. A WHILE loop then runs for `@max_rounds` iterations: in each iteration, `pro_argument` is called with the full CON history as context (forcing a direct rebuttal), and `con_argument` is called with the updated PRO history, with each rebuttal appended to its side's running transcript and written to a per-round log file. After the loop concludes, a third CREATE FUNCTION—`judge_debate`—receives both complete transcripts and produces a verdict via GENERATE. The workflow uses three distinct prompt roles (advocate-pro, advocate-con, impartial judge) to enforce adversarial discipline: each debater prompt explicitly forbids balanced views, while the judge prompt scores on argument strength, rebuttal quality, and persuasiveness. RETURN delivers the verdict with `status='complete'` and the final round count; two EXCEPTION handlers catch `MaxIterationsReached` (still runs the judge on partial transcripts, returns `status='partial'`) and `BudgetExceeded` (returns the PRO transcript with `status='budget_limit'` immediately).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW debate_arena` | `WORKFLOW <name>` | Declares the top-level orchestration with typed inputs and a single `@verdict` output |
| `CREATE FUNCTION pro_argument` | `CREATE FUNCTION <name>` | Parameterized prompt template with `{topic}` and `{previous}` slots; returns persuasive PRO argument |
| `CREATE FUNCTION con_argument` | `CREATE FUNCTION <name>` | Same structure as pro; prompt instructs model to argue strictly against the motion |
| `CREATE FUNCTION judge_debate` | `CREATE FUNCTION <name>` | Three-parameter template (`{topic}`, `{pro_history}`, `{con_history}`); produces scored verdict with declared winner |
| `GENERATE pro_argument(...) INTO @pro` | `GENERATE <fn>(...) INTO @<var>` | LLM call; result stored in `@pro` / `@pro_rebuttal`; called twice per loop iteration |
| `GENERATE con_argument(...) INTO @con` | `GENERATE <fn>(...) INTO @<var>` | Same pattern for CON side |
| `GENERATE judge_debate(...) INTO @verdict` | `GENERATE <fn>(...) INTO @<var>` | Final LLM call after loop exits |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO @<var>` | Side-effect file write; result discarded via `NONE` |
| `WHILE @round < @max_rounds DO ... END` | `WHILE <cond> DO ... END` | Bounded rebuttal loop; counter `@round` incremented each iteration |
| `RETURN @verdict WITH status='complete', rounds=@round` | `RETURN @<var> WITH <k>=<v>, ...` | Non-trivial status token drives exception branch differentiation |
| `EXCEPTION WHEN MaxIterationsReached` | `EXCEPTION WHEN <Type> THEN ...` | Graceful degradation: judge still runs on partial transcripts |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type> THEN ...` | Hard stop: returns raw PRO history with budget status |
| `@pro_history`, `@con_history`, `@round` | SPL `@vars` (shared state) | Mutable accumulators threaded through the WHILE loop as running transcripts |

---

### 4. Logical Functions / Prompts

**`pro_argument(topic, previous)`**
- **Role:** Opening advocate and rebuttal generator for the PRO side.
- **Key conventions:** The `{previous}` slot is seeded with the literal string `'opening statement'` on the first call, and with the full `@con_history` transcript on rebuttal calls—this forces the model to respond to the most recent opposing content. The prompt explicitly instructs the model to argue one side only and to counter opponent points when rebuttaling. Target length is 3–5 paragraphs.

**`con_argument(topic, previous)`**
- **Role:** Opening advocate and rebuttal generator for the CON side; structurally identical to `pro_argument` but with inverted stance.
- **Key conventions:** On rebuttal calls, `{previous}` receives `@pro_history` (the full updated PRO transcript including the just-generated PRO rebuttal), giving CON a slight informational lag advantage. Same one-sided instruction and length target as PRO.

**`judge_debate(topic, pro_history, con_history)`**
- **Role:** Impartial evaluator that receives both complete transcripts and declares a winner.
- **Key conventions:** Three explicit scoring dimensions are listed in the prompt (argument strength, rebuttal quality, clarity/persuasiveness). The output must declare a winner (`PRO` or `CON`) and explain the ruling in 2–3 paragraphs. This prompt is invoked both on the happy path and inside the `MaxIterationsReached` exception handler, so it must tolerate incomplete transcript histories.

---

### 5. Control Flow

1. **Initialization:** `@round`, `@pro_history`, and `@con_history` are set to zero/empty strings.
2. **Opening statements:** `pro_argument` and `con_argument` are each called once with `'opening statement'` as the `previous` value; results populate the history accumulators and are written to `opening_pro.md` / `opening_con.md`.
3. **Rebuttal loop (WHILE `@round < @max_rounds`):** Each iteration generates a PRO rebuttal against the current CON history, appends it to `@pro_history`, writes it to disk, then generates a CON rebuttal against the now-updated PRO history, appends it to `@con_history`, writes it to disk, and increments `@round`. The asymmetry (CON sees the PRO rebuttal within the same round) is intentional.
4. **Judgement:** After the WHILE loop exits normally, `judge_debate` is called with both full transcripts; the result is stored in `@verdict` and written to `verdict.md`.
5. **Termination:** RETURN with `status='complete'` and the actual round count.
6. **Exception paths:**
   - `MaxIterationsReached` → judge still runs on whatever partial transcripts exist → RETURN with `status='partial'`.
   - `BudgetExceeded` → skip judgement entirely → RETURN raw `@pro_history` with `status='budget_limit'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Run a multi-round structured debate between two opposing LLM \
personas on any motion, then produce a judged verdict with a declared winner. \
The debate_arena WORKFLOW accepts a motion, a round count, and a log directory. \
It generates opening statements from pro_argument and con_argument functions via GENERATE, \
persists both via CALL write_file, then runs a WHILE loop for max_rounds iterations where \
pro_argument rebuts the full CON history and con_argument rebuts the updated PRO history, \
each appended to running transcripts and written to per-round files. After the loop, \
judge_debate receives both transcripts and produces a verdict via GENERATE. \
RETURN delivers the verdict with status='complete' and round count. \
EXCEPTION handlers cover MaxIterationsReached (judge runs on partial transcripts, \
status='partial') and BudgetExceeded (returns raw PRO history, status='budget_limit')." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile debate_arena.spl --lang python/pocketflow
spl3 splc compile debate_arena.spl --lang python/langgraph
spl3 splc compile debate_arena.spl --lang go
```