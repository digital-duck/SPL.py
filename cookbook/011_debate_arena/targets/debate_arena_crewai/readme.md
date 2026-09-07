## Debate Arena — CrewAI

### Setup

```bash
pip install crewai          # core framework
# Optional: set a default LLM via environment
export OPENAI_API_KEY=...   # if using OpenAI models
# or configure Ollama locally (no key required)
```

### Run

```bash
# Default topic, 3 rounds, local Ollama
python debate.py

# Custom topic + model
python debate.py \
  --topic "Remote work is better than office work" \
  --max-rounds 2 \
  --model "ollama/gemma3"

# OpenAI
python debate.py \
  --topic "Tabs are better than spaces" \
  --model "openai/gpt-4o-mini"
```

### Expected output

```
08:14:01 INFO    Debate started | topic: AI should be open-sourced | rounds: 3
08:14:12 INFO    Opening statements complete
08:14:22 DEBUG   Round 0 | pro rebuttal ...
08:14:33 DEBUG   Round 0 | con rebuttal ...
08:14:34 INFO    Round 1 complete
...
08:15:01 INFO    All rounds done — judge deliberating ...
08:15:12 INFO    Verdict ready | rounds=3

============================================================
Status : complete
Rounds : 3
============================================================
After careful evaluation of both sides...
The winner is: PRO / CON
...
```

Log files are written to `cookbook/11_debate_arena/logs-crewai/`:

```
opening_pro.md
opening_con.md
round_0_pro.md   round_0_con.md
round_1_pro.md   round_1_con.md
round_2_pro.md   round_2_con.md
verdict.md
```

### SPL → CrewAI construct map

| SPL construct | CrewAI / Python equivalent |
|---|---|
| `CREATE FUNCTION name(...) AS $$ prompt $$` | `Agent(role, goal, backstory)` + `_name_prompt()` builder function |
| `GENERATE fn(@args) INTO @var` | `_run_task(agent, prompt)` → `crew.kickoff()` → `str` |
| `WORKFLOW debate_arena INPUT:/OUTPUT:` | `def debate_arena(...) -> dict` |
| `@var := value` | Python variable assignment |
| `@a := @a \|\| '\n---\n' \|\| @b` | `a = a + "\n---\n" + b` |
| `WHILE @round < @max_rounds DO … END` | `while round_num < max_rounds:` |
| `CALL write_file(path, content) INTO NONE` | `_write_file(path, content)` (stdlib `pathlib`) |
| `LOGGING … LEVEL INFO/DEBUG` | `logger.info()` / `logger.debug()` |
| `RETURN @val WITH status='complete', rounds=@round` | `return {"verdict": val, "status": "complete", "rounds": round_num}` |
| `EXCEPTION WHEN MaxIterationsReached THEN` | `except MaxIterationsReached:` |
| `EXCEPTION WHEN BudgetExceeded THEN` | `except BudgetExceeded:` |

### Notes

- **One Crew per LLM call**: CrewAI's `Crew` is stateless between rounds, so `_run_task()` creates a fresh single-agent, single-task Crew each time. This preserves the SPL sequential-GENERATE semantics exactly — each call is independent and the caller accumulates history manually (mirroring `@pro_history` concatenation in SPL).
- **Exception mapping**: `MaxIterationsReached` and `BudgetExceeded` are defined as Python exceptions. If your CrewAI version raises its own iteration limit error, wrap `_run_task()` to re-raise as `MaxIterationsReached`.
- **LLM selection**: Pass any [LiteLLM-compatible model string](https://docs.litellm.ai/docs/providers) via `--model`. Omitting `--model` uses whatever CrewAI's default LLM is configured to (typically `OPENAI_API_KEY` → `gpt-4o-mini`).