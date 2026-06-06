## 0. High-level Description
The `ResearchAssistant` WORKFLOW implements an iterative research agent pattern designed to synthesize information from external sources before providing a final answer. It begins by initializing a research context and entering a WHILE loop that persists as long as the agent chooses to "search" and the iteration count is under five. Within this loop, the workflow uses GENERATE to invoke the `DecideAction` function, which evaluates the current context against the user query. An EVALUATE block checks the LLM output: if it contains the "search" keyword, the workflow triggers a side-effect via CALL to `search_web` and appends the results to the context; otherwise, it sets the action to "done" to exit the loop. Once the information gathering phase is complete, the workflow uses GENERATE to call `AnswerQuestion` for final synthesis and uses RETURN WITH to provide the final response alongside a "complete" status and the total iteration count.

## 1. Purpose
This implementation automates a multi-step research process where an LLM autonomously decides whether to gather more web data or synthesize a final answer based on current knowledge.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `ResearchAssistant` | `run_research_assistant(user_query)` | The main entry point for the orchestration logic. |
| **CREATE FUNCTION** | `decide_action`, `answer_question` | Reusable prompt templates wrapped in LLM call logic. |
| **GENERATE** | `call_llm(prompt)` inside functions | Invokes the OpenRouter/Gemini model to produce text. |
| **CALL** | `search_web(query)` | Side-effect tool call using the DuckDuckGo Search API. |
| **WHILE** | `while "search" in action.lower() and iteration < 5:` | Loops until the agent satisfies its info need or hits the limit. |
| **EVALUATE** | `if "search" in action.lower(): ... else:` | Branches logic based on the LLM's decision string. |
| **@var** (Shared State) | `context`, `action`, `iteration` | Local variables within the workflow function scope. |
| **RETURN WITH** | `return {"final_response": ..., "status": "complete", ...}` | Returns final payload with non-trivial "complete" status. |

## 3. Logical Functions / Prompts
- **DecideAction**: Acts as the router/brain. It takes the query and current context to output a single-word sentinel ("search" or "answer") to control the workflow loop.
- **AnswerQuestion**: Acts as the synthesizer. It takes the accumulated research findings and the original query to produce a comprehensive final response.

## 4. Control Flow
The workflow starts by setting the initial `@action` to "search". It enters a **WHILE** loop governed by the condition that the action remains "search" and iterations are less than 5. Inside, **GENERATE** `DecideAction` updates the action variable. An **EVALUATE** block checks if the response contains "search"; if true, **CALL** `search_web` is executed, the `@context` is updated with new findings, and the iteration counter increments. If the LLM returns anything else, the loop is terminated by setting the action to "done". Finally, **GENERATE** `AnswerQuestion` creates the result, and the workflow terminates with **RETURN WITH** status "complete".

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The ResearchAssistant WORKFLOW implements an iterative research agent pattern designed to synthesize information from external sources before providing a final answer. It begins by initializing a research context and entering a WHILE loop that persists as long as the agent chooses to 'search' and the iteration count is under five. Within this loop, the workflow uses GENERATE to invoke the DecideAction function, which evaluates the current context against the user query. An EVALUATE block checks the LLM output: if it contains the 'search' keyword, the workflow triggers a side-effect via CALL to search_web and appends the results to the context; otherwise, it sets the action to 'done' to exit the loop. Once the information gathering phase is complete, the workflow uses GENERATE to call AnswerQuestion for final synthesis and uses RETURN WITH to provide the final response alongside a 'complete' status and the total iteration count." --mode workflow

# Step 2 — compile to any target
spl3 splc compile research_assistant.spl --lang python/pocketflow
spl3 splc compile research_assistant.spl --lang python/langgraph
spl3 splc compile research_assistant.spl --lang go
```