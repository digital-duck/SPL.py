## Summary

The Customer Support Triage workflow automates the full lifecycle of an inbound support ticket: it classifies the issue, looks up real order data, scores urgency, and either escalates immediately or drafts a tone-appropriate response — revising once if the draft quality is below threshold. Support teams and customer success operations benefit by eliminating manual triage, ensuring every ticket is grounded in verified order records, and routing high-urgency cases instantly without human judgment.

---

## Detailed Specification

### 1. Purpose

Automatically classify, triage, and draft a grounded support response for any inbound customer ticket, escalating critical cases immediately and performing a single quality-gate revision on borderline drafts.

---

### 2. High-level Description

The `support_triage` WORKFLOW accepts a raw ticket string, an optional product name, and an optional tone preference, then executes a deterministic extraction + LLM pipeline in six logical stages. Two non-LLM CALL steps first extract any order number from the ticket text and fetch the matching order record from a local data store, making all downstream LLM calls factually grounded. Three CREATE FUNCTION helpers — `support_categories`, `response_tone_guide`, and `order_context_prompt` — act as parameterized prompt templates injected inline into GENERATE calls, keeping prompt logic reusable and zero-cost. The workflow then uses GENERATE to classify the ticket against a category taxonomy, extract structured ticket details, and score urgency on a 0–10 scale. An EVALUATE on the urgency score branches the execution: if urgency exceeds 8, GENERATE produces an escalation alert and RETURN delivers it with `status = 'escalated'`; otherwise, GENERATE drafts a full customer response, a second GENERATE scores the draft quality, and a nested EVALUATE triggers a one-time GENERATE revision if the quality score falls below 6, returning `status = 'drafted_revised'` or `status = 'drafted'` accordingly. An EXCEPTION WHEN GenerationError handler catches any LLM failure and falls back to a safe generic response with `status = 'fallback'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW support_triage` | `WORKFLOW` | Named top-level workflow; INPUT declares `@ticket`, `@product`, `@tone`; OUTPUT declares `@drafted_response` |
| `CREATE FUNCTION support_categories()` | `CREATE FUNCTION` | Static prompt fragment listing category definitions; no LLM call, zero cost |
| `CREATE FUNCTION response_tone_guide(tone)` | `CREATE FUNCTION` | Parameterized CASE-based prompt returning tone instructions; injected into draft GENERATE |
| `CREATE FUNCTION order_context_prompt(order_context)` | `CREATE FUNCTION` | Conditional prompt fragment; normalizes absent/invalid/valid order context into consistent LLM instruction |
| `CALL extract_order_numbers(@ticket) INTO @order_numbers` | `CALL` | Deterministic tool; parses ticket text for order IDs — no LLM |
| `CALL lookup_order(@order_numbers) INTO @order_context` | `CALL` | Deterministic tool; fetches order record from `orders.json` — no LLM |
| `GENERATE classify_ticket(...) INTO @classification_json` | `GENERATE` | LLM classifies ticket into category taxonomy; outputs JSON |
| `GENERATE extract_ticket_details(...) INTO @details_json` | `GENERATE` | LLM extracts structured fields from ticket + order context |
| `GENERATE detect_urgency(...) INTO @urgency_score` | `GENERATE` | LLM scores urgency 0–10; output used in EVALUATE branch |
| `EVALUATE @urgency_score WHEN > 8` | `EVALUATE` | Numeric branch: critical path → escalation; else → draft path |
| `GENERATE escalation_alert(...) INTO @alert` | `GENERATE` | LLM composes escalation notification; returned immediately |
| `GENERATE draft_response(...) INTO @drafted_response` | `GENERATE` | LLM drafts full customer-facing response using all context + tone guide |
| `GENERATE check_response_quality(...) INTO @quality_score` | `GENERATE` | LLM scores draft quality 0–10 against ticket and order context |
| `EVALUATE @quality_score WHEN < 6` | `EVALUATE` | Quality gate: below threshold triggers one-time revision GENERATE |
| `GENERATE improve_response(...) INTO @drafted_response` | `GENERATE` | LLM revises the draft; overwrites `@drafted_response` in place |
| `RETURN @drafted_response WITH status = 'drafted_revised'` | `RETURN WITH status=` | Non-trivial token; signals a revision was performed |
| `RETURN @drafted_response WITH status = 'drafted'` | `RETURN WITH status=` | Non-trivial token; signals first-pass draft passed quality gate |
| `RETURN @alert WITH status = 'escalated'` | `RETURN WITH status=` | Non-trivial token; signals critical escalation path was taken |
| `EXCEPTION WHEN GenerationError` | `EXCEPTION WHEN` | Catches any LLM generation failure; falls back to generic response |
| `@ticket`, `@order_context`, `@classification_json`, etc. | SPL `@vars` | Shared mutable state passed across steps within the workflow frame |

---

### 4. Logical Functions / Prompts

**`support_categories()`**
- Role: static taxonomy injected into `classify_ticket` to constrain LLM output to known categories
- Key conventions: maps 7 categories (billing, account, shipping, technical, product, complaint, general) to routing team, SLA, and priority; no LLM invocation

**`response_tone_guide(tone)`**
- Role: parameterized tone instruction injected into `draft_response`
- Key conventions: CASE expression over `empathetic | formal | friendly | (default)`; each arm provides voice and phrasing directives; default is "professional but approachable"

**`order_context_prompt(order_context)`**
- Role: normalizes the raw order lookup result into a consistent LLM instruction
- Key conventions: three cases — no order number found, order not in system (prompt LLM to ask customer to confirm ID), valid order (instruct LLM to ground response in real data)

**`classify_ticket`**
- Role: assigns the ticket to one of the 7 support categories with routing metadata
- Key conventions: receives ticket text + category definitions + normalized order context; expected output format is JSON

**`extract_ticket_details`**
- Role: pulls structured fields (customer name, product, issue type, affected IDs) from the ticket
- Key conventions: uses both raw ticket and verified order context; output JSON feeds downstream drafting

**`detect_urgency`**
- Role: scores ticket urgency 0–10 to drive the escalation branch
- Key conventions: uses ticket text and classification JSON; numeric score output is consumed directly by EVALUATE; higher scores reflect anger signals, SLA breach risk, or repeated escalation

**`escalation_alert`**
- Role: composes an internal alert notification for the critical-path branch
- Key conventions: includes ticket text, classification, and order context; intended for internal team, not the end customer

**`draft_response`**
- Role: produces the customer-facing reply grounded in all available context
- Key conventions: receives ticket, classification JSON, details JSON, order context, product name, and full tone guide; most context-rich GENERATE in the workflow

**`check_response_quality`**
- Role: evaluates the draft against the original ticket and order context
- Key conventions: 0–10 numeric score; threshold is 6; output consumed directly by the quality-gate EVALUATE

**`improve_response`**
- Role: revises a below-threshold draft
- Key conventions: receives the original draft alongside ticket and order context; overwrites `@drafted_response` in the same variable slot; executed at most once (no WHILE loop)

**`fallback_response`**
- Role: safe generic response when any LLM call fails
- Key conventions: uses only `@ticket` and `@product`; minimal context to maximize reliability under error conditions

---

### 5. Control Flow

The workflow begins with two sequential deterministic CALL steps (order number extraction → order record lookup), then fans out into three sequential GENERATE steps (classify → extract details → score urgency). An EVALUATE on `@urgency_score` creates the primary branch: if the score exceeds 8, the workflow immediately GENERATEs an escalation alert and RETURNs with `status = 'escalated'`, terminating without a customer draft. On the non-escalated path, `draft_response` is generated, then `check_response_quality` scores the draft. A nested EVALUATE on `@quality_score` performs a single conditional revision: below 6 triggers `improve_response` and RETURN with `status = 'drafted_revised'`; 6 or above exits immediately with `status = 'drafted'` and the raw quality score attached. An EXCEPTION WHEN GenerationError wraps the entire workflow body; any LLM failure diverts to `fallback_response` and RETURN with `status = 'fallback'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 1 as the text2spl input)
spl3 text2spl --description "Automatically classify, triage, and draft a grounded \
support response for any inbound customer ticket, escalating critical cases \
immediately and performing a single quality-gate revision on borderline drafts." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile support_triage.spl --lang python/pocketflow
spl3 splc compile support_triage.spl --lang python/langgraph
spl3 splc compile support_triage.spl --lang go
```