## 0. High-level Description
This WORKFLOW implements an iterative Evaluator-Optimizer pattern to refine product marketing content. The process begins by using a CREATE FUNCTION named `Generator` to draft a description based on a user-provided task. The output is then passed to a `Judge` function which performs an LLM-as-Judge evaluation, scoring the content on clarity and persuasiveness and providing structured feedback. A WHILE loop orchestrates the refinement process, continuing as long as the evaluation score is below a threshold and the maximum attempt count of three has not been reached. Inside the loop, an EVALUATE construct checks the judge's verdict: if it contains a failure signal, the `Generator` is called again, this time incorporating the feedback captured in a variable to improve the next draft. Once the judge returns a "PASS" or the loop terminates due to exhausted attempts, the workflow uses RETURN WITH to output the final description and the corresponding quality score.

## 1. Purpose
This implementation automates the iterative drafting and quality-assurance of product descriptions to ensure they meet a specific persuasiveness threshold (score >= 7) before delivery.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** | `create_judge_flow()` | Orchestrates the `Generator` and `Judge` nodes. |
| **CREATE FUNCTION** | `Generator.exec()` / `Judge.exec()` | Defines the prompt templates and expected YAML formats. |
| **GENERATE** | `call_llm(prompt)` | Executes the LLM call within the node's `exec` method. |
| **@var (Shared State)** | `shared` dictionary | Stores `task`, `draft`, `feedback`, and `attempts`. |
| **WHILE** | `judge - "fail" >> generator` | Implicit loop logic in `flow.py` managed by the node connections. |
| **EVALUATE** | `if verdict.upper() == "PASS" ...` | Conditional logic in `Judge.post` determines the next state. |
| **RETURN WITH** | `return "pass"` / `return "fail"` | Non-trivial status tokens used to drive the loop or terminate. |

## 3. Logical Functions / Prompts

### Generator
- **Role**: Creative content author.
- **Key Conventions**: Accepts `task` and optional `feedback`. It uses a YAML sentinel block (```yaml ... ```) to ensure the `description` field is easily parsable.

### Judge
- **Role**: Quality gatekeeper and critic.
- **Key Conventions**: Scores content on a 1-10 scale. It outputs a structured YAML object containing `score`, `reasoning`, `verdict` (PASS/FAIL), and specific `feedback` for the generator.

## 4. Control Flow
The execution starts with the `Generator` creating an initial draft from the input task. The flow then enters a cycle where the `Judge` evaluates the draft. 
- **WHILE Condition**: The flow continues to loop back to the `Generator` as long as the `Judge` returns a `fail` status.
- **Branch Logic**: Inside the `Judge` logic, an **EVALUATE** equivalent checks if the score is $\ge 7$ or if the attempt counter has hit 3. 
- **Termination**: If either condition is met, the workflow returns a `pass` status, exiting the loop and providing the final content via **RETURN WITH** including the final score and description.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements an iterative Evaluator-Optimizer pattern to refine product marketing content. The process begins by using a CREATE FUNCTION named Generator to draft a description based on a user-provided task. The output is then passed to a Judge function which performs an LLM-as-Judge evaluation, scoring the content on clarity and persuasiveness and providing structured feedback. A WHILE loop orchestrates the refinement process, continuing as long as the evaluation score is below a threshold and the maximum attempt count of three has not been reached. Inside the loop, an EVALUATE construct checks the judge's verdict: if it contains a failure signal, the Generator is called again, this time incorporating the feedback captured in a variable to improve the next draft. Once the judge returns a 'PASS' or the loop terminates due to exhausted attempts, the workflow uses RETURN WITH to output the final description and the corresponding quality score." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```