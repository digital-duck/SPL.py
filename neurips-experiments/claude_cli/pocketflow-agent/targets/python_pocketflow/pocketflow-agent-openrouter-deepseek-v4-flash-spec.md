## 0. High-level Description

This workflow implements a ReAct (Reasoning + Acting) research agent that iteratively decides whether to search the web or answer a question. It is declared as a WORKFLOW named `react_research`. Two prompt templates are defined as CREATE FUNCTION blocks: `DecideAction` (which takes `{question}` and `{context}` and outputs a YAML decision with `action: search` or `action: answer`) and `AnswerQuestion` (which synthesizes a final answer from the full research context). The core loop is a WHILE construct that repeats until the DecideAction function returns an “answer” action or a maximum iteration count is reached. Inside the loop, a GENERATE call to an LLM (using the `DecideAction` function) stores the decision in `@decision`. An EVALUATE block then inspects `@decision` for the substring `'action: answer'`; if found, control exits the loop and proceeds to the answer branch; otherwise, a CALL side-effect tool `web_search` is invoked (using the search query extracted from the YAML decision) and the results are appended to `@context`. The loop then repeats. After the loop terminates, a final GENERATE call to the `AnswerQuestion` function produces `@answer`, and the workflow returns with a RETURN statement that includes the answer, a status (`"complete"` or `"max_iterations"`), and the iteration count. The entire state is managed via SPL `@vars` (shared store). There is no explicit exception handling in this implementation, though the prompts include instructions to handle YAML parsing errors gracefully.

## 1. Purpose

This implementation enables an end user to ask a research question and receive a synthesized answer, automatically performing iterative web searches until sufficient context is gathered or a maximum number of search rounds is reached.

## 2. SPL ↔ Python—PocketFlow Construct Mapping

| SPL Construct | Python—PocketFlow Equivalent | Notes |
|---------------|------------------------------|-------|
| `WORKFLOW react_research` | `main()` function + `build_flow()` | The workflow is defined implicitly by the flow wiring and CLI entry point. |
| `CREATE FUNCTION DecideAction` | String constant `DECIDEACTION_PROMPT` | Prompt template with `{question}` and `{context}` slots. |
| `CREATE FUNCTION AnswerQuestion` | String constant `ANSWERQUESTION_PROMPT` | Prompt template with `{question}` and `{context}` slots. |
| `GENERATE DecideAction(...) INTO @decision` | `DecideNode.exec()` → `_call_llm(...)` | LLM call stores result in `shared["decision"]`. |
| `GENERATE AnswerQuestion(...) INTO @answer` | `AnswerNode.exec()` → `_call_llm(...)` | Final LLM call stores result in `shared["answer"]`. |
| `EVALUATE @decision WHEN contains('action: answer') THEN ... ELSE ...` | `DecideNode.post()` → `if 'action: answer' in exec_res: return "answer"` | Routes to answer branch or search branch. |
| `WHILE <condition> DO ... END` | Implicit via `DecideNode.post()` returning `"search"` and `SearchNode.post()` returning `"decide"` | The loop is encoded as a back‑edge in the flow graph; condition is checked in `DecideNode.post()` (iteration count and action). |
| `CALL web_search(@decision) INTO @search_results` | `SearchNode.exec()` → `_web_search(decision)` | Side‑effect tool call; result stored in `shared["search_results"]`. |
| `RETURN @answer WITH status=..., iterations=...` | `AnswerNode.post()` prints and sets `shared["status"]` | No explicit `RETURN` statement; metadata is stored in shared state and printed. |
| Shared state (`@question`, `@context`, `@iteration`, etc.) | `shared` dictionary in `main()` | All variables are stored in the shared dict passed through the flow. |
| `EXCEPTION WHEN ...` | Not present | No exception handling in this implementation. |

## 3. Logical Functions / Prompts

### DecideAction
- **Role**: Determines the next action: either perform a web search or produce a final answer.
- **Key prompt conventions**:
  - Asks the LLM to think step‑by‑step.
  - Output must be in YAML format with keys `reasoning`, `action`, and `search_query`.
  - Action must be either `search` or `answer`.
  - Includes an instruction to ensure valid YAML and to correct syntax errors if they occur.
- **Slots**: `{question}`, `{context}`

### AnswerQuestion
- **Role**: Synthesizes a comprehensive final answer from the entire research context.
- **Key prompt conventions**:
  - Directs the LLM to provide a thorough, well‑structured response.
  - Asks to reference key findings and sources.
- **Slots**: `{question}`, `{context}`

## 4. Control Flow

1. **Initialization**: The workflow receives `@question` and `@max_iterations`. `@context` is initialized with the question, `@iteration` is set to 0.
2. **Loop entry** (WHILE): The `DecideAction` function is generated with `@question` and `@context`, storing the result in `@decision`.
3. **Branching** (EVALUATE):
   - If `@decision` contains the substring `'action: answer'` (or the iteration count exceeds `@max_iterations`), the workflow proceeds to the **answer** branch.
   - Otherwise, it goes to the **search** branch.
4. **Search branch** (CALL): The `web_search` tool is called with `@decision`. The tool extracts the `search_query` from the YAML and returns results. These results are appended to `@context` and `@iteration` is incremented. Control returns to step 2 (WHILE back‑edge).
5. **Answer branch**: The `AnswerQuestion` function is generated with `@question` and `@context`, producing `@answer`.
6. **Termination** (RETURN): The workflow returns `@answer` with metadata: `status` set to `"complete"` if iterations were below max, otherwise `"max_iterations"`, and the iteration count.

## 5. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```