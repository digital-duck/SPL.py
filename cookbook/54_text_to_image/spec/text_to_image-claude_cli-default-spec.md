## Summary

This workflow accepts a text description and optional style parameters, optionally enriches the prompt using a local LLM, then hands the final prompt to a backend image-generation runner that calls either OpenAI DALL-E 3 (cloud) or Stable Diffusion (local). It separates the intelligent prompt-enhancement step — expressed in SPL — from the image-rendering side effect, which is delegated to a physical runner (`run.py`). Content creators and developers benefit by getting higher-quality images without manually crafting detailed generation prompts.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality image from a user-supplied text description by optionally enriching the prompt with an LLM before delegating to a configurable image-generation backend.

---

### 2. High-level Description

The `text_to_image` WORKFLOW accepts a natural-language prompt together with style, aspect-ratio, quality, and backend-selection parameters. If the `@enhance` flag is TRUE, the workflow invokes a single GENERATE call using the `enhance_prompt` function — a CREATE FUNCTION template that instructs an LLM to add lighting, camera-angle, mood, and style keywords while preserving the original subject — storing the result in `@final_prompt`; otherwise an EVALUATE branch assigns the raw `@prompt` directly to `@final_prompt`. The GENERATE step is budget-capped at 512 output tokens and executed against a configurable local model (default `gemma4:e4b`), enabling offline or low-cost enhancement without consuming image-generation credits. After enhancement, the workflow returns `@final_prompt` to the physical runner (`run.py`), which performs the actual image synthesis against either DALL-E 3 (cloud target) or Stable Diffusion via ComfyUI/diffusers (local target) and writes the result to the configured output directory. An EXCEPTION handler catches `ModelUnavailable` faults — signalling that the image backend is unreachable — and terminates with `status = 'failed'` alongside a human-readable error message.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW text_to_image` | `WORKFLOW text_to_image` | Top-level orchestration; declares all `INPUT` vars and `OUTPUT @image_path IMAGE` |
| `CREATE FUNCTION enhance_prompt` | `CREATE FUNCTION enhance_prompt(prompt, style, aspect)` | Reusable prompt template; returns TEXT (the enhanced prompt) |
| `GENERATE enhance_prompt(...) INTO @final_prompt` | `GENERATE enhance_prompt(@prompt, @style, @aspect) WITH OUTPUT BUDGET 512 TOKENS USING MODEL @llm_model INTO @final_prompt` | LLM call; budget-capped; model is runtime-configurable |
| `EVALUATE @enhance WHEN = TRUE` | `EVALUATE @enhance WHEN = TRUE THEN ... ELSE ... END` | Boolean branch: GENERATE path vs. direct assignment path |
| `@final_prompt := @prompt` | shared-state assignment inside EVALUATE ELSE | Direct variable assignment; no LLM call |
| `@var` shared state | `@prompt`, `@style`, `@aspect`, `@final_prompt`, `@image_path`, etc. | Workflow-scoped variables threaded through all steps |
| `EXCEPTION WHEN ModelUnavailable` | `EXCEPTION WHEN ModelUnavailable THEN ... RETURN '...' WITH status = 'failed'` | Non-trivial terminal status drives error reporting to the caller |
| `LOGGING ... LEVEL INFO/DEBUG/ERROR` | `LOGGING f'...' LEVEL INFO` | Structured log emission at INFO, DEBUG, and ERROR severity |

---

### 4. Logical Functions / Prompts

#### `enhance_prompt`

- **Role**: Pre-processing prompt engineer; transforms a terse user description into a richly detailed generation prompt suitable for DALL-E 3 or Stable Diffusion.
- **Key prompt conventions**:
  - Persona framing: *"You are a professional prompt engineer for image generation models."*
  - Parameterised slots: `{prompt}`, `{style}`, `{aspect}` injected at call time.
  - Hard rules encoded in the system prompt: preserve the core subject, add lighting/angle/mood details, append style-appropriate keywords, stay under 200 words.
  - Output sentinel: *"Return ONLY the enhanced prompt, no explanation"* — suppresses any prose wrapper so the raw output can be forwarded directly to the image backend.
  - Token budget: 512 output tokens (enforced at GENERATE call site).

---

### 5. Control Flow

1. **Entry** — workflow begins; LOGGING emits the input prompt and style at INFO level.
2. **EVALUATE branch** — checks `@enhance`:
   - **TRUE path**: GENERATE calls `enhance_prompt` via the local LLM; result stored in `@final_prompt`; DEBUG log confirms the enhanced prompt is ready.
   - **FALSE path**: `@final_prompt` is assigned directly from `@prompt`; no LLM call is made.
3. **Hand-off** — LOGGING emits the chosen image model at INFO level; the workflow RETURNs `@final_prompt` to the physical runner (`run.py`), which performs the image synthesis and writes `@image_path`.
4. **Exception path** — if `ModelUnavailable` is raised at any point, the handler emits an ERROR log and RETURNs with `status = 'failed'`, terminating the workflow without producing an image.

There is no WHILE loop; execution is strictly linear through the EVALUATE branch and terminates after a single image-generation cycle.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a high-quality image from a user-supplied text description by optionally enriching the prompt with an LLM before delegating to a configurable image-generation backend." --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_image.spl --lang python/pocketflow
spl3 splc compile text_to_image.spl --lang python/langgraph
spl3 splc compile text_to_image.spl --lang go

# Cloud vs local image backend selection
spl3 splc compile text_to_image.spl --lang python/pocketflow --target cloud   # DALL-E 3
spl3 splc compile text_to_image.spl --lang python/pocketflow --target local   # Stable Diffusion
```