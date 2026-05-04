## 0. High-level Description
This workflow implements an evaluator-optimizer pattern that iteratively refines a product description using an LLM-as-judge loop. The process begins with a `GENERATE` call to the `generate_description` function, which drafts a concise, persuasive text and optionally incorporates prior feedback. A subsequent `GENERATE` call to the `evaluate_description` function scores the draft on clarity and persuasiveness, extracting structured YAML metadata including a numeric score, verdict, and improvement suggestions. The workflow employs an `EVALUATE` block to branch on the judge’s verdict; if the score falls below the quality threshold and the iteration limit has not been reached, it assigns a `fail` status and loops back via a `WHILE` condition to regenerate the content with the new feedback. Once the quality threshold is met or the maximum attempt count is exceeded, the workflow triggers a non-trivial `RETURN` with a `pass` status, persisting the final draft and score to shared state before optionally writing the result to disk. Underlying LLM routing is abstracted through a multi-model shim, allowing the workflow to remain provider-agnostic, while parsing failures or network drops are handled via implicit fallback routines rather than explicit `EXCEPTION` handlers.

## 1. Purpose
This implementation automatically generates, evaluates, and iteratively refines a product description until it meets a configurable quality threshold or reaches a maximum number of attempts.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| `WORKFLOW` | `Flow(start=generator)` in `flow.py` | Orchestrates the directed acyclic graph (DAG) with a single feedback edge and manages shared state lifecycle |
| `CREATE FUNCTION` | Prompt strings in `Generator.exec()` & `Judge.exec()` | Reusable templates with `{task}`, `{draft}`, `{feedback}` interpolation slots and strict YAML formatting instructions |
| `GENERATE` | `call_llm(prompt)` + YAML parsing | Executes the LLM inference and extracts structured response blocks into local variables |
| `EVALUATE` | `if verdict.upper() == "PASS" or score >= 7:` in `Judge.post()` | Branches control flow based on LLM-extracted `score` and `verdict` metadata |
| `WHILE` | `while shared["attempts"] < 3` implicit loop | Driven by the `"fail"` routing edge; exits when `attempts >= 3` or a pass occurs |
| `RETURN` | `return "pass"` / `return "fail"` in `Judge.post()` | Non-default action tokens that explicitly route execution to pipeline termination or the next iteration |
| `EXCEPTION` | Not explicitly modeled | Python relies on default crash/traceback behavior; SPL would map to `EXCEPTION WHEN YAMLParseError THEN ...` for malformed outputs |
| Shared `@vars` | `shared` dictionary | Holds `@task`, `@draft`, `@attempts`, `@feedback`, `@final_description`, and `@final_score` across steps |

## 3. Logical Functions / Prompts
**`generate_description`**
- **Role**: Draft the initial or revised product description based on the input task and any accumulated critique.
- **Key prompt conventions**: Enforces a strict 2–3 sentence limit, mandates YAML output with a single `description` key, and conditionally appends a "Previous attempt was rejected. Here is the feedback:" block when revision is needed.

**`evaluate_description`**
- **Role**: Act as an LLM judge to score the draft's clarity/persuasiveness, determine pass/fail status, and generate actionable revision guidance.
- **Key prompt conventions**: Requires a 1–10 numeric scale, mandates YAML output with `score`, `reasoning`, `verdict` ("PASS"/"FAIL"), and `feedback` keys, and explicitly instructs the model to only populate `feedback` when `verdict` is "FAIL".

## 4. Control Flow
The workflow initializes by invoking `GENERATE generate_description(task, feedback="")` to produce the first draft and storing it in `@draft`. Execution then proceeds to `GENERATE evaluate_description(@draft)` which returns structured judgment metadata. An `EVALUATE` block inspects the extracted `score` and `verdict`; if the score is at least 7, a `RETURN` with status=`pass` is emitted, saving `@draft` and `@score` to final shared variables and terminating the pipeline. If the threshold is not met, the system increments `@attempts` and stores the LLM’s critique in `@feedback`. A `WHILE @attempts < 3` condition governs the iteration: when true and the status is `fail`, control routes back to the generator node to produce a revised draft incorporating the new feedback. When `@attempts` reaches 3, the loop forcibly breaks, the current draft is accepted, and the workflow commits the final result before optional disk persistence.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```