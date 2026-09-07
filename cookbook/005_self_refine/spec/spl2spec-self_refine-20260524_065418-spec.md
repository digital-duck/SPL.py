## Summary

This implementation is a Self-Refine Pattern workflow that uses LLMs (Large Language Models) to iteratively improve written content through critique and refinement. The workflow takes as input a task, an output budget, and several model names, and produces a final output after a maximum of 3 iterations or when the budget is exceeded.

## Detailed Specification

### 1. Purpose

This implementation accomplishes the task of iteratively improving written content through critique and refinement using LLMs.

### 2. High-level Description

The Self-Refine Pattern workflow uses three LLM functions: `draft`, `critique`, and `refine`. These functions work together in a loop to improve the input text based on feedback from both an expert writer model and a strict critic model. The process starts with an initial draft, which is then critiqued and refined until either a maximum number of iterations or budget exhaustion occurs. Throughout this process, side effects such as logging progress and writing intermediate files are handled using separate tool calls.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
| --- | --- | --- |
| WORKFLOW | CREATE WORKFLOW | Declares a named multi-step LLM orchestration workflow |
| CREATE FUNCTION | CREATE FUNCTION | Reusable prompt template with {param} slots |
| GENERATE | GENERATE | LLM call, stores result in a variable |
| CALL | CALL | Side-effect tool call (file write, HTTP, etc.) |
| WHILE | WHILE | Loop until condition is false |
| EXCEPTION | EXCEPTION | Named exception handler |
| EVALUATE | EVALUATE | Branch on LLM output |
| RETURN | RETURN | Return with metadata (status, iterations, etc.) |

Note: The `RETURN` construct only appears when a non-trivial status token ("complete", "partial", or "budget_limit") drives a real branch or terminates the loop.

### 4. Logical Functions / Prompts

*   *draft*
    *   Role in workflow: Initial text generation
    *   Key prompt conventions: Output budget, model name
*   *critique*
    *   Role in workflow: Feedback analysis
    *   Key prompt conventions: Model name, input text output
*   *refine*
    *   Role in workflow: Text refinement
    *   Key prompt conventions: Input text output, feedback

### 5. Control Flow

1.  Initial draft generation
2.  Loop until maximum iterations or budget exhaustion:
    *   Critique the current draft
    *   Refine the current draft based on critique feedback
3.  If loop exhausted, commit best effort and return final result.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "<paste Section 1 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```