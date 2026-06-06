## 0. High-level Description
The WORKFLOW content_refinement_process implements an iterative self-correction pattern to ensure high-quality text generation. It utilizes two logical functions: draft_content, which acts as the primary generator, and evaluate_content, which serves as a strict quality judge. The process begins by initializing state variables for attempts and feedback before entering a WHILE loop that persists as long as the content evaluation results in a "FAIL" and the attempt count is below a threshold of three. Within the loop, the workflow uses GENERATE to produce content and subsequently uses GENERATE to evaluate that content against a specific topic. An EVALUATE construct checks the judge's verdict; if it contains a "FAIL" sentinel, the feedback is updated to include the judge's critique for the next iteration, otherwise, the loop terminates. Finally, the workflow uses RETURN WITH to provide the final content alongside a non-trivial status of either "complete" or "max_attempts" based on the final verdict.

## 1. Purpose
This implementation automates the drafting and rigorous peer-review of technical articles to ensure they meet quality standards before final delivery.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| WORKFLOW | `run_content_refinement(topic)` | The main entry point for the orchestration logic. |
| CREATE FUNCTION | `draft_content(...)`, `evaluate_content(...)` | Reusable prompt templates with parameter slots. |
| GENERATE | `call_llm(prompt)` inside functions | Execution of the LLM call and assignment to variables. |
| WHILE | `while "FAIL" in verdict and attempts < _MAX_ATTEMPTS:` | Loop condition based on judge feedback and safety counter. |
| EVALUATE | `if "FAIL" in verdict:` | Branching logic to extract feedback from the LLM output. |
| @vars | `attempts`, `verdict`, `content`, `feedback` | Shared state maintained throughout the workflow execution. |
| RETURN WITH | `return {"status": "complete" ...}` | Returns the final result with specific lifecycle status tokens. |

## 3. Logical Functions / Prompts

### draft_content
- **Role**: Creative generator responsible for producing the core article.
- **Key Conventions**: Accepts an optional `feedback` parameter. If feedback exists, it is appended to the prompt to guide the LLM in revising the previous draft.

### evaluate_content
- **Role**: Quality gatekeeper/judge.
- **Key Conventions**: Uses specific sentinel tokens ("PASS" or "FAIL"). It is instructed to provide the verdict first, followed by a newline and detailed feedback if the content is insufficient.

## 4. Control Flow
The workflow starts by setting the initial state: `attempts` at 0 and `verdict` as "FAIL" to trigger the entry condition. It enters a **WHILE** loop constrained by the "FAIL" status and a maximum of 3 attempts. Inside the loop, it **GENERATE**s a draft, followed by a **GENERATE** call to the evaluator. An **EVALUATE** block checks the LLM response: if it contains "FAIL", the feedback variable is updated with the judge's comments; otherwise, it proceeds toward completion. The workflow terminates when a "PASS" is detected or the limit is reached, finally executing a **RETURN WITH** `status="complete"` or `status="max_attempts"`.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The WORKFLOW content_refinement_process implements an iterative self-correction pattern to ensure high-quality text generation. It utilizes two logical functions: draft_content, which acts as the primary generator, and evaluate_content, which serves as a strict quality judge. The process begins by initializing state variables for attempts and feedback before entering a WHILE loop that persists as long as the content evaluation results in a 'FAIL' and the attempt count is below a threshold of three. Within the loop, the workflow uses GENERATE to produce content and subsequently uses GENERATE to evaluate that content against a specific topic. An EVALUATE construct checks the judge's verdict; if it contains a 'FAIL' sentinel, the feedback is updated to include the judge's critique for the next iteration, otherwise, the loop terminates. Finally, the workflow uses RETURN WITH to provide the final content alongside a non-trivial status of either 'complete' or 'max_attempts' based on the final verdict." --mode workflow

# Step 2 — compile to any target
spl3 splc compile content_refinement.spl --lang python/pocketflow
spl3 splc compile content_refinement.spl --lang python/langgraph
spl3 splc compile content_refinement.spl --lang go
```