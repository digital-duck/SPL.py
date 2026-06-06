## 0. High-level Description
This workflow implements a self-correcting generation-and-evaluation loop that refines a textual description until it meets a predefined quality threshold. It defines two reusable prompt templates via CREATE FUNCTION: a generator that drafts or improves a description based on the current state and iterative feedback, and an evaluator that scores the output and issues a structured pass/fail verdict. The orchestration uses a WHILE loop bounded by a maximum retry count and a workflow status flag, executing sequential GENERATE calls to produce the draft and then assess it against quality criteria. An EVALUATE branch inspects the evaluator’s response for a "pass" sentinel; if matched, it transitions the status to terminate the loop, otherwise it captures the feedback payload to seed the next iteration. The process concludes by RETURNing the final polished description alongside a completion status, while relying on a shared HTTP-backed LLM client that provides a graceful mock fallback for zero-configuration execution. No named EXCEPTION handlers are invoked, as transient failures and refinement cycles are natively absorbed by the retry bounds and state tracking.

## 1. Purpose
This implementation automatically iterates on a generated text description, using LLM-based self-evaluation and feedback integration to produce a high-quality, concise final output within a strictly bounded number of refinement cycles.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `def S3_judge_openrouter_qwen(initial_state: str) -> Dict[str, Any]` | Entry function that encapsulates the orchestration logic and shared context |
| `CREATE FUNCTION` | `generate_description()` and `evaluate_description()` | Python functions containing f-string prompt templates and returning LLM text |
| `GENERATE` | `context["description"] = generate_description(...)`<br>`context["verdict"] = evaluate_description(...)` | Direct invocations of prompt functions; results stored in context dict acting as SPL `@vars` |
| `WHILE <cond> DO ... END` | `while context["attempts"] <= 2 and context["status"] == "retry":` | Loop guard enforces max 2 retries OR early exit on success |
| `EVALUATE <var> WHEN contains(...) THEN ... ELSE ... END` | `if "pass" in context["verdict"].lower(): ... else: ...` | String-matching branch that routes to success state or feedback accumulation |
| `@<var>` (shared state) | `context` dictionary | Holds `shared_state`, `attempts`, `verdict`, `feedback`, `status`, and `description` across steps |
| `RETURN @<var> WITH status = ...` | `return {"final_result": final_result, "status": context["status"]}` | Non-trivial termination token that exits loop and surfaces metadata to caller |

## 3. Logical Functions / Prompts
**`generate_description(state, feedback)`**
- **Role**: Produces an initial draft or iteratively refines a description based on prior evaluator feedback.
- **Key Prompt Conventions**: Parameterized with `{state}` and `{feedback}`; explicitly enforces conciseness, clarity, and anti-repetition; expects plain text output.

**`evaluate_description(description)`**
- **Role**: Acts as a quality gate/scorer that determines whether the draft meets acceptance thresholds.
- **Key Prompt Conventions**: Requires strict sentinel formatting (`VERDICT: pass` or `VERDICT: fail`); mandates a numeric score; demands specific improvement suggestions on failure; implicitly uses `score >= 7` as the pass/fail boundary.

## 4. Control Flow
The workflow begins by initializing shared state variables, setting `@status` to `"retry"` and `@attempts` to `0`. It immediately enters a WHILE loop conditioned on `@attempts <= 2 AND @status = "retry"`. Inside the loop, it first GENERATEs a description using the current `@shared_state` and `@feedback`, storing the output in `@description`. It then GENERATEs an evaluation of that description, storing the result in `@verdict`. An EVALUATE construct inspects `@verdict` for the `"pass"` substring; if detected, `@status` is set to `"pass"`, which satisfies the loop exit condition on the next evaluation. If `"pass"` is absent, the workflow increments `@attempts`, assigns the full `@verdict` text to `@feedback` for the next generation cycle, and continues looping. Once the WHILE condition evaluates to false, the final `@description` is captured and the workflow terminates by RETURNing the result with the resolved status metadata.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a self-correcting generation-and-evaluation loop that refines a textual description until it meets a predefined quality threshold. It defines two reusable prompt templates via CREATE FUNCTION: a generator that drafts or improves a description based on the current state and iterative feedback, and an evaluator that scores the output and issues a structured pass/fail verdict. The orchestration uses a WHILE loop bounded by a maximum retry count and a workflow status flag, executing sequential GENERATE calls to produce the draft and then assess it against quality criteria. An EVALUATE branch inspects the evaluator’s response for a "pass" sentinel; if matched, it transitions the status to terminate the loop, otherwise it captures the feedback payload to seed the next iteration. The process concludes by RETURNing the final polished description alongside a completion status, while relying on a shared HTTP-backed LLM client that provides a graceful mock fallback for zero-configuration execution. No named EXCEPTION handlers are invoked, as transient failures and refinement cycles are natively absorbed by the retry bounds and state tracking." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```