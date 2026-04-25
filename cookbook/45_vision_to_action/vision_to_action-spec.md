## 0. High-level Description

This workflow implements a **vision-to-action** pattern that combines a single bounded LLM classification step with a fully deterministic decision tree — keeping LLM cost to exactly one call per execution. A single CREATE FUNCTION named `classify` drives the entire intelligence layer: it casts the LLM into the role of a security analyst and instructs it to return exactly one of three sentinel tokens (`DELIVERY`, `INTRUSION`, or `IGNORE`) with no additional prose, making downstream parsing reliable. After GENERATE stores the result in `@scene_label`, an EVALUATE block branches on `contains()` matches rather than strict equality, deliberately tolerating whitespace or punctuation that a model might append around the sentinel. Each branch assigns a deterministic string to `@action_taken` and emits a LOGGING statement at an appropriate severity level (WARN for intrusions, INFO for deliveries, DEBUG for routine activity), producing a structured audit trail without further model calls. The RETURN statement carries both the human-readable summary and structured metadata fields (`status`, `label`, `action`) for downstream consumers. A single EXCEPTION handler for `GenerationError` provides a fail-safe by defaulting to `IGNORE`, logging a WARN, and returning a degraded-but-safe response rather than propagating the error.

## 1. Purpose

Given a plain-text description of a surveillance image, classify the scene using an LLM and automatically dispatch the appropriate security action (sound alarm, notify homeowner, or do nothing) with no human intervention.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@image_description` | `'Image shows a package being delivered to the front door.'` | Natural-language description of the surveillance image (TEXT stand-in for the IMAGE type planned in SPL v3.0) |

## 3. Process

1. **Log the incoming description** at INFO level so operators can correlate analysis runs with their inputs.
2. **Call `classify(@image_description)`** via GENERATE — the prompt instructs the model to act as a security analyst and return exactly one of three tokens: `DELIVERY`, `INTRUSION`, or `IGNORE`. The result is stored in `@scene_label`.
3. **Log the raw classification** at DEBUG level for diagnostic tracing.
4. **Enter the EVALUATE decision tree** on `@scene_label` using `contains()` matching:
   - **INTRUSION match** → log a WARN, set `@action_taken := 'SOUND_ALARM_CALL_POLICE'`.
   - **DELIVERY match** → log INFO, set `@action_taken := 'NOTIFY_HOMEOWNER_DELIVERY'`.
   - **Anything else** → log DEBUG, set `@action_taken := 'IGNORE'`.
5. **RETURN** a formatted string plus structured metadata (`status`, `label`, `action`).

## 4. Error Handling

- **`GenerationError`** — the LLM call in step 2 failed (timeout, model overload, etc.). The workflow logs a WARN message explaining the fallback rationale ("defaulting to IGNORE for safety"), then returns a safe no-op response with `status = 'error'` and `reason = 'classification_failed'`. No alarm is sounded on uncertainty.

## 5. Output

`RETURN` yields a human-readable string of the form `Action taken: <value>` accompanied by the following metadata fields:

| Field | Type | Values / Notes |
|---|---|---|
| `status` | string | `'complete'` on success; `'error'` on GenerationError |
| `label` | string | Raw classification token from the LLM (`DELIVERY`, `INTRUSION`, `IGNORE`, or absent on error) |
| `action` | string | Dispatched action: `SOUND_ALARM_CALL_POLICE`, `NOTIFY_HOMEOWNER_DELIVERY`, or `IGNORE` (absent on error) |
| `reason` | string | `'classification_failed'` — only present when `status = 'error'` |