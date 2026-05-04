## 0. High-level Description
This WORKFLOW orchestrates a structured Chain-of-Thought (CoT) reasoning process to solve complex problems by managing an external plan and evaluation loop. The core logic is encapsulated in a single logical function, `ChainOfThoughtStep`, which acts as a recursive reasoner. It consumes a problem statement, a history of previous thoughts, and a structured plan to GENERATE a YAML-formatted response containing current thinking, an updated plan, and a termination flag. The workflow utilizes a WHILE loop that persists as long as the LLM indicates that `next_thought_needed` is true. Within each iteration, the LLM performs an EVALUATE-like self-assessment of the prior step, executes the next pending task from the plan, and refines the plan structure (adding sub-steps or correction tasks). When the LLM executes the "Conclusion" step and sets the termination flag, the workflow returns the final reasoning trace with a "done" status.

## 1. Purpose
This implementation enables standard LLMs to solve complex reasoning problems by enforcing a systematic, multi-step process with externalized planning and self-correction.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `ChainOfThought` | `create_chain_of_thought_flow()` | Declares the orchestration of the CoT process. |
| **CREATE FUNCTION** `ChainOfThoughtStep` | `ChainOfThoughtNode` (Prompt in `exec`) | Template for generating reasoning, plans, and state updates. |
| **GENERATE** | `call_llm(prompt)` in `nodes.py` | The actual LLM call to produce the next thought. |
| **WHILE** `next_thought_needed` | `cot_node - "continue" >> cot_node` | Loop continues as long as the status is "continue". |
| **EVALUATE** | LLM internal "Evaluation of Thought N" | The prompt instructs the LLM to branch logic based on previous errors. |
| **@vars** | `shared` dictionary | Stores `problem`, `thoughts`, and `current_thought_number`. |
| **RETURN** | `return "end"` in `post` method | Terminates the loop when `next_thought_needed` is false. |

## 3. Logical Functions / Prompts

### `ChainOfThoughtStep`
- **Role**: The central reasoning engine. It evaluates history, executes the current plan item, and predicts the next state of the plan.
- **Key Prompt Conventions**: 
    - **Sentinel Tokens**: Specifically asks for output enclosed in ```yaml ... ``` blocks.
    - **Scoring/Evaluation**: Forced self-evaluation header: "Evaluation of Thought N: [Correct/Minor Issues/Major Error]".
    - **Output Format**: Structured YAML containing `current_thinking` (string), `planning` (list of dicts with statuses), and `next_thought_needed` (boolean).

## 4. Control Flow
The workflow begins by initializing the shared state with the user's question and an empty thought history. It enters a **WHILE** loop directed by the `ChainOfThoughtStep` function. In each iteration, the LLM receives the full context of previous thoughts and the current plan. The LLM then **GENERATES** a response that updates the plan status (e.g., marking a step "Done" and adding "Pending" sub-steps). The workflow **EVALUATES** the `next_thought_needed` flag within the LLM's YAML output; if true, it triggers a **RETURN WITH status="continue"** to repeat the loop. Once the LLM performs the "Conclusion" step, it sets the flag to false, and the workflow performs a final **RETURN WITH status="done"**, extracting the final thinking as the solution.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW orchestrates a structured Chain-of-Thought (CoT) reasoning process to solve complex problems by managing an external plan and evaluation loop. The core logic is encapsulated in a single logical function, ChainOfThoughtStep, which acts as a recursive reasoner. It consumes a problem statement, a history of previous thoughts, and a structured plan to GENERATE a YAML-formatted response containing current thinking, an updated plan, and a termination flag. The workflow utilizes a WHILE loop that persists as long as the LLM indicates that next_thought_needed is true. Within each iteration, the LLM performs an EVALUATE-like self-assessment of the prior step, executes the next pending task from the plan, and refines the plan structure. When the LLM executes the Conclusion step and sets the termination flag, the workflow returns the final reasoning trace with a done status." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```