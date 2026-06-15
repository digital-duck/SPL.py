## Summary

This workflow accepts a plain-text search query, retrieves live web results via SerpAPI, and passes them to an LLM for synthesis into a structured analysis containing a summary, key facts, and suggested follow-up queries. It eliminates the manual loop of searching and reading multiple pages by delivering a single, curated briefing. Researchers, analysts, and developers who need fast, distilled web intelligence are the primary beneficiaries.

## Detailed Specification

### 1. Purpose

Perform a live web search for a user-supplied query and produce an LLM-synthesized analysis comprising a summary, key points, and follow-up queries — all in one automated pass.

### 2. High-level Description

The workflow follows a two-stage GENERATE pipeline with no iterative refinement. In the first stage, a CALL to an external SerpAPI tool retrieves the top-N organic search results (titles, snippets, and URLs) for the user's query, storing them in a shared `@search_results` variable. In the second stage, a GENERATE call passes the original query together with the collected results to GPT-4, which synthesizes a structured analysis object containing three fields: a prose summary, a list of key factual points, and a list of suggested follow-up queries. The final analysis is stored in `@analysis` and printed to the console. There are no WHILE loops, no EVALUATE branches, and no exception handlers in the current implementation — the control flow is strictly linear and terminates after the analysis step. The design cleanly separates retrieval (a deterministic tool call) from synthesis (a probabilistic GENERATE call), which is the canonical SPL pattern for tool-augmented research workflows.

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW WebSearchAnalysis` | `create_flow()` + `Flow(start=search)` | Top-level orchestration unit |
| `CALL search_tool(...) INTO @search_results` | `SearchNode.exec()` → `SearchTool.search(query, num_results)` | Deterministic retrieval; not an LLM call |
| `GENERATE analyze_results(...) INTO @analysis` | `AnalyzeResultsNode.exec()` → `analyze_results(query, results)` | LLM synthesis via GPT-4 |
| `INPUT: @query, @num_results` | `shared = {"query": ..., "num_results": 5}` in `main.py` | Shared state initialized before flow runs |
| `@search_results` (shared var) | `shared["search_results"]` written in `SearchNode.post()` | Inter-node data bus |
| `@analysis` (shared var) | `shared["analysis"]` written in `AnalyzeResultsNode.post()` | Final output variable |
| `CREATE FUNCTION analyze_results` | `tools/parser.py::analyze_results()` | Prompt template wrapping query + results |

### 4. Logical Functions / Prompts

**`search_tool` (SerpAPI retrieval)**
- Role: Deterministic web retrieval; produces structured result objects (title, snippet, link) from Google organic results.
- Key conventions: Returns an empty list on missing query; result count controlled by `num_results` parameter (default 5). This is a CALL, not a GENERATE — no LLM involved.

**`analyze_results` (LLM synthesis)**
- Role: Synthesizes raw search snippets into a human-readable briefing using GPT-4.
- Key conventions: Takes the original `query` as context anchor alongside the result list. Output is a structured object with exactly three keys: `summary` (prose string), `key_points` (list of strings), `follow_up_queries` (list of strings). Returns a graceful default when the result list is empty (`"No search results to analyze"`).

### 5. Control Flow

```
[Start] → CALL search_tool(query, num_results) INTO @search_results
        → GENERATE analyze_results(query, @search_results) INTO @analysis
        → print @analysis to console
[End]
```

Execution is strictly linear with no branching or looping. The only guard is an early-exit in `analyze_results` when `@search_results` is empty, which returns a stub analysis object rather than calling the LLM.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Perform a live web search for a user-supplied query and \
produce an LLM-synthesized analysis comprising a summary, key points, and follow-up \
queries. First, CALL a SerpAPI tool with the query and num_results parameters, storing \
results in @search_results. Then GENERATE an analysis using GPT-4 that takes the query \
and @search_results as input and returns a structured object with summary, key_points, \
and follow_up_queries fields stored in @analysis." --mode workflow

# Step 2 — compile to any target
spl3 splc compile web_search_analysis.spl --lang python/pocketflow
spl3 splc compile web_search_analysis.spl --lang python/langgraph
spl3 splc compile web_search_analysis.spl --lang go
```