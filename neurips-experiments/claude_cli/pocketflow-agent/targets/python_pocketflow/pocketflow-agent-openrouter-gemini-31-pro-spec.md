## 0. High-level Description
The `react_research` WORKFLOW implements an iterative ReAct pattern to autonomously gather information and answer user questions. Execution begins with a WHILE loop that continues as long as the iteration count is less than the specified maximum. Within the loop, a GENERATE statement calls the DecideAction function to prompt the llama3.2 model, which outputs a YAML-formatted decision based on the current context. An EVALUATE construct then inspects this decision; WHEN it contains 'action: answer', the workflow breaks out of the loop, ELSE it executes a CALL to a web_search tool, appends the results to the context, and increments the iteration counter. After the loop terminates, a final GENERATE step invokes the AnswerQuestion function to synthesize the accumulated research into a coherent response. The workflow concludes with a RETURN statement that outputs the final answer along with metadata indicating the termination status and total iterations.

## 1. Purpose
This workflow provides an autonomous, iterative research agent that searches the web to gather sufficient context before synthesizing a comprehensive and accurate answer to a user's question.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
| :--- | :--- | :--- |
| `WORKFLOW` | `build_flow() -> Flow` & `@click.command() main()` | Orchestrates the nodes and defines the initial staging area (`shared` dict). |
| `CREATE FUNCTION` | Global string constants | `DECIDEACTION_PROMPT` and `ANSWERQUESTION_PROMPT` act as the reusable prompt templates. |
| `GENERATE` | `Node.exec()` calling `_call_llm()` | LLM generation logic isolated in the `Transform` step of the ETL node pattern. |
| `CALL` | `Node.exec()` calling `_web_search()` | Side-effect tool invocations handled exactly like LLM generation within a Node's `exec()`. |
| `EVALUATE` | `DecideNode.post()` `if/elif` statements | Branching logic routes the graph by returning edge names (e.g., `"answer"` vs `"search"`). |
| `WHILE` | Cyclic edges (`search - "decide" >> decide`) | The loop is formed by a back-edge in the graph, guarded by an iteration counter in `post()`. |
| `RETURN` | `AnswerNode.post()` returning `None` | Returning `None` terminates the PocketFlow graph. Final variables are flushed to the console/state. |
| shared state (`@var`) | `shared` dictionary | The ETL staging area passed between `prep()`, `exec()`, and `post()` methods to maintain state. |

## 3. Logical Functions / Prompts

### DecideAction
* **Role**: Evaluates the current research context to determine if the agent has enough information to answer the question or if it needs to search for more data.
* **Key Conventions**: 
  * Expects strict YAML formatting.
  * Outputs three fields: `reasoning` (step-by-step analysis), `action` (the sentinel token), and `search_query`.
  * Uses sentinel tokens `"search"` or `"answer"` to drive downstream routing.

### AnswerQuestion
* **Role**: Synthesizes the final response presented to the user.
* **Key Conventions**: 
  * Ingests the original `{question}` and the fully accumulated `{context}`.
  * Instructed to provide a thorough, well-structured response that references key findings without outputting intermediate reasoning syntax.

## 4. Control Flow

1. **Initial Step**: The workflow initializes the shared state, setting the starting `@context` to include the original question, and sets `@iteration` to 0. It enters the `DecideNode`.
2. **Loop Condition**: The workflow effectively operates a `WHILE` loop governed by `@iteration < @max_iterations`. (In PocketFlow, this is evaluated dynamically during the `DecideNode.post` routing).
3. **Branch Logic**: 
   * `GENERATE DecideAction INTO @decision`.
   * `EVALUATE @decision` to check for the sentinel token.
   * `WHEN contains('action: answer')` (or if max iterations are reached): Break the loop and transition to the `AnswerNode`.
   * `ELSE`: Transition to `SearchNode`. `CALL web_search INTO @search_results`, append the results to `@context`, increment `@iteration`, and loop back to the `DecideNode`.
4. **Termination**: `GENERATE AnswerQuestion INTO @answer`. Finally, `RETURN @answer WITH status=@status, iteration=@iteration`, terminating the execution.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```