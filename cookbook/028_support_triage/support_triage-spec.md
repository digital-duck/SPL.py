## 0. High-level Description

This workflow implements a **classify → route → draft** customer support triage pipeline using a multi-step SPL WORKFLOW named `support_triage`. The pipeline begins with two deterministic CALL side-effects — `extract_order_numbers` and `lookup_order` — that ground all subsequent LLM work in verified order data at zero LLM cost before any GENERATE step runs. Three helper CREATE FUNCTIONs serve as prompt-construction utilities evaluated locally: `support_categories` encodes a routing table mapping seven ticket categories to teams, SLA windows, and priorities; `response_tone_guide` is a SQL-style CASE expression selecting one of four tone personas driven by the `@tone` INPUT parameter; and `order_context_prompt` applies a three-branch CASE to produce a grounding preamble that gracefully handles missing or unrecognised order numbers. The control flow uses two nested EVALUATE branches: the outer branch checks whether `@urgency_score` exceeds 8 and short-circuits to an escalation alert with `status = 'escalated'`; the inner branch checks `@quality_score` against a threshold of 6 and triggers a single revision pass (`improve_response`) if the draft falls short, implementing a lightweight self-refine pattern capped at one iteration. LOGGING statements are emitted at INFO for pipeline entry and urgency, at DEBUG for order context, classification, and quality scores, and at WARN on both escalation and quality-below-threshold events. A top-level `EXCEPTION WHEN GenerationError` handler ensures any LLM failure degrades gracefully by invoking a `fallback_response` function and returning `status = 'fallback'`.

## 1. Purpose

Given a raw customer support ticket, the workflow classifies it, looks up any referenced order data, scores urgency, and either escalates critical issues immediately or drafts (and optionally revises) a tone-appropriate, order-grounded reply — returning the response with a structured status label for downstream routing.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@ticket` | *(required)* | Raw customer support ticket text to be triaged |
| `@product` | `'CloudDash'` | Product name used for contextualising the drafted response and fallback |
| `@tone` | `'professional'` | Tone persona for the response; accepts `professional`, `empathetic`, `formal`, or `friendly` |

## 3. Process

1. **Log entry point** — emit an INFO log recording `@product` and `@tone` to mark the start of the triage run.
2. **Extract order numbers** — CALL `extract_order_numbers(@ticket)` deterministically (no LLM) to parse any order IDs mentioned in the ticket text; store result in `@order_numbers`.
3. **Lookup order record** — CALL `lookup_order(@order_numbers)` deterministically to fetch matching records from the order store; store the result string in `@order_context`. Emit a DEBUG log with the extracted numbers.
4. **Classify ticket** — GENERATE `classify_ticket` using the ticket text, the `support_categories()` routing table, and the `order_context_prompt(@order_context)` grounding preamble. Store the structured result in `@classification_json`. Emit a DEBUG log of the classification.
5. **Extract ticket details** — GENERATE `extract_ticket_details` using the ticket and order context to produce structured key details in `@details_json`.
6. **Score urgency** — GENERATE `detect_urgency` using the ticket and classification to produce a numeric score (0–10) in `@urgency_score`. Emit an INFO log of the score.
7. **Route on urgency** — EVALUATE `@urgency_score`:
   - **If > 8 (critical path):** emit a WARN log, GENERATE `escalation_alert` using the ticket, classification, and order context into `@alert`, then RETURN immediately with `status = 'escalated'`, `priority = 'critical'`.
   - **Otherwise (standard path):** proceed to step 8.
8. **Draft response** — GENERATE `draft_response` using the ticket, classification, details, order context, product name, and the `response_tone_guide(@tone)` persona string; store in `@drafted_response`.
9. **Quality check** — GENERATE `check_response_quality` scoring the draft against the original ticket and order context (0–10) into `@quality_score`. Emit a DEBUG log of the score.
10. **Route on quality** — EVALUATE `@quality_score`:
    - **If < 6:** emit a WARN log, GENERATE `improve_response` to revise the draft in-place into `@drafted_response`, RETURN with `status = 'drafted_revised'`.
    - **If ≥ 6:** RETURN `@drafted_response` with `status = 'drafted'` and `quality = @quality_score`.

## 4. Error Handling

- **`GenerationError`** — any LLM GENERATE call that fails triggers this handler; the workflow calls `fallback_response(@ticket, @product)` to produce a safe, minimal reply and returns it with `status = 'fallback'`. This ensures the pipeline never surfaces a raw error to the caller.

*(No other EXCEPTION types are declared; the single handler covers all generation failures uniformly.)*

## 5. Output

The workflow returns `@drafted_response` (type `TEXT`) via one of four exit paths:

| `status` | Condition | Additional metadata |
|---|---|---|
| `escalated` | `@urgency_score > 8` | `priority = 'critical'` |
| `drafted` | Quality check passed (score ≥ 6) | `quality = @quality_score` |
| `drafted_revised` | Quality check failed (score < 6); one revision applied | *(none)* |
| `fallback` | A `GenerationError` was caught at any step | *(none)* |