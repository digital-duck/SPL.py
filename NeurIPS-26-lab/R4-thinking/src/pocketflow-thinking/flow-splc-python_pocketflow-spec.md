# SPL Functional Specification: Chain-of-Thought Reasoning Workflow

## 0. High-level Description

This WORKFLOW implements an iterative chain-of-thought reasoning system that processes complex problems through sequential deliberation steps. The workflow uses a CREATE FUNCTION for step-by-step thought generation that maintains a structured planning state across iterations. A WHILE loop continues reasoning until a conclusion is reached, with each iteration using GENERATE to produce thinking content and plan updates in YAML format. The workflow employs EVALUATE logic to assess previous thoughts and determine continuation based on a next_thought_needed flag. State management through shared variables tracks problem context, thought history, current step numbers, and planning structures represented as lists of status-tracked dictionaries. RETURN delivers the final solution with metadata, while EXCEPTION handling validates YAML parsing and required response fields.

## 1. Purpose

Solves complex reasoning problems by generating sequential thoughts that evaluate previous steps, maintain a structured execution plan, and iteratively refine the approach until reaching a definitive conclusion.

## 2. SPL ↔ Python PocketFlow Construct Mapping

| SPL Construct | Python PocketFlow Equivalent | Notes |
|---------------|------------------------------|--------|
| WORKFLOW | Flow class with node routing | Flow(start=node) defines entry point |
| CREATE FUNCTION | ChainOfThoughtNode.prep() + .exec() | prep() builds prompt, exec() calls LLM |
| GENERATE INTO @var | call_llm(prompt) → exec_res | LLM call stores result in exec_res |
| WHILE condition DO | node → "continue" routing | Self-loop based on post() return value |
| EVALUATE @var WHEN | post() method decision logic | Checks next_thought_needed flag |
| @variable state | shared dictionary | Persistent state across node executions |
| RETURN WITH metadata | shared["solution"] assignment | Final result with completion status |
| EXCEPTION WHEN | assert statements in exec() | YAML validation and required field checks |

## 3. Logical Functions / Prompts

### ChainOfThoughtNode Prompt Function
- **Name**: Chain-of-thought reasoning step generator
- **Role**: Generates structured thoughts that evaluate previous work, execute plan steps, and update planning state
- **Key Prompt Conventions**:
  - YAML output format with ```yaml...``` delimiters
  - Required fields: current_thinking, planning, next_thought_needed  
  - Planning as list of dictionaries with description/status/result/mark keys
  - Status values: "Pending", "Done", "Verification Needed"
  - Evaluation pattern: "Evaluation of Thought N: [Assessment]"
  - Termination signal: next_thought_needed: false when executing Conclusion step

## 4. Control Flow

Initial step: ChainOfThoughtNode.prep() constructs prompt with problem context and previous thoughts → ChainOfThoughtNode.exec() performs GENERATE call to LLM for structured reasoning → Loop condition: WHILE post() method EVALUATE returns "continue" based on next_thought_needed flag → Branch logic: EVALUATE previous thought quality, execute pending plan step, update planning structure with status changes → Termination: RETURN WITH solution when next_thought_needed=false and Conclusion step executed, storing final thinking content as solution.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements an iterative chain-of-thought reasoning system that processes complex problems through sequential deliberation steps. The workflow uses a CREATE FUNCTION for step-by-step thought generation that maintains a structured planning state across iterations. A WHILE loop continues reasoning until a conclusion is reached, with each iteration using GENERATE to produce thinking content and plan updates in YAML format. The workflow employs EVALUATE logic to assess previous thoughts and determine continuation based on a next_thought_needed flag. State management through shared variables tracks problem context, thought history, current step numbers, and planning structures represented as lists of status-tracked dictionaries. RETURN delivers the final solution with metadata, while EXCEPTION handling validates YAML parsing and required response fields." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```