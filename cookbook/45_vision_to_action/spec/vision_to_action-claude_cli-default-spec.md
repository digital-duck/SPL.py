## Summary

Vision to Action is a surveillance scene triage workflow that accepts a text description of an image (or OCR output) and emits a deterministic action code — `SOUND_ALARM_CALL_POLICE`, `NOTIFY_HOMEOWNER_DELIVERY`, or `IGNORE`. It uses a single LLM call to classify the scene and then branches entirely in deterministic logic, keeping latency and cost minimal. Security operations teams, smart-home platforms, and edge-camera pipelines benefit from this pattern.

---

## Detailed Specification

### 1. Purpose

Accept a natural-language description of a surveillance image and produce a concrete, machine-readable action code by combining one bounded LLM classification with a deterministic decision tree.

---

### 2. High-level Description

The WORKFLOW `vision_to_action` accepts a single TEXT input `@image_description` (with a sensible default) and produces `@action_taken` as its output. A single CREATE FUNCTION named `classify` encodes a tightly constrained prompt that instructs the LLM to act as a security analyst and reply with exactly one of three sentinel tokens — `DELIVERY`, `INTRUSION`, or `IGNORE` — and nothing else; this hard output constraint keeps downstream branching reliable. One GENERATE call invokes `classify` and stores the raw LLM reply in `@scene_label`. Control then passes immediately to a deterministic EVALUATE block that pattern-matches `@scene_label` using `contains()` guards (tolerating whitespace or punctuation artefacts) and assigns `@action_taken` accordingly: `SOUND_ALARM_CALL_POLICE` for intrusion, `NOTIFY_HOMEOWNER_DELIVERY` for delivery, and `IGNORE` for anything else. There is no WHILE loop — the workflow is intentionally single-pass to bound latency and LLM spend. An EXCEPTION handler for `GenerationError` catches any LLM failure and defaults safely to `IGNORE` with `status='error'`, ensuring the system degrades gracefully rather than alerting falsely. Every logical branch is instrumented with LOGGING at appropriate severity levels (INFO, DEBUG, WARN).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW vision_to_action` | `WORKFLOW <name>` | Top-level orchestration entry point; declares INPUT/OUTPUT variables |
| `CREATE FUNCTION classify(...)` | `CREATE FUNCTION <name>` | Reusable prompt template with `{image_description}` slot; returns TEXT |
| `GENERATE classify(@image_description) INTO @scene_label` | `GENERATE <fn>(...) INTO @<var>` | Single LLM call; result stored in shared state variable `@scene_label` |
| `EVALUATE @scene_label WHEN contains(...) THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Deterministic branch on LLM output; `contains()` guards tolerate formatting noise |
| `@image_description`, `@scene_label`, `@action_taken` | Shared state (`@<var>`) | Mutable workflow-scoped variables passed between steps |
| `RETURN ... WITH status='complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'complete'` signals successful termination |
| `RETURN ... WITH status='error'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token `'error'` signals degraded/fallback termination |
| `EXCEPTION WHEN GenerationError THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Named handler for LLM generation failures; emits safe default action |

---

### 4. Logical Functions / Prompts

**`classify`**

- **Role:** The sole LLM interaction in the workflow. Takes the raw image description and produces a classification label that drives all downstream branching.
- **Prompt conventions:**
  - Persona framing: "You are a security analyst reviewing surveillance footage."
  - Closed vocabulary: exactly one of `DELIVERY`, `INTRUSION`, or `IGNORE` — all caps, no prose.
  - Definitions block: each label is precisely defined to reduce ambiguity at the boundary cases (e.g. "known courier" vs. "unauthorized entry").
  - Sentinel-token output format: "Reply with only the classification word — nothing else." This makes `contains()` matching in EVALUATE reliable even if the model adds trailing punctuation or whitespace.
  - Input slot: `{image_description}` — the only variable injected at call time.

---

### 5. Control Flow

```
START
  │
  ▼
LOGGING (INFO) — log incoming image description
  │
  ▼
GENERATE classify(@image_description) INTO @scene_label   ← single LLM call
  │
  ▼  (GenerationError?) ──────────────────────────────────────────────┐
  │                                                                    │
  ▼                                                              EXCEPTION
EVALUATE @scene_label                                          @action_taken := IGNORE
  ├─ contains('INTRUSION') → @action_taken := SOUND_ALARM_CALL_POLICE  RETURN status='error'
  ├─ contains('DELIVERY')  → @action_taken := NOTIFY_HOMEOWNER_DELIVERY
  └─ ELSE                  → @action_taken := IGNORE
  │
  ▼
RETURN WITH status='complete', label=@scene_label, action=@action_taken
```

There is no WHILE loop. The workflow executes in a single linear pass: classify → branch → return. The two non-trivial RETURN status tokens (`'complete'` and `'error'`) distinguish normal from degraded termination and can be used by a caller to decide whether to escalate, retry, or log an alert.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Accept a natural-language description of a surveillance image and produce a concrete, machine-readable action code by combining one bounded LLM classification with a deterministic decision tree." --mode workflow

# Step 2 — compile to any target
spl3 splc compile vision_to_action.spl --lang python/pocketflow
spl3 splc compile vision_to_action.spl --lang python/langgraph
spl3 splc compile vision_to_action.spl --lang go
```