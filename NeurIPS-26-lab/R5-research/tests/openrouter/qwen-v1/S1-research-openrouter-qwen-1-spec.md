## 0. High-level Description
This WORKFLOW implements a recursive map-reduce research orchestration that iteratively plans web searches, extracts factual summaries, and synthesizes a comprehensive report until knowledge gaps are resolved or a maximum iteration threshold is met. It begins by invoking a CREATE FUNCTION named `plan_queries` to GENERATE a batch of diverse search directives based on a user topic and optional prior feedback, storing them in a shared state array. Each directive triggers a parallel CALL to a web search tool followed by a CREATE FUNCTION `extract_facts` call to GENERATE concise factual notes from the retrieved snippets, which are aggregated into a cumulative notes list while routing prompts through an environment-configured multi-model adapter. The orchestration then enters a WHILE loop governed by an iteration counter and an EVALUATE step that inspects the structured output of the `assess_and_synthesize` function to branch between further research and finalization. If gaps persist, the EVALUATE branch updates the feedback state and loops back to the planner; otherwise, the workflow executes a final GENERATE step to draft a markdown report, routes parsing or API failures through an EXCEPTION WHEN handler, and concludes with a side-effect file write followed by a RETURN statement that delivers the document alongside execution metadata.

## 1. Purpose
This implementation automates iterative, LLM-driven web research to systematically gather, validate, and synthesize comprehensive markdown reports on a given topic while automatically identifying and filling knowledge gaps.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `Flow(start=planner)` + `main()` CLI entrypoint | Declares the directed graph topology, wires nodes, and manages execution lifecycle |
| `CREATE FUNCTION <name>` | `Node.exec()` methods containing prompt templates | Encapsulates reusable LLM instructions for planning, extraction, assessment, and reporting |
| `GENERATE <fn>(...) INTO @<var>` | `utils.call_llm(prompt)` | Routes structured/unstructured prompts to environment-configured OpenAI/Gemini endpoints |
| `EVALUATE @<var> WHEN contains('...') THEN ...` | `if exec_res["action"] == "research": return "research" else ...` | Branches execution path based on YAML-parsed `action` field in `SynthesizerNode.post()` |
| `WHILE <cond> DO ... END` | `synthesizer - "research" >> planner` loop + `loop_count < 2` guard | Recursively cycles through plan-research-synthesize until threshold or finalization condition fails |
| `CALL <tool>(...) INTO @<var>` | `utils.search_web(query)` / `Path().write_text()` | Performs external web scraping via DuckDuckGo and persists final markdown to disk |
| `EXCEPTION WHEN <Type> THEN ...` | Implicit error handling in `call_llm` & YAML parsing blocks | SPL requires explicit handlers for API timeouts, rate limits, or malformed YAML splits |
| `RETURN @<var> WITH <k>=<v>` | `shared["report"] = ...` + terminal output & file write in `main()` | Terminates workflow, exposes final artifact, and tracks metadata like iteration count |
| Shared State (`@vars`) | `shared` dict (`topic`, `notes`, `loop_count`, etc.) | Mutable context object passed via `prep()`, `exec()`, and `post()` across node instances |

## 3. Logical Functions / Prompts
**1. `plan_queries`**
- **Role:** Generates targeted web search directives to explore a topic or address previously identified knowledge gaps.
- **Key Prompt Conventions:** Forces strict YAML output via markdown code fences. Expects schema `queries: ["string", "string", "string"]`. Explicitly forbids conversational filler to ensure reliable YAML parsing.

**2. `extract_facts`**
- **Role:** Distills raw web search results into concise, topic-relevant factual statements.
- **Key Prompt Conventions:** Direct instruction format ("Extract key facts relevant to this query. Be brief."). Outputs plain text summary per query. Results are manually wrapped with `Q: {query}\nFacts: {extracted}` for downstream aggregation.

**3. `assess_and_synthesize`**
- **Role:** Evaluates information sufficiency, identifies remaining gaps, or triggers final report generation.
- **Key Prompt Conventions:** YAML-only output inside code fences. Strict routing schema: `action: research` (requires `feedback: string`) OR `action: finalize` (requires `content: markdown text`). Used as the decision gate for loop continuation.

**4. `write_report`** (Synthesizer Forced Path)
- **Role:** Generates the final comprehensive markdown report from accumulated research notes when the iteration limit is reached.
- **Key Prompt Conventions:** Direct synthesis instruction bypassing YAML routing. Expects raw markdown output. Activated deterministically when `@loop_count >= 2`.

## 4. Control Flow
The workflow initializes by executing a `GENERATE` call through the planner function, populating the `@queries` state array with three distinct search directives. A `CALL` to the web search tool is triggered in parallel for each directive, followed immediately by a `GENERATE` call to extract and aggregate factual notes into `@notes`. The orchestrator then enters a `WHILE` loop governed by the `@loop_count` variable, which is evaluated at the start of each cycle. Inside the loop, the synthesis function executes a `GENERATE` prompt that outputs a structured YAML decision block. An `EVALUATE` step inspects the `action` field of this output; if it matches `research` and `@loop_count` is below two, the evaluator increments the counter, updates the `@feedback` state, and routes execution back to the planner via a directed graph edge. If the condition evaluates to `finalize` or the loop threshold is breached, the `EVALUATE` branch bypasses the planner, triggers a final `GENERATE` step to compose the markdown report, and routes to a terminal `CALL` for file persistence. The workflow concludes by executing a `RETURN` statement that emits the final report alongside execution metadata like iteration count and status.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```