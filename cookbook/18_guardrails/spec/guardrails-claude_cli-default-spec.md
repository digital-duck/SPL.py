## Summary

The Guardrails Pipeline is a safety-first LLM workflow that filters user requests through four sequential gates before returning a response. It combines fast deterministic checks (keyword screening, PII detection) with nuanced LLM-based classification to block harmful or off-topic content, redact sensitive data, generate a response only on clean input, and then validate that the output itself is safe. Security teams and product owners building compliant AI assistants are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Protect users and systems by enforcing a four-gate safety pipeline — input keyword screening, LLM content classification, PII detection and redaction, safe response generation, and output validation — before any LLM-generated text is returned to the caller.

---

### 2. High-level Description

The workflow is declared as `WORKFLOW guardrails_pipeline` and accepts two optional TEXT inputs: `@input_id` (a catalog key for pre-defined test cases) and `@user_input` (ad-hoc freeform text). A deterministic `CALL load_test_input` resolves the catalog entry into `@test_context`; when no catalog key is provided, `@user_input` is used directly.

Gate 1a is a fast deterministic `CALL classify_input_keywords` that pattern-matches obvious harmful or off-topic signals. An `EVALUATE` on `@keyword_class` short-circuits with a blocked `RETURN` carrying `status='blocked_harmful'` or `status='blocked_off_topic'` before any token is spent on an LLM. Gate 1b handles the nuanced cases that keywords miss: a `GENERATE classify_input` call produces `@input_class`, and a second `EVALUATE` applies the same block logic with `gate='llm_classifier'` metadata.

Gate 2 runs a deterministic `CALL detect_pii` against `@user_input`. When PII is found, a second deterministic `CALL redact_pii` sanitizes the text into `@clean_input`; otherwise `@clean_input` is set directly to `@user_input`. Gate 3 calls `GENERATE safe_response` on the now-clean input to produce `@raw_response`. Gate 4 calls `GENERATE validate_output` to check for PII leakage or hallucination in the generated text; an `EVALUATE` on `@output_check` either accepts the response, redacts it, retries generation with lower temperature (`RETRY WITH temperature=0.1 LIMIT 3`), or substitutes a safe fallback message.

The workflow concludes with `RETURN @safe_response WITH status='complete'` and carries `input_class` and `pii_detected` metadata for downstream audit. Three named `EXCEPTION` handlers cover `RefusalToAnswer`, `HallucinationDetected`, and `BudgetExceeded`, each returning a status-tagged refusal message.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW guardrails_pipeline` | `WORKFLOW <name>` | Declares the named pipeline; INPUT/OUTPUT/SECURITY annotations are part of the signature |
| `CALL load_test_input(...)` | `CALL <tool>(...) INTO @<var>` | Deterministic catalog lookup; no LLM involved |
| `CALL classify_input_keywords(...)` | `CALL <tool>(...) INTO @<var>` | Fast keyword pre-screen; deterministic |
| `CALL detect_pii(...)` | `CALL <tool>(...) INTO @<var>` | Deterministic regex/rule-based PII scan |
| `CALL redact_pii(...)` | `CALL <tool>(...) INTO @<var>` | Deterministic redaction; called conditionally on both input and output |
| `GENERATE classify_input(...)` | `GENERATE <fn>(...) INTO @<var>` | LLM call for nuanced input classification |
| `GENERATE safe_response(...)` | `GENERATE <fn>(...) INTO @<var>` | LLM call with safety-tuned prompt; may be retried |
| `GENERATE validate_output(...)` | `GENERATE <fn>(...) INTO @<var>` | LLM call to check output for PII leakage or hallucination |
| `EVALUATE @keyword_class WHEN STARTSWITH ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Drives early-exit branches on Gate 1a |
| `EVALUATE @input_class WHEN ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Drives early-exit branches on Gate 1b |
| `EVALUATE @pii_report WHEN STARTSWITH 'pii_found'` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Conditionally invokes redaction |
| `EVALUATE @output_check WHEN ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Gate 4 output dispatch: accept / redact / retry / fallback |
| `RETRY WITH temperature=0.1 LIMIT 3` | `RETRY WITH <param> LIMIT <n>` | Retry sub-loop on hallucination detection; bound at 3 attempts |
| `RETURN ... WITH status='blocked_*'` | `RETURN @<var> WITH <k>=<v>, ...` | Early exits carrying gate and keyword metadata |
| `RETURN @safe_response WITH status='complete'` | `RETURN @<var> WITH <k>=<v>, ...` | Terminal return with audit metadata |
| `EXCEPTION WHEN RefusalToAnswer THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named exception handler for model refusals |
| `EXCEPTION WHEN HallucinationDetected THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named exception handler for escaped hallucinations |
| `EXCEPTION WHEN BudgetExceeded THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named exception handler for token/cost limits |
| `@user_input`, `@clean_input`, `@safe_response` | Shared state `@<var>` | Pipeline state passed between CALLs and GENERATEs |

---

### 4. Logical Functions / Prompts

**`classify_input`**
- **Role:** Gate 1b — LLM-based content classification for inputs that pass keyword screening but may still be harmful, off-topic, or borderline.
- **Key conventions:** Accepts `@user_input` and `@test_context`. Expected to return a single categorical label: `'harmful'`, `'off_topic'`, or an acceptable label that falls through to the ELSE branch. No free-form text — the output must be a sentinel token for `EVALUATE` to pattern-match against.

**`safe_response`**
- **Role:** Gate 3 — the primary LLM generation step; produces a response to the sanitized user input using a safety-tuned system prompt.
- **Key conventions:** Accepts `@clean_input` (PII-redacted). Called a second time inside the `EVALUATE @output_check` branch when a hallucination is detected, with `RETRY` lowering temperature to `0.1` and limiting to 3 attempts. The prompt should encode content restrictions explicitly to minimize the chance of policy-violating output.

**`validate_output`**
- **Role:** Gate 4 — LLM-as-judge pass over `@raw_response` to detect PII leakage or hallucinated content before the response is committed.
- **Key conventions:** Accepts `@raw_response` and `@clean_input`. Must return one of four sentinel tokens: `'safe'`, `'contains_pii'`, `'hallucination'`, or a catch-all (matched by the ELSE branch). The ELSE branch substitutes a hard-coded safe fallback, so no label other than the four above should trigger acceptance.

---

### 5. Control Flow

1. **Load catalog entry** — `CALL load_test_input` resolves `@input_id`; if blank, `@user_input` is used as-is.
2. **Gate 1a — keyword pre-screen** — `CALL classify_input_keywords` runs a deterministic check. `EVALUATE @keyword_class`: if the result starts with `'harmful'` or `'off_topic'`, the workflow exits immediately via `RETURN` with a blocked status and gate metadata.
3. **Gate 1b — LLM classifier** — `GENERATE classify_input` handles nuanced cases. `EVALUATE @input_class`: same two exit conditions as Gate 1a, but gate metadata records `'llm_classifier'`.
4. **Gate 2 — PII gating** — `CALL detect_pii` scans `@user_input`. `EVALUATE @pii_report`: if PII is found, `CALL redact_pii` writes `@clean_input`; otherwise `@clean_input = @user_input`.
5. **Gate 3 — safe generation** — `GENERATE safe_response(@clean_input)` produces `@raw_response`.
6. **Gate 4 — output validation** — `GENERATE validate_output` judges `@raw_response`. `EVALUATE @output_check` dispatches:
   - `'safe'` → `@safe_response = @raw_response`
   - `'contains_pii'` → `CALL redact_pii(@raw_response)` writes `@safe_response`
   - `'hallucination'` → re-run `GENERATE safe_response` with `RETRY temperature=0.1 LIMIT 3`
   - ELSE → hard-coded fallback message assigned to `@safe_response`
7. **Terminal return** — `RETURN @safe_response WITH status='complete'`, `input_class`, `pii_detected`.
8. **Exception paths** — `RefusalToAnswer`, `HallucinationDetected`, and `BudgetExceeded` each return a status-tagged refusal message and terminate the workflow.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile guardrails_pipeline.spl --lang python/pocketflow
spl3 splc compile guardrails_pipeline.spl --lang python/langgraph
spl3 splc compile guardrails_pipeline.spl --lang go
```