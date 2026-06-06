# Debate Arena — CrewAI

Compiled from `debate.spl` (SPL Recipe 11). Two LLM personas argue opposing sides of a topic over configurable rebuttal rounds; an impartial judge declares the winner.

## Setup

```bash
pip install crewai          # crewai >= 0.70 recommended (CrewOutput.raw API)

# For Ollama (local, default)
ollama pull gemma3

# For OpenAI / OpenRouter — set the usual env vars instead:
# export OPENAI_API_KEY=sk-...
# export OPENAI_API_BASE=https://openrouter.ai/api/v1   # if using OpenRouter
```

## Run

```bash
# Default (Ollama / gemma3, 3 rebuttal rounds)
python debate.py

# Custom topic and model
python debate.py --topic "Remote work is better than office work" \
                 --max-rounds 2 \
                 --model ollama/llama3.2

# OpenAI example
python debate.py --topic "Tabs are better than spaces" \
                 --model openai/gpt-4o \
                 --log-dir /tmp/debate_logs
```

## Expected output pattern

```
2026-04-20 12:00:00 [INFO] Debate started | topic: ... | rounds: 3
2026-04-20 12:00:05 [INFO] Opening statements complete
2026-04-20 12:00:06 [DEBUG] Round 0 | pro rebuttal ...
...
2026-04-20 12:00:40 [INFO] All rounds done — judge deliberating ...
2026-04-20 12:00:45 [INFO] Verdict ready | rounds=3
============================================================
STATUS : complete
ROUNDS : 3
============================================================
**Winner: PRO**

The pro side demonstrated consistently stronger argumentation ...
```

Log files are written to `--log-dir` (default `cookbook/11_debate_arena/logs-crewai/`):

| File | Contents |
|---|---|
| `opening_pro.md` | Pro's opening statement |
| `opening_con.md` | Con's opening statement |
| `round_N_pro.md` | Pro's rebuttal in round N |
| `round_N_con.md` | Con's rebuttal in round N |
| `verdict.md` | Judge's final ruling |

## SPL → CrewAI construct map

| SPL construct | CrewAI / Python equivalent | Location in `debate.py` |
|---|---|---|
| `CREATE FUNCTION pro_argument(...)` | `Agent(role="Pro Debater", ...)` + `_PRO_ARGUMENT_TMPL` | `pro_agent`, `_PRO_ARGUMENT_TMPL` |
| `CREATE FUNCTION con_argument(...)` | `Agent(role="Con Debater", ...)` + `_CON_ARGUMENT_TMPL` | `con_agent`, `_CON_ARGUMENT_TMPL` |
| `CREATE FUNCTION judge_debate(...)` | `Agent(role="Debate Judge", ...)` + `_JUDGE_TMPL` | `judge_agent`, `_JUDGE_TMPL` |
| `WORKFLOW debate_arena` | `def debate_arena(...)` | `debate_arena()` |
| `INPUT: @topic TEXT DEFAULT '...'` | `def debate_arena(topic: str = "...", ...)` | function signature |
| `OUTPUT: @verdict TEXT` | `return {"output": verdict, ...}` | `return` statements |
| `GENERATE fn(...) INTO @var` | `_generate(agent, prompt) → str` | `_generate()` helper |
| `@a := @b \|\| '\n---\n' \|\| @c` | `a = b + "\n---\n" + c` | rebuttal loop body |
| `WHILE @round < @max_rounds DO` | `while round_num < max_rounds:` | rebuttal loop |
| `@round := @round + 1` | `round_num += 1` | end of loop body |
| `LOGGING '...' LEVEL INFO` | `log.info(...)` | throughout |
| `LOGGING '...' LEVEL DEBUG` | `log.debug(...)` | rebuttal loop |
| `CALL write_file(...) INTO NONE` | `_write_file(path, content)` | `_write_file()` helper |
| `EXCEPTION WHEN MaxIterationsReached THEN` | `except MaxIterationsReached:` | exception block |
| `EXCEPTION WHEN BudgetExceeded THEN` | `except BudgetExceeded:` | exception block |
| `RETURN @x WITH status='complete', rounds=@r` | `return {"output": x, "status": "complete", "rounds": r}` | all `return` paths |

## Notes

- **`_generate()`** creates a minimal `Crew(agents=[agent], tasks=[task])` per call, which faithfully models SPL's `GENERATE … INTO @var` semantics (one prompt → one result, no shared state between calls).
- **`MaxIterationsReached` / `BudgetExceeded`** are declared as Python exception classes so that a wrapping orchestrator or adapter layer can raise them and trigger the SPL-equivalent `EXCEPTION` branches.
- The `model` parameter accepts any CrewAI LLM string (`ollama/gemma3`, `openai/gpt-4o`, `openrouter/...`), mirroring SPL's `--adapter` / `--model` flags at the CLI layer.