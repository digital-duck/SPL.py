# 034 — Communication (Word Stats Loop)  *(migrated from PocketFlow)*

**Source:** [pocketflow-communication](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-communication)
**Difficulty:** ★★☆
**Category:** basics

## What it does

Processes a delimited list of text inputs one at a time in a WHILE loop, computing running word-count statistics (count, total words, average words per text) and accumulating a formatted log entry for each input. The loop exits early on an "exit" sentinel value. This demonstrates the use of deterministic arithmetic tool functions (`int_add`, `safe_divide`) to maintain running state across WHILE loop iterations without LLM involvement in the computation.

## Real-world use cases

- **Content auditing**: Process a batch of marketing copy snippets, computing word count statistics to flag overlong or underlong texts before publication
- **Writing metrics dashboards**: Accumulate word counts across a session's writing inputs to track productivity or enforce length constraints
- **Document preprocessing**: Compute per-document statistics (word count, density) as a metadata pass before downstream embedding or classification
- **Data pipeline reporting**: Process a stream of text inputs and accumulate summary statistics that roll up into a final batch report

## Key SPL constructs

- `CREATE TOOL_API int_add(a, b)` — deterministic integer addition over TEXT-typed accumulator variables
- `CREATE TOOL_API safe_divide(numerator, denominator, decimals)` — division with zero-guard, returns rounded TEXT result
- `CALL list_get(@user_inputs, @i, @delimiter)` — index into a delimited list by position
- `CALL word_count(@current_input)` — deterministic word count tool
- `WHILE @i < @max_inputs DO` — main processing loop
- `EVALUATE @check_input WHEN contains("exit")` — sentinel-value exit: sets `@i := @max_inputs` to force loop termination
- String accumulation pattern: `@running_log := @running_log + ...` — builds output text inline across iterations

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@user_inputs` | TEXT | `"Hello world, The quick brown fox..., exit"` | Comma-delimited list of text inputs; "exit" terminates the loop |
| `@delimiter` | TEXT | `","` | Delimiter separating the input items |
| `@max_inputs` | INTEGER | 50 | Safety cap on the number of iterations |

**Output:** `@final_output TEXT` — formatted running log followed by final statistics (total texts, total words, average words/text)

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/034_communication/communication.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Add a `GENERATE classify_text(@current_input)` step inside the loop to tag each input (positive/negative/neutral) alongside its word count
- Replace the comma-delimited list with `CALL read_file` + line-by-line iteration to process files of arbitrary size
- Accumulate per-category statistics separately (e.g., word count by label) using multiple `int_add` accumulators
- Pipe the final stats output into `032_deep_research` as a dataset summary for AI-assisted analysis

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-communication-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-communication-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-communication-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-communication-claude-sonnet-4-6.spl       # raw mmd2spl output (= communication.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.
