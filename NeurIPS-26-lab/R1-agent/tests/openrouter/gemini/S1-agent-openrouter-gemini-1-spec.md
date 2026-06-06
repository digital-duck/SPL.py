## 0. High-level Description
This WORKFLOW implements a recursive Research Agent pattern that autonomously decides between gathering information and synthesizing a final response. The process begins with a WHILE loop that persists as long as the agent determines more information is required. Inside the loop, the `DecideAction` logical function evaluates the user's question against the current research context and produces a structured YAML response. An EVALUATE construct parses this decision: if the agent selects "search," it triggers a CALL to a web search tool and appends the results to the context before repeating the loop. If the agent selects "answer," it exits the loop to trigger the `AnswerQuestion` logical function, which generates the final comprehensive response. The workflow maintains a shared state for the research history and terminates by returning the final synthesized answer.

## 1. Purpose
Automates a multi-step research process where an LLM dynamically decides to perform web searches until it has sufficient information to provide a comprehensive answer.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `ResearchAgent` | `create_agent_flow()` in `flow.py` | Defines the overall graph structure. |
| **CREATE FUNCTION** | `DecideAction.exec` / `AnswerQuestion.exec` | Logical prompt templates for decision making and writing. |
| **GENERATE** | `call_llm(prompt)` | LLM invocation within node execution. |
| **CALL** | `search_web_duckduckgo(query)` | Side-effect tool call to fetch external data. |
| **WHILE** | `search - "decide" >> decide` (cycle) | The loop logic formed by the "search" vs "answer" branch. |
| **EVALUATE** | `decide - "search" >> search` | Conditional branching based on the LLM's "action" field. |
| **@vars** | `shared` dictionary | Shared state containing `question`, `context`, and `answer`. |
| **RETURN WITH** | `return "done"` in `AnswerQuestion` | Signals the terminal state of the agent. |

## 3. Logical Functions / Prompts

### `DecideAction`
- **Role**: The "brain" of the agent; performs meta-cognition to determine if the current context is sufficient.
- **Key Prompt Conventions**: Uses a strict YAML output format with block scalars (`|`) for reasoning and answers to ensure parsing robustness. It maps inputs to an "Action Space" consisting of `search` or `answer`.

### `AnswerQuestion`
- **Role**: The "writer"; synthesizes all gathered research into a final polished output.
- **Key Prompt Conventions**: Context-heavy prompt that provides the original question and the accumulated `Research` context (concatenated search results).

## 4. Control Flow
The workflow initializes with a user `question` and an empty `context`. It enters a cycle starting at **DecideAction**, which generates a decision. 
- Using **EVALUATE** on the action field:
    - If "search", it captures a `search_query`, performs a **CALL** to the search tool, updates the `@context` variable, and loops back (**WHILE** condition implicit in the "decide" transition).
    - If "answer", it breaks the cycle.
- Finally, it triggers **AnswerQuestion** to produce the final result and exits via **RETURN WITH** `status="done"`.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements a recursive Research Agent pattern that autonomously decides between gathering information and synthesizing a final response. The process begins with a WHILE loop that persists as long as the agent determines more information is required. Inside the loop, the DecideAction logical function evaluates the user's question against the current research context and produces a structured YAML response. An EVALUATE construct parses this decision: if the agent selects 'search,' it triggers a CALL to a web search tool and appends the results to the context before repeating the loop. If the agent selects 'answer,' it exits the loop to trigger the AnswerQuestion logical function, which generates the final comprehensive response. The workflow maintains a shared state for the research history and terminates by returning the final synthesized answer." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```