## 0. High-level Description
This workflow implements a ReAct-style research agent orchestration that iteratively decides between querying external knowledge and synthesizing a final response. It declares a WORKFLOW that delegates all reasoning and synthesis to a unified LLM backend via a configurable adapter shim, ensuring consistent prompt routing regardless of the underlying provider. The orchestration begins by invoking a CREATE FUNCTION decision prompt, which instructs the model to output a structured YAML response selecting either a search or answer action. The workflow uses EVALUATE to branch on the parsed action token: if search, a CALL executes a web search tool and appends results to the shared context before looping back to the decision phase; if answer, a second prompt generates the final text. Shared state variables persist across iterations via a centralized dictionary, while an EXCEPTION handler automatically repairs malformed YAML outputs and retries parsing before halting execution. The graph terminates cleanly when the synthesis node issues a RETURN with status done, materializing the final answer for CLI output and optional file persistence.

## 1. Purpose
This implementation enables users to ask open-ended research questions and automatically retrieves, evaluates, and synthesizes web search results into a comprehensive final answer through an autonomous LLM agent.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `pocketflow.Flow(start=decide)` | Defines the directed graph topology and initializes execution at the decision node |
| `CREATE FUNCTION` | Inline prompt strings in `DecideAction.exec` & `AnswerQuestion.exec` | Parameterized with `{question}` and `{context}` slots for dynamic injection |
| `GENERATE` | `call_llm(prompt)` | Invokes the LLM API and captures raw text output into a variable |
| `CALL` | `search_web_duckduckgo(query)` | Side-effect tool execution that fetches external data over HTTP |
| `EVALUATE` | Conditional routing logic in `DecideAction.post()` | Branches execution path based on the parsed `action` field (`search` vs `answer`) |
| `WHILE` | `"decide"` edge routing from `SearchWeb` back to `DecideAction` | Implicit loop that repeats the research cycle until the LLM selects the answer action |
| `EXCEPTION` | `parse_yaml_safely()` fallback in `nodes.py` | Catches YAML parsing failures, applies heuristic block-scalar repairs, and retries |
| Shared state (`@var`) | `shared` dictionary passed through node lifecycle | Stores `@question`, `@context`, `@search_query`, and `@answer` across steps |
| `RETURN WITH status=` | `post()` methods returning `"done"`, `"search"`, or `"answer"` | Drives non-trivial routing and explicit workflow termination |

## 3. Logical Functions / Prompts
**decide_action_prompt**
- **Role:** Orchestrator/Planner that evaluates the current research gap and selects the next operational mode.
- **Key prompt conventions:** Enforces strict YAML output with an explicit action space (`search` vs `answer`). Requires `|` block scalars for `thinking`, `reason`, and `answer` fields to prevent syntax breaks from colons or quotes. Includes a parsing retry heuristic for malformed outputs.

**answer_question_prompt**
- **Role:** Synthesizer/Writer that compiles accumulated research findings into a cohesive, comprehensive response.
- **Key prompt conventions:** Direct instruction format that explicitly references the original `Question:` and aggregated `Research:` context blocks. Expects unstructured prose output without wrapper tags.

## 4. Control Flow
Execution initializes by populating shared state with the user query and entering the decision phase. The workflow triggers an EVALUATE on the LLM's parsed output: if the action matches `search`, the query variable is updated, a CALL executes the web scraper, and the retrieved snippets are concatenated into the context before routing back to the decision prompt. This forms a WHILE loop that repeats the search-accumulate cycle until the evaluator matches `answer`. At that point, the accumulated context is cached, the synthesis prompt is invoked, and the resulting text is stored in the answer variable. The synthesis node then issues a RETURN with status `done`, which halts the graph and propagates the final payload to the CLI layer for display and optional filesystem persistence.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```