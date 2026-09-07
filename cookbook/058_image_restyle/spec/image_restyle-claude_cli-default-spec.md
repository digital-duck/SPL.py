## Summary

Recipe 54 takes a source photograph and a plain-text style instruction, uses a local vision model to understand the image and compose a detailed DALL-E 3 prompt, then hands that prompt off to an image-generation step that produces a restyled output file. It exists to automate the otherwise manual loop of describing an image, crafting a generation prompt, and calling two different AI services. Creative professionals and developers who want to batch-restyle photos without hand-writing prompts are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Transform a source photograph into a restyled image by (1) analysing it with a local vision model to produce a structured description and DALL-E 3 prompt, and (2) generating the final image via DALL-E 3 using that prompt.

---

### 2. High-level Description

The `image_restyle` WORKFLOW implements a two-stage multimodal pipeline bridging a local vision model and a cloud image-generation service. A single CREATE FUNCTION `analyse_and_prompt` acts as the sole prompt template; it instructs a vision-capable model (defaulting to Gemma4 via Ollama) to examine the input IMAGE, apply the caller-supplied style and preservation constraints, and return a JSON object containing a human-readable `description` and a detailed `dalle_prompt`. The WORKFLOW begins by logging its startup parameters, then issues a GENERATE call to `analyse_and_prompt` with an output budget of 512 tokens, storing the JSON result in `@result`. Because the DALL-E 3 call involves a side-effectful HTTP request and file write that are handled by the companion `run.py` script, the SPL layer simply RETURNs `@result` so that the runner can extract `dalle_prompt` and execute the image generation step. There is no iterative refinement loop (no WHILE) and no output-quality branch (no EVALUATE); the control flow is strictly linear. An EXCEPTION handler for `ModelUnavailable` catches cases where the Ollama vision model is unreachable and RETURNs a sentinel error string WITH `status = 'failed'`, allowing the caller to distinguish a hard failure from a successful JSON payload.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW image_restyle` | `WORKFLOW <name>` | Declares the named orchestration entry point with typed INPUT/OUTPUT |
| `CREATE FUNCTION analyse_and_prompt` | `CREATE FUNCTION <name>` | Reusable prompt template with `{style}`, `{preserve}` param slots and an IMAGE slot |
| `GENERATE analyse_and_prompt(...) INTO @result` | `GENERATE <fn>(...) INTO @<var>` | LLM call; stores JSON TEXT in `@result`; `WITH OUTPUT BUDGET 512 TOKENS` caps response length |
| `USING MODEL @vision_model` | model-selection clause on GENERATE | Routes the call to the local Gemma4/Ollama endpoint; model is runtime-configurable |
| `LOGGING ... LEVEL INFO/ERROR` | side-effect logging | Structured log emission; not a CALL with a return value |
| `RETURN @result WITH status = 'failed'` | `RETURN @<var> WITH <k>=<v>` | Only in EXCEPTION handler; `status='failed'` is a non-trivial token that lets callers detect model-unavailability |
| `EXCEPTION WHEN ModelUnavailable THEN` | `EXCEPTION WHEN <Type> THEN` | Named exception handler for Ollama connectivity failures |
| Shared state `@result` | SPL `@<var>` | Single pipeline variable; written by GENERATE, read by RETURN and by `run.py` at runtime |

---

### 4. Logical Functions / Prompts

#### `analyse_and_prompt`

- **Role:** The sole prompt template; bridges vision understanding and image-generation prompt engineering in one LLM call.
- **Key prompt conventions:**
  - Persona framing: *"You are a visual artist and prompt engineer"* focuses the model on both perceptual description and generative-prompt craft.
  - Structured JSON output: the model must return exactly two fields — `description` (1–2 sentences of what is seen) and `dalle_prompt` (a detailed regeneration prompt). Using a strict JSON schema enables downstream parsing without additional extraction logic.
  - Word-budget rule: `dalle_prompt` is capped at 150 words to stay within DALL-E 3 prompt limits.
  - Preservation contract: the `{preserve}` parameter explicitly lists composition elements the style transformation must not destroy, giving the model a negative-space constraint alongside the positive style instruction.
  - `WITH OUTPUT BUDGET 512 TOKENS` on the GENERATE call enforces a hard token ceiling on the LLM response, preventing verbose or runaway output.

---

### 5. Control Flow

1. **Entry:** WORKFLOW `image_restyle` receives INPUT parameters (`@photo`, `@style`, `@preserve`, model and directory settings).
2. **Log startup:** LOGGING emits photo path and style string at INFO level.
3. **Vision analysis:** GENERATE calls `analyse_and_prompt`, invoking the local vision model with the source IMAGE and style TEXT; result is stored in `@result` (a JSON string).
4. **Log completion:** LOGGING emits a progress message at INFO level.
5. **Termination (happy path):** RETURN `@result` — the JSON payload is passed back to the caller (`run.py`), which extracts `dalle_prompt` and invokes DALL-E 3 to produce the final image file.
6. **Termination (failure path):** If the vision model is unreachable, the EXCEPTION handler catches `ModelUnavailable`, logs an ERROR, and RETURNs a literal error string WITH `status = 'failed'` so callers can branch on the failure without inspecting the payload.

There is no WHILE loop and no EVALUATE branch in the main path; execution is strictly linear.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Transform a source photograph into a restyled image by (1) analysing it with a local vision model to produce a structured description and DALL-E 3 prompt, and (2) generating the final image via DALL-E 3 using that prompt." --mode workflow

# Step 2 — compile to any target
spl3 splc compile image_restyle.spl --lang python/pocketflow
spl3 splc compile image_restyle.spl --lang python/langgraph
spl3 splc compile image_restyle.spl --lang go
```