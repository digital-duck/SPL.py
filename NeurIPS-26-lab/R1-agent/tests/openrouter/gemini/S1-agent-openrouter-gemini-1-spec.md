## 0. High-level Description
The Research Agent WORKFLOW orchestrates a cyclic search-and-reasoning loop to provide comprehensive answers to user queries. It begins by using a CREATE FUNCTION prompt named `DecideAction` which acts as the central controller, evaluating the current research context against the user question to determine if more information is needed. Using a WHILE loop, the workflow continues as long as the agent decides more research is required. If the agent chooses to search, it triggers a CALL to a web search tool and appends the results to a persistent context variable. When the agent evaluates that it has sufficient information, it breaks the loop and uses the `AnswerQuestion` CREATE FUNCTION to synthesize the gathered research into a final response. The workflow terminates by using RETURN to output the final answer along with the accumulated research context.

## 1. Purpose
This implementation creates an autonomous research assistant that iteratively searches the web and synthesizes information until it can provide a complete answer to a specific question.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** | `create_agent_flow()` / `Flow` | Defines the overall state machine and node connections. |
| **CREATE FUNCTION** | `DecideAction.exec` / `AnswerQuestion.exec` | The raw prompt templates defined within the node methods. |
| **GENERATE** | `call_llm(prompt)` | The actual execution of the LLM call within the nodes. |
| **CALL** | `search_web_duckduckgo(query)` | Side-effect tool call to fetch external data. |
| **EVALUATE** | `if exec_res["action"] == "search":` | Logic branching based on the LLM's YAML "action" field. |
| **WHILE** | `search - "decide" >> decide` | The cyclic graph connection creates a functional loop. |
| **RETURN** | `shared["answer"]` in `main.py` | The final extraction and printing of the result. |
| **@vars** | `shared` dictionary | Shared state passed between nodes (question, context, query). |

## 3. Logical Functions / Prompts

- **DecideAction**
    - **Role**: The "Brain." Determines whether to perform a web search or generate the final answer.
    - **Conventions**: Uses a YAML code block output format. Requires `thinking`, `action` (search/answer), `reason`, and `search_query` or `answer` fields.
- **AnswerQuestion**
    - **Role**: The "Writer." Synthesizes all gathered research into a polished final response.
    - **Conventions**: Takes the original question and the accumulated `context` string; produces a comprehensive markdown-style answer.

## 4. Control Flow
1. **Initial Step**: Initialize `@context` as "No previous search" and `@question` from user input.
2. **Loop (WHILE)**: Enter a loop driven by the `DecideAction` function.
3. **Branching (EVALUATE)**:
    - If `action` is "search":
        - **CALL** `search_web_duckduckgo` using the generated query.
        - Append results to `@context`.
        - Repeat loop.
    - If `action` is "answer":
        - **GENERATE** final response using `AnswerQuestion`.
        - Exit loop.
4. **Termination**: **RETURN** the final answer string and the research history.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The Research Agent WORKFLOW orchestrates a cyclic search-and-reasoning loop to provide comprehensive answers to user queries. It begins by using a CREATE FUNCTION prompt named DecideAction which acts as the central controller, evaluating the current research context against the user question to determine if more information is needed. Using a WHILE loop, the workflow continues as long as the agent decides more research is required. If the agent chooses to search, it triggers a CALL to a web search tool and appends the results to a persistent context variable. When the agent evaluates that it has sufficient information, it breaks the loop and uses the AnswerQuestion CREATE FUNCTION to synthesize the gathered research into a final response. The workflow terminates by using RETURN to output the final answer along with the accumulated research context." --mode workflow

# Step 2 — compile to any target
spl3 splc compile research_agent.spl --lang python/pocketflow
```