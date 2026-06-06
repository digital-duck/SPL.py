## Summary

This workflow implements an adaptive failover strategy for LLM-generated content, transparently switching from a cheap, fast primary model to a higher-quality fallback model when the primary output fails a deterministic quality gate. It exists to balance cost and latency against output quality without requiring the caller to know which model was ultimately used. Platform operators, API cost-conscious teams, and any pipeline where response quality must be guaranteed will benefit.

---

## Detailed Specification

### 1. Purpose

Generate a technically accurate summary of a user query using the cheapest available model, automatically escalating to a higher-capability fallback model only when the primary output fails a deterministic quality check.

---

### 2. High-level Description

The workflow is built around a single CREATE FUNCTION (`summarize`) that roles a senior-scientist persona to produce detailed, mechanistically rich technical summaries from a free-text query. On entry, the workflow logs its intent and writes the raw query to disk via a CALL side-effect. It then issues a GENERATE call against the primary (cheap/fast) model and immediately submits the output to a deterministic CALL (`check_quality`) that returns a pass/fail token — incurring zero LLM cost for the gate itself. An EVALUATE block branches on that token: when the primary output passes, it is accepted as the final response; otherwise the workflow transparently re-issues the same GENERATE call against the fallback model, absorbing the extra cost only when necessary. The accepted response is then written to disk and the workflow exits via RETURN with a `status='complete'` metadata tag carrying the quality token and the primary model name for audit purposes. A top-level EXCEPTION handler catches any GenerationError (e.g., both models unreachable) and returns `status='error'` with `reason='both_models_failed'` so callers can respond gracefully.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION summarize` | `CREATE FUNCTION` | Single reusable prompt template; senior-scientist persona; `{query}` slot |
| `WORKFLOW adaptive_failover` | `WORKFLOW` | Parameterized entry point; four INPUTs, one OUTPUT |
| `GENERATE summarize(@query) USING MODEL @primary_model INTO @primary_output` | `GENERATE ... INTO @var` | First LLM call; model resolved at runtime from INPUT variable |
| `CALL check_quality(@primary_output) INTO @quality_status` | `CALL` | Deterministic Python tool; no LLM cost; returns pass/fail token |
| `CALL write_file(...) INTO NONE` | `CALL` | Side-effect file write; result discarded |
| `EVALUATE @quality_status WHEN contains('pass') THEN ... ELSE ... END` | `EVALUATE` | Single-level branch; drives model escalation decision |
| `GENERATE summarize(@query) USING MODEL @fallback_model INTO @final_response` | `GENERATE ... INTO @var` | Second LLM call; only executed on EVALUATE else-branch |
| `RETURN @final_response WITH status='complete', quality=..., model=...` | `RETURN ... WITH` | Non-default terminal status; carries audit metadata |
| `EXCEPTION WHEN GenerationError THEN RETURN ... WITH status='error'` | `EXCEPTION WHEN` | Typed handler; non-default error status signals both-model failure to caller |
| `@primary_output`, `@quality_status`, `@final_response` | `@var` shared state | Workflow-scoped variables threading data between GENERATE, CALL, and EVALUATE |

---

### 4. Logical Functions / Prompts

#### `summarize`
- **Role:** The sole prompt template; invoked once or twice depending on the quality gate outcome.
- **Persona:** Senior scientist — establishes authoritative, technically dense framing.
- **Output conventions:** Prose; expected to cover core concept, key mechanisms, and practical significance. No sentinel tokens or scoring rubric — quality evaluation is fully delegated to the external `check_quality` tool rather than self-reported by the LLM.

---

### 5. Control Flow

```
START
  → LOG intent + CALL write_file(query)
  → GENERATE summarize(@query) [primary model] INTO @primary_output
  → CALL check_quality(@primary_output) INTO @quality_status   ← deterministic, no LLM
  → EVALUATE @quality_status
        WHEN contains('pass'):  @final_response := @primary_output        ← cheap path
        ELSE:                   GENERATE summarize(@query) [fallback model] INTO @final_response  ← escalation
  → CALL write_file(response)
  → RETURN WITH status='complete', quality=@quality_status, model=@primary_model

EXCEPTION GenerationError
  → RETURN WITH status='error', reason='both_models_failed'
```

There is no WHILE loop. The failover is a single-shot escalation: the fallback model is tried exactly once; if generation itself fails at any point, the EXCEPTION handler terminates the workflow with a structured error rather than retrying.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as the text2spl input)
spl3 text2spl \
  --description "Generate a technically accurate summary of a user query using the cheapest available model, automatically escalating to a higher-capability fallback model only when the primary output fails a deterministic quality check. Use a single CREATE FUNCTION with a senior-scientist persona and a {query} slot. Issue a GENERATE call against a runtime-specified primary model, then pass the output to a deterministic CALL check_quality tool that returns a pass/fail token at zero LLM cost. Use an EVALUATE block to branch: on pass, accept the primary output; on fail, re-issue GENERATE against a fallback model. Write the query and final response to disk via CALL write_file side-effects. Exit with RETURN WITH status='complete' carrying quality and model metadata. Handle GenerationError via an EXCEPTION block that returns status='error' with reason='both_models_failed'." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile adaptive_failover.spl --lang python/langgraph
spl3 splc compile adaptive_failover.spl --lang python/pocketflow
spl3 splc compile adaptive_failover.spl --lang go
```