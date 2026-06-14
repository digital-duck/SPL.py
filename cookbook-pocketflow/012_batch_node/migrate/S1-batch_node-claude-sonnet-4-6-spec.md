## Summary

This workflow processes a large CSV file containing sales data by splitting it into fixed-size row chunks, computing per-chunk statistics independently, then aggregating and displaying the totals. It exists to demonstrate memory-efficient batch processing over files too large to load into memory at once. Data engineers and analysts benefit from this pattern when dealing with datasets that exceed available RAM.

---

## Detailed Specification

### 1. Purpose

Compute total sales, average sale value, and transaction count from an arbitrarily large CSV file by reading and processing it in memory-efficient, independently-executable chunks.

---

### 2. High-level Description

This is a linear two-node pipeline with no LLM calls — all computation is performed via `CALL` tool functions. The first node, `CSVProcessor`, implements the SPL batch-parallel pattern: its `prep` phase partitions the CSV into fixed-size DataFrame chunks (default 1000 rows each), its `exec` phase is invoked once per chunk to produce per-chunk totals and counts, and its `post` phase reduces those per-chunk results into aggregate statistics stored in a shared `@statistics` variable. The second node, `ShowStats`, reads `@statistics` from shared state and formats the results for console output. Because no language model is consulted, there are no `GENERATE` calls, no `EVALUATE` branches, no `WHILE` loops, and no `EXCEPTION` handlers — only `CALL` side-effect operations and a `RETURN WITH status="end"` to terminate the flow. The routing token `"show_stats"` returned by `CSVProcessor.post()` drives an explicit node transition before the terminal `"end"` signal closes execution.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW csv_batch_processor` | `create_flow()` + `Flow.run(shared)` | Flow is the workflow; `shared` dict is the execution context |
| `CALL read_csv_chunks(...) INTO @chunks` | `CSVProcessor.prep()` → `pd.read_csv(..., chunksize=N)` | Returns a lazy iterator; no data loaded until `exec` consumes it |
| `CALL PARALLEL exec_chunk(@chunk) INTO @results` | `BatchNode.exec(chunk)` invoked per chunk by the framework | Each chunk is independent; framework collects results as a list |
| `CALL aggregate(@results) INTO @statistics` | `CSVProcessor.post()` reduction loop | Sums per-chunk dicts; writes final stats dict to shared state |
| `@statistics` (shared variable) | `shared["statistics"]` | Passed between nodes via the shared store |
| `CALL display_stats(@statistics)` | `ShowStats.post()` → `print(...)` | Side-effect-only output node; no return value of substance |
| `RETURN WITH status="show_stats"` | `return "show_stats"` in `CSVProcessor.post()` | Routes flow from batch processor to display node |
| `RETURN WITH status="end"` | `return "end"` in `ShowStats.post()` | Explicit flow termination |
| `GENERATE` | *(not used)* | No LLM calls in this workflow |
| `EVALUATE` | *(not used)* | No conditional branching |
| `WHILE` | *(not used)* | No iterative refinement |
| `EXCEPTION` | *(not used)* | No error handlers defined |

---

### 4. Logical Functions / Prompts

This workflow contains no LLM prompts. The logical functions are pure data-processing tool functions:

**`read_csv_chunks`**
- Role: Ingests the input file and partitions it into fixed-size DataFrame chunks.
- Key conventions: `chunk_size` parameter (default 1000 rows) controls memory footprint; returns a lazy `TextFileReader` iterator — not an in-memory list — so the full file is never held in RAM at once.

**`exec_chunk`**
- Role: Computes per-chunk statistics from the `amount` column.
- Key conventions: Stateless; each invocation is independent with no dependency on prior or subsequent chunks; returns a plain dict with keys `total_sales`, `num_transactions`, and `total_amount`.

**`aggregate_chunks`**
- Role: Reduces the list of per-chunk dicts into a single workflow-level statistics object.
- Key conventions: Sums `total_sales` and `num_transactions` across all chunks; derives `average_sale = total_amount / total_transactions`; writes result to `shared["statistics"]` for the display node to consume.

**`display_stats`**
- Role: Formats and prints the aggregated statistics to stdout.
- Key conventions: Currency formatting (`$x,.2f`); comma-separated integers; purely a side-effect node — no downstream consumer of its output.

---

### 5. Control Flow

Linear execution with two explicit routing decisions:

1. Flow starts at `CSVProcessor` (BatchNode).
2. `prep` produces a lazy chunk iterator from the input CSV path stored in `shared["input_file"]`.
3. The BatchNode framework invokes `exec` once per chunk; results accumulate in an ordered list.
4. `post` aggregates all chunk results and writes them to `shared["statistics"]`; returns `"show_stats"` — driving an explicit node transition.
5. `ShowStats` reads `@statistics` from shared state, prints formatted output, then returns `"end"`.
6. The `"end"` token terminates the flow — equivalent to `RETURN WITH status="end"`.

There are no loops, no LLM-driven branches, and no exception paths.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Compute total sales, average sale value, and \
transaction count from a large CSV file by reading and processing it in \
memory-efficient chunks. Use a batch-parallel pattern: split the CSV into \
fixed-size chunks via a CALL tool, process each chunk independently with \
CALL PARALLEL to compute per-chunk totals and counts, then aggregate all \
chunk results into a shared @statistics variable. Display the final statistics \
via a CALL to an output tool, then RETURN WITH status='end'." --mode workflow

# Step 2 — compile to any target
spl3 splc compile csv_batch_processor.spl --lang python/pocketflow
spl3 splc compile csv_batch_processor.spl --lang python/langgraph
spl3 splc compile csv_batch_processor.spl --lang go
```