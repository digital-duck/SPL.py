## Summary

Debate Arena orchestrates a structured multi-round debate between two LLM personas — one arguing in favor of a motion, one against — then invokes a third impartial LLM judge to declare a winner. It demonstrates adversarial generation and multi-perspective reasoning in a single, self-contained workflow. Educators, product teams, and researchers use it to stress-test propositions by surfacing the strongest arguments on both sides.

---

## Detailed Specification

### 1. Purpose

Orchestrate a structured adversarial debate between a PRO persona and a CON persona over a configurable number of rebuttal rounds, then produce an impartial judge verdict that identifies the winning side and explains the reasoning.

---

### 2. High-level Description

The `debate_arena` WORKFLOW accepts a debate motion, a maximum round count, and a log directory as inputs, and yields a judge's verdict as its sole OUTPUT. It opens with two unconditional GENERATE calls that produce the PRO and CON opening statements, which are written to disk via CALL `write_file` side-effects and accumulated into growing history variables. A WHILE loop then runs for `@max_rounds` iterations: in each iteration, `pro_argument` is called with the accumulated CON history as context (producing a rebuttal), then `con_argument` is called with the updated PRO history, maintaining the alternating-rebuttal structure. After the loop exhausts, a final GENERATE call to `judge_debate` receives the full PRO and CON transcripts and emits the verdict, which is also persisted to disk. The workflow terminates with RETURN `@verdict` WITH `status = 'complete'` and the actual round count as metadata. Two EXCEPTION handlers provide graceful degradation: `MaxIterationsReached` still runs the judge on whatever history was accumulated (status `'partial'`), while `BudgetExceeded` returns the raw PRO history immediately (status `'budget_limit'`), ensuring the workflow always exits with a usable result.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `debate_arena` node class / graph | `WORKFLOW debate_arena` | Top-level named orchestration unit with INPUT/OUTPUT declarations |
| Shared graph state / blackboard | `@topic`, `@round`, `@pro_history`, `@con_history`, `@verdict` | Mutable variables accumulate cross-turn context |
| PRO argument node | `CREATE FUNCTION pro_argument(topic, previous)` | Prompt template; `{previous}` carries opponent's last turn |
| CON argument node | `CREATE FUNCTION con_argument(topic, previous)` | Mirror of PRO; same slot convention |
| Judge node | `CREATE FUNCTION judge_debate(topic, pro_history, con_history)` | Receives full transcripts; declares winner with rationale |
| LLM call / node execution | `GENERATE <fn>(...) INTO @var` | Each GENERATE is one LLM round-trip; result bound to a named variable |
| File-write side-effect | `CALL write_file(...) INTO NONE` | Persists each round's output and the final verdict to `@log_dir` |
| Rebuttal loop | `WHILE @round < @max_rounds DO ... END` | Counter-driven iteration; both personas rebuttal inside each iteration |
| Normal termination | `RETURN @verdict WITH status = 'complete', rounds = @round` | Carries round count as metadata |
| Partial termination (loop overflow) | `RETURN @verdict WITH status = 'partial'` | EXCEPTION `MaxIterationsReached` — judge still runs on partial history |
| Budget abort | `RETURN @pro_history WITH status = 'budget_limit'` | EXCEPTION `BudgetExceeded` — skips judge entirely |
| Observability | `LOGGING ... LEVEL INFO/DEBUG` | Structured log lines at each phase boundary; not part of LLM data flow |

---

### 4. Logical Functions / Prompts

**`pro_argument(topic, previous)`**
- **Role:** Generates one PRO turn (opening statement or rebuttal). On the opening turn, `previous` is the literal string `'opening statement'`; in rebuttal rounds it receives the accumulated CON history.
- **Key conventions:** Persona is explicitly constrained to argue *only* in favor ("Do NOT offer balanced views"). Rebuttal is triggered implicitly by the presence of opponent content in `{previous}`. Output is prose, 3–5 paragraphs.

**`con_argument(topic, previous)`**
- **Role:** Mirror image of `pro_argument`; persona argues *only against* the motion.
- **Key conventions:** Same slot structure (`{topic}`, `{previous}`) and length guideline. In rebuttal rounds, `{previous}` carries the full PRO history, so each CON turn can directly counter the latest PRO argument.

**`judge_debate(topic, pro_history, con_history)`**
- **Role:** Impartial adjudicator that receives the complete accumulated transcripts of both sides and produces a final verdict.
- **Key conventions:** Evaluation criteria are enumerated inline (argument strength, rebuttal quality, clarity/persuasiveness). Output must declare a winner (`PRO` or `CON`) in 2–3 paragraphs. No scoring tokens or structured output format are required — the verdict is free-form prose.

---

### 5. Control Flow

1. **Initialization** — `@round`, `@pro_history`, and `@con_history` are set to zero/empty. A LOGGING statement marks debate start.
2. **Opening statements** — Two sequential GENERATE calls produce `@pro` and `@con`; both are written to disk and seeded into their respective history accumulators.
3. **Rebuttal loop** — WHILE `@round < @max_rounds`:
   - GENERATE `pro_argument(@topic, @con_history)` → appended to `@pro_history`, written to disk.
   - GENERATE `con_argument(@topic, @pro_history)` → appended to `@con_history`, written to disk.
   - `@round` incremented. Loop repeats.
4. **Judgment** — After the loop exits normally, GENERATE `judge_debate` over full histories → `@verdict`, written to disk.
5. **Termination** — RETURN `@verdict` WITH `status = 'complete'`, `rounds = @round`.
6. **Exception paths:**
   - `MaxIterationsReached`: jumps directly to the judge GENERATE with whatever history exists; RETURN WITH `status = 'partial'`.
   - `BudgetExceeded`: skips judgment entirely; RETURN the raw PRO history WITH `status = 'budget_limit'`.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "Orchestrate a structured adversarial debate between a PRO persona and a CON persona over a configurable number of rebuttal rounds, then produce an impartial judge verdict that identifies the winning side and explains the reasoning. The debate_arena WORKFLOW accepts a debate motion, a maximum round count, and a log directory as inputs, and yields a judge's verdict as its sole OUTPUT. It opens with two unconditional GENERATE calls that produce the PRO and CON opening statements, which are written to disk via CALL write_file side-effects and accumulated into growing history variables. A WHILE loop then runs for max_rounds iterations: in each iteration, pro_argument is called with the accumulated CON history as context, then con_argument is called with the updated PRO history, maintaining the alternating-rebuttal structure. After the loop exhausts, a final GENERATE call to judge_debate receives the full PRO and CON transcripts and emits the verdict, also persisted to disk. The workflow terminates with RETURN verdict WITH status='complete' and the actual round count as metadata. Two EXCEPTION handlers provide graceful degradation: MaxIterationsReached still runs the judge on partial history (status 'partial'), while BudgetExceeded returns the raw PRO history immediately (status 'budget_limit')." --mode workflow --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile debate_arena.spl --lang python/pocketflow
spl3 splc compile debate_arena.spl --lang python/langgraph
spl3 splc compile debate_arena.spl --lang go
```