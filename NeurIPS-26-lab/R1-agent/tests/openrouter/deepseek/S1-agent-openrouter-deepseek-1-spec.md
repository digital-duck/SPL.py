## 0. High-level Description

This workflow implements a research agent using a **WHILE** loop pattern. It declares a **WORKFLOW** named `ResearchAgent`. It defines three logical functions: `DecideAction`, `SearchWeb`, and `AnswerQuestion`. The `DecideAction` function uses a **GENERATE** call to an LLM to decide whether to search or answer, outputting a structured YAML decision. If the decision is `search`, the workflow **CALL**s a web search tool and then loops back to `DecideAction` via **WHILE**. If the decision is `answer`, it proceeds to `AnswerQuestion`, which **GENERATE**s a final answer using the accumulated context. The workflow uses **EVALUATE** to branch on the LLM’s decision. After the loop terminates, it **RETURN** the answer with status. Exception handling can be added for LLM or parsing errors.

## 1. Purpose

This implementation provides an automated research agent that iteratively searches the web and synthesizes a comprehensive answer to a user’s question.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---------------|-------------------|-------|
| `WORKFLOW ResearchAgent` | `create_agent_flow()` returning `Flow(start=decide)` | The graph flow is the workflow; SPL models it as a linear/loop sequence with explicit transitions. |
| `CREATE FUNCTION DecideAction` | `class DecideAction` with `exec` method containing prompt | The prompt template is the function; `exec` performs the LLM call. |
| `GENERATE DecideAction(prompt) INTO @decision` | `call_llm(prompt)` and YAML parsing | LLM call to decide the next action. |
| `EVALUATE @decision WHEN contains('action: search') THEN ... ELSE ... END` | Edge connections: `decide - "search" >> search` and `decide - "answer" >> answer` | Branching based on the `action` field in the YAML output. |
| `WHILE @decision.action != "answer" DO ... END` | Implicit loop via `search - "decide" >> decide` | SPL WHILE loop with condition checked after each iteration. |
| `CALL search_web(@search_query) INTO @search_results` | `search_web_duckduckgo(search_query)` | Side-effect tool call returning search results. |
| `GENERATE AnswerQuestion(prompt) INTO @answer` | `call_llm(prompt)` in `AnswerQuestion.exec` | Final answer generation. |
| `RETURN @answer WITH status="completed"` | `AnswerQuestion.post` sets `shared["answer"]` and returns `"done"` | Returns answer with metadata. |
| `EXCEPTION WHEN YAMLError THEN ...` | `try-except` in `parse_yaml_safely` | Exception handling for YAML parsing errors. |
| Shared state: `@question`, `@context`, `@search_query`, `@answer` | `shared` dictionary | SPL `@vars` store workflow state across nodes. |

## 3. Logical Functions / Prompts

### DecideAction
- **Role**: Decides whether to search the web or answer the question based on current context.
- **Prompt conventions**: Uses section markers (`### CONTEXT`, `### ACTION SPACE`, `## NEXT ACTION`). Expects output as a fenced YAML block (` ```yaml ... ``` `) with fields `thinking`, `action`, `reason`, `answer`, `search_query`. Employs block scalars (`|`) for multi-line fields to avoid YAML breakage. Includes explicit instruction to keep `search_query` as a plain string.

### AnswerQuestion
- **Role**: Generates the final comprehensive answer from the accumulated research context.
- **Prompt conventions**: Uses `### CONTEXT` and `## YOUR ANSWER` sections. Output is free‑form text (no structured format required). The prompt instructs the LLM to “answer the question using the research results.”

## 4. Control Flow

The execution begins at the **DecideAction** node, which **GENERATE**s a structured decision. The decision is evaluated via **EVALUATE**:
- If the `action` field equals `"search"`, the workflow **CALL**s the web search tool with the provided `search_query`. After the search, it returns `"decide"`, which causes the **WHILE** loop to continue (since `action != "answer"`), sending control back to **DecideAction**.
- If the `action` field equals `"answer"`, the workflow proceeds to **AnswerQuestion**, which **GENERATE**s the final answer. This node returns `"done"`, terminating the **WHILE** loop.

After loop termination, the workflow **RETURN**s `@answer` with `status="completed"`. Exception handling (e.g., for YAML parsing errors) would be triggered by an **EXCEPTION** block, though the current Python implementation handles it inline.

## 5. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```