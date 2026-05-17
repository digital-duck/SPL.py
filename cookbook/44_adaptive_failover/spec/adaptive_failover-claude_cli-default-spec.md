## Summary

This workflow implements an adaptive failover strategy for LLM-powered text generation: it first tries a fast, cheap primary model and only escalates to a higher-quality fallback model when a deterministic quality gate rejects the primary output. The pattern reduces cost and latency for the common case while guaranteeing a minimum response quality. DevOps teams, API platform engineers, and any team running production LLM pipelines will benefit from this resilience pattern.

---

## Detailed Specification

### 1. Purpose

Produce a technically accurate scientific summary for a given query by transparently switching from a fast primary model to a capable fallback model when the primary output fails a deterministic quality check.

---

### 2. High-level Description

The workflow is declared as `WORKFLOW adaptive_failover` and accepts four inputs: the user query, a primary model identifier, a fallback model identifier, and a log directory path. It uses a single `CREATE FUNCTION summarize` — a senior-scientist prompt template that requests a detailed, technically accurate summary covering core concepts, key mechanisms, and practical significance. Execution begins by logging progress and persisting the raw query to disk via a `CALL write_file` side-effect. The workflow then issues a `GENERATE summarize(@query) USING MODEL @primary_model` call to produce an initial response at minimal cost. Rather than using a second LLM call to judge quality, it invokes a deterministic `CALL check_quality` tool that returns a simple pass/fail status string. An `EVALUATE` branch inspects that status: when it `contains('pass')`, the primary output is promoted to `@final_response`; otherwise the workflow transparently retries by issuing a second `GENERATE summarize(@query) USING MODEL @fallback_model` and stores its result. The chosen response is then persisted via a final `CALL write_file` and returned with `status='complete'`, the quality verdict, and the primary model name as metadata. A top-level `EXCEPTION WHEN GenerationError` handler catches failures from either model and returns the original query with `status='error'` and `reason='both_models_failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| Python `AdaptiveFailoverFlow` class | `WORKFLOW adaptive_failover` | Top-level orchestration unit |
| `SummarizeNode` prompt class | `CREATE FUNCTION summarize(query TEXT)` | Single reusable prompt template; LLM-facing |
| `SummarizeNode.exec()` with primary model | `GENERATE summarize(@query) USING MODEL @primary_model INTO @primary_output` | First LLM call; cheap/fast path |
| `QualityGateNode.exec()` | `CALL check_quality(@primary_output) INTO @quality_status` | Deterministic tool; zero LLM cost |
| `if quality_status == 'pass'` branch | `EVALUATE @quality_status WHEN contains('pass') THEN … ELSE … END` | Single-branch gate; drives model selection |
| `SummarizeNode.exec()` with fallback model | `GENERATE summarize(@query) USING MODEL @fallback_model INTO @final_response` | Second LLM call; higher-quality fallback |
| `open(...).write(query)` / `open(...).write(response)` | `CALL write_file(path, content) INTO NONE` | Side-effect; no return value consumed |
| `flow.shared["final_response"]` etc. | `@query`, `@primary_output`, `@quality_status`, `@final_response` | SPL shared-state variables |
| `return {"status": "complete", …}` | `RETURN @final_response WITH status='complete', quality=@quality_status, model=@primary_model` | Non-trivial status token drives observability |
| `except Exception` on generation | `EXCEPTION WHEN GenerationError THEN RETURN @query WITH status='error', reason='both_models_failed'` | Catches failure of either model |

---

### 4. Logical Functions / Prompts

**`summarize`**

- **Role:** The sole LLM-facing prompt template; called up to twice per workflow run (once for the primary model, once for the fallback if needed).
- **Persona:** "You are a senior scientist" — establishes authoritative, technical register.
- **Key prompt conventions:**
  - Instructs the model to cover three dimensions: core concept, key mechanisms, and practical significance.
  - Single `{query}` slot; no few-shot examples or structured output format enforced — free-form prose is expected.
  - No sentinel tokens or scoring rubrics; quality judgement is fully offloaded to the deterministic `check_quality` tool rather than embedded in the prompt itself.

---

### 5. Control Flow

1. **Initialization** — log the attempt, write `query.md` to disk.
2. **Primary generation** — `GENERATE summarize(@query) USING MODEL @primary_model INTO @primary_output`.
3. **Quality gate** — `CALL check_quality(@primary_output) INTO @quality_status`; deterministic, no LLM cost.
4. **`EVALUATE` branch:**
   - `contains('pass')` → promote `@primary_output` to `@final_response`; log success.
   - `ELSE` → log failover warning; `GENERATE summarize(@query) USING MODEL @fallback_model INTO @final_response`; log completion.
5. **Persist result** — `CALL write_file` saves `response.md`.
6. **Termination** — `RETURN @final_response WITH status='complete', quality=@quality_status, model=@primary_model`.
7. **Error path** — `EXCEPTION WHEN GenerationError` short-circuits to `RETURN @query WITH status='error', reason='both_models_failed'`.

There is no `WHILE` loop; control flow is linear with a single conditional branch at the quality gate.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "Produce a technically accurate scientific summary for a given query by transparently switching from a fast primary model to a capable fallback model when the primary output fails a deterministic quality check." --mode workflow

# Step 2 — compile to any target
spl3 splc compile adaptive_failover.spl --lang python/pocketflow
spl3 splc compile adaptive_failover.spl --lang python/langgraph
spl3 splc compile adaptive_failover.spl --lang go
```