## 0. High-level Description

This workflow implements a **nested-procedures** pattern in SPL, where a top-level WORKFLOW (`layered_explainer`) delegates distinct subtasks to three reusable PROCEDURE units rather than inlining all logic. The three inner procedures each encapsulate a single concern: `explain_layer` wraps a `GENERATE` call to produce an audience-tailored explanation with a configurable `style` parameter (defaulting to `'clear and engaging'`); `make_example` wraps a `GENERATE` call to produce a grounded, context-aware concrete example; and `calibrate_complexity` uses a GENERATE/EVALUATE branch to assess the reading level of a text and conditionally simplify it if the assessed grade exceeds a `target_grade` threshold (default 8), otherwise passing the text through unchanged. The outer WORKFLOW sequences five steps — a direct GENERATE for topic research, two CALL invocations into the explanation and example procedures, a third CALL into the complexity-calibration procedure (which itself contains an internal EVALUATE branch), and a final GENERATE to assemble all pieces into a finished article — before issuing a RETURN with `status` and `audience` metadata. There are no explicit EXCEPTION handlers or LOGGING statements in this script; resource-limit and error propagation are left to the runtime defaults. The `@depth` INPUT parameter is threaded through to the final assembly step, allowing callers to control article elaboration without altering the inner procedures.

## 1. Purpose

Produce a calibrated, audience-appropriate explanatory article on any topic by composing reusable explanation, example-generation, and reading-level-calibration procedures under a single orchestrating workflow.

## 2. Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `@topic` | *(required)* | The subject matter to research and explain |
| `@audience` | *(required)* | The target reader (e.g. `"high school students"`, `"policy makers"`) — passed to all inner procedures |
| `@depth` | `'standard'` | Controls elaboration level in the final article assembly step |

> **Inner procedure parameters** (not external inputs, but documented for completeness):
>
> | Parameter | Default | Description |
> |-----------|---------|-------------|
> | `style` *(explain_layer)* | `'clear and engaging'` | Prose style directive for the explanation |
> | `target_grade` *(calibrate_complexity)* | `8` | Maximum acceptable reading-grade level before simplification is triggered |

## 3. Process

1. **Research** — GENERATE `research_overview(@topic)` to produce a factual summary of the topic, stored in `@overview`.
2. **Explain** — CALL `explain_layer` with `@overview` as content, `@audience`, and the hardcoded style `'clear, engaging, avoid jargon'`; the procedure internally GENERATEs `explain(...)` and returns the result into `@base_explanation`.
3. **Exemplify** — CALL `make_example` with `@topic` as the concept, `@base_explanation` as context, and `@audience`; the procedure internally GENERATEs `concrete_example(...)` and returns a grounded example into `@example`.
4. **Calibrate complexity** — CALL `calibrate_complexity` with `@base_explanation`, `@audience`, and `target_grade = 8`:
   - Internally GENERATEs `assess_reading_level(@base_explanation)` into `@reading_level`.
   - EVALUATE `@reading_level`: if it exceeds `target_grade`, GENERATEs `simplify(text, audience)` and returns the simplified text; otherwise returns the original text unchanged.
   - Result stored in `@calibrated_explanation`.
5. **Assemble** — GENERATE `assemble_article(@topic, @calibrated_explanation, @example, @depth)` to combine all pieces into the finished `@article`, with `@depth` governing elaboration level.
6. **Return** — RETURN `@article` with metadata `status = 'complete'` and `audience = @audience`.

## 4. Error Handling

- *(None declared.)* This script contains no EXCEPTION blocks. Any runtime errors (e.g., `ModelOverloaded`, `ContextLengthExceeded`, `QualityBelowThreshold`) will propagate to the SPL runtime's default handler. Adding EXCEPTION clauses around the GENERATE or CALL steps would be a recommended hardening step for production use.

## 5. Output

| Field | Value |
|-------|-------|
| `@article` | The assembled explanatory article (TEXT) — researched, explained, exemplified, and reading-level-calibrated for the specified audience |
| `status` | `'complete'` (static string, set unconditionally on the happy path) |
| `audience` | Echo of the `@audience` INPUT, useful for downstream routing or logging |