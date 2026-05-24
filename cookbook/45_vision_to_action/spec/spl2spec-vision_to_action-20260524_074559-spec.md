## Summary

Vision to Action is a surveillance scene classifier that takes a natural-language description of an image, uses a single LLM call to label the activity as DELIVERY, INTRUSION, or IGNORE, and then routes to a deterministic action with no further LLM cost. It is designed for smart-home or physical-security systems that need fast, auditable responses to camera events. Security operators and homeowners benefit from automated triage that separates genuine threats from routine activity.

---

## Detailed Specification

### 1. Purpose

Given a text description of a surveillance image, classify the scene into one of three security categories and emit a concrete action string that a downstream system can act on immediately.

---

### 2. High-level Description

This workflow implements a **classify-then-branch** pattern using a single GENERATE call followed by a deterministic EVALUATE decision tree. The workflow declares one INPUT variable, `@image_description`, typed as TEXT (a stand-in for the IMAGE type arriving in SPL v3.0), and one OUTPUT variable, `@action_taken`. A single CREATE FUNCTION named `classify` encapsulates a zero-temperature security-analyst prompt that instructs the LLM to reply with exactly one sentinel token — `DELIVERY`, `INTRUSION`, or `IGNORE` — and nothing else. The GENERATE step stores the classification result in `@scene_label`, and EVALUATE then branches on `contains()` guards to assign `@action_taken` a concrete dispatch string (`SOUND_ALARM_CALL_POLICE`, `NOTIFY_HOMEOWNER_DELIVERY`, or `IGNORE`) without issuing any further LLM calls. The workflow terminates via RETURN WITH `status = 'complete'` carrying the label and action as metadata. An EXCEPTION WHEN `GenerationError` handler provides a safe fallback: if the LLM call fails, the workflow returns `status = 'error'` and defaults the action to IGNORE rather than leaving the caller with no directive.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW vision_to_action` | `WORKFLOW` | Single entry point; declares INPUT/OUTPUT contract |
| `CREATE FUNCTION classify(...)` | `CREATE FUNCTION` | Prompt template with one `{image_description}` slot; enforces sentinel-token output |
| `GENERATE classify(@image_description) INTO @scene_label` | `GENERATE ... INTO @var` | The only LLM call in the workflow; all downstream logic is deterministic |
| `EVALUATE @scene_label WHEN contains(...) THEN ... ELSE ... END` | `EVALUATE` | Three-way branch on sentinel tokens; `contains()` tolerates whitespace/punctuation padding from the LLM |
| `@action_taken := '...'` | Shared state (`@var` assignment) | Mutable workflow variable set inside each EVALUATE branch |
| `RETURN ... WITH status='complete'` | `RETURN WITH status=` | Non-trivial terminal status; carries `label` and `action` metadata to the caller |
| `EXCEPTION WHEN GenerationError THEN ... RETURN ... WITH status='error'` | `EXCEPTION WHEN ... THEN` | Typed error handler; fail-safe default prevents a dead caller |

---

### 4. Logical Functions / Prompts

#### `classify`

- **Role:** The sole LLM interaction in the workflow. Acts as a zero-shot security analyst that reads a scene description and emits a single classification word.
- **Key prompt conventions:**
  - Persona framing: *"You are a security analyst reviewing surveillance footage."*
  - Closed-set output: exactly one of `DELIVERY`, `INTRUSION`, or `IGNORE` — no explanatory text.
  - Sentinel-token discipline: definitions are provided inline so the LLM has sufficient grounding without needing chain-of-thought.
  - The downstream EVALUATE uses `contains()` rather than strict equality to absorb any stray whitespace or punctuation the LLM might append despite the instruction.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING: announce image being analyzed
  │
  ├─ GENERATE classify(@image_description) → @scene_label   [one LLM call]
  │
  ├─ LOGGING: emit classification label
  │
  ├─ EVALUATE @scene_label
  │       WHEN contains('INTRUSION') → @action_taken := 'SOUND_ALARM_CALL_POLICE'
  │       WHEN contains('DELIVERY')  → @action_taken := 'NOTIFY_HOMEOWNER_DELIVERY'
  │       ELSE                       → @action_taken := 'IGNORE'
  │
  └─ RETURN WITH status='complete', label=@scene_label, action=@action_taken

EXCEPTION WHEN GenerationError
  └─ RETURN WITH status='error', reason='classification_failed', action='IGNORE'
```

There is no WHILE loop — the workflow is intentionally single-pass. The only branching is the EVALUATE decision tree, which is purely deterministic (no LLM cost). RETURN WITH `status='complete'` is the normal terminal state; `status='error'` is the exception-path terminal state.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a text description of a surveillance image, \
classify the scene into one of three security categories (DELIVERY, INTRUSION, IGNORE) \
using a single LLM call and emit a concrete action string via a deterministic \
EVALUATE branch with no further LLM cost. Handle GenerationError with a safe IGNORE default." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile vision_to_action.spl --lang python/pocketflow
spl3 splc compile vision_to_action.spl --lang python/langgraph
spl3 splc compile vision_to_action.spl --lang go
```