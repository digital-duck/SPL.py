## Summary

This SPL implementation, "Self-Refine Pattern", is a multi-step LLM workflow designed to improve written content through iterative critique and refinement. It takes an initial draft, evaluates it using two critical models (writer and critic), provides feedback, and then refines the content based on that feedback until it reaches a satisfactory level or exhausts its budget.

## Detailed Specification

### 1. Purpose
This workflow aims to produce high-quality written content through continuous refinement and critique, ensuring the output meets the desired standards.

### 2. High-level Description

The `self_refine` workflow is a multi-step process that starts with an initial draft of a text task (`What are the benefits of meditation?`). It then enters a loop where:

- The **Draft** prompt generates an initial response using a specified writer model.
- The **Critique** prompt evaluates the draft using a critic model, providing feedback if necessary. If the content is deemed fully satisfactory, it outputs [APPROVED]; otherwise, it provides actionable feedback.
- The **Refine** prompt refines the draft based on the critique feedback from both models.

The loop continues until:

- The maximum number of iterations has been reached (`@max_iterations`).
- The output budget has been exceeded (`@output_budget`).

At any point within or after the loop, if an approved response is received (`[APPROVED]`) or a task is exhausted, the workflow **Returns** with a specific status token indicating completion or partial success.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
| --- | --- | --- |
| WORKFLOW <name> | WORKFLOW <name> | Declares a named multi-step LLM orchestration workflow. |
| CREATE FUNCTION <name> | CREATE FUNCTION <name> | Reusable prompt template with {param} slots to define functions for draft, critique, and refine tasks. |
| GENERATE <fn>(...) INTO @<var> | GENERATE <fn>(...) INTO @<var> | LLM call that generates output into a variable at compile-time.|
| CALL <tool>(...) INTO @<var> | CALL <tool>(...) INTO @<var> | Side-effect tool call (file write, HTTP, etc.) that writes output to a file or performs an operation and returns the result to a variable. |
| WHILE <cond> DO ... END | WHILE <cond> DO ... END | Loop until condition is false, indicating iterative refinement process.|
| EXCEPTION WHEN <Type> THEN ... | EXCEPTION WHEN <Type> THEN ... | Exception handling for named exceptions (e.g., MaxIterationsReached, BudgetExceeded). |
| EVALUATE @<var> WHEN contains('...') THEN ... ELSE ... END | EVALUATE @<var> WHEN contains('...') THEN ... ELSE ... END | Branch on LLM output; in this case, checks for the presence of '[APPROVED]'. |

### 4. Logical Functions / Prompts

- **Draft**: Generates initial response.
  - Role: Initial draft of a text task.
  - Key Prompt Conventions: Uses `@writer_model` to generate content.

- **Critique**: Evaluates and provides feedback on the draft.
  - Role: Critical evaluation and feedback.
  - Key Prompt Conventions: Uses `@critic_model` to evaluate the draft, providing [APPROVED] for satisfactory content.

- **Refine**: Refines the draft based on critique feedback.
  - Role: Refinement process incorporating critical feedback.
  - Key Prompt Conventions: Uses both `@writer_model` and `@critic_model` to improve the content.

### 5. Control Flow

1. The workflow starts with an initial **Draft** prompt, generating the first response.
2. It then enters a loop where it:
   - Generates feedback from the **Critique** prompt if necessary.
   - Refines the draft based on this feedback using the **Refine** prompt.
3. This iterative process continues until one of two conditions is met:
   - The maximum number of iterations (`@max_iterations`) has been reached.
   - An approved response (`[APPROVED]`) is received, indicating that the content meets all desired criteria.
4. Upon reaching either condition, the workflow **Returns** with a specific status token to indicate completion or partial success.

### 6. How to Regenerate as SPL

1. Copy the `Self-Refine Pattern` specification into your text editor.
2. Run `spl3 text2spl --description "<paste Section 1 here>" --mode workflow`
3. Compile the generated SPL file for desired output languages (e.g., Python, PocketFlow, Go) using:
   - For Python/PocketFlow: `spl3 splc compile <output.spl> --lang python/pocketflow`
   - For Go: `spl3 splc compile <output.spl> --lang go`