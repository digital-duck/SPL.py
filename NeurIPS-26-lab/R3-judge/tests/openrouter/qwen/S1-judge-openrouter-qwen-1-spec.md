## 0. High-level Description
This WORKFLOW implements an evaluator-optimizer pattern using an LLM-as-Judge architecture to iteratively refine product descriptions until a quality threshold is met or a retry limit is reached. The process begins by invoking a CREATE FUNCTION for the Generator, which composes a persuasive 2-3 sentence description using an initial task parameter and any prior revision feedback, storing the output into a @draft variable via a GENERATE call. A second CREATE FUNCTION defines the Judge prompt, which evaluates the draft for clarity and persuasiveness on a 1-10 scale and returns structured YAML feedback, captured through another GENERATE call that supports interchangeable backend models via an API routing shim. The orchestration uses a WHILE loop that continues until the @score reaches at least 7 or the @attempts counter exceeds 3, branching internally with an EVALUATE statement that routes execution back to the Generator on FAIL or proceeds to finalization on PASS. Upon successful validation or exhaustion of retries, the workflow persists the accepted text and metadata via a RETURN statement, optionally triggering a CALL side-effect to write the final result to a markdown file, while wrapping all parsing and network operations in an EXCEPTION handler for graceful failure recovery.

## 1. Purpose
This implementation automatically generates, evaluates, and iteratively refines product descriptions using an LLM judge until the output achieves a minimum clarity and persuasiveness score of 7 out of 10 or reaches a maximum of three attempts.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---------------|-------------------|-------|
| `WORKFLOW <name>` | `flow.create_judge_flow()` + `Flow(start=generator)` | Declares the top-level orchestration container and entry node |
| `CREATE FUNCTION <name>` | `prompt` template strings inside `Generator.exec()` and `Judge.exec()` | Defines reusable prompt templates with `{task}`, `{feedback}`, and `{draft}` interpolation slots |
| `GENERATE <fn>(...) INTO @<var>` | `utils.call_llm(prompt)` + `yaml.safe_load()` parsing | Executes the LLM call, parses structured response, and assigns result to workflow variables (`@draft`, `@judgment`) |
| `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | `if verdict.upper() == "PASS" or score >= 7:` conditional in `Judge.post()` | Routes control flow based on structured LLM output (`@verdict`, `@score`) |
| `WHILE <cond> DO ... END` | `judge - "fail" >> generator` edge + `shared.get("attempts", 0) < 3` guard | Implements the retry loop with explicit failure routing and attempt counter limit |
| `RETURN @<var> WITH <k>=<v>, ...` | `shared["final_description"] = ...` + CLI output in `main.py` | Exits the workflow, surfaces the accepted draft, and attaches metadata (`status`, `score`, `iterations`) |
| `EXCEPTION WHEN <Type> THEN ...` | Implicit `try/except` around `call_llm` and `yaml.safe_load()` | Handles malformed YAML responses, API timeouts, or parsing failures gracefully |
| Shared state (`@<var>`) | `shared` dictionary passed through `prep()`, `exec()`, and `post()` | Centralized context store for `@task`, `@attempts`, `@draft`, `@feedback`, and final results |

## 3. Logical Functions / Prompts
### GenProductDescription
- **Role in the workflow:** Drafts the initial or revised product description based on the core task specification and iterative judge feedback.
- **Key prompt conventions:** Enforces a strict 2-3 sentence length constraint. Requires output wrapped in ````yaml` code blocks. Expects a single `description: |` key. Dynamically appends a revision instruction block when `@feedback` is non-empty.

### JudgeProductDescription
- **Role in the workflow:** Acts as the quality gate by scoring the draft, determining pass/fail status, and generating actionable critique for the next iteration.
- **Key prompt conventions:** Uses a 1-10 numeric scale for clarity and persuasiveness. Requires strict ````yaml` output containing four keys: `score` (int), `reasoning` (string), `verdict` ("PASS"/"FAIL"), and `feedback` (string). The `verdict` token must align with `score >= 7` to trigger loop termination.

## 4. Control Flow
Execution initializes `@task` from user input, sets `@attempts = 0`, and immediately invokes the first `GENERATE` step to produce `@draft`. A subsequent `GENERATE` step evaluates the draft and populates `@score`, `@verdict`, and `@feedback`. The workflow then enters a `WHILE @attempts < 3 AND @score < 7 DO` loop. Inside the loop, an `EVALUATE @verdict WHEN contains("PASS") OR @score >= 7 THEN` branch assigns `@final_description = @draft`, updates `@final_score`, and breaks the loop. In the `ELSE` branch, `@attempts` increments, `@feedback` captures the judge's critique, and control returns to the `GENERATE` step with the updated context. Once the loop condition evaluates to false (either via successful pass or max retry exhaustion), the workflow executes `RETURN @final_description WITH status="completed", score=@final_score, iterations=@attempts`. If an output path is specified, a `CALL write_file` side-effect persists the result. Any `YAMLError` or network timeout during `GENERATE` triggers the `EXCEPTION WHEN ParseError` block, which logs the fault and falls back to returning the last valid `@draft` with `status="degraded"`.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```