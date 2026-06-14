## Summary

This implementation reads a large CSV file of sales transactions and produces aggregate statistics (total revenue, average sale, transaction count) by splitting the file into fixed-size row chunks, computing per-chunk summaries in parallel, and then merging them into a single result. It exists to show how PocketFlow's `BatchNode` handles inputs too large to process in one pass. Data engineers or analysts benefit by getting a reusable, chunk-aware pipeline pattern that scales to arbitrarily large files without memory pressure.

---

## Detailed Specification

### 1. Purpose

Process an arbitrarily large CSV file of sales transactions in fixed-size row chunks, aggregate per-chunk statistics into global totals, and display the final summary to the user.

---

### 2. High-level Description

This workflow implements a **map-reduce data pipeline** — no LLM calls are made; all computation is deterministic. The pipeline has two stages wired in sequence. The first stage, `CSVProcessor`, acts as the map phase: its `prep` step reads the CSV file path from shared state (`@input_file`) and emits an iterator of `chunk_size`-row DataFrames; its `exec` step is applied independently to every chunk and returns a statistics dictionary (`total_sales`, `num_transactions`, `total_amount`); its `post` step reduces the list of per-chunk results by summing into global totals, computing `average_sale`, and writing the aggregated record into shared state (`@statistics`). The second stage, `ShowStats`, reads `@statistics` and renders the formatted summary to stdout. Control flow is strictly linear: `CSVProcessor` transitions to `ShowStats` via the `"show_stats"` action token emitted from `post`, which is the only non-default routing decision in the graph. There is no looping, no branching on output content, and no exception handling defined in the implementation.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW csv_batch_processor` | `create_flow()` + `Flow(start=processor)` | Top-level orchestration unit |
| `INPUT: @input_file` | `shared["input_file"]` passed into `flow.run(...)` | Entry parameter |
| `CALL PARALLEL ... END` | `BatchNode.exec(chunk)` called once per chunk | `BatchNode` maps `exec` over all prep outputs independently |
| `CREATE FUNCTION chunk_stats` | `CSVProcessor.exec(chunk)` | Deterministic transform; no prompt — pure Python |
| `CALL aggregate(...) INTO @statistics` | `CSVProcessor.post(...)` writing `shared["statistics"]` | Reduce step; writes to shared state |
| `@statistics` (SPL shared var) | `shared["statistics"]` dict | Passed between nodes via PocketFlow shared store |
| `CALL show_results(@statistics)` | `ShowStats.post(...)` printing to stdout | Terminal side-effect node |
| `RETURN @statistics WITH status='show_stats'` | `return "show_stats"` in `CSVProcessor.post` | Only non-trivial action token; drives the single routing edge |

> **Note:** There are no `GENERATE`, `EVALUATE`, `WHILE`, or `EXCEPTION` constructs in this implementation — it is a purely deterministic data pipeline with no LLM calls.

---

### 4. Logical Functions / Prompts

This pipeline contains no LLM prompt templates. All functions are deterministic Python transforms:

**`CSVProcessor.prep`**
- Role: Input partitioner — converts a file path into a lazy iterator of `pd.DataFrame` chunks
- Key convention: uses `pandas.read_csv(..., chunksize=N)` so chunks are generated lazily, bounding memory usage

**`CSVProcessor.exec`**
- Role: Per-chunk mapper — computes `total_sales`, `num_transactions`, `total_amount` from a single DataFrame slice
- Key convention: stateless; result is a plain dict; no side effects

**`CSVProcessor.post`**
- Role: Reducer — sums all per-chunk dicts, derives `average_sale = total_amount / total_transactions`, writes `@statistics` to shared store
- Key convention: the only place global state is mutated; emits `"show_stats"` to route to the display node

**`ShowStats.post`**
- Role: Terminal display — formats and prints the aggregated statistics with locale-aware number formatting
- Key convention: read-only consumer of `@statistics`; returns `"end"` as a terminal signal

---

### 5. Control Flow

```
Flow.run({"input_file": path})
  └─► CSVProcessor.prep()      — read CSV, yield DataFrames of chunk_size rows
        ↓ (BatchNode maps exec over each chunk in parallel)
      CSVProcessor.exec(chunk) — per-chunk stats dict   [× N chunks]
        ↓ (BatchNode collects exec results into exec_res_list)
      CSVProcessor.post()      — reduce, write @statistics
        │
        RETURN status="show_stats"   ← only non-trivial routing decision
        │
  └─► ShowStats.post()         — print formatted summary → terminal
        │
        RETURN "end"           ← flow terminates
```

No loops, no conditional branches on content, no retries.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 above as the description)
spl3 text2spl --description "Process an arbitrarily large CSV file of sales \
transactions in fixed-size row chunks, aggregate per-chunk statistics into \
global totals, and display the final summary to the user. The pipeline has \
two stages: a map stage that splits the CSV into chunks and computes per-chunk \
totals (total_sales, num_transactions, total_amount), and a reduce stage that \
sums chunk results, derives average_sale, writes aggregated statistics to a \
shared variable, then calls a display procedure to print the formatted output." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile csv_batch_processor.spl --lang python/pocketflow
spl3 splc compile csv_batch_processor.spl --lang python/langgraph
spl3 splc compile csv_batch_processor.spl --lang go
```

> **Regeneration note:** Because this workflow has no `GENERATE` (LLM) calls, `text2spl` will produce a pure `CALL`-based pipeline. If the intent is to add an LLM layer (e.g. anomaly detection or natural-language summary of the statistics), add that to the description before running `text2spl`.