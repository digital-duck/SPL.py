## Iterative Research Agent (PocketFlow)

An agentic research loop that answers open-ended questions by iteratively deciding whether to search the web or synthesize a final answer. Each iteration the agent inspects accumulated context and either fires a DuckDuckGo search or terminates with a comprehensive response.

### Requirements

```
pip install pocketflow openai duckduckgo-search pyyaml
```

### Setup

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | one of | OpenAI API key |
| `OPENROUTER_API_KEY` | one of | OpenRouter key (takes precedence) |
| `LLM_MODEL` | optional | Model ID (default: `gpt-4o-mini`) |

```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini      # optional override
```

### Usage

```bash
# Default example question
python research_agent.py

# Custom question
python research_agent.py "Who won the 2025 Nobel Prize in Physics and why?"
```

**Expected output:**
```
Question : Who won the 2025 Nobel Prize in Physics and why?
======================================================================
[iter 1] SEARCH → 2025 Nobel Prize in Physics winner
   Retrieved 5 snippet(s)
[iter 2] SEARCH → Nobel Physics 2025 citation discovery details
   Retrieved 5 snippet(s)
[iter 3] ANSWER (action=answer)

======================================================================
FINAL ANSWER
======================================================================
The 2025 Nobel Prize in Physics was awarded to ...

Status     : done
Iterations : 3
```

### Workflow Logic

```
START
  │
  ▼
DecideActionNode  ←──────────────────────┐
  │  (LLM call: decide_action prompt)    │
  │  → parse YAML with block-scalar      │
  │    fallback on known keys            │
  ├──"search"──► SearchWebNode           │
  │               │ DuckDuckGo query     │
  │               │ append to @context   │
  │               └──"decide"────────────┘
  │
  └──"answer"──► AnswerQuestionNode
                  │ use draft if present,
                  │ else call synthesize LLM
                  │ store @answer, status=done
                  └──"done"──► TERMINATE
```

1. **DecideActionNode** — Sends accumulated `@context` + question to the LLM. Parses the YAML response; if the first `yaml.safe_load` fails, forces block-scalar (`|`) notation on `search_query`, `answer`, and `reasoning` fields and retries. Returns action `"search"` or `"answer"`.
2. **SearchWebNode** — Runs the `search_query` through DuckDuckGo (5 results), appends a labelled block to `@context`, returns `"decide"` to loop back.
3. **AnswerQuestionNode** — Uses the LLM-supplied draft answer (from `decide_action`) directly if non-empty, otherwise calls a dedicated synthesis prompt. Stores the final answer in `shared["answer"]` and sets `shared["status"] = "done"`.
4. **Loop guard** — After `MAX_ITERATIONS` (5) the `DecideActionNode` forces the `"answer"` branch regardless of the LLM's preference.