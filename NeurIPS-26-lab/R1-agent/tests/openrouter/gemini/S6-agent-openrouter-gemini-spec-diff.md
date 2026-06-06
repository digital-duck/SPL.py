# File Comparison Report

**Files Compared:**
- File 1: `S1-agent-openrouter-gemini-1-spec.md` (.md)
- File 2: `S5-agent-openrouter-gemini-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 16:33:19
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files describe the same fundamental pattern — an iterative research agent that loops between searching and answering — but they differ meaningfully in **precision of loop control**, **naming**, **construct mapping fidelity**, and **prompt design detail**. **File 2 is stronger overall**: it adds an explicit iteration cap (safety bound), uses more precise SPL construct mappings, and produces a richer RETURN WITH payload. **File 1 is stronger in prompt engineering detail** (Section 3), describing YAML output formatting and block scalars that are critical for reliable LLM-driven control flow.

---

## Content Analysis

### File 1 Strengths

- **Prompt engineering specificity** (Section 3): Explicitly describes YAML output format with block scalars (`|`) for parsing robustness — this is operationally important and would survive round-trip regeneration better.
- **"Action Space" framing**: Naming the decision output as an explicit action space (`search` | `answer`) gives a clearer mental model for the LLM's role.
- **Richer DecideAction description**: Calls it the "brain" performing "meta-cognition," and explains *how* the prompt is structured, not just *what* it does.
- **Graph-style Python mapping**: The `search - "decide" >> decide` notation in the construct table hints at a PocketFlow graph definition, which is closer to the actual target code.

### File 2 Strengths

- **Iteration safety bound**: The `iteration < 5` cap is a critical production safeguard missing from File 1. Unbounded WHILE loops over LLM decisions are a real failure mode.
- **More accurate SPL construct usage**: Maps WHILE to `while "search" in action.lower() and iteration < 5:` — this is a complete, copy-pasteable condition, not a graph-edge shorthand.
- **Richer RETURN WITH**: Returns `status`, `final_response`, *and* `iteration` count — the iteration metadata is useful for observability and debugging.
- **Workflow naming**: `ResearchAssistant` is a cleaner, more conventional name than `ResearchAgent` (minor, but "assistant" better reflects the non-autonomous nature).
- **Explicit initialization**: States that `@action` is initialized to `"search"` before the loop — File 1 leaves this implicit.
- **Section 0 is more self-contained**: The high-level description includes the iteration bound and the RETURN WITH payload shape, making it a better input for `text2spl` regeneration.

### Common Elements

- Same 5-section structure (Description → Purpose → Mapping Table → Functions/Prompts → Control Flow → Regeneration)
- Same two logical functions: `DecideAction` (router) and `AnswerQuestion` (synthesizer)
- Same tool: DuckDuckGo web search
- Same SPL constructs: WORKFLOW, GENERATE, CALL, WHILE, EVALUATE, RETURN WITH
- Same regeneration workflow: `text2spl` → `splc compile`
- Both correctly identify shared state (`@vars` / `shared` dict) as the communication mechanism

---

## Detailed Comparison

### Structure & Organization

Both follow an identical 6-section layout (0–5), which is good for consistency. Neither has extraneous sections.

**File 1** uses slightly more narrative prose in Section 4 (Control Flow), which reads well but is less precise. The graph-edge notation in the mapping table (`search - "decide" >> decide`) is framework-specific (PocketFlow) and assumes reader familiarity.

**File 2** is more systematic: Section 4 walks through initialization → loop → branch → exit → return as discrete steps. The mapping table uses standard Python syntax that any reader can parse.

### Logic & Completeness

| Aspect | File 1 | File 2 |
|---|---|---|
| Loop termination | LLM decides "answer" (unbounded) | LLM decides non-"search" OR iteration ≥ 5 |
| Variable initialization | Implicit | Explicit (`@action = "search"`) |
| Return payload | `status="done"` | `status="complete"`, `iteration` count, `final_response` |
| Error/edge cases | None addressed | Iteration cap prevents runaway loops |
| Decision parsing | YAML with block scalars | Simple string containment (`"search" in action.lower()`) |

File 1's YAML-based decision parsing is more robust for complex outputs but more brittle if the LLM deviates from format. File 2's string containment is simpler and more fault-tolerant but less structured.

**File 2 wins on completeness** — the iteration bound and explicit initialization are not optional details; they're load-bearing for correct execution.

**File 1 wins on decision parsing design** — in production, structured YAML output with explicit action fields is more reliable than substring matching.

### Quality & Sophistication

File 1 shows deeper understanding of **prompt engineering** (YAML format constraints, block scalars, action space abstraction). This matters because the spec's primary purpose is to regenerate working SPL, and prompt design directly affects the generated workflow's reliability.

File 2 shows deeper understanding of **systems engineering** (bounded loops, observability via iteration count, explicit state initialization). These are the concerns that prevent production failures.

Neither addresses: exception handling (what if search fails?), context window overflow (unbounded context growth), or token budgets.

### Syntax & Technical Accuracy

- **File 1**: Uses `status="done"` in RETURN WITH — SPL convention is `status="complete"` (per CLAUDE.md: non-complete status raises `WorkflowCompositionError`). This is a **correctness bug**.
- **File 2**: Correctly uses `status="complete"`. Also correctly notes this is "non-trivial" in the mapping table.
- **File 1**: `create_agent_flow()` as the Python equivalent of WORKFLOW is PocketFlow-specific, which is fine but less general.
- **File 2**: `run_research_assistant(user_query)` is a plain function signature, more portable.
- Both use valid `spl3 text2spl` and `spl3 splc compile` commands in Section 5.

---

## Recommendations

### 1. Best Choice: **File 2**

File 2 is the stronger specification for regeneration purposes. It has correct SPL status semantics, an iteration safety bound, explicit state initialization, and a richer return payload. The only significant gap versus File 1 is prompt engineering detail in Section 3.

### 2. Improvements to File 2

1. **Expand Section 3** with File 1's prompt design details: add the YAML output format specification, block scalar convention, and "Action Space" framing to `DecideAction`. This is the single most impactful improvement.
2. **Replace string containment** (`"search" in action.lower()`) with structured output parsing (YAML or JSON with an explicit `action` field). Substring matching will false-positive on answers that mention searching.
3. **Add a note on context growth**: mention that `@context` is append-only and may need truncation or summarization after several iterations.

### 3. Hybrid Approach

Take File 2 as the base and:
- Graft File 1's Section 3 prompt detail (YAML format, block scalars, action space) into File 2's `DecideAction` description.
- Keep File 2's iteration bound, explicit initialization, and `status="complete"`.
- Add File 1's "meta-cognition" framing to the `DecideAction` role description — it communicates intent better than "router/brain."
- Use structured YAML parsing (File 1) instead of substring matching (File 2) in the EVALUATE mapping.

---

## Scoring

| Dimension | File 1 | File 2 | Notes |
|---|---|---|---|
| **Structure** | 8/10 | 8/10 | Identical layout; both well-organized |
| **Logic** | 6/10 | 8/10 | File 1 lacks iteration bound and has wrong status value |
| **Quality** | 7/10 | 8/10 | File 1 has better prompt detail; File 2 has better systems thinking |
| **Syntax** | 6/10 | 9/10 | File 1's `status="done"` is an SPL correctness bug |
| **Overall** | **6.5/10** | **8/10** | File 2 is the better regeneration spec; File 1's prompt detail is its main differentiator |

The `status="done"` issue in File 1 is particularly significant in this codebase — per SPL semantics, a non-`"complete"` status in RETURN WITH / COMMIT raises a `WorkflowCompositionError` in any calling workflow, making File 1's generated SPL silently broken when composed.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-agent-openrouter-gemini-1-spec.md
+++ b/S5-agent-openrouter-gemini-2-spec.md
@@ -1,46 +1,36 @@
 ## 0. High-level Description

-This WORKFLOW implements a recursive Research Agent pattern that autonomously decides between gathering information and synthesizing a final response. The process begins with a WHILE loop that persists as long as the agent determines more information is required. Inside the loop, the `DecideAction` logical function evaluates the user's question against the current research context and produces a structured YAML response. An EVALUATE construct parses this decision: if the agent selects "search," it triggers a CALL to a web search tool and appends the results to the context before repeating the loop. If the agent selects "answer," it exits the loop to trigger the `AnswerQuestion` logical function, which generates the final comprehensive response. The workflow maintains a shared state for the research history and terminates by returning the final synthesized answer.

+The `ResearchAssistant` WORKFLOW implements an iterative research agent pattern designed to synthesize information from external sources before providing a final answer. It begins by initializing a research context and entering a WHILE loop that persists as long as the agent chooses to "search" and the iteration count is under five. Within this loop, the workflow uses GENERATE to invoke the `DecideAction` function, which evaluates the current context against the user query. An EVALUATE block checks the LLM output: if it contains the "search" keyword, the workflow triggers a side-effect via CALL to `search_web` and appends the results to the context; otherwise, it sets the action to "done" to exit the loop. Once the information gathering phase is complete, the workflow uses GENERATE to call `AnswerQuestion` for final synthesis and uses RETURN WITH to provide the final response alongside a "complete" status and the total iteration count.

 

 ## 1. Purpose

-Automates a multi-step research process where an LLM dynamically decides to perform web searches until it has sufficient information to provide a comprehensive answer.

+This implementation automates a multi-step research process where an LLM autonomously decides whether to gather more web data or synthesize a final answer based on current knowledge.

 

 ## 2. SPL ↔ Python Construct Mapping

 

 | SPL Construct | Python Equivalent | Notes |

 | :--- | :--- | :--- |

-| **WORKFLOW** `ResearchAgent` | `create_agent_flow()` in `flow.py` | Defines the overall graph structure. |

-| **CREATE FUNCTION** | `DecideAction.exec` / `AnswerQuestion.exec` | Logical prompt templates for decision making and writing. |

-| **GENERATE** | `call_llm(prompt)` | LLM invocation within node execution. |

-| **CALL** | `search_web_duckduckgo(query)` | Side-effect tool call to fetch external data. |

-| **WHILE** | `search - "decide" >> decide` (cycle) | The loop logic formed by the "search" vs "answer" branch. |

-| **EVALUATE** | `decide - "search" >> search` | Conditional branching based on the LLM's "action" field. |

-| **@vars** | `shared` dictionary | Shared state containing `question`, `context`, and `answer`. |

-| **RETURN WITH** | `return "done"` in `AnswerQuestion` | Signals the terminal state of the agent. |

+| **WORKFLOW** `ResearchAssistant` | `run_research_assistant(user_query)` | The main entry point for the orchestration logic. |

+| **CREATE FUNCTION** | `decide_action`, `answer_question` | Reusable prompt templates wrapped in LLM call logic. |

+| **GENERATE** | `call_llm(prompt)` inside functions | Invokes the OpenRouter/Gemini model to produce text. |

+| **CALL** | `search_web(query)` | Side-effect tool call using the DuckDuckGo Search API. |

+| **WHILE** | `while "search" in action.lower() and iteration < 5:` | Loops until the agent satisfies its info need or hits the limit. |

+| **EVALUATE** | `if "search" in action.lower(): ... else:` | Branches logic based on the LLM's decision string. |

+| **@var** (Shared State) | `context`, `action`, `iteration` | Local variables within the workflow function scope. |

+| **RETURN WITH** | `return {"final_response": ..., "status": "complete", ...}` | Returns final payload with non-trivial "complete" status. |

 

 ## 3. Logical Functions / Prompts

-

-### `DecideAction`

-- **Role**: The "brain" of the agent; performs meta-cognition to determine if the current context is sufficient.

-- **Key Prompt Conventions**: Uses a strict YAML output format with block scalars (`|`) for reasoning and answers to ensure parsing robustness. It maps inputs to an "Action Space" consisting of `search` or `answer`.

-

-### `AnswerQuestion`

-- **Role**: The "writer"; synthesizes all gathered research into a final polished output.

-- **Key Prompt Conventions**: Context-heavy prompt that provides the original question and the accumulated `Research` context (concatenated search results).

+- **DecideAction**: Acts as the router/brain. It takes the query and current context to output a single-word sentinel ("search" or "answer") to control the workflow loop.

+- **AnswerQuestion**: Acts as the synthesizer. It takes the accumulated research findings and the original query to produce a comprehensive final response.

 

 ## 4. Control Flow

-The workflow initializes with a user `question` and an empty `context`. It enters a cycle starting at **DecideAction**, which generates a decision. 

-- Using **EVALUATE** on the action field:

-    - If "search", it captures a `search_query`, performs a **CALL** to the search tool, updates the `@context` variable, and loops back (**WHILE** condition implicit in the "decide" transition).

-    - If "answer", it breaks the cycle.

-- Finally, it triggers **AnswerQuestion** to produce the final result and exits via **RETURN WITH** `status="done"`.

+The workflow starts by setting the initial `@action` to "search". It enters a **WHILE** loop governed by the condition that the action remains "search" and iterations are less than 5. Inside, **GENERATE** `DecideAction` updates the action variable. An **EVALUATE** block checks if the response contains "search"; if true, **CALL** `search_web` is executed, the `@context` is updated with new findings, and the iteration counter increments. If the LLM returns anything else, the loop is terminated by setting the action to "done". Finally, **GENERATE** `AnswerQuestion` creates the result, and the workflow terminates with **RETURN WITH** status "complete".

 

 ## 5. How to Regenerate as SPL

 ```bash

 # Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "This WORKFLOW implements a recursive Research Agent pattern that autonomously decides between gathering information and synthesizing a final response. The process begins with a WHILE loop that persists as long as the agent determines more information is required. Inside the loop, the DecideAction logical function evaluates the user's question against the current research context and produces a structured YAML response. An EVALUATE construct parses this decision: if the agent selects 'search,' it triggers a CALL to a web search tool and appends the results to the context before repeating the loop. If the agent selects 'answer,' it exits the loop to trigger the AnswerQuestion logical function, which generates the final comprehensive response. The workflow maintains a shared state for the research history and terminates by returning the final synthesized answer." --mode workflow

+spl3 text2spl --description "The ResearchAssistant WORKFLOW implements an iterative research agent pattern designed to synthesize information from external sources before providing a final answer. It begins by initializing a research context and entering a WHILE loop that persists as long as the agent chooses to 'search' and the iteration count is under five. Within this loop, the workflow uses GENERATE to invoke the DecideAction function, which evaluates the current context against the user query. An EVALUATE block checks the LLM output: if it contains the 'search' keyword, the workflow triggers a side-effect via CALL to search_web and appends the results to the context; otherwise, it sets the action to 'done' to exit the loop. Once the information gathering phase is complete, the workflow uses GENERATE to call AnswerQuestion for final synthesis and uses RETURN WITH to provide the final response alongside a 'complete' status and the total iteration count." --mode workflow

 

 # Step 2 — compile to any target

-spl3 splc compile <output.spl> --lang python/pocketflow

-spl3 splc compile <output.spl> --lang python/langgraph

-spl3 splc compile <output.spl> --lang go

+spl3 splc compile research_assistant.spl --lang python/pocketflow

+spl3 splc compile research_assistant.spl --lang python/langgraph

+spl3 splc compile research_assistant.spl --lang go

 ```
```
---

*Generated by SPL semantic comparison tool*