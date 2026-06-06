## 0. High-level Description
This workflow orchestrates an external Chain-of-Thought reasoning loop that guides an instruction-following LLM to solve complex quantitative or logical problems through iterative, structured self-reflection. It initializes a hierarchical planning state and enters a `WHILE` loop that persists until the model explicitly signals completion via a boolean termination token. In each cycle, a `CREATE FUNCTION` template dynamically assembles historical context and current plan status into a strict prompt that forces the LLM to evaluate prior reasoning, execute the next pending step, and output a revised task hierarchy. The `GENERATE` block invokes the target model, and an `EVALUATE` construct inspects the parsed decision flag to either advance the loop or trigger a terminating `RETURN` that extracts the final reasoning trace. The pipeline incorporates side-effects to stream progress to standard output and optionally persist the solution to disk, while an `EXCEPTION` handler gracefully catches YAML parsing failures or missing schema keys to prevent state corruption. By externalizing planning and validation, this design reliably scales across diverse foundational models like Claude or GPT-4 without depending on proprietary extended-thinking endpoints.

## 1. Purpose
Enables reliable, step-by-step reasoning on complex problems by externalizing the model's planning, execution, and self-evaluation cycle into a controlled, stateful iterative loop.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `create_chain_of_thought_flow()` + `Flow(start=...)` | Defines the orchestration graph entry point and binds the self-looping node. |
| `CREATE FUNCTION <name>` | String interpolation in `exec()` (`instruction_base`, `instruction_context`, `instruction_format`) | Dynamically injects `{problem}`, `{thoughts_text}`, `{last_plan_text}`, and `{is_first_thought}` into the system prompt. |
| `GENERATE <fn>(...) INTO @<var>` | `response = call_llm(prompt)` + `yaml.safe_load()` | Dispatches the prompt to the Anthropic shim, extracts the YAML block, and materializes `thought_data`. |
| `EVALUATE @<var> WHEN ...` | `if not exec_res.get("next_thought_needed", True):` in `post()` | Branches on the boolean continuation flag to route execution toward either loop repetition or termination. |
| `WHILE <cond> DO ... END` | `cot_node - "continue" >> cot_node` + `post()` returning `"continue"` | Self-looping PocketFlow edge that repeats `prep`/`exec`/`post` until the termination condition is met. |
| `EXCEPTION WHEN <Type> THEN` | `assert` statements validating YAML keys and structure | Catches schema violations or parsing errors; in SPL this would map to a named error handler or retry fallback. |
| `RETURN @<var> WITH <k>=<v>` | `shared["solution"] = ...` + `return "end"` | Terminates the workflow, propagates the final answer to shared state, and attaches metadata like status. |
| Shared State (`@<var>`) | `shared` dictionary | Persistently tracks `problem`, `thoughts`, `current_thought_number`, `solution`, and plan snapshots across iterations. |

## 3. Logical Functions / Prompts
- **Name:** `generate_thought_step`
- **Role in the workflow:** Serves as the core reasoning driver. It receives the original problem, a formatted history of previous thoughts, and the current plan state. It instructs the LLM to critically audit the last step, perform the next actionable item, update the hierarchical plan dictionary, and decide whether further reasoning is required.
- **Key prompt conventions:** 
  - Enforces strict YAML output wrapped in triple backticks.
  - Mandates three top-level keys: `current_thinking` (evaluation + execution narrative), `planning` (list of dicts with `description`, `status` ∈ `{"Pending","Done","Verification Needed"}`, `result`, `mark`, and optional `sub_steps`), and `next_thought_needed` (boolean).
  - Uses `next_thought_needed: false` as the exclusive termination sentinel, activated only when the plan reaches the `"Conclusion"` step.
  - Adapts context via the `{is_first_thought}` flag to either seed an initial three-tier plan or resume an existing one.
  - Requires status transitions to explicitly reflect execution outcomes (`Done` + `result` summary, or `Verification Needed` + `mark` rationale).

## 4. Control Flow
The execution path begins by initializing shared state with the input problem and a baseline plan skeleton, then immediately enters a `WHILE` loop governed by the `next_thought_needed` flag. During each iteration, the `CREATE FUNCTION` compiles historical reasoning and the current planning snapshot, passing them into a `GENERATE` call that invokes the LLM. The raw response is parsed and structurally validated; if schema checks fail, an `EXCEPTION` handler intercepts the error to prevent invalid state propagation. An `EVALUATE` block then inspects the boolean continuation flag: when true, the workflow appends the new thought to the history, prints interim progress, and cycles back to the loop condition. When false, the `EVALUATE` triggers a terminating transition that extracts the final `current_thinking` as the definitive solution, prints a formatted conclusion, and executes a file-write side-effect if an output path was specified. The workflow concludes with `RETURN @solution WITH status="solved", iterations=@current_thought_number`, carrying the complete reasoning trace out of the orchestration layer.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow orchestrates an external Chain-of-Thought reasoning loop that guides an instruction-following LLM to solve complex quantitative or logical problems through iterative, structured self-reflection. It initializes a hierarchical planning state and enters a WHILE loop that persists until the model explicitly signals completion via a boolean termination token. In each cycle, a CREATE FUNCTION template dynamically assembles historical context and current plan status into a strict prompt that forces the LLM to evaluate prior reasoning, execute the next pending step, and output a revised task hierarchy. The GENERATE block invokes the target model, and an EVALUATE construct inspects the parsed decision flag to either advance the loop or trigger a terminating RETURN that extracts the final reasoning trace. The pipeline incorporates side-effects to stream progress to standard output and optionally persist the solution to disk, while an EXCEPTION handler gracefully catches YAML parsing failures or missing schema keys to prevent state corruption. By externalizing planning and validation, this design reliably scales across diverse foundational models like Claude or GPT-4 without depending on proprietary extended-thinking endpoints." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```