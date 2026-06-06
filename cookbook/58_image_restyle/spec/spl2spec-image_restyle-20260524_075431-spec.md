## Summary

The Image Restyle workflow takes a source photograph and a plain-text style instruction, then uses a local vision model to produce a structured JSON payload containing a human-readable image description and a ready-to-submit DALL-E 3 prompt. It forms the first half of a two-stage multimodal pipeline: SPL handles the vision-to-text bridge, while a companion Python script (`run.py`) submits the DALL-E prompt and saves the generated image. Non-technical users benefit from a clean separation between local inference (private, free) and cloud image generation (pay-per-call), with the SPL workflow acting as the controllable, auditable middle layer.

---

## Detailed Specification

### 1. Purpose

Produce a JSON payload — containing an image description and a DALL-E 3 regeneration prompt — by running a user-supplied photograph through a local multimodal vision model, enabling a downstream script to generate a restyled version of that image via the OpenAI image API.

---

### 2. High-level Description

The `image_restyle` WORKFLOW implements a multimodal vision-to-prompt bridge using a single `CREATE FUNCTION` called `analyse_and_prompt`, which instructs the LLM to act as a visual artist and prompt engineer. The function receives an IMAGE input, a style directive (e.g. "watercolor painting, soft edges"), and a preservation constraint (e.g. "composition, main subject") and returns a strict JSON object with two fields: `description` (a 1-2 sentence caption of the original) and `dalle_prompt` (a detailed, style-transformed DALL-E 3 regeneration prompt under 150 words). The workflow dispatches this function via `GENERATE … INTO @result` using `generate_multimodal()` dispatch — triggered automatically because the `@photo` INPUT variable carries the IMAGE type — targeting a configurable vision model (default `gemma4:e4b` via Ollama). The output budget is capped at 512 tokens to prevent runaway JSON. Control flow is linear: a single `GENERATE` step followed by `RETURN @result`; the actual DALL-E image generation is intentionally delegated to `run.py` outside the SPL layer, keeping the workflow adapter-agnostic and the IMAGE-generation cost isolated. An `EXCEPTION WHEN ModelUnavailable` handler catches the case where the local vision model is unreachable and returns `RETURN WITH status='failed'`, which signals the caller to abort downstream processing.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW image_restyle` | `WORKFLOW` | Top-level orchestration unit; declares all runtime-configurable `INPUT:` vars including paths, model, style, and quality flags |
| `CREATE FUNCTION analyse_and_prompt` | `CREATE FUNCTION` | Reusable multimodal prompt template; `{style}` and `{preserve}` are interpolated slots; output format is strict JSON with sentinel fields `description` and `dalle_prompt` |
| `GENERATE analyse_and_prompt(...) INTO @result` | `GENERATE … INTO @var` | Triggers `generate_multimodal()` dispatch (IMAGE input detected); output captured into `@result` as TEXT |
| `WITH OUTPUT BUDGET 512 TOKENS` | token budget modifier | Prevents runaway generation; keeps JSON tight |
| `USING MODEL @vision_model` | model selection | Parameterised at runtime; default `gemma4:e4b`; enables adapter swap without touching the `.spl` |
| `LOGGING … LEVEL INFO/ERROR` | side-effect (CALL-like) | Audit trail; not a data transformation |
| `EXCEPTION WHEN ModelUnavailable THEN` | `EXCEPTION WHEN <Type>` | Catches offline/unreachable local vision model; only non-trivial termination path |
| `RETURN … WITH status='failed'` | `RETURN WITH status=` | Non-default error token; signals caller/runner to abort DALL-E step |
| `@photo IMAGE`, `@style TEXT`, `@result TEXT` | `@vars` (INPUT/OUTPUT) | Shared workflow state; IMAGE type on `@photo` drives multimodal dispatch |

---

### 4. Logical Functions / Prompts

**`analyse_and_prompt(photo IMAGE, style TEXT, preserve TEXT)`**

- **Role:** The sole LLM interaction in the workflow. Bridges from raw pixels to a structured, machine-readable DALL-E 3 prompt.
- **Prompt conventions:**
  - Persona framing: "You are a visual artist and prompt engineer."
  - Two interpolation slots: `{style}` (transformation directive) and `{preserve}` (compositional constraints the DALL-E prompt must honour).
  - Strict JSON output sentinel: exactly the two keys `description` and `dalle_prompt` — no markdown wrapping, no extra keys.
  - Hard constraint on `dalle_prompt`: under 150 words; must include lighting, mood, technical detail, and an explicit style transformation.
  - Uses double-brace escaping `{{ }}` around the JSON schema block to prevent SPL variable interpolation.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING: emit photo path + style (INFO)
  │
  ├─ GENERATE analyse_and_prompt(@photo, @style, @preserve)
  │       USING MODEL @vision_model
  │       WITH OUTPUT BUDGET 512 TOKENS
  │       INTO @result
  │
  ├─ LOGGING: "vision analysis done" (INFO)
  │
  └─ RETURN @result
          │
          └─ [DALL-E generation delegated to run.py outside SPL]

EXCEPTION
  └─ WHEN ModelUnavailable
          └─ LOGGING: error (ERROR)
          └─ RETURN '[ERROR] Vision model unavailable.' WITH status='failed'
             (caller/run.py aborts DALL-E step on non-complete status)
```

The only non-trivial control-flow decision is the `EXCEPTION WHEN ModelUnavailable` branch, which emits `status='failed'` to suppress downstream image generation. There is no WHILE loop and no EVALUATE branch — the happy path is a single LLM call followed by a linear return.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 "High-level Description" as input)
spl3 text2spl \
  --description "The image_restyle WORKFLOW implements a multimodal vision-to-prompt bridge \
using a single CREATE FUNCTION called analyse_and_prompt, which instructs the LLM to act as a \
visual artist and prompt engineer. The function receives an IMAGE input, a style directive, and a \
preservation constraint and returns a strict JSON object with two fields: description (a 1-2 sentence \
caption of the original) and dalle_prompt (a detailed DALL-E 3 regeneration prompt under 150 words). \
The workflow dispatches via GENERATE into @result using multimodal dispatch because @photo carries the \
IMAGE type, targeting a configurable vision model capped at 512 output tokens. Control flow is linear; \
an EXCEPTION WHEN ModelUnavailable handler returns WITH status='failed' to signal the caller to abort." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile image_restyle.spl --lang python/pocketflow
spl3 splc compile image_restyle.spl --lang python/langgraph
spl3 splc compile image_restyle.spl --lang go
```