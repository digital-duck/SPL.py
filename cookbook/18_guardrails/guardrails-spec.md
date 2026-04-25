## 0. High-level Description

This workflow implements a **safety-first guardrails pipeline** that subjects every user request to four sequential gates before committing a response. The pattern combines deterministic pre-screening (keyword matching and PII detection via CALL side-effects) with LLM-based nuanced classification and response generation, ensuring that cheap, fast checks run before any tokens are spent on inference. Two CREATE FUNCTIONs drive the LLM gates: `classify_input`, which labels the cleaned input as `harmful`, `off_topic`, or acceptable, and `safe_response`, which generates the actual reply under a safety-tuned prompt; a third GENERATE call to `validate_output` acts as a post-generation auditor checking for PII leakage, hallucination, or harmful content in the output. Control flow is expressed entirely through EVALUATE branches on the string values returned by each gate: a `STARTSWITH 'harmful'` or `STARTSWITH 'off_topic'` match on the keyword pre-screen (@keyword_class) short-circuits execution immediately via RETURN with a `gate = 'keyword_prescreen'` metadata tag, while the LLM classifier gate and output validation gate each carry their own `gate` or status metadata through their own EVALUATE blocks. PII management is handled by two CALL tools — `detect_pii` and `redact_pii` — applied symmetrically to both input and output, and a `hallucination` branch in the output gate triggers a retry GENERATE with `temperature = 0.1` capped at three attempts. The workflow handles three EXCEPTION types: `RefusalToAnswer`, `HallucinationDetected` (global fallback beyond the inline retry), and `BudgetExceeded` (returns whatever partial response exists).

---

## 1. Purpose

Safely process a user text request through four sequential content-safety gates — keyword pre-screening, LLM classification, PII redaction, and output validation — returning either a sanitized response or an explanatory refusal, with full status metadata at each decision point.

---

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `@input_id` | `''` (empty string) | Key into a test-input catalog; when non-empty, `load_test_input` resolves it to a predefined request and context. Pass `list` to discover available entries. |
| `@user_input` | `''` (empty string) | Raw user text to process. Used directly when `@input_id` is blank; also used for all gate checks regardless of catalog lookup. |

---

## 3. Process

1. **Catalog lookup (deterministic).** CALL `load_test_input(@input_id)` → `@test_context`. If `@input_id` is blank, `@test_context` is empty and `@user_input` flows through unchanged.

2. **Gate 1a — Keyword pre-screen (deterministic).** CALL `classify_input_keywords(@user_input)` → `@keyword_class`. No LLM tokens are spent.
   - EVALUATE `@keyword_class`:
     - STARTSWITH `'harmful'` → RETURN immediate refusal with `status = 'blocked_harmful'`, `gate = 'keyword_prescreen'`. Pipeline ends.
     - STARTSWITH `'off_topic'` → RETURN scope refusal with `status = 'blocked_off_topic'`, `gate = 'keyword_prescreen'`. Pipeline ends.
     - ELSE → continue.

3. **Gate 1b — LLM input classification.** GENERATE `classify_input(@user_input, @test_context)` → `@input_class`. Handles nuanced cases the keyword screen cannot catch.
   - EVALUATE `@input_class`:
     - `'harmful'` → RETURN refusal, `status = 'blocked_harmful'`, `gate = 'llm_classifier'`. Pipeline ends.
     - `'off_topic'` → RETURN scope refusal, `status = 'blocked_off_topic'`, `gate = 'llm_classifier'`. Pipeline ends.
     - ELSE → input is acceptable, continue.

4. **Gate 2 — PII detection (deterministic).** CALL `detect_pii(@user_input)` → `@pii_report`.
   - EVALUATE `@pii_report`:
     - STARTSWITH `'pii_found'` → CALL `redact_pii(@user_input)` → `@clean_input`. PII is stripped before generation.
     - ELSE → SET `@clean_input = @user_input`.

5. **Gate 3 — Safe response generation.** GENERATE `safe_response(@clean_input)` → `@raw_response` using a safety-tuned prompt against the redacted input.

6. **Gate 4 — Output validation.** GENERATE `validate_output(@raw_response, @clean_input)` → `@output_check`. Audits the generated text for PII leakage, hallucination, or harmful content.
   - EVALUATE `@output_check`:
     - `'safe'` → SET `@safe_response = @raw_response`.
     - `'contains_pii'` → CALL `redact_pii(@raw_response)` → `@safe_response` (deterministic PII scrub on output).
     - `'hallucination'` → GENERATE `safe_response(@clean_input)` → `@safe_response` with RETRY at `temperature = 0.1`, up to 3 attempts.
     - ELSE → SET `@safe_response` to a static fallback message.

7. **Return.** RETURN `@safe_response` WITH `status = 'complete'`, `input_class = @input_class`, `pii_detected = @pii_report`.

---

## 4. Error Handling

- **`RefusalToAnswer`** — the model declines to answer; returns the static message `'This request cannot be processed.'` with `status = 'refused'`.
- **`HallucinationDetected`** — a hallucination is signalled at the global exception level (beyond the inline Gate 4 retry budget); returns `'Unable to provide a verified response.'` with `status = 'hallucination_blocked'`.
- **`BudgetExceeded`** — token or cost budget is exhausted mid-pipeline; returns whatever is currently in `@safe_response` (possibly empty) with `status = 'budget_limit'`, allowing partial results to surface rather than losing them.

---

## 5. Output

**Variable returned:** `@safe_response TEXT`

On the happy path the RETURN carries:

| Field | Value | Notes |
|-------|-------|-------|
| `status` | `'complete'` | Indicates all four gates passed |
| `input_class` | value of `@input_class` | LLM classifier label (e.g. `'safe'`) |
| `pii_detected` | value of `@pii_report` | Raw PII detection report from Gate 2 |

On early-exit (blocked) paths, the RETURN replaces `@safe_response` with a canned refusal string and carries:

| Field | Values | Notes |
|-------|--------|-------|
| `status` | `'blocked_harmful'` \| `'blocked_off_topic'` | Which policy triggered |
| `gate` | `'keyword_prescreen'` \| `'llm_classifier'` | Which gate blocked the request |
| `keyword_match` | value of `@keyword_class` | Present only on keyword pre-screen exits |

Exception paths return a static string with `status` set to `'refused'`, `'hallucination_blocked'`, or `'budget_limit'`.