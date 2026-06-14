## 0. High-level Description

This workflow implements an evaluator-optimizer loop using the LLM-as-Judge pattern to iteratively generate and refine product descriptions. A `Generator` function (CREATE FUNCTION) takes a product task and optional prior feedback as inputs, calling the LLM (GENERATE) to produce a 2–3 sentence description in YAML-fenced format; on subsequent iterations it incorporates structured feedback from the previous failed attempt. A `Judge` function (CREATE FUNCTION) receives the draft and calls the LLM (GENERATE) to rate clarity and persuasiveness on a 1–10 scale, returning a YAML-fenced object containing `score`, `reasoning`, `verdict`, and `feedback` fields. Control flow is expressed as a WHILE loop (WHILE attempts < 3 AND score < 7) with an EVALUATE branch on the verdict field: when verdict equals "PASS" or score >= 7, the loop exits and the workflow RETURNs the accepted description WITH status="pass", score, and iteration count; otherwise the Judge stores its feedback into shared state (@feedback), increments @attempts, and the loop routes back to the Generator. A hard-coded max-attempts guard of 3 forces a terminal RETURN WITH status="max_attempts" if the quality threshold is never reached, ensuring the workflow always terminates. The implementation uses a single LLM provider (OpenAI gpt-4o or Gemini gemini-2.0-flash, selected at runtime) and writes the final result to an optional file via a CALL side-effect; no explicit EXCEPTION handler is defined, relying on node-level retry logic (max_retries=3, wait=10s) for transient LLM failures.

---

## 1. Purpose

Automatically produce a high-quality product description by running an LLM generator/judge loop that refines drafts based on structured feedback until a clarity-and-persuasiveness score of 7/10 or higher is achieved (or 3 attempts are exhausted).

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW judge_optimizer` | `create_judge_flow()` + `Flow.run(shared)` | Entire flow object and its `run()` call constitute the workflow entry point |
| `CREATE FUNCTION generator` | `Generator(Node)` class (`prep` + `exec` + `post`) | `prep` reads shared state; `exec` builds and calls the prompt; `post` writes back to shared |
| `CREATE FUNCTION judge` | `Judge(Node)` class (`prep` + `exec` + `post`) | Same three-phase pattern |
| `GENERATE generator(task, feedback) INTO @draft` | `call_llm(prompt)` inside `Generator.exec`, result written to `shared["draft"]` in `post` | YAML fencing is the structured output contract |
| `GENERATE judge(draft) INTO @evaluation` | `call_llm(prompt)` inside `Judge.exec`, parsed dict returned | Score, verdict, and feedback fields extracted from YAML block |
| `WHILE attempts < 3 AND score < 7 DO` | `judge - "fail" >> generator` edge + attempts counter in `Judge.post` | PocketFlow graph routing; loop termination encoded in edge action string |
| `EVALUATE @verdict WHEN contains('PASS')` | `if verdict.upper() == "PASS" or score >= 7` in `Judge.post` | Returns `"pass"` or `"fail"` action string to drive routing |
| `RETURN @draft WITH status="pass", score=, iterations=` | `shared["final_description"]`, `shared["final_score"]` set before returning `"pass"` | Caller reads these keys from `shared` after `flow.run()` |
| `RETURN @draft WITH status="max_attempts"` | `if shared["attempts"] >= 3: ... return "pass"` | Forced exit with below-threshold score still uses the `"pass"` action |
| `CALL write_file(path, content)` | `Path(out).write_text(...)` in `main.py` | Conditional side-effect; only executed when `--out` flag is provided |
| `EXCEPTION WHEN RetryError` | `max_retries=3, wait=10` on each `Node` constructor | PocketFlow built-in retry; no explicit `EXCEPTION WHEN` block in user code |
| Shared state (`@var`) | `shared` dict passed through every `prep`/`post` | Single mutable dict acts as the SPL variable namespace across all nodes |

---

## 3. Logical Functions / Prompts

### `generator`
- **Role**: Drafts a 2–3 sentence product description for a given task; incorporates structured feedback when revising a prior rejected draft.
- **Key prompt conventions**:
  - Conditional feedback block appended only when `shared["feedback"]` is non-empty.
  - Sentinel tokens: ` ```yaml ` / ` ``` ` fence wrapping a single `description:` key.
  - Output format: YAML block parsed with `yaml.safe_load`; `.strip()` applied to the scalar value.

### `judge`
- **Role**: Evaluates the current draft on a 1–10 scale for clarity and persuasiveness; produces a structured verdict with improvement feedback.
- **Key prompt conventions**:
  - Scoring rubric embedded in prompt: "1–10 for clarity and persuasiveness."
  - Sentinel tokens: ` ```yaml ` / ` ``` ` fence wrapping four keys: `score` (int), `reasoning` (str), `verdict` ("PASS"/"FAIL"), `feedback` (str, populated only on FAIL).
  - Pass threshold is defined in prose inside the prompt comment (`# Use "PASS" if score >= 7`), making it a soft contract; hard enforcement is done in `Judge.post`.

---

## 4. Control Flow

```
START
  │
  ▼
GENERATE generator(task, feedback="") INTO @draft          ← first iteration, no feedback
  │
  ▼
GENERATE judge(@draft) INTO @evaluation
  │
  ▼
EVALUATE @evaluation.verdict
  WHEN "PASS" OR score >= 7  ──────────────────────────────► RETURN @draft
  THEN                                                         WITH status="pass",
       shared["final_description"] = draft                         score=@evaluation.score
       shared["final_score"] = score
       action = "pass"
  │
  ELSE (verdict == "FAIL" AND score < 7)
       shared["attempts"] += 1
       shared["feedback"] = evaluation.feedback
       │
       IF attempts >= 3  ──────────────────────────────────► RETURN @draft
       THEN                                                    WITH status="max_attempts",
            shared["final_description"] = draft                    score=@evaluation.score
            shared["final_score"] = score
            action = "pass"   ← forced exit
       │
       ELSE
            action = "fail"
            │
            ▼
       WHILE action == "fail" DO
            GENERATE generator(task, @feedback) INTO @draft
            ...loop back to EVALUATE
       END
  END
```

Termination is guaranteed by the attempt counter; the WHILE resolves to either a quality-pass RETURN or a max-attempts RETURN, both with `status` metadata.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```