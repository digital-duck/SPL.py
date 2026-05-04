## 0. High-level Description
This `WORKFLOW` implements a recursive map-reduce research orchestration that iteratively plans web searches, gathers factual snippets in parallel, and synthesizes a comprehensive markdown report. It begins by invoking `GENERATE plan_queries` to produce a structured list of search objectives, then executes `CALL search_web` for each query followed by `GENERATE extract_facts` to distill raw results into a shared `@notes` buffer. Control flow is governed by a `WHILE @iteration_count < 2` refinement loop, where `EVALUATE @synthesis_action` routes execution back to the planner on `"research"` or terminates with `RETURN @report WITH status=complete` when `"finalize"` is triggered. The `CREATE FUNCTION assess_and_report` dynamically switches between gap-analysis and final-document generation based on accumulated context, while strict YAML parsing ensures reliable LLM-to-code transitions across multiple inference providers. Side effects include persistent file I/O for the final deliverable and console progress logging, and `EXCEPTION` handling is delegated to the underlying HTTP client and LLM shim, surfacing network or quota failures as immediate workflow halts.

## 1. Purpose
This implementation autonomously researches a user-specified topic by iteratively generating targeted web queries, extracting concise factual summaries, and refining the scope until a comprehensive markdown report is synthesized and saved.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `create_deep_research_flow()` + `Flow(start=planner)` | Defines the node chain, shared context, and routing edges |
| `CREATE FUNCTION` | Prompt strings inside `PlannerNode.exec`, `ResearcherNode.exec`, `SynthesizerNode.exec` | Reusable templates with `{topic}`, `{feedback}`, `{notes}` interpolation slots |
| `GENERATE` | `call_llm(prompt)` inside each node | LLM inference call; results parsed from YAML blocks into `@queries`, `@notes`, `@report` |
| `CALL` (tool) | `search_web(query)`, `Path(out).write_text(...)` | External side-effects: DuckDuckGo HTTP search and markdown file persistence |
| `WHILE` / `EVALUATE` | `SynthesizerNode.post` returning `"research"` vs `"finalize"`, `shared["loop_count"] < 2` | Branches back to planner on gap feedback or exits when sufficient data/max iterations reached |
| `RETURN` (non-trivial) | `return "research"` / `return "finalize"` in `post()` | Explicit status tokens that override implicit linear progression and drive loop termination or routing |
| Shared State (`@var`) | `shared` dictionary passed through `prep`/`post` | Mutable context carrying `@topic`, `@current_queries`, `@notes`, `@loop_count`, `@feedback`, `@report` |

## 3. Logical Functions / Prompts
- **Name**: `plan_queries`
  - **Role in workflow**: Generates the initial or gap-filling search strategy to guide information gathering.
  - **Key prompt conventions**: Enforces strict YAML output with `queries:` list; conditionally injects `feedback` string from previous synthesis when gaps are detected; expects exactly three diverse query strings.
- **Name**: `extract_facts`
  - **Role in workflow**: Maps raw web search snippets into concise, query-relevant insights for downstream aggregation.
  - **Key prompt conventions**: Input formatted as `Query: ... \n Search result: ...`; instructs extreme brevity; outputs plain text prefixed with `Q: ... Facts: ...` for clean list extension.
- **Name**: `assess_and_report`
  - **Role in workflow**: Evaluates research completeness, identifying knowledge gaps or triggering final document generation.
  - **Key prompt conventions**: Forces YAML with `action: research|finalize` and corresponding `feedback:` or `content:` keys; uses `\n---\n` as delimiter when injecting `@notes` context; bypasses LLM evaluation and forces `action: finalize` if `@loop_count >= 2`.

## 4. Control Flow
The workflow initializes shared context with `@topic` and immediately executes `GENERATE plan_queries` to populate `@current_queries`. These queries undergo parallel processing: each triggers `CALL search_web` followed by `GENERATE extract_facts`, with outputs aggregated into the `@notes` list. The orchestrator then evaluates the synthesis result; if `EVALUATE @synthesis_action` yields `"research"` and `@loop_count < 2`, the loop increments, stores the gap description in `@feedback`, and routes execution back to the planning step. When `EVALUATE` returns `"finalize"` (either by LLM judgment or forced by the iteration limit), the workflow halts the `WHILE` loop, `RETURN`s the generated markdown in `@report WITH status=complete, iterations=@loop_count`, and triggers the final file-write side effect before terminating.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```