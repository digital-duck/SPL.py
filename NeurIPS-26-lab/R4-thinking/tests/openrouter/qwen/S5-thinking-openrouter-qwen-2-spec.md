## 0. High-level Description
This workflow implements an iterative chain-of-thought reasoning engine using a structured WHILE loop and EVALUATE branching to progressively solve a given problem according to a predefined plan. A CREATE FUNCTION template named `assemble_prompt` formats the current reasoning state and plan, instructing the LLM to output strict YAML containing either a `CONTINUE` flag to advance the loop or a `FINAL` flag to terminate. The GENERATE construct abstracts the network request to support configurable model targeting, currently routing to an OpenRouter-hosted Qwen instance, while capturing the response into a shared variable that drives the EVALUATE conditions for error handling, state accumulation, and loop continuation. Upon exiting the iteration bound, a CALL construct persists the extracted solution to a markdown file, and the workflow concludes by RETURNing the final output with a completion status metadata tag. Environment variable validation is enforced through an EXCEPTION handler that halts execution if API credentials are missing, ensuring robust side-effect and network interaction management.

## 1. Purpose
This implementation orchestrates an iterative, LLM-driven chain-of-thought reasoning process that progressively refines a solution until completion or iteration limits are reached, then persists the final result to disk.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW ChainOfThoughtLoop` | `class S3ThinkingOpenrouterQwen:` + `run()` method | Encapsulates the full orchestration scope and execution entry point. |
| `CREATE FUNCTION assemble_prompt` | `def assemble_prompt(state, plan):` | Reusable f-string template with `{state}` and `{plan}` injection slots. |
| `GENERATE ... INTO @llm_output` | `self._call_llm(prompt_text)` | Synchronous HTTP POST to OpenRouter; parses JSON response to extract text. |
| `WHILE @next_thought_needed = "true" AND @iteration < 3 DO` | `while next_thought_needed == "true" and iteration < 3:` | Bounded loop enforcing max 3 reasoning steps or early termination. |
| `EVALUATE @llm_output WHEN contains(...) THEN` | Nested `if ... in llm_output:` / `elif ... in llm_output:` | Drives branching based on YAML sentinel values in the LLM response. |
| `CALL write_file(...)` | `with open("chain_of_thought.md", "w", ...) as f: f.write(...)` | Side-effect operation persisting the final extracted result to disk. |
| `EXCEPTION WHEN EnvironmentError` | `if not self.api_key: raise EnvironmentError(...)` | Pre-flight guard that aborts workflow execution on missing credentials. |
| `@vars (shared state)` | Local Python variables (`state`, `iteration`, `final_result`, etc.) | Mutable state carried across loop iterations and branching paths. |
| `RETURN @final_result WITH status="complete"` | `return final_result` | Terminates the workflow and outputs the resolved answer with metadata. |

## 3. Logical Functions / Prompts
- **Name:** `assemble_prompt`
- **Role in the workflow:** Serves as the single reusable prompt template for every reasoning iteration. It injects the accumulated reasoning trace (`@state`) and the strategic directive (`@plan`) to guide the LLM's next step.
- **Key prompt conventions:** 
  - Enforces strict YAML output without markdown code blocks or conversational filler.
  - Requires explicit boolean sentinel fields (`CONTINUE: true` or `FINAL: true`) to programmatically signal loop continuation versus termination.
  - Designed for deterministic parsing via string containment checks in the `EVALUATE` branches.

## 4. Control Flow
The workflow initializes by concatenating the input `@problem` and `@plan` into an initial `@state`, sets `@next_thought_needed` to `"true"`, and zeroes the `@iteration` counter. Execution immediately enters a WHILE loop constrained by both the continuation flag and a hard cap of three iterations. Inside the loop, a GENERATE call produces a YAML reasoning step into `@llm_output` and increments the iteration counter. The response is routed through sequential EVALUATE branches: if `YAML_ERROR` is detected, the loop continues for a self-correction pass; if `CONTINUE: true` is present, `@state` is appended with the new reasoning step and the loop proceeds; if neither sentinel appears, the final branch extracts the solution into `@final_result`, sets `@next_thought_needed` to `"false"`, and forces loop termination. After exiting the WHILE block, a CALL operation writes `@final_result` to a local markdown file, and the workflow executes a RETURN statement tagged with `status="complete"` to deliver the output.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements an iterative chain-of-thought reasoning engine using a structured WHILE loop and EVALUATE branching to progressively solve a given problem according to a predefined plan. A CREATE FUNCTION template named assemble_prompt formats the current reasoning state and plan, instructing the LLM to output strict YAML containing either a CONTINUE flag to advance the loop or a FINAL flag to terminate. The GENERATE construct abstracts the network request to support configurable model targeting, currently routing to an OpenRouter-hosted Qwen instance, while capturing the response into a shared variable that drives the EVALUATE conditions for error handling, state accumulation, and loop continuation. Upon exiting the iteration bound, a CALL construct persists the extracted solution to a markdown file, and the workflow concludes by RETURNing the final output with a completion status metadata tag. Environment variable validation is enforced through an EXCEPTION handler that halts execution if API credentials are missing, ensuring robust side-effect and network interaction management." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```