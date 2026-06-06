## 0. High-level Description
This workflow implements a structured, self-correcting decision agent that iteratively gathers external information before synthesizing a final answer. It begins with `CREATE FUNCTION` templates that prompt the language model to output a YAML routing structure containing an explicit action token. Execution enters a bounded outer `WHILE` loop that tracks step count and a completion flag, ensuring strict iteration limits. Within each cycle, an inner validation `WHILE` loop paired with `EVALUATE` branches checks for YAML syntax; if malformed, it automatically triggers a repair prompt, increments a retry counter, and loops until valid or until the retry ceiling is reached. After validation, a second `EVALUATE` branch inspects the extracted action token: a `search` directive executes a `CALL` side-effect to query DuckDuckGo and appends results to shared memory, while an `answer` directive invokes a synthesis prompt and sets the termination flag. Network timeouts or API errors are intercepted by `EXCEPTION` handlers that inject deterministic fallback strings, preserving linear execution flow without crashing. The workflow concludes with a post-loop safety guard and a `RETURN` statement that delivers the compiled response with a `complete` status.

## 1. Purpose
This implementation provides an autonomous, self-validating research agent that dynamically decides when to query external search engines and when to synthesize accumulated context into a final answer.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `class S3AgentOpenRouterQwen` + `run()` method | Defines the orchestration container with typed inputs/outputs and manages a shared context dictionary. |
| `CREATE FUNCTION <name>` | `prompt_decide_action()`, `prompt_validate_yaml()`, `prompt_repair_output()`, `prompt_extract_action()`, `prompt_generate_final()` | Python f-string functions returning prompt templates with `{param}` interpolation slots. |
| `GENERATE <fn>(...) INTO @<var>` | `generate(prompt_function(...))` | Wraps the OpenRouter API call with system prompts and temperature control, assigning the raw string to `ctx["..."]`. |
| `CALL <tool>(...) INTO @<var>` | `web_search()` | Executes a DuckDuckGo API call, formats snippets, and returns the structured text to shared state. |
| `WHILE <cond> DO ... END` | `while not ctx["@done"] and ctx["@iteration"] < 3:` (outer) and `while not ctx["@parse_valid"] and ctx["@parse_iter"] < 3:` (inner) | Iterative loops bounded by boolean flags and integer counters to prevent runaway execution. |
| `EVALUATE @<var> WHEN contains(...) THEN ... ELSE ... END` | `if "keyword" in ctx["..."].lower():` | Case-insensitive substring matching that routes execution based on LLM-generated validation or routing tokens. |
| Shared State (`@vars`) | `ctx = {"@user_query": ..., "@shared_state": "", ...}` | A single mutable Python dictionary acting as workflow memory, updated in-place across steps. |
| `EXCEPTION WHEN <Type> THEN ...` | `try/except` blocks inside `generate()` and `web_search()` | Catches network timeouts/import errors and returns safe fallback strings (`[MOCK_LLM_RESPONSE]`, etc.) so the loop continues. |
| `RETURN @<var> WITH status="complete"` | `return {"status": "complete", "final_response": ctx["@final_response"]}` | Terminates the workflow and packages the output with a non-trivial status token for downstream consumers. |

## 3. Logical Functions / Prompts
- **`decide_action`**
  - **Role:** Routing/Orchestration prompt that determines whether the agent should fetch new data or compile existing context.
  - **Key Conventions:** Requires YAML output containing an explicit `action` token and an optional `query` field. Low temperature (0.1) enforces deterministic formatting.
- **`validate_yaml`**
  - **Role:** Syntax validator for the routing LLM's output.
  - **Key Conventions:** Strict binary output convention: must return exactly `valid` or `malformed` to drive the inner repair loop.
- **`repair_output`**
  - **Role:** Self-correction prompt that fixes broken YAML structures.
  - **Key Conventions:** Forces strict YAML compliance; expects clean, parseable output on retry without conversational filler.
- **`extract_action`**
  - **Role:** Parser/token isolator that pulls the routing directive from validated YAML.
  - **Key Conventions:** Outputs a single lowercase keyword (`search` or `answer`) for deterministic `EVALUATE` branching.
- **`generate_final`**
  - **Role:** Synthesizer that compiles accumulated search results into a coherent, user-facing response.
  - **Key Conventions:** Consumes full `@shared_state` and original `@user_query`; expects comprehensive prose without YAML artifacts or tool-call syntax.

## 4. Control Flow
Execution initializes the shared context with the user query, empty state, and zeroed iteration/termination counters. The workflow enters a bounded outer `WHILE` loop that persists until `@done` is true or `@iteration` reaches three. Inside, it invokes `GENERATE decide_action` to produce routing YAML, which is immediately validated by an inner `WHILE` loop. This inner loop uses `EVALUATE` to check for a `malformed` token; if detected, it triggers `GENERATE repair_output`, increments the parse counter, and repeats until valid YAML is confirmed or the retry limit is hit. Once validated, `GENERATE extract_action` isolates the routing directive, followed by a second `EVALUATE` branch. If the directive contains `search`, the workflow executes `CALL web_search`, appends the results to `@shared_state`, and increments the outer iteration counter before looping back. If the directive contains `answer`, it invokes `GENERATE generate_final` to produce the output, sets `@done` to true, and exits the loop. A post-loop guard ensures `@final_response` is populated even if iteration limits are reached, finally executing `RETURN @final_response WITH status="complete"` to deliver the result.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```