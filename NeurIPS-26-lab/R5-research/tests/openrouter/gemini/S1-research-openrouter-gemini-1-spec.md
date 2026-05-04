## 0. High-level Description
This WORKFLOW implements a recursive map-reduce research agent designed to iteratively gather and synthesize information on a given topic. The process begins with a planning function that generates diverse search queries, which are then processed in parallel by a research function that performs web searches and extracts key facts. A synthesis function then evaluates the collected data to determine if knowledge gaps remain. Using a WHILE loop constrained by a maximum iteration count, the workflow uses EVALUATE to branch between generating additional search queries based on feedback or finalizing a comprehensive markdown report. The workflow utilizes side-effect tool calls to perform live web searches and maintains shared state to accumulate research notes across iterations.

## 1. Purpose
The workflow automates deep topical research by iteratively searching the web, extracting facts, and synthesizing a final report until sufficient information is gathered or a loop limit is reached.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `deep_research` | `create_deep_research_flow()` | Orchestrates the Planner, Researcher, and Synthesizer nodes. |
| **CREATE FUNCTION** | `PlannerNode`, `ResearcherNode`, `SynthesizerNode` | Prompt templates for query generation, fact extraction, and synthesis. |
| **GENERATE** | `call_llm(prompt)` | LLM invocations within the `exec` methods of the nodes. |
| **CALL** | `search_web(query)` | Side-effect tool call to DuckDuckGo search. |
| **WHILE** | `synthesizer - "research" >> planner` | Loop logic driven by the synthesizer's feedback and loop count. |
| **EVALUATE** | `if exec_res["action"] == "research":` | Branching logic in Synthesizer to decide between more research or finality. |
| **RETURN WITH** | `return "research"` / `return "finalize"` | Non-trivial status tokens used to drive the loop or terminate. |
| **@vars** | `shared["topic"]`, `shared["notes"]`, etc. | Shared state dictionary passed between nodes. |

## 3. Logical Functions / Prompts

- **planner**: Generates 3 diverse YAML-formatted search queries. It accepts both the initial topic and optional feedback strings to refine queries in subsequent loops.
- **researcher**: A map-reduce style function. It takes a single query, performs a web search, and extracts brief, relevant facts from the raw search results.
- **synthesizer**: Evaluates accumulated notes against the topic. It outputs YAML specifying an `action` ("research" or "finalize"). If "research", it provides a `feedback` string; if "finalize", it generates the markdown report.

## 4. Control Flow
1.  **Initialization**: The workflow starts with the `planner` generating an initial set of queries based on the `@topic`.
2.  **Research Loop**: A `WHILE` loop (or recursive connection) executes as long as the `synthesizer` returns a `research` status and the `loop_count` is less than 2.
    -   **Map Phase**: The `researcher` function is called for each query in the current batch.
    -   **Tool Call**: Inside the researcher, `search_web` is triggered.
    -   **Reduce Phase**: Results are extracted and appended to the global `@notes` variable.
3.  **Branching**: The `synthesizer` uses **EVALUATE** on the accumulated notes.
    -   **Condition 1**: If gaps are identified, it returns `WITH status="research"`, triggering the loop back to the `planner`.
    -   **Condition 2**: If info is sufficient (or max loops reached), it returns `WITH status="finalize"`.
4.  **Termination**: The workflow returns the final markdown report and exits.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements a recursive map-reduce research agent designed to iteratively gather and synthesize information on a given topic. The process begins with a planning function that generates diverse search queries, which are then processed in parallel by a research function that performs web searches and extracts key facts. A synthesis function then evaluates the collected data to determine if knowledge gaps remain. Using a WHILE loop constrained by a maximum iteration count, the workflow uses EVALUATE to branch between generating additional search queries based on feedback or finalizing a comprehensive markdown report. The workflow utilizes side-effect tool calls to perform live web searches and maintains shared state to accumulate research notes across iterations." --mode workflow

# Step 2 — compile to any target
spl3 splc compile research_flow.spl --lang python/pocketflow
spl3 splc compile research_flow.spl --lang python/langgraph
spl3 splc compile research_flow.spl --lang go
```