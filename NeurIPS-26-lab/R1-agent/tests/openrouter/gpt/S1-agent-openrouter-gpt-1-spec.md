## 0. High-level Description
This workflow is a graph-style research agent implemented as an SPL `WORKFLOW` with three logical stages: a decision `GENERATE`, a web-search `CALL`, and a final answering `GENERATE`. It uses one prompt function to decide the next action from the current question plus accumulated research context, requiring YAML-structured output that names either `search` or `answer`, and another prompt function to synthesize a comprehensive final response from the question and collected context. Control flow is equivalent to a `WHILE` loop that repeatedly returns to the decision step after each search, with an `EVALUATE` branch on the decision model’s `action` field: when action is `search`, invoke the web search tool and append results into shared context; otherwise transition to final answer generation or accept the direct answer already produced by the decision model as sufficient context. The design is effectively multi-capability and potentially multi-model: LLM calls are abstracted through a `call_llm` adapter while search is performed through a DuckDuckGo tool call, so the workflow separates prompt generation from external retrieval side effects. Shared state is maintained in workflow variables for `question`, `context`, `search_query`, and `answer`, and the workflow terminates with a `RETURN` carrying the final answer plus status metadata; parsing and YAML-repair logic in Python should map to SPL-level structured-output validation and `EXCEPTION` handling for malformed LLM responses or tool failures, while optional file output in the CLI is an additional side-effect outside the core agent workflow.

## 1. Purpose
This implementation answers a user’s research question by iteratively deciding whether to search the web for more information or produce a final answer from the accumulated context.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `create_agent_flow()` returning `Flow(start=decide)` | The PocketFlow graph definition is the workflow boundary. |
| `CREATE FUNCTION <name>` | Prompt-building code inside `DecideAction.exec()` and `AnswerQuestion.exec()` | Each inline prompt string is a reusable logical prompt template in SPL terms. |
| `GENERATE <fn>(...) INTO @var` | `response = call_llm(prompt)` / `answer = call_llm(prompt)` | LLM invocations occur in decision and answer nodes. |
| `CALL <tool>(...) INTO @var` | `results = search_web_duckduckgo(search_query)` | Web search is a tool call with side effects external to the LLM. |
| `EVALUATE @var WHEN ... THEN ... ELSE ... END` | `if exec_res["action"] == "search": ... else: ...` in `DecideAction.post()` | Branching is based on the structured `action` field returned by the decision LLM. |
| `WHILE <cond> DO ... END` | Graph cycle `DecideAction -> SearchWeb -> DecideAction` | The loop continues until the decision branch selects `answer`. |
| `RETURN @var WITH ...` | Final answer stored in `shared["answer"]`; flow ends after `AnswerQuestion.post()` | Python does not explicitly return a structured workflow object, but the effective return value is the final shared answer plus CLI display/save behavior. |
| `EXCEPTION WHEN <Type> THEN ...` | `try/except` around YAML parsing; `ValueError` on malformed YAML | Python includes local recovery for bad YAML and would map to structured exception handlers in SPL. |
| Shared state `@vars` | `shared` dictionary | Keys like `question`, `context`, `search_query`, and `answer` are SPL workflow variables. |
| Structured output contract | YAML fenced block and `yaml.safe_load(...)` | The decision prompt explicitly defines a schema; Python validates and repairs it. |
| Workflow transition labels | `return "search"`, `return "answer"`, `return "decide"`, `return "done"` | These are graph edge selectors; in SPL they become branch targets or loop transitions. |
| Side-effect output | CLI writes answer file via `Path(out).write_text(...)` | This is not part of the core agent loop but can be modeled as a final optional `CALL write_file(...)`. |
| Model abstraction / multi-model design | `call_llm` shim in `utils.py` | The implementation allows swapping the underlying LLM backend through environment-driven adapter logic. |

## 3. Logical Functions / Prompts

### 3.1 DecideAction
- **Role in the workflow**: Determines whether the agent should perform another web search or proceed toward answering, based on the original question and accumulated research context.
- **Key prompt conventions**:
  - Includes sections `### CONTEXT`, `### ACTION SPACE`, and `## NEXT ACTION`.
  - Requires YAML output with fields: `thinking`, `action`, `reason`, `answer`, `search_query`.
  - Strongly enforces block scalar `|` formatting for multi-line fields to avoid YAML breakage.
  - The `action` field is the routing sentinel and must be either `search` or `answer`.
  - `search_query` must remain a single-line plain string.
  - Output may be wrapped in fenced ```yaml code blocks, which are extracted before parsing.
  - Python includes repair logic that rewrites malformed scalar fields into block-scalar form before reparsing.

### 3.2 AnswerQuestion
- **Role in the workflow**: Produces the final user-facing response using the accumulated research context.
- **Key prompt conventions**:
  - Includes `### CONTEXT` and `## YOUR ANSWER`.
  - Expects free-form natural language output rather than structured YAML.
  - Instructs the LLM to provide a comprehensive answer grounded in the gathered research.
  - Uses the original `question` and current `context` as inputs.

### 3.3 SearchWeb Tool Invocation
- **Role in the workflow**: Retrieves supporting evidence from the web to enrich context before another decision cycle.
- **Key prompt conventions**:
  - Not a prompt template, but a logical function/tool in workflow terms.
  - Uses DuckDuckGo text search with `max_results=5`.
  - Normalizes results into a concatenated text block with repeated fields: `Title`, `URL`, `Snippet`.
  - These formatted results are appended into shared context with `SEARCH:` and `RESULTS:` markers, which act like sentinel delimiters for later model reasoning.

## 4. Control Flow
The workflow starts by initializing shared variables with at least `@question`, then entering the decision stage. The decision stage performs a `GENERATE` using the current `@question` and `@context`, parses the structured YAML output, and then `EVALUATE`s the resulting action. If the action is `search`, the workflow stores `@search_query`, executes `CALL search_web(...) INTO @results`, appends the formatted search results into `@context`, and loops back through a `WHILE`-equivalent cycle to the decision stage. If the action is `answer`, the Python implementation first stores the model’s answer text into `@context`, then transitions to the final answer generation node, which performs another `GENERATE` to create `@answer`. The workflow terminates after the answer node with an implicit `RETURN @answer WITH status="done"`; if regeneration as SPL wants to preserve CLI behavior, it may optionally add a final conditional file-write `CALL` and `RETURN @answer WITH status="saved"` or `status="done"` depending on whether an output path is supplied. Malformed YAML from the decision model should be handled through `EXCEPTION WHEN ParseError`-style behavior, reflecting the Python retry-and-repair parsing logic before failing.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```