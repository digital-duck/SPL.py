## 0. High-level Description

This workflow implements a **single-pass generation with LLM-as-judge quality gating and conditional self-refinement** pattern. Three prompt functions are defined: `response`, a straightforward assistant prompt that takes a free-text `{prompt}` and returns a direct reply; `quality_assess`, a structured judge prompt that evaluates any `{result}` and constrains its output to exactly one of three sentinel tokens (`high_quality`, `acceptable`, `low_quality`); and `improved`, a self-refinement prompt that accepts both the original `{prompt}` and the `{current result}` to produce a revised answer. Control flow proceeds by first GENERATing an initial response, then GENERATing a quality judgment, and branching via EVALUATE: a `high_quality` verdict short-circuits to an immediate RETURN, an `acceptable` verdict triggers one further GENERATE through `improved` before returning with status `refined`, and any other verdict returns the original output as `best_effort`. Four EXCEPTION types are handled: `HallucinationDetected` triggers a fresh conservative re-generation; `ContextLengthExceeded` retries up to three times with a low temperature of 0.1 to reduce verbosity; `RefusalToAnswer` surfaces the original prompt back to the caller with status `refused`; and `BudgetExceeded` returns whatever partial result exists with status `truncated`. No CALL side-effects or LOGGING statements are present in this script.

## 1. Purpose

Generate a high-quality LLM response to a user prompt, automatically assessing and optionally refining the output, while gracefully degrading under hallucination, context, refusal, and budget failure conditions.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@prompt` | `'Explain how encryption works'` | The free-text prompt submitted to the LLM for response generation |

## 3. Process

1. **Initial generation** — GENERATE `response(@prompt)` and store the result in `@result`.
2. **Quality assessment** — GENERATE `quality_assess(@result)` and store the one-token verdict in `@quality`.
3. **Branch on verdict** via EVALUATE `@quality`:
   - **`high_quality`** — RETURN `@result` immediately with `status = 'high_quality'`. No further work is done.
   - **`acceptable`** — GENERATE `improved(@result, @prompt)` to produce a refined answer, overwrite `@result`, then RETURN with `status = 'refined'`.
   - **anything else** (i.e. `low_quality` or unexpected token) — RETURN the original `@result` as-is with `status = 'best_effort'`.

## 4. Error Handling

- **`HallucinationDetected`** — discards the suspect result and issues a fresh GENERATE `response(@prompt)`, returning the new output with `status = 'conservative'`. Implies the runtime detected potential hallucination during step 1 or 3.
- **`ContextLengthExceeded`** — retries the failing GENERATE with `temperature = 0.1` up to 3 times, using low temperature to encourage a more concise, less verbose response that fits within the context window.
- **`RefusalToAnswer`** — the model declined to respond; returns the original `@prompt` (not a result) with `status = 'refused'`, signalling to the caller that no usable content was produced.
- **`BudgetExceeded`** — token or cost budget was exhausted mid-run; returns whatever is currently held in `@result` (possibly partial) with `status = 'truncated'`.

## 5. Output

The workflow always returns `@result` (a TEXT value) accompanied by a `status` metadata field. The possible status codes and their meanings are:

| Status | Trigger condition |
|---|---|
| `high_quality` | Judge rated the initial response as high quality |
| `refined` | Judge rated it acceptable; one self-refinement pass was applied |
| `best_effort` | Judge rated it low quality; returned without further improvement |
| `conservative` | Hallucination was detected; a fresh generation was substituted |
| `truncated` | Budget was exhausted; partial result returned |
| `refused` | Model refused to answer; `@result` contains the original prompt, not a response |