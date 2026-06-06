## 0. High-level Description
The `SearchAndAnswer` WORKFLOW implements a self-correcting information retrieval pattern that iteratively decides whether to perform a web search or provide a final response. The workflow begins by initializing a `@context` variable and enters a WHILE loop governed by a maximum iteration threshold to prevent infinite loops. Inside the loop, it uses the `DecideAction` FUNCTION to analyze the current state, followed by an EVALUATE block that branches based on whether the LLM output contains the 'search' keyword. If a search is required, the workflow performs a side-effect via a CALL to the `web_search` tool, appends the results to the `@context`, and increments the iteration counter. Once the LLM determines it has sufficient information, it invokes the `AnswerQuestion` FUNCTION to generate the final output and exits via a RETURN statement. If the loop completes without a definitive 'answer' decision, a fallback GENERATE call ensures a final answer is produced before returning with a 'max_iterations' status.

## 1. Purpose
This implementation automates a multi-step research process where an LLM autonomously decides to gather external data via web search to provide a factual, context-aware answer to a user query.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| `WORKFLOW SearchAndAnswer` | `class SearchAndAnswerWorkflow(Flow)` | The class encapsulates the entire logic and state. |
| `CREATE FUNCTION <name>` | `def <name>_fn(...)` | Python functions containing f-string templates. |
| `GENERATE <fn> INTO @var` | `self.state["var"] = <fn>(...)` | Calling the LLM-wrapped function and storing the result. |
| `CALL web_search(...)` | `web_search(query)` | Invocation of the DuckDuckGo search utility. |
| `WHILE <cond> DO` | `while self.state["iteration"] < ...:` | Loop controlling the search-refinement cycle. |
| `EVALUATE @action` | `if "search" in self.state["action"].lower():` | Conditional branching based on LLM decision string. |
| `@var := <value>` | `self.state["var"] = <value>` | Updates to the internal state dictionary. |
| `RETURN @ans WITH ...` | `return {"answer": ..., "status": ...}` | Returning a dictionary with result and metadata. |
| `EXCEPTION` | `try...except` / `raise` | Error handling in `call_llm` and `web_search`. |

## 3. Logical Functions / Prompts

### DecideAction
- **Role**: Acts as the router/orchestrator for the workflow.
- **Conventions**: Returns one of two specific sentinel tokens: 'search' or 'answer'. It evaluates the gap between the current `@context` and the `@question`.

### AnswerQuestion
- **Role**: The final synthesis engine.
- **Conventions**: Consolidates all accumulated `@context` (original question + multiple search results) into a coherent, comprehensive prose response.

## 4. Control Flow
1.  **Initialize**: Set `@iteration` to 0, `@context` to the original question, and `@status` to 'in_progress'.
2.  **Loop**: Enter a **WHILE** loop that runs as long as `@iteration < 3`.
3.  **Decide**: **GENERATE** a decision via `DecideAction`.
4.  **Branch**: **EVALUATE** the decision.
    - **WHEN** 'search': **CALL** `web_search`, update `@context` with results, increment `@iteration`, and continue loop.
    - **ELSE** ('answer'): **GENERATE** `AnswerQuestion` and **RETURN** immediately with `status='complete'`.
5.  **Termination**: If the loop exits due to `@max_iterations`, **GENERATE** a final `AnswerQuestion` and **RETURN** with `status='max_iterations'`.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The SearchAndAnswer WORKFLOW implements a self-correcting information retrieval pattern... [copy full Section 0]" --mode workflow

# Step 2 — compile to any target
spl3 splc compile search_answer.spl --lang python/pocketflow
spl3 splc compile search_answer.spl --lang python/langgraph
spl3 splc compile search_answer.spl --lang go
```