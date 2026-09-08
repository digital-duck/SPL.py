## Summary

The Guardrails Pipeline is a safety-first LLM orchestration workflow that applies four sequential gates before delivering any response to the user. It combines fast deterministic checks (keyword matching, PII detection) with LLM-based semantic judgments (content classification, output validation) to ensure harmful, off-topic, and privacy-violating content is blocked or sanitized before the response is committed. This workflow benefits any product team that needs to deploy a consumer-facing LLM feature with compliance, trust, and safety guarantees.

---

## Detailed Specification

### 1. Purpose

Execute a multi-gate content safety pipeline that validates user input, generates a safety-tuned response, and validates the output — blocking or sanitizing at every stage before returning a verified safe response.

---

### 2. High-level Description

The `guardrails_pipeline` WORKFLOW accepts a raw user input (or a named test case from a catalog) and routes it through four sequential safety gates before committing any response. The first gate is a two-stage input classification: a deterministic keyword pre-screen (`classify_input_keywords` tool call) that immediately blocks obvious harmful or off-topic content via EVALUATE and RETURN, followed by a GENERATE call to `classify_input` that uses an LLM to catch nuanced violations the keyword filter misses — again terminating early via EVALUATE and RETURN if the input is rejected. The second gate is a deterministic PII detection tool call (`detect_pii`); if PII is found, a second tool call (`redact_pii`) sanitizes the input before it is passed forward, otherwise the original input proceeds as `@clean_input`. The third gate is the core GENERATE call to `safe_response`, which produces a draft answer using a safety-tuned prompt. The fourth gate is a GENERATE call to `validate_output`, which inspects the draft for PII leakage or hallucination; safe output is committed directly, PII-containing output is redacted via tool call, and hallucinated output triggers an inline RETRY of `safe_response` with `temperature=0.1` up to three times before falling back to a refusal message. Three named EXCEPTION handlers — `RefusalToAnswer`, `HallucinationDetected`, and `BudgetExceeded` — catch system-level failures and return structured status tokens so callers can route accordingly.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW guardrails_pipeline` | `WORKFLOW` | Single workflow, no sub-workflow CALL composition |
| `CALL load_test_input(...)` | `CALL <tool>` | Deterministic catalog lookup; no LLM token spend |
| `CALL classify_input_keywords(...)` | `CALL <tool>` | Deterministic keyword pre-screen; fast path before LLM |
| `CALL detect_pii(...)` | `CALL <tool>` | Deterministic PII detector (regex / rule-based) |
| `CALL redact_pii(...)` | `CALL <tool>` | Deterministic redaction applied to input and/or output |
| `GENERATE classify_input(...)` | `GENERATE <fn>(...) INTO @var` | LLM-based semantic content classifier |
| `GENERATE safe_response(...)` | `GENERATE <fn>(...) INTO @var` | Safety-tuned response generator; may be retried |
| `GENERATE validate_output(...)` | `GENERATE <fn>(...) INTO @var` | LLM output inspector for PII leakage and hallucination |
| `EVALUATE @keyword_class WHEN STARTSWITH 'harmful'` | `EVALUATE` | Early-exit branch on deterministic classifier result |
| `EVALUATE @input_class WHEN 'harmful'` | `EVALUATE` | Early-exit branch on LLM classifier result |
| `EVALUATE @pii_report WHEN STARTSWITH 'pii_found'` | `EVALUATE` | Branch to redaction vs. pass-through |
| `EVALUATE @output_check WHEN 'hallucination'` | `EVALUATE` | Drives RETRY of response generation |
| `RETURN ... WITH status='blocked_harmful'` | `RETURN @var WITH status=` | Non-trivial early exit; drives caller branch logic |
| `RETURN ... WITH status='blocked_off_topic'` | `RETURN @var WITH status=` | Non-trivial early exit; drives caller branch logic |
| `RETURN @safe_response WITH status='complete'` | `RETURN @var WITH status=` | Terminal commit with metadata |
| `RETRY WITH temperature=0.1 LIMIT 3` | Inline RETRY | Hallucination recovery; bounded re-generation |
| `@test_context`, `@keyword_class`, `@pii_report`, `@clean_input`, `@raw_response`, `@output_check`, `@safe_response` | SPL `@vars` | Shared mutable state threaded through all gates |
| `EXCEPTION WHEN RefusalToAnswer` | `EXCEPTION WHEN <Type>` | System-level refusal catch |
| `EXCEPTION WHEN HallucinationDetected` | `EXCEPTION WHEN <Type>` | Unrecoverable hallucination catch |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type>` | Token/cost budget overrun catch |

---

### 4. Logical Functions / Prompts

**`classify_input`**
- **Role**: LLM-based semantic input classifier; catches harmful or off-topic intent that keyword matching cannot detect.
- **Key conventions**: Output must be a single classification token — `harmful`, `off_topic`, or a safe class — so the downstream EVALUATE can branch without further parsing. Prompt should instruct the model to err on the side of caution and never explain or engage with the content being classified.

**`safe_response`**
- **Role**: Core response generator; takes the sanitized `@clean_input` and produces a helpful, factual, policy-compliant answer.
- **Key conventions**: Prompt is safety-tuned — includes explicit instructions to avoid speculation, refuse harmful sub-tasks, and never reproduce PII. May be called twice if Gate 4 detects hallucination (RETRY with lowered temperature).

**`validate_output`**
- **Role**: Output auditor; inspects `@raw_response` against `@clean_input` for PII leakage, hallucinated facts, or residual harmful content.
- **Key conventions**: Output must resolve to one of four sentinel tokens: `safe`, `contains_pii`, `hallucination`, or a fallback class. The EVALUATE downstream branches strictly on these tokens, so prompt must constrain the model to produce exactly one token or short label — no prose.

---

### 5. Control Flow

```
load_test_input(@input_id)
    → classify_input_keywords(@user_input)           [deterministic]
        EVALUATE @keyword_class
            harmful    → RETURN status='blocked_harmful'    [early exit]
            off_topic  → RETURN status='blocked_off_topic'  [early exit]
            else       → continue
    → classify_input(@user_input, @test_context)     [LLM Gate 1b]
        EVALUATE @input_class
            harmful    → RETURN status='blocked_harmful'    [early exit]
            off_topic  → RETURN status='blocked_off_topic'  [early exit]
            else       → continue
    → detect_pii(@user_input)                        [deterministic]
        EVALUATE @pii_report
            pii_found  → redact_pii(@user_input) → @clean_input
            else       → @clean_input = @user_input
    → safe_response(@clean_input)                    [LLM Gate 3]
        → @raw_response
    → validate_output(@raw_response, @clean_input)   [LLM Gate 4]
        EVALUATE @output_check
            safe          → @safe_response = @raw_response
            contains_pii  → redact_pii(@raw_response) → @safe_response
            hallucination → RETRY safe_response(temp=0.1, limit=3) → @safe_response
            else          → @safe_response = refusal message
    → RETURN @safe_response WITH status='complete'

EXCEPTION handlers (any gate):
    RefusalToAnswer      → RETURN status='refused'
    HallucinationDetected → RETURN status='hallucination_blocked'
    BudgetExceeded       → RETURN status='budget_limit'
```

The flow is linear with multiple early-exit points driven by EVALUATE and RETURN. There is no top-level WHILE loop; the only bounded iteration is the inline RETRY on the hallucination branch of Gate 4.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (use Section 1 above as text2spl input)
spl3 text2spl --description "Execute a multi-gate content safety pipeline that validates \
user input, generates a safety-tuned response, and validates the output — blocking or \
sanitizing at every stage before returning a verified safe response." --mode workflow

# Step 2 — compile to any target
spl3 splc compile guardrails_pipeline.spl --lang python/pocketflow
spl3 splc compile guardrails_pipeline.spl --lang python/langgraph
spl3 splc compile guardrails_pipeline.spl --lang go
```