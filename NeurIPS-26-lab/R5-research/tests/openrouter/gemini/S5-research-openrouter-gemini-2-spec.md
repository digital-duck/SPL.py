## 0. High-level Description
The Research_Agent WORKFLOW implements an iterative research pattern designed to gather information and synthesize a final report. It begins by using the planner_fn to generate search queries, which are then processed by researcher_fn and passed to the search_web tool to fetch external data. This process is governed by a WHILE loop that executes up to two iterations, during which search results are processed by extractor_fn and merged into a persistent state using accumulate_notes_fn. Within the loop, the workflow employs an EVALUATE construct on the output of synthesizer_fn to determine if the gathered information is sufficient; if not, it triggers feedback_generator_fn to refine the next planning phase, otherwise it breaks the loop via a RETURN WITH status="complete" logic. Finally, the workflow uses finalizer_fn to generate a Markdown report from the accumulated notes and utilizes a side-effect tool call to save the result to a file.

## 1. Purpose
This implementation automates the process of multi-step web research, fact extraction, and report synthesis for a given topic using an iterative feedback loop.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW Research_Agent** | `run_research_agent(...)` | The main entry point for the orchestration logic. |
| **CREATE FUNCTION** | `def ..._fn(...)` | Python functions containing prompt templates and LLM calls. |
| **GENERATE** | `call_llm(prompt)` | Used within function implementations to produce LLM content. |
| **CALL search_web** | `search_web(query)` | A tool call using the DuckDuckGo Search API. |
| **CALL write_file** | `fh.write(report)` | A side-effect tool call to persist the final report. |
| **WHILE** | `while loop_count < 2` | Iterative loop to deepen research if initial results are insufficient. |
| **EVALUATE** | `if "Need More Info" in status` | Branching logic based on the LLM's assessment of note sufficiency. |
| **@vars** | `all_notes`, `feedback`, `report` | Shared state variables maintained across the workflow. |
| **RETURN WITH** | `return {"report": ..., "status": "complete"}` | Terminates the workflow with a "complete" status metadata. |

## 3. Logical Functions / Prompts

- **planner_fn**: Acts as the strategist. It takes a topic and feedback to generate exactly three distinct search queries using the `QUERY_N:` sentinel format.
- **extract_query_fn**: A utility parser. It extracts a specific query string from the planner's formatted output based on a position index.
- **researcher_fn**: A query optimizer. It transforms raw query ideas into optimized strings suitable for a search engine.
- **extractor_fn**: A data processor. It filters raw search results to extract key facts while removing "fluff."
- **accumulate_notes_fn**: A state merger. It takes existing notes and three new batches, merging them into a coherent, de-duplicated collection.
- **synthesizer_fn**: A quality gate. It outputs "Need More Info" or "Sufficient Info" to drive the workflow's control flow.
- **feedback_generator_fn**: A refinement tool. If research is insufficient, it identifies gaps to guide the next iteration.
- **finalizer_fn**: A content creator. It transforms the final collection of notes into a polished Markdown report.

## 4. Control Flow
The workflow starts by initializing the research state and entering a **WHILE** loop capped at two iterations. Inside the loop, three queries are generated, optimized, and executed via the `search_web` tool. The results are extracted and merged into `@all_notes`. An **EVALUATE** step checks the sufficiency of the notes: if the LLM identifies a need for more info, it generates feedback and continues the loop; if info is sufficient, it breaks early. After the loop, the workflow generates the final report, writes it to disk, and uses **RETURN WITH status="complete"** to signal successful termination.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The Research_Agent WORKFLOW implements an iterative research pattern designed to gather information and synthesize a final report. It begins by using the planner_fn to generate search queries, which are then processed by researcher_fn and passed to the search_web tool to fetch external data. This process is governed by a WHILE loop that executes up to two iterations, during which search results are processed by extractor_fn and merged into a persistent state using accumulate_notes_fn. Within the loop, the workflow employs an EVALUATE construct on the output of synthesizer_fn to determine if the gathered information is sufficient; if not, it triggers feedback_generator_fn to refine the next planning phase, otherwise it breaks the loop via a RETURN WITH status='complete' logic. Finally, the workflow uses finalizer_fn to generate a Markdown report from the accumulated notes and utilizes a side-effect tool call to save the result to a file." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```