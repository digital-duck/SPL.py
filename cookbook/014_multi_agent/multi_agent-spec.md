## 0. High-level Description

This workflow implements a **multi-agent pipeline** pattern in which three specialized agents — Researcher, Analyst, and Writer — collaborate sequentially to produce a polished report on an arbitrary topic. Each agent is defined as a named PROCEDURE (SPL's reusable sub-workflow construct) that encapsulates a distinct role: the `researcher` PROCEDURE issues two GENERATE calls (`research_facts` and `identify_key_themes`) to gather raw facts and distill dominant themes; the `analyst` PROCEDURE issues three GENERATE calls (`analyze_trends`, `assess_risks`, `find_opportunities`) to synthesize the researcher's output into structured intelligence; and the `writer` PROCEDURE implements a **self-refine** loop — GENERATE `draft_report`, then GENERATE `critique`, then GENERATE `revise_report` — to iteratively improve the output before returning it. The orchestrator WORKFLOW `multi_agent_report` coordinates these agents strictly in sequence using CALL-based delegation, passing each agent's result as an INPUT to the next, and persists every intermediate artifact to disk via `write_file` CALL side-effects (`research.md`, `analysis.md`, `report.md`) under the configurable `@log_dir` path. LOGGING statements bracket every major stage at both INFO (workflow start/end) and DEBUG (per-agent input/output) levels, providing full observability into the pipeline. Two EXCEPTION types are handled: `BudgetExceeded` triggers an early RETURN with the partial research artifact, while `HallucinationDetected` triggers a RETRY with reduced temperature (0.1) up to three times.

---

## 1. Purpose

Orchestrate three specialized LLM agents — Researcher, Analyst, and Writer — to automatically produce a structured, self-refined report on any user-supplied topic, persisting intermediate outputs to disk.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | *(required)* | The subject on which the report will be generated (e.g. "Impact of AI on healthcare"). |
| `@log_dir` | `cookbook/14_multi_agent/logs-spl` | Directory path where intermediate and final artifacts are written as Markdown files. |

---

## 3. Process

1. **Log workflow start** — emit an INFO-level log message recording the topic.
2. **Agent 1 — Researcher** (`CALL researcher(@topic) INTO @research`):
   - GENERATE raw facts about the topic via `research_facts`.
   - GENERATE a distilled list of key themes via `identify_key_themes`.
   - Concatenate facts and themes into `@result` and return it as `@research`.
3. **Log research output** at DEBUG level; write `@research` to `{@log_dir}/research.md`.
4. **Agent 2 — Analyst** (`CALL analyst(@research, @topic) INTO @analysis`):
   - GENERATE trend analysis via `analyze_trends`.
   - GENERATE risk assessment via `assess_risks`.
   - GENERATE opportunity identification via `find_opportunities`.
   - Concatenate all three sections under labeled headings and return as `@analysis`.
5. **Log analysis output** at DEBUG level; write `@analysis` to `{@log_dir}/analysis.md`.
6. **Agent 3 — Writer** (`CALL writer(@research, @analysis, @topic) INTO @report`):
   - GENERATE an initial draft via `draft_report` (consumes research, analysis, and topic).
   - GENERATE editorial critique of the draft via `critique`.
   - GENERATE a revised final report via `revise_report` (self-refine step).
   - Return the revised report as `@final`.
7. **Log report output** at DEBUG level; write `@report` to `{@log_dir}/report.md`.
8. **Log workflow completion** at INFO level.
9. **RETURN `@report`** with metadata `status = 'complete'`.

---

## 4. Error Handling

- **`BudgetExceeded`** — the workflow is cut short before the Analyst or Writer agents run; returns whatever research has been collected so far (`@research`) with `status = 'partial_research_only'`.
- **`HallucinationDetected`** — the current generation step is retried with `temperature = 0.1` (low-temperature grounding) up to a maximum of 3 attempts before the exception propagates.

---

## 5. Output

| Field | Value / Type |
|---|---|
| **Primary return value** | `@report` — `TEXT` containing the Writer agent's final, self-refined report. |
| `status` (success path) | `'complete'` |
| `status` (budget exceeded) | `'partial_research_only'` — accompanied by `@research` instead of `@report`. |

No additional metadata fields (e.g. iteration counts or model identifiers) are included in the RETURN statement beyond `status`.