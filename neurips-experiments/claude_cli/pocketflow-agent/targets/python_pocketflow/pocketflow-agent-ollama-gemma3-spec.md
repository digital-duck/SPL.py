## 0. High-level Description
This workflow, named `react_research`, is a deterministic LLM orchestration designed to investigate a given question, iteratively refining its understanding through a combination of LLM reasoning, web search, and a structured decision-making process. The workflow begins by assessing whether the question can be answered with the current context. If not, it initiates a web search to gather additional information, updating the research context accordingly. This iterative search and analysis continues until a comprehensive answer is generated or a maximum number of iterations is reached. The workflow utilizes a multi-model approach integrating an LLM for reasoning and decision-making, a web search tool for information retrieval, and a structured approach managed through defined prompts and variables. Side-effects, like file writes and web searches, are handled via designated "tool" calls. Exception handling is included to gracefully manage potential errors during the process. The workflow returns the final answer with metadata summarizing the findings and execution status.

## 1. Purpose
This implementation provides a system for systematically investigating a user-provided question using an LLM and web search, returning a comprehensive answer after iterative refinement.

## 2. SPL ↔ Python — PocketFlow Construct Mapping
| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `Flow` object creation in PocketFlow | Defines the overall orchestration flow. |
| `CREATE FUNCTION <name>` | `Node` class definition in PocketFlow | Represents a reusable prompt template and its associated logic. |
| `GENERATE <fn>(...) INTO @<var>` | `Node.exec()` method call in PocketFlow | Executes the prompt template and stores the LLM output in a PocketFlow variable. |
| `CALL <tool>(...) INTO @<var>` | `Node.post()` method call with tool call in PocketFlow | Executes a side-effect tool (web search in this case) and stores the result in a PocketFlow variable. |
| `WHILE <cond> DO ... END` | Loop control within the `Node.post()` method using shared state and iterative calls. | The WHILE loop continues until a specific condition is met. |
| `EVALUATE @<var> WHEN contains('...') THEN ... ELSE ... END` | Conditional logic within `Node.post()` based on the LLM output and shared state. | Uses the LLM output to make decisions and branch the execution flow. |
| `RETURN @<var> WITH <k>=<v>, ...` | `Node.post()` method returns a dictionary of metadata upon completion. | Returns metadata such as status, iterations, and the final answer. |
| `EXCEPTION WHEN <Type> THEN ...` | Custom exception handlers within the `Node` class. (Not explicitly present in this example but could be added for robustness) | Provides a mechanism to handle potential errors and exceptions. |
| Shared state (@vars) | `shared` dictionary in PocketFlow | Stores intermediate results, context, and variables used across multiple nodes. |

## 3. Logical Functions / Prompts
- **`DECIDEACTION_PROMPT`**:
    - **Role**:  Decision-making template.  It determines whether the LLM should "answer" or "search" based on the current context and question.
    - **Key Prompt Conventions**: Uses a step-by-step reasoning approach, explicitly requesting the LLM to analyze gaps and provide a decision in a YAML format.  The output *must* be valid YAML to ensure consistent parsing.  Sentinel tokens are not explicitly used, but the YAML format acts as a structural constraint. Scoring is implicit in the LLM’s response quality.
    - **Output Format**: YAML with `reasoning` and `action` keys.
- **`ANSWERQUESTION_PROMPT`**:
    - **Role**: Synthesis template. It takes the research context and question to generate a comprehensive answer using the LLM.
    - **Key Prompt Conventions**:  Instructs the LLM to synthesize a thorough response referencing key findings and sources. Sentinel tokens are not explicitly used, but the consistent prompt structure is crucial. Scoring is implicit in the LLM’s response quality.
    - **Output Format**: A free-form text response.
- **`web_search(query)`**:
    - **Role**:  Side-effect tool.  Performs a web search using DuckDuckGo, extracting the search query from the input YAML.
    - **Key Prompt Conventions**: Uses the `search_query` field from the input YAML, allowing flexible search terms.  Error handling is included to handle cases where no results are found.
    - **Output Format**: A string containing the search results.

## 4. Control Flow
The workflow's execution follows a `WHILE` loop, driven by the `DECIDEACTION` node. Initially, the `DECIDEACTION` node is executed, which uses the `DECIDEACTION_PROMPT` to determine whether to `search` or `answer`.

1.  **Initialization**: The `DECIDEACTION` node is run, setting up the initial shared state (question, max_iterations, context).
2.  **Decision**: The `DECIDEACTION_PROMPT` generates a decision (search or answer).
3.  **Loop**:
    *   If the decision is "search", the `SEARCH` node is executed, initiating a web search using the `web_search` tool. The search results are added to the context.
    *   If the decision is "answer", the `ANSWERQUESTION` node is executed, generating the final answer based on the accumulated research context.
4.  **Termination**: The `WHILE` loop continues until the `DECIDEACTION_PROMPT` determines that the question has been answered, or the `max_iterations` limit is reached. The workflow then exits, returning the final answer and metadata.

## 5.  Summary
The `react_research` workflow is a robust and flexible system for investigating questions using an LLM and web search. It’s designed for iterative refinement, with a clear decision-making process and structured data handling through PocketFlow. The use of well-defined prompts and the careful management of shared state allows for a deterministic and repeatable workflow.
