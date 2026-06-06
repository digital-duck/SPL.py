## 0. High-level Description

This workflow implements a classic **chain-of-thought** pattern in SPL, decomposing a complex reasoning task into three sequential GENERATE stages that each feed their output into the next as a workflow variable. Three CREATE FUNCTIONs are defined — `research`, which issues a broad fact-gathering prompt for a given `{topic}`; `analyze`, which receives the raw `{research}` text and extracts key trends and implications; and `summarize_analysis`, which condenses the `{analysis}` into an executive brief. The control flow is strictly linear: no WHILE loop, no EVALUATE branch, and no CALL side-effects — the entire pipeline is pure LLM chaining. A single INPUT variable `@topic` drives all three GENERATE calls, while `@summary` is the sole declared OUTPUT. The WORKFLOW concludes with a RETURN carrying `status = 'complete'` metadata. No EXCEPTION handlers are defined, so any runtime errors propagate to the caller unhandled.

## 1. Purpose

Transforms a free-text topic into a polished executive summary by chaining three LLM passes: research, analysis, and summarization.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | `'distributed AI inference'` | The subject to research, analyze, and summarize |

## 3. Process

1. **Research** — `GENERATE research(@topic) INTO @research`: the LLM is prompted to produce key facts about the topic; the result is stored in `@research`.
2. **Analyze** — `GENERATE analyze(@research) INTO @analysis`: the LLM receives the research output and identifies trends and implications; the result is stored in `@analysis`.
3. **Summarize** — `GENERATE summarize_analysis(@analysis) INTO @summary`: the LLM condenses the analysis into a concise executive brief; the result is stored in `@summary`.
4. **Return** — `RETURN @summary WITH status = 'complete'`: the final summary is returned to the caller with a completion status tag.

## 4. Error Handling

- No EXCEPTION handlers are declared. All runtime errors (e.g. `ModelOverloaded`, `ContextLengthExceeded`) propagate unhandled to the caller.

## 5. Output

| Field | Value | Description |
|---|---|---|
| `@summary` | `TEXT` | Executive brief distilled from the three-stage reasoning chain |
| `status` | `'complete'` | Metadata confirming the workflow ran to normal completion |