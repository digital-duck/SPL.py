## Summary

This workflow fetches concise summaries of three independent news topics — technology, science, and business — in parallel, then synthesises them into a single, polished morning briefing. It exists to save a busy professional the time of reading across multiple sources by delivering one coherent, editor-quality digest on demand. Anyone who needs a quick situational overview each morning benefits directly from the output.

---

## Detailed Specification

### 1. Purpose

Generate a consolidated, 200-word morning news digest by summarising three independent topic areas concurrently and merging the results into a single executive-ready briefing.

### 2. High-level Description

The implementation declares two top-level WORKFLOW blocks and two CREATE FUNCTION prompt templates. The sub-workflow `summarise_single` accepts a single topic string and calls GENERATE with the `summarise_topic` function, capping the model output at 256 tokens via an OUTPUT BUDGET clause; it is designed to be dispatched as a self-contained unit. The main orchestrator `parallel_news_digest` invokes `summarise_single` three times simultaneously using CALL PARALLEL, each branch receiving its own snapshot of the parent scope (technology, science, and business topics) and writing its result into a dedicated SPL variable (@tech\_summary, @sci\_summary, @biz\_summary) with no shared mutable state between branches. Once all three branches complete, a single GENERATE call applies the `morning_briefing` function to merge the three summaries into one coherent digest bounded by a configurable OUTPUT BUDGET. The workflow uses LOGGING statements at DEBUG and INFO levels throughout to trace execution. Two EXCEPTION handlers guard the outer workflow: WHEN ModelUnavailable triggers a RETURN WITH status='failed', and WHEN BudgetExceeded allows a graceful RETURN WITH status='truncated' so callers can detect partial output rather than a hard error.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW parallel_news_digest` | `WORKFLOW <name>` | Main orchestrator; declares INPUT/OUTPUT and exception scope |
| `WORKFLOW summarise_single` | `WORKFLOW <name>` | Reusable sub-workflow dispatched by the orchestrator via CALL PARALLEL |
| `CREATE FUNCTION summarise_topic` | `CREATE FUNCTION <name>` | Prompt template with `{topic}` and `{context}` slots |
| `CREATE FUNCTION morning_briefing` | `CREATE FUNCTION <name>` | Prompt template with `{tech}`, `{science}`, `{business}` slots |
| `GENERATE summarise_topic(...) INTO @summary` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call inside sub-workflow; bounded by OUTPUT BUDGET 256 |
| `GENERATE morning_briefing(...) INTO @digest` | `GENERATE <fn>(...) INTO @<var>` | Merge LLM call in orchestrator; bounded by configurable OUTPUT BUDGET |
| `CALL PARALLEL ... END` | `CALL PARALLEL` | Fan-out: three concurrent sub-workflow invocations, each result captured in its own `INTO @<var>` |
| `USING MODEL @digest_model` | model parameter on GENERATE | Single model string threaded through all levels via a shared input parameter |
| `@tech_summary`, `@sci_summary`, `@biz_summary`, `@digest` | `@<var>` (shared state) | SPL variables carrying intermediate and final outputs |
| `RETURN @digest WITH status='failed'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial return; signals hard failure to caller |
| `RETURN @digest WITH status='truncated'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial return; signals partial output to caller |
| `EXCEPTION WHEN ModelUnavailable` | `EXCEPTION WHEN <Type> THEN` | Catches model unavailability at the orchestrator boundary |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN <Type> THEN` | Catches token-budget overflow; returns best-effort output |

### 4. Logical Functions / Prompts

**`summarise_topic(topic, context)`**
- **Role:** Generates a standalone 3-sentence factual summary for a single news topic.
- **Key conventions:** Instructs the model to be neutral and factual; requires the final sentence to be a near-term outlook statement; accepts an optional `context` slot for additional constraints or filtering instructions. Output is capped at 256 tokens via the calling GENERATE's OUTPUT BUDGET.

**`morning_briefing(tech, science, business)`**
- **Role:** Merges the three independently produced summaries into a unified, executive-quality digest.
- **Key conventions:** Prescribes a strict document structure — one orienting sentence, then each topic under a **bold header**, closing with a "watch today" callout for the most time-sensitive item. Target length is approximately 200 words. Output budget is caller-configurable (default 512 tokens).

### 5. Control Flow

1. **Initialisation:** `parallel_news_digest` logs its model and topic parameters, then immediately issues a CALL PARALLEL block.
2. **Fan-out (concurrent):** Three invocations of `summarise_single` execute concurrently. Each receives its topic string and the shared `@digest_model`; each writes its result into a distinct variable (@tech\_summary, @sci\_summary, @biz\_summary). No ordering between branches is implied or required.
3. **Fan-in (merge):** After CALL PARALLEL completes, a single GENERATE call applies `morning_briefing` to the three summary variables, producing @digest.
4. **Termination:** The workflow returns @digest. If a ModelUnavailable exception is raised at any point, execution jumps to the handler and RETURN WITH status='failed' terminates the workflow with an error sentinel string. If BudgetExceeded is raised during the merge GENERATE, execution jumps to the handler and RETURN WITH status='truncated' delivers whatever partial output was captured.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a consolidated 200-word morning news digest by \
summarising three independent topic areas (technology, science, business) concurrently \
using CALL PARALLEL on a reusable summarise_single sub-workflow, then merging the \
results with a morning_briefing prompt function via GENERATE. Guard with EXCEPTION \
handlers for ModelUnavailable (return status=failed) and BudgetExceeded \
(return status=truncated)." --mode workflow

# Step 2 — compile to any target
spl3 splc compile parallel_news_digest.spl --lang python/pocketflow
spl3 splc compile parallel_news_digest.spl --lang python/langgraph
spl3 splc compile parallel_news_digest.spl --lang go
```