# File Comparison Report

**Files Compared:**
- File 1: `S1-research-openrouter-gemini-1-spec.md` (.md)
- File 2: `S5-research-openrouter-gemini-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 16:33:35
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files describe an iterative research agent that plans queries, searches the web, extracts facts, and synthesizes a report. **File 2 is stronger overall** — it decomposes the pipeline into more granular, well-named functions with clearer responsibilities, maps SPL constructs more precisely, and covers an additional capability (file writing). File 1 is more concise and uses a PocketFlow-flavored node/edge vocabulary that slightly blurs the SPL abstraction, but its high-level description and control flow narrative read more naturally.

---

## Content Analysis

### File 1 Strengths

- **Cleaner high-level description**: The Section 0 prose is tighter and uses SPL-native terminology ("EVALUATE to branch", "side-effect tool calls", "shared state") without over-specifying implementation details.
- **Map-reduce framing is explicit**: The researcher is described as a "map-reduce style function," which correctly captures the parallel-query-then-aggregate pattern and maps naturally to `CALL PARALLEL`.
- **Control flow narrative is more readable**: Section 4 uses a numbered sequence with clearly labeled phases (Map, Reduce, Branching, Termination) that a reader can follow linearly.
- **Correct `bash` fence in Section 5**: The regeneration block is properly annotated with the `bash` language tag.

### File 2 Strengths

- **Finer-grained function decomposition**: Eight distinct functions (`planner_fn`, `extract_query_fn`, `researcher_fn`, `extractor_fn`, `accumulate_notes_fn`, `synthesizer_fn`, `feedback_generator_fn`, `finalizer_fn`) vs. three in File 1. This is closer to how an actual SPL file would be authored — each `CREATE FUNCTION` does one thing.
- **More complete SPL construct coverage**: Includes `CALL write_file` (file persistence side-effect) and `RETURN WITH status="complete"`, both of which are absent from File 1. The `RETURN WITH` mapping to `{"report": ..., "status": "complete"}` is more precise SPL semantics.
- **Separation of concerns is explicit**: The synthesizer is a pure quality gate (outputs a binary decision), while feedback generation and finalization are separate functions. File 1 overloads the synthesizer with both decision-making and report generation.
- **Each function has a role label**: "strategist", "query optimizer", "data processor", "quality gate", "refinement tool", "content creator" — these labels communicate intent instantly.
- **Additional capability**: The `write_file` tool call for persisting the report to disk reflects a more complete real-world workflow.

### Common Elements

- Both use the same 6-section structure (Sections 0–5) and identical table format for SPL↔Python mapping.
- Both model the core loop as `WHILE` with a cap of 2 iterations.
- Both use `EVALUATE` to branch between "continue researching" and "finalize."
- Both generate 3 search queries per iteration.
- Both reference `search_web` via DuckDuckGo and `call_llm` for LLM invocations.
- Both provide the same `spl3 text2spl` + `spl3 splc compile` regeneration workflow.

---

## Detailed Comparison

### Structure & Organization

Both follow the identical 6-section template, so macro-structure is equivalent. The difference is in **information density per section**:

- **Section 2 (mapping table)**: File 2 has 9 rows vs. File 1's 8, and File 2's rows are more specific (e.g., separating `CALL search_web` and `CALL write_file` instead of a single generic `CALL`). File 1's `WHILE` mapping to `synthesizer - "research" >> planner` leaks PocketFlow edge syntax into what should be an SPL-centric spec.
- **Section 3 (functions)**: File 2 lists 8 functions with one-line role descriptions; File 1 lists 3 with multi-sentence descriptions. File 2's granularity better mirrors how SPL `CREATE FUNCTION` blocks would actually be authored.
- **Section 5 (regeneration)**: Nearly identical, but File 1 uses a `bash`-fenced code block while File 2 uses an untagged fence — a minor formatting gap.

### Logic & Completeness

| Aspect | File 1 | File 2 |
|---|---|---|
| **Query extraction** | Implicit (bundled into planner/researcher) | Explicit `extract_query_fn` — acknowledges the parsing step |
| **Note accumulation** | "Appended to global `@notes`" — hand-waved | Dedicated `accumulate_notes_fn` with de-duplication |
| **Synthesizer scope** | Overloaded: decides AND generates report | Single-responsibility: only decides |
| **Feedback generation** | Implicit in synthesizer | Explicit `feedback_generator_fn` |
| **Report finalization** | Done by synthesizer | Separate `finalizer_fn` |
| **File output** | Not covered | `CALL write_file` mapped |
| **Loop termination** | `RETURN WITH status="finalize"` | `RETURN WITH status="complete"` (matches SPL convention) |

File 2 is more **logically complete** — every non-trivial operation has a named function, and no function is overloaded with multiple responsibilities. File 1 is more **logically compact**, which is fine for a high-level overview but would produce a less faithful SPL reconstruction.

File 2's use of `status="complete"` aligns with SPL's `COMMIT @var WITH STATUS = 'complete'` convention, while File 1's `status="finalize"` is a custom token that would need additional handling.

### Quality & Sophistication

- **Abstraction level**: File 2 operates at the right abstraction level for an SPL spec — each function maps 1:1 to a `CREATE FUNCTION` block. File 1 groups multiple logical steps into coarser nodes, which is more natural for a PocketFlow graph but less useful for SPL regeneration.
- **Role annotations**: File 2's labeling ("strategist", "quality gate", etc.) adds a layer of semantic clarity that aids both human understanding and LLM-driven regeneration.
- **De-duplication awareness**: File 2 explicitly mentions de-duplication in `accumulate_notes_fn`, reflecting a real-world concern that File 1 ignores.
- **Map-reduce terminology**: File 1's explicit use of "map-reduce" is more sophisticated from a distributed-systems perspective and maps well to `CALL PARALLEL`.

### Syntax & Technical Accuracy

- **SPL fidelity**: File 2's construct mapping is more accurate to SPL semantics. File 1's `synthesizer - "research" >> planner` is PocketFlow edge syntax, not SPL.
- **Status tokens**: File 2 uses `"complete"` which is the canonical SPL `COMMIT` status. File 1 uses `"finalize"` — valid but non-standard.
- **Code fences**: File 1 properly uses ` ```bash `, File 2 uses bare ` ``` ` — minor but File 1 is more correct.
- **Placeholder usage**: File 2 uses `<output.spl>` in Section 5 (a placeholder), while File 1 uses the concrete `research_flow.spl`. File 1 is more immediately usable.

---

## Recommendations

### 1. Best Choice: **File 2**

File 2 is the better spec for SPL regeneration because its function decomposition maps 1:1 to `CREATE FUNCTION` blocks, its construct table is more accurate, and it covers the complete pipeline including file persistence. If the goal is to feed this spec into `text2spl` and get a faithful `.spl` file, File 2 will produce a closer result.

### 2. Improvements for File 1

- **Decompose the synthesizer**: Split into three functions (synthesizer for decision, feedback_generator for gap analysis, finalizer for report writing).
- **Add `extract_query_fn`**: Make the query parsing step explicit.
- **Add `write_file` tool call**: Cover file persistence.
- **Fix PocketFlow leakage**: Replace `synthesizer - "research" >> planner` with SPL-native terminology in the mapping table.
- **Use `status="complete"`** instead of `"finalize"` to match SPL conventions.

### 3. Hybrid Approach

Take File 2's function decomposition and construct mapping as the foundation, then:
- Adopt File 1's Section 0 prose style (tighter, more SPL-native language).
- Use File 1's Section 4 structure with labeled phases (Map/Reduce/Branching/Termination) for readability.
- Keep File 1's explicit "map-reduce" framing for the parallel research step.
- Use File 1's `bash`-tagged code fences and concrete filename in Section 5.

---

## Scoring

| Dimension | File 1 | File 2 | Notes |
|---|---|---|---|
| **Structure** | 7/10 | 8/10 | Both follow the template; File 2's granularity is better suited to SPL |
| **Logic** | 6/10 | 9/10 | File 2 covers every logical step explicitly; File 1 bundles and omits |
| **Quality** | 7/10 | 8/10 | File 2's role labels and SRP decomposition are more professional |
| **Overall** | **6.5/10** | **8.5/10** | File 2 is the stronger spec for faithful SPL regeneration |

**Bottom line**: File 2 is more complete, more accurate to SPL semantics, and would produce a better `.spl` file if fed back through `text2spl`. File 1 reads more naturally as a human summary but sacrifices fidelity by grouping responsibilities and leaking PocketFlow idioms.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-research-openrouter-gemini-1-spec.md
+++ b/S5-research-openrouter-gemini-2-spec.md
@@ -1,46 +1,44 @@
 ## 0. High-level Description

-This WORKFLOW implements a recursive map-reduce research agent designed to iteratively gather and synthesize information on a given topic. The process begins with a planning function that generates diverse search queries, which are then processed in parallel by a research function that performs web searches and extracts key facts. A synthesis function then evaluates the collected data to determine if knowledge gaps remain. Using a WHILE loop constrained by a maximum iteration count, the workflow uses EVALUATE to branch between generating additional search queries based on feedback or finalizing a comprehensive markdown report. The workflow utilizes side-effect tool calls to perform live web searches and maintains shared state to accumulate research notes across iterations.

+The Research_Agent WORKFLOW implements an iterative research pattern designed to gather information and synthesize a final report. It begins by using the planner_fn to generate search queries, which are then processed by researcher_fn and passed to the search_web tool to fetch external data. This process is governed by a WHILE loop that executes up to two iterations, during which search results are processed by extractor_fn and merged into a persistent state using accumulate_notes_fn. Within the loop, the workflow employs an EVALUATE construct on the output of synthesizer_fn to determine if the gathered information is sufficient; if not, it triggers feedback_generator_fn to refine the next planning phase, otherwise it breaks the loop via a RETURN WITH status="complete" logic. Finally, the workflow uses finalizer_fn to generate a Markdown report from the accumulated notes and utilizes a side-effect tool call to save the result to a file.

 

 ## 1. Purpose

-The workflow automates deep topical research by iteratively searching the web, extracting facts, and synthesizing a final report until sufficient information is gathered or a loop limit is reached.

+This implementation automates the process of multi-step web research, fact extraction, and report synthesis for a given topic using an iterative feedback loop.

 

 ## 2. SPL ↔ Python Construct Mapping

 

 | SPL Construct | Python Equivalent | Notes |

 | :--- | :--- | :--- |

-| **WORKFLOW** `deep_research` | `create_deep_research_flow()` | Orchestrates the Planner, Researcher, and Synthesizer nodes. |

-| **CREATE FUNCTION** | `PlannerNode`, `ResearcherNode`, `SynthesizerNode` | Prompt templates for query generation, fact extraction, and synthesis. |

-| **GENERATE** | `call_llm(prompt)` | LLM invocations within the `exec` methods of the nodes. |

-| **CALL** | `search_web(query)` | Side-effect tool call to DuckDuckGo search. |

-| **WHILE** | `synthesizer - "research" >> planner` | Loop logic driven by the synthesizer's feedback and loop count. |

-| **EVALUATE** | `if exec_res["action"] == "research":` | Branching logic in Synthesizer to decide between more research or finality. |

-| **RETURN WITH** | `return "research"` / `return "finalize"` | Non-trivial status tokens used to drive the loop or terminate. |

-| **@vars** | `shared["topic"]`, `shared["notes"]`, etc. | Shared state dictionary passed between nodes. |

+| **WORKFLOW Research_Agent** | `run_research_agent(...)` | The main entry point for the orchestration logic. |

+| **CREATE FUNCTION** | `def ..._fn(...)` | Python functions containing prompt templates and LLM calls. |

+| **GENERATE** | `call_llm(prompt)` | Used within function implementations to produce LLM content. |

+| **CALL search_web** | `search_web(query)` | A tool call using the DuckDuckGo Search API. |

+| **CALL write_file** | `fh.write(report)` | A side-effect tool call to persist the final report. |

+| **WHILE** | `while loop_count < 2` | Iterative loop to deepen research if initial results are insufficient. |

+| **EVALUATE** | `if "Need More Info" in status` | Branching logic based on the LLM's assessment of note sufficiency. |

+| **@vars** | `all_notes`, `feedback`, `report` | Shared state variables maintained across the workflow. |

+| **RETURN WITH** | `return {"report": ..., "status": "complete"}` | Terminates the workflow with a "complete" status metadata. |

 

 ## 3. Logical Functions / Prompts

 

-- **planner**: Generates 3 diverse YAML-formatted search queries. It accepts both the initial topic and optional feedback strings to refine queries in subsequent loops.

-- **researcher**: A map-reduce style function. It takes a single query, performs a web search, and extracts brief, relevant facts from the raw search results.

-- **synthesizer**: Evaluates accumulated notes against the topic. It outputs YAML specifying an `action` ("research" or "finalize"). If "research", it provides a `feedback` string; if "finalize", it generates the markdown report.

+- **planner_fn**: Acts as the strategist. It takes a topic and feedback to generate exactly three distinct search queries using the `QUERY_N:` sentinel format.

+- **extract_query_fn**: A utility parser. It extracts a specific query string from the planner's formatted output based on a position index.

+- **researcher_fn**: A query optimizer. It transforms raw query ideas into optimized strings suitable for a search engine.

+- **extractor_fn**: A data processor. It filters raw search results to extract key facts while removing "fluff."

+- **accumulate_notes_fn**: A state merger. It takes existing notes and three new batches, merging them into a coherent, de-duplicated collection.

+- **synthesizer_fn**: A quality gate. It outputs "Need More Info" or "Sufficient Info" to drive the workflow's control flow.

+- **feedback_generator_fn**: A refinement tool. If research is insufficient, it identifies gaps to guide the next iteration.

+- **finalizer_fn**: A content creator. It transforms the final collection of notes into a polished Markdown report.

 

 ## 4. Control Flow

-1.  **Initialization**: The workflow starts with the `planner` generating an initial set of queries based on the `@topic`.

-2.  **Research Loop**: A `WHILE` loop (or recursive connection) executes as long as the `synthesizer` returns a `research` status and the `loop_count` is less than 2.

-    -   **Map Phase**: The `researcher` function is called for each query in the current batch.

-    -   **Tool Call**: Inside the researcher, `search_web` is triggered.

-    -   **Reduce Phase**: Results are extracted and appended to the global `@notes` variable.

-3.  **Branching**: The `synthesizer` uses **EVALUATE** on the accumulated notes.

-    -   **Condition 1**: If gaps are identified, it returns `WITH status="research"`, triggering the loop back to the `planner`.

-    -   **Condition 2**: If info is sufficient (or max loops reached), it returns `WITH status="finalize"`.

-4.  **Termination**: The workflow returns the final markdown report and exits.

+The workflow starts by initializing the research state and entering a **WHILE** loop capped at two iterations. Inside the loop, three queries are generated, optimized, and executed via the `search_web` tool. The results are extracted and merged into `@all_notes`. An **EVALUATE** step checks the sufficiency of the notes: if the LLM identifies a need for more info, it generates feedback and continues the loop; if info is sufficient, it breaks early. After the loop, the workflow generates the final report, writes it to disk, and uses **RETURN WITH status="complete"** to signal successful termination.

 

 ## 5. How to Regenerate as SPL

-```bash

+```

 # Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "This WORKFLOW implements a recursive map-reduce research agent designed to iteratively gather and synthesize information on a given topic. The process begins with a planning function that generates diverse search queries, which are then processed in parallel by a research function that performs web searches and extracts key facts. A synthesis function then evaluates the collected data to determine if knowledge gaps remain. Using a WHILE loop constrained by a maximum iteration count, the workflow uses EVALUATE to branch between generating additional search queries based on feedback or finalizing a comprehensive markdown report. The workflow utilizes side-effect tool calls to perform live web searches and maintains shared state to accumulate research notes across iterations." --mode workflow

+spl3 text2spl --description "The Research_Agent WORKFLOW implements an iterative research pattern designed to gather information and synthesize a final report. It begins by using the planner_fn to generate search queries, which are then processed by researcher_fn and passed to the search_web tool to fetch external data. This process is governed by a WHILE loop that executes up to two iterations, during which search results are processed by extractor_fn and merged into a persistent state using accumulate_notes_fn. Within the loop, the workflow employs an EVALUATE construct on the output of synthesizer_fn to determine if the gathered information is sufficient; if not, it triggers feedback_generator_fn to refine the next planning phase, otherwise it breaks the loop via a RETURN WITH status='complete' logic. Finally, the workflow uses finalizer_fn to generate a Markdown report from the accumulated notes and utilizes a side-effect tool call to save the result to a file." --mode workflow

 

 # Step 2 — compile to any target

-spl3 splc compile research_flow.spl --lang python/pocketflow

-spl3 splc compile research_flow.spl --lang python/langgraph

-spl3 splc compile research_flow.spl --lang go

+spl3 splc compile <output.spl> --lang python/pocketflow

+spl3 splc compile <output.spl> --lang python/langgraph

+spl3 splc compile <output.spl> --lang go

 ```
```
---

*Generated by SPL semantic comparison tool*