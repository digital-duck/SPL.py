## 0. High-level Description
This workflow implements an iterative research agent that dynamically decides between web searching and answering through a graph-based orchestration pattern. It begins with a CREATE FUNCTION for action planning that prompts the language model to evaluate the current research context and output a structured YAML decision containing either a search query or a direct answer, which is parsed with an EXCEPTION handler to gracefully recover from malformed syntax. The core control flow uses a WHILE loop that repeatedly EVALUATEs the model's decision routing, where a search action triggers a CALL to a web search tool that appends new findings to the shared @context variable before returning to the planner, while an answer action breaks the loop and invokes a second CREATE FUNCTION for synthesis. Upon completion, the workflow uses RETURN to expose the final @answer alongside metadata such as iteration count and routing decisions. The design relies on a single LLM backbone but supports adapter swapping via environment configuration, and all intermediate state is maintained in shared @variables to enable seamless state persistence across tool calls and evaluation branches.

## 1. Purpose
This implementation autonomously researches a user-provided question by iteratively searching the web, synthesizing gathered context, and generating a comprehensive answer until sufficient information is collected.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `create_agent_flow()` + `Flow(start=decide)` | Defines the execution graph and entry point for the multi-step orchestration. |
| `CREATE FUNCTION` | `DecideAction.exec()` prompt & `AnswerQuestion.exec()` prompt | Reusable prompt templates with injected `{param}` slots for question and context. |
| `GENERATE` | `call_llm(prompt)` in both nodes | Invokes the LLM, captures raw string output, and stores it for parsing. |
| `CALL` | `search_web_duckduckgo(query)` in `SearchWeb.exec()` | Side-effect tool call for external data retrieval; returns scraped text. |
| `WHILE` | Graph cycle `search - "decide" >> decide` + routing in `post()` | Implicit loop that continues until the planner outputs `"answer"`. |
| `EVALUATE` | `post()` methods returning `"search"` or `"answer"` | Branches execution path based on the parsed `action` field from the LLM. |
| `RETURN` | `post()` returning `"done"` + `shared["answer"]` assignment | Terminates the flow and surfaces the final payload with completion metadata. |
| `EXCEPTION` | `parse_yaml_safely()` try/except block with YAML auto-repair | Fallback handler that repairs missing block scalars and retries parsing on LLM format errors. |
| Shared State (`@var`) | `shared` dictionary passed through `prep()`/`post()` | Centralized store for `@question`, `@context`, `@search_query`, and `@answer`. |

## 3. Logical Functions / Prompts

### `plan_next_action`
- **Role:** Orchestrator/Router that evaluates current knowledge and chooses between gathering more data or concluding the task.
- **Key Prompt Conventions:** Requires strict YAML output wrapped in fenced code blocks; uses `|` block scalars for multi-line fields to prevent parsing collisions; defines a discrete action space (`search` vs `answer`); mandates `thinking` and `reason` fields for transparent reasoning.

### `synthesize_final_answer`
- **Role:** Generator that composes a comprehensive, citation-aware response using accumulated research context.
- **Key Prompt Conventions:** Direct instruction to provide a comprehensive answer; expects free-form prose output; relies entirely on injected `@context` and `@question` variables; no strict formatting constraints beyond factual synthesis.

## 4. Control Flow
The execution begins by `GENERATE`-ing the initial decision prompt using `@question` and an empty `@context`. The workflow then enters a `WHILE action != "answer" DO ... END` loop. Inside the loop, `EVALUATE @decision WHEN contains("search") THEN` triggers a `CALL` to the web search tool, stores results in `@search_results`, appends them to `@context`, and loops back to the planner. `EVALUATE @decision WHEN contains("answer") THEN` breaks the loop condition, allowing control to fall through to the synthesis step. Here, a second `GENERATE` call produces `@answer` from the accumulated `@context`. Finally, the workflow executes `RETURN @answer WITH status="complete", iterations=@loop_count` to terminate execution and surface the final result alongside metadata.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```