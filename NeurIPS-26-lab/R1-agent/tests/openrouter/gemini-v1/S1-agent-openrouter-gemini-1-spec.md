## 0. High-level Description
This WORKFLOW implements an iterative Research Agent pattern that autonomously gathers information to answer complex queries. The orchestration begins by invoking a `DecideAction` function, which acts as the central router by evaluating the current research context against the user's question. Based on this evaluation, the workflow enters a WHILE loop that continues as long as the agent determines more information is needed. Inside the loop, the agent uses a `search_web` tool call to fetch real-time data, appends this to the shared research context, and then re-evaluates the next step. Once the agent decides it has sufficient information, it breaks the loop and uses the `AnswerQuestion` function to synthesize a final comprehensive response. The control flow is driven by an EVALUATE construct that inspects a structured YAML response to branch between searching and final answering.

## 1. Purpose
Automates a multi-step web research process where an LLM dynamically decides whether to gather more data or provide a final answer based on accumulated evidence.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `ResearchAgent` | `create_agent_flow()` in `flow.py` | Orchestrates the connection between nodes. |
| **CREATE FUNCTION** | `DecideAction.exec` / `AnswerQuestion.exec` | Prompt templates for decision making and synthesis. |
| **GENERATE** | `call_llm(prompt)` in `utils.py` | The actual LLM inference call. |
| **CALL** | `search_web_duckduckgo(query)` | Side-effect tool to fetch external data. |
| **WHILE** | `search - "decide" >> decide` loop | The cyclic graph connection creates a functional loop. |
| **EVALUATE** | `decide - "search" >> ...` branch | Logic based on the `action` field in the LLM's YAML output. |
| **@vars** | `shared` dictionary | Shared state containing `question`, `context`, and `answer`. |
| **RETURN WITH** | `return "done"` in `AnswerQuestion` | Signals completion of the workflow. |

## 3. Logical Functions / Prompts

### `DecideAction`
- **Role**: The "Brain" or Router. It analyzes the gap between the question and current research.
- **Conventions**: Uses a strict YAML output format with block scalars (`|`) for `thinking` and `reason`. It outputs a specific `action` token ("search" or "answer").

### `AnswerQuestion`
- **Role**: The "Writer". Synthesizes all gathered context into a final readable response.
- **Conventions**: Simple instruction-following prompt that prioritizes accuracy based on the provided `Research` context.

## 4. Control Flow
The workflow starts with a **GENERATE** call to `DecideAction`. The output is processed via **EVALUATE** to check the `action` key. 
- If the action is "search", the workflow enters a **WHILE** loop: it triggers a **CALL** to the web search tool, updates the `@context` variable, and repeats the `DecideAction` step.
- If the action is "answer", the loop terminates (or is bypassed), and the workflow proceeds to **GENERATE** a final response via `AnswerQuestion`. 
- The process concludes with **RETURN WITH status="done"** once the final answer is stored in `@answer`.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements an iterative Research Agent pattern that autonomously gathers information to answer complex queries. The orchestration begins by invoking a DecideAction function, which acts as the central router by evaluating the current research context against the user's question. Based on this evaluation, the workflow enters a WHILE loop that continues as long as the agent determines more information is needed. Inside the loop, the agent uses a search_web tool call to fetch real-time data, appends this to the shared research context, and then re-evaluates the next step. Once the agent decides it has sufficient information, it breaks the loop and uses the AnswerQuestion function to synthesize a final comprehensive response. The control flow is driven by an EVALUATE construct that inspects a structured YAML response to branch between searching and final answering." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```