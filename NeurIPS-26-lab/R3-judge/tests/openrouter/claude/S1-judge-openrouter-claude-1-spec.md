## 0. High-level Description

This workflow implements a **generate-then-judge** pattern for producing high-quality product descriptions using two cooperative LLM-backed logical functions: **Generator** and **Judge**. The Generator function uses a prompt template with `{task}` and `{feedback}` parameter slots to produce a 2–3 sentence product description in YAML format; when feedback from a prior failed attempt is present, it is injected into the prompt to guide revision. The Judge function evaluates the draft on a 1–10 scale for clarity and persuasiveness, returning a structured YAML response containing a numeric score, a verdict token (`PASS` or `FAIL`), reasoning, and improvement feedback. A WHILE loop drives repeated generation-and-evaluation cycles: the Judge's `"fail"` action token routes control back to the Generator for revision, while a `"pass"` token (issued when `score >= 7` or the verdict is `PASS`) terminates the loop and commits the draft as the final result. A hard cap of three attempts is enforced inside the Judge's post-processing logic — if the maximum is reached, the current draft is accepted unconditionally and the workflow exits with `status=pass`. Shared state (`@shared`) carries the task description, the current draft, the attempt counter, feedback text, and the final accepted description and score across all nodes. A CALL side-effect optionally writes the final description, score, and task to a file when an output path is provided. The LLM backend is abstracted through a shim that auto-selects GPT-4o (OpenAI) or Gemini-2.0-Flash based on available API keys, making the workflow multi-model by configuration.

---

## 1. Purpose

This workflow automatically generates and iteratively refines a product description for a given task, using an LLM judge to enforce a quality threshold (score ≥ 7/10), and optionally saves the accepted result to a file.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW create_judge_flow` | `create_judge_flow()` in `flow.py` + `main()` in `main.py` | Declares the named orchestration pipeline and its entry point |
| `CREATE FUNCTION Generator` | `class Generator(Node)` with `prep/exec/post` methods | Prompt template with `{task}` and `{feedback}` slots; builds prompt dynamically in `exec` |
| `CREATE FUNCTION Judge` | `class Judge(Node)` with `prep/exec/post` methods | Prompt template for scoring; parses YAML score, verdict, reasoning, and feedback |
| `GENERATE Generator(...) INTO @draft` | `Generator.exec(inputs)` → `shared["draft"]` | LLM call producing the product description; result stored in shared state |
| `GENERATE Judge(...) INTO @evaluation` | `Judge.exec(draft)` → `exec_res` dict | LLM call producing score, verdict, reasoning, feedback; result parsed from YAML |
| `WHILE verdict == "FAIL" AND attempts < 3 DO` | `judge - "fail" >> generator` edge + attempt counter in `Judge.post` | Loop back to Generator on failure; loop exits on `"pass"` or max attempts |
| `EVALUATE @verdict WHEN contains('PASS') THEN ... ELSE ...` | `if verdict.upper() == "PASS" or score >= 7` in `Judge.post` | Branches on verdict/score; `"pass"` exits loop, `"fail"` re-enters Generator |
| `RETURN @result WITH status="pass"` | `return "pass"` from `Judge.post`; sets `shared["final_description"]`, `shared["final_score"]` | Non-trivial action token that terminates the loop and commits the final result |
| `RETURN @result WITH status="fail"` | `return "fail"` from `Judge.post` | Non-trivial action token that routes control back to Generator for revision |
| `CALL FileWrite(...) INTO @saved` | `Path(out).write_text(...)` in `main.py` | Optional side-effect; writes task, score, and description to a file path |
| `EXCEPTION WHEN MaxRetriesExceeded` | `if shared["attempts"] >= 3` → force `"pass"` | Hard cap on iterations; accepts current draft unconditionally at limit |
| Shared state (`@shared` vars) | `shared` dict passed through all `prep/exec/post` calls | Carries `task`, `draft`, `attempts`, `feedback`, `final_description`, `final_score` |
| Multi-model backend | `call_llm()` shim in `utils.py` | Auto-selects GPT-4o or Gemini-2.0-Flash based on `OPENAI_API_KEY` / `GEMINI_API_KEY` |

---

## 3. Logical Functions / Prompts

### Generator

- **Role:** Produces a 2–3 sentence product description for the given task; on revision cycles, incorporates judge feedback to improve the prior draft.
- **Key prompt conventions:**
  - Primary instruction: *"Write a product description for: {task}. The description should be clear, persuasive, and compelling. Keep it to 2–3 sentences."*
  - Conditional feedback injection: if `{feedback}` is non-empty, appends *"Previous attempt was rejected. Here is the feedback: {feedback}. Please improve based on this feedback."*
  - **Output format:** Fenced YAML block with a single `description` key containing a multi-line string.
  - **Sentinel:** ` ```yaml ` / ` ``` ` fences used to extract and parse the structured response.
  - Result stored in `shared["draft"]` after stripping whitespace.

### Judge

- **Role:** Evaluates the current draft on clarity and persuasiveness, assigns a score, issues a binary verdict, and generates actionable feedback for failed attempts.
- **Key prompt conventions:**
  - Primary instruction: *"Rate this product description on a scale of 1–10 for clarity and persuasiveness."*
  - Input: the full draft text interpolated directly into the prompt.
  - **Output format:** Fenced YAML block with four keys:
    - `score` (integer 1–10)
    - `reasoning` (multi-line string, brief justification)
    - `verdict` (string sentinel: `"PASS"` if score ≥ 7, otherwise `"FAIL"`)
    - `feedback` (multi-line string, specific improvement suggestions; meaningful only on `FAIL`)
  - **Sentinel tokens:** `PASS` / `FAIL` drive the EVALUATE branch that determines loop continuation.
  - Scoring threshold: `score >= 7` is treated as equivalent to `PASS` even if the verdict field disagrees.
  - On `PASS` or max-attempts: commits `shared["final_description"]` and `shared["final_score"]`.
  - On `FAIL`: increments `shared["attempts"]`, stores feedback in `shared["feedback"]` for the next Generator call.

---

## 4. Control Flow

1. **Initialization:** `shared` is seeded with `{"task": <user input>, "attempts": 0}`; no feedback is present on the first cycle.
2. **Generator (first call):** Reads `task` and empty `feedback` from `shared`; calls the LLM; stores the resulting description in `shared["draft"]`.
3. **Judge (evaluation):** Reads `shared["draft"]`; calls the LLM; parses the YAML evaluation.
   - **EVALUATE branch — PASS path:** If `verdict == "PASS"` or `score >= 7`, the Judge writes `final_description` and `final_score` to `shared` and returns `"pass"`, terminating the loop.
   - **EVALUATE branch — FAIL path:** If `verdict == "FAIL"` and `score < 7`, the Judge increments `shared["attempts"]` and stores feedback.
     - **WHILE condition check (max-attempts guard):** If `shared["attempts"] >= 3`, the Judge force-accepts the draft (writes `final_description` and `final_score`) and returns `"pass"`, terminating the loop — this is the `EXCEPTION WHEN MaxRetriesExceeded` handler.
     - Otherwise, returns `"fail"`, routing control back to the Generator for a feedback-informed revision.
4. **Generator (revision cycles):** On re-entry, `feedback` is now populated in `shared`; the prompt is augmented with the judge's suggestions before the next LLM call.
5. **Termination:** The WHILE loop exits when the Judge returns `"pass"` (either by quality threshold or max-attempts cap). The final description and score are printed to stdout.
6. **Optional side-effect (CALL FileWrite):** If `--out` was provided, the result is written to the specified file path, with parent directories created as needed.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a generate-then-judge pattern for \
producing high-quality product descriptions using two cooperative LLM-backed logical \
functions: Generator and Judge. The Generator function uses a prompt template with {task} \
and {feedback} parameter slots to produce a 2–3 sentence product description in YAML \
format; when feedback from a prior failed attempt is present, it is injected into the \
prompt to guide revision. The Judge function evaluates the draft on a 1–10 scale for \
clarity and persuasiveness, returning a structured YAML response containing a numeric \
score, a verdict token (PASS or FAIL), reasoning, and improvement feedback. A WHILE loop \
drives repeated generation-and-evaluation cycles: the Judge's fail action token routes \
control back to the Generator for revision, while a pass token (issued when score >= 7 \
or the verdict is PASS) terminates the loop and commits the draft as the final result. \
A hard cap of three attempts is enforced inside the Judge — if the maximum is reached, \
the current draft is accepted unconditionally and the workflow exits with status=pass. \
Shared state carries the task description, the current draft, the attempt counter, \
feedback text, and the final accepted description and score across all nodes. A CALL \
side-effect optionally writes the final description, score, and task to a file when an \
output path is provided. The LLM backend auto-selects GPT-4o or Gemini-2.0-Flash based \
on available API keys." \
--mode workflow

# Step 2 — compile to any target runtime
spl3 splc compile judge_workflow.spl --lang python/pocketflow
spl3 splc compile judge_workflow.spl --lang python/langgraph
spl3 splc compile judge_workflow.spl --lang go
```