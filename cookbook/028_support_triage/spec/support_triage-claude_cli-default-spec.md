## Summary

This workflow automates first-line customer support triage for a SaaS product: it classifies an incoming support ticket, enriches it with real order data, scores urgency, and either escalates critical cases immediately or drafts a tone-appropriate response — revising it once if quality is insufficient. Support teams benefit by getting consistently structured, grounded responses without manual routing, while high-urgency tickets are surfaced to human agents before any draft is written.

---

## Detailed Specification

### 1. Purpose

Automatically classify, enrich, and respond to a customer support ticket — escalating critical cases or producing a quality-checked draft reply grounded in verified order data.

---

### 2. High-level Description

The `support_triage` WORKFLOW accepts a raw ticket, an optional product name, and a tone preference, then orchestrates eight steps across two deterministic tool calls and up to six LLM generations. Two upfront CALL operations extract any order number from the ticket text and fetch the corresponding order record from a data store, providing a factual grounding context with zero LLM cost. Three GENERATE steps then classify the ticket against a predefined category taxonomy (produced by the `support_categories` CREATE FUNCTION), extract structured ticket details, and score urgency on a 0–10 scale. An EVALUATE on the urgency score drives the first branch: tickets scoring above 8 bypass drafting entirely — a `escalation_alert` GENERATE produces an alert and the workflow RETURNs immediately with `status='escalated'`. For all other tickets, a `draft_response` GENERATE produces a reply incorporating classification, extracted details, order context, and the tone guide supplied by the `response_tone_guide` CREATE FUNCTION; a second EVALUATE on a quality score gates a one-shot revision via `improve_response`, returning `status='drafted_revised'` if a revision was needed or `status='drafted'` otherwise. A top-level EXCEPTION handler on `GenerationError` falls back to a minimal safe response, returning `status='fallback'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW support_triage` | `WORKFLOW <name>` | Declares the top-level named workflow with typed INPUT/OUTPUT |
| `CREATE FUNCTION support_categories()` | `CREATE FUNCTION <name>` | Pure text template; no parameters; returns the category routing table |
| `CREATE FUNCTION response_tone_guide(tone TEXT DEFAULT 'professional')` | `CREATE FUNCTION <name>` | Parameterised template with default; returns tone instruction string |
| `CREATE FUNCTION order_context_prompt(order_context TEXT)` | `CREATE FUNCTION <name>` | Parameterised template; conditionally formats order data as grounding text |
| `CALL extract_order_numbers(...) INTO @order_numbers` | `CALL <tool>(...) INTO @<var>` | Deterministic tool — regex/parse, no LLM |
| `CALL lookup_order(...) INTO @order_context` | `CALL <tool>(...) INTO @<var>` | Deterministic tool — JSON file lookup, no LLM |
| `GENERATE classify_ticket(...) INTO @classification_json` | `GENERATE <fn>(...) INTO @<var>` | LLM call; output is structured JSON |
| `GENERATE extract_ticket_details(...) INTO @details_json` | `GENERATE <fn>(...) INTO @<var>` | LLM call; extracts structured fields from ticket text |
| `GENERATE detect_urgency(...) INTO @urgency_score` | `GENERATE <fn>(...) INTO @<var>` | LLM call; produces numeric score 0–10 |
| `EVALUATE @urgency_score WHEN > 8 THEN ... ELSE ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | First branch gate — escalation vs. draft path |
| `GENERATE escalation_alert(...) INTO @alert` | `GENERATE <fn>(...) INTO @<var>` | LLM call on escalation branch only |
| `GENERATE draft_response(...) INTO @drafted_response` | `GENERATE <fn>(...) INTO @<var>` | LLM call; multi-param, grounded generation |
| `GENERATE check_response_quality(...) INTO @quality_score` | `GENERATE <fn>(...) INTO @<var>` | LLM call; returns numeric quality score 0–10 |
| `EVALUATE @quality_score WHEN < 6 THEN ...` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Second branch gate — revision trigger |
| `GENERATE improve_response(...) INTO @drafted_response` | `GENERATE <fn>(...) INTO @<var>` | LLM call; overwrites `@drafted_response` in place |
| `RETURN @alert WITH status='escalated'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial early exit; drives escalation path |
| `RETURN @drafted_response WITH status='drafted_revised'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial; signals a revision occurred |
| `RETURN @drafted_response WITH status='drafted'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial; carries quality score as metadata |
| `EXCEPTION WHEN GenerationError THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Top-level handler; catches any LLM generation failure |
| `@ticket`, `@order_context`, `@classification_json`, etc. | Shared state `@<var>` | Workflow-scoped variables passed between steps |
| `LOGGING ... LEVEL INFO/DEBUG/WARN` | `LOGGING` | Structured log emission at named severity levels |

---

### 4. Logical Functions / Prompts

**`support_categories()`**
- Role: provides the classification taxonomy; injected as context into `classify_ticket`
- Key conventions: enumerates seven categories with team owner, SLA target, priority level, and representative trigger phrases; no LLM call

**`response_tone_guide(tone TEXT DEFAULT 'professional')`**
- Role: supplies tone-specific writing instructions to `draft_response`
- Key conventions: SQL-style CASE expression; four variants (`empathetic`, `formal`, `friendly`, default professional); plain-English style rules including pronoun and naming conventions

**`order_context_prompt(order_context TEXT)`**
- Role: normalises the order lookup result into one of three prose framings for LLM consumption
- Key conventions: three cases — no order found, order number not in system, verified order data present; when data is present, prefixes the raw record with an explicit grounding instruction

**`classify_ticket(ticket, categories, order_context)`**
- Role: assigns the ticket to one category from the taxonomy; output is JSON carrying category, team, SLA, and priority
- Key conventions: structured JSON output; grounded with both the category table and real order data

**`extract_ticket_details(ticket, order_context)`**
- Role: pulls structured fields from the free-text ticket (customer name, order ID, issue summary, etc.)
- Key conventions: JSON output format; uses order context to validate or fill in referenced IDs

**`detect_urgency(ticket, classification_json)`**
- Role: produces a single integer score 0–10 representing ticket urgency
- Key conventions: numeric scalar output; informed by both ticket language and classification result; score > 8 is the escalation sentinel

**`escalation_alert(ticket, classification_json, order_context)`**
- Role: generates a brief internal alert message for the human escalation queue
- Key conventions: invoked only on urgency > 8; output is returned directly as the workflow response

**`draft_response(ticket, classification_json, details_json, order_context, product, tone_guide)`**
- Role: produces the customer-facing reply; the primary output of the non-escalation path
- Key conventions: richest parameter set in the workflow; grounded in order data; tone shaped by `response_tone_guide` output

**`check_response_quality(drafted_response, ticket, order_context)`**
- Role: self-evaluates the draft on a 0–10 scale
- Key conventions: numeric scalar output; score < 6 triggers a revision pass; score is carried as metadata in the RETURN

**`improve_response(drafted_response, ticket, order_context)`**
- Role: rewrites the draft to address quality shortfalls
- Key conventions: receives the failing draft as input; output overwrites `@drafted_response` in-place; executed at most once per ticket

**`fallback_response(ticket, product)`**
- Role: last-resort safe response when any generation step fails
- Key conventions: minimal parameters; invoked only inside the `GenerationError` exception handler

---

### 5. Control Flow

**Entry:** workflow receives `@ticket`, `@product`, `@tone`.

**Steps 1–2 (deterministic):** `extract_order_numbers` and `lookup_order` run as CALL tool operations, populating `@order_numbers` and `@order_context` without any LLM call.

**Steps 3–5 (enrichment):** three sequential GENERATE calls produce `@classification_json`, `@details_json`, and `@urgency_score`.

**First EVALUATE — urgency gate:**
- `@urgency_score > 8` → GENERATE `escalation_alert`, RETURN with `status='escalated'` and `priority='critical'` — workflow terminates here.
- Otherwise → continue to drafting.

**Steps 7–8 (drafting branch):**
- GENERATE `draft_response` → `@drafted_response`
- GENERATE `check_response_quality` → `@quality_score`

**Second EVALUATE — quality gate:**
- `@quality_score < 6` → GENERATE `improve_response`, overwrite `@drafted_response`, RETURN with `status='drafted_revised'`.
- Otherwise → RETURN with `status='drafted'` and `quality=@quality_score`.

**Exception path:** any `GenerationError` at any step jumps to the EXCEPTION handler, which runs `fallback_response` and RETURNs with `status='fallback'`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "<paste Section 2 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile support_triage.spl --lang python/pocketflow
spl3 splc compile support_triage.spl --lang python/langgraph
spl3 splc compile support_triage.spl --lang go
```