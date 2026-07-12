# 011 — Supervisor  *(migrated from PocketFlow)*

**Source:** [pocketflow-supervisor](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-supervisor)
**Difficulty:** ★☆☆
**Category:** multi-agent

## What it does

Implements a two-level agent architecture: an inner ReAct research agent iterates search → reason until it decides it has enough information, then generates a candidate answer; an outer supervisor agent validates the answer for coherence and factual grounding and either accepts it or triggers a fresh research cycle. This pattern separates the information-gathering concern (inner loop) from the quality-assurance concern (outer loop).

## Real-world use cases

- **Fact-checked research assistants**: Build pipelines where a fast research agent drafts answers and a critical supervisor rejects unsubstantiated or off-topic responses before they reach users
- **Customer support automation**: Have a search-augmented agent draft responses to customer tickets and a supervisor validate them against company policy before sending
- **Compliance Q&A systems**: Require a second LLM pass to confirm that answers to regulatory questions are grounded in retrieved documents, not hallucinated
- **Autonomous report generation**: Generate draft reports with a research agent and run a quality gate before committing to file

## Key SPL constructs

- `CREATE FUNCTION decide_search_or_answer(@question, @search_history)` — inner agent gate: "search" or "answer"
- `CREATE FUNCTION extract_search_query(...)` — formulates a targeted search query
- `CREATE FUNCTION reason_over_results(...)` — extracts and summarizes relevant facts from search results
- `CREATE FUNCTION generate_candidate_answer(...)` — produces a draft answer from accumulated research
- `CREATE FUNCTION validate_answer(@question, @candidate_answer)` — supervisor gate: "valid" or "invalid"
- Nested `WHILE` loops — outer retry loop (max 3) wraps inner search loop (max 5 iterations)
- `EVALUATE @supervisor_decision WHEN contains("valid")` — force-exits outer loop on acceptance

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@question` | TEXT | _(required)_ | The question to research and answer |
| `@max_search_iterations` | INTEGER | 5 | Maximum search steps per research cycle |
| `@max_retries` | INTEGER | 3 | Maximum supervisor retry cycles |

**Output:** `@verified_answer TEXT` — the first answer that passed supervisor validation

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/011_supervisor/supervisor.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Use a stronger model for `validate_answer` and a faster/cheaper model for the research loop to optimize cost
- Add `CALL PARALLEL` to run two independent research cycles simultaneously and take the first validated answer
- Log each rejected cycle to a file for quality analysis and fine-tuning signal collection
- Chain with `052_batch` to run this supervisor pattern over a list of questions in bulk

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-supervisor-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-supervisor-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-supervisor-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-supervisor-claude-sonnet-4-6.spl       # raw mmd2spl output (= supervisor.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.
