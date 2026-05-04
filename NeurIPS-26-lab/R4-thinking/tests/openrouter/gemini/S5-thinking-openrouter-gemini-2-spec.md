## 0. High-level Description
This WORKFLOW, named `chain_of_thought_process`, implements a recursive reasoning pattern that iteratively refines a solution using a multi-step "Chain of Thought" technique. The process begins by initializing a history with a user query and starts a WHILE loop that continues as long as the LLM indicates more reasoning is required, capped at a maximum of ten iterations. Inside the loop, the workflow uses the `generate_cot_step` FUNCTION to produce a YAML-formatted reasoning block containing current thinking, an updated plan, and a boolean flag. A second FUNCTION, `parse_yaml`, is used to EVALUATE the LLM's output and extract the continuation signal, which determines whether the loop should persist. Each iteration's raw response is appended to the historical trace to maintain context. Upon completion—either through a logical conclusion or by hitting the iteration limit—the workflow uses a RETURN construct to provide the full reasoning history along with a "complete" status metadata flag.

## 1. Purpose
This implementation automates a self-correcting, multi-step reasoning process that allows an LLM to "think" through complex queries by breaking them into sequential, planned steps.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `chain_of_thought_process` | `run_chain_of_thought(initial_query)` | The main entry point for the orchestration logic. |
| **CREATE FUNCTION** `generate_cot_step` | `generate_cot_step(history, plan)` | Template for generating the YAML reasoning block. |
| **CREATE FUNCTION** `parse_yaml` | `parse_yaml(raw_output)` | Template/logic for state extraction from LLM text. |
| **GENERATE** | `call_llm(prompt)` / function calls | Maps to the OpenRouter API request within the functions. |
| **WHILE** | `while next_thought_needed == "true"...` | Controls the iterative reasoning loop with a safety cap. |
| **@var** (State) | Local variables (`history`, `plan`, etc.) | SPL shared state variables mapped to Python locals. |
| **RETURN ... WITH** | `return {"final_trace": ..., "status": "complete"}` | Terminates the workflow with meaningful metadata. |

## 3. Logical Functions / Prompts

### `generate_cot_step`
*   **Role**: Acts as the primary reasoning engine for each step of the chain.
*   **Key Conventions**: Enforces a strict YAML output format. It requires the LLM to provide three specific keys: `thinking`, `plan`, and `next_thought_needed`. This structure allows the workflow to separate content from control logic.

### `parse_yaml`
*   **Role**: A utility function to ensure robust state transition.
*   **Key Conventions**: Uses a dual-strategy approach. It first attempts a simple string-based heuristic to find the boolean flag; if ambiguous, it performs a secondary LLM call to explicitly extract the "true" or "false" value from the previous output.

## 4. Control Flow
The workflow initiates by setting `@history` to the user's query and `@next_thought_needed` to "true". It enters a **WHILE** loop that monitors the `@next_thought_needed` variable and an iteration counter. In each cycle, it **GENERATE**s a new reasoning step, then **GENERATE**s an extraction to update the loop condition. The loop continues until the LLM sets the flag to "false" or the iteration count reaches 10. Finally, the workflow exits the loop and performs a **RETURN WITH status="complete"**, passing back the accumulated trace.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW, named chain_of_thought_process, implements a recursive reasoning pattern that iteratively refines a solution using a multi-step 'Chain of Thought' technique. The process begins by initializing a history with a user query and starts a WHILE loop that continues as long as the LLM indicates more reasoning is required, capped at a maximum of ten iterations. Inside the loop, the workflow uses the generate_cot_step FUNCTION to produce a YAML-formatted reasoning block containing current thinking, an updated plan, and a boolean flag. A second FUNCTION, parse_yaml, is used to EVALUATE the LLM's output and extract the continuation signal, which determines whether the loop should persist. Each iteration's raw response is appended to the historical trace to maintain context. Upon completion—either through a logical conclusion or by hitting the iteration limit—the workflow uses a RETURN construct to provide the full reasoning history along with a 'complete' status metadata flag." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```