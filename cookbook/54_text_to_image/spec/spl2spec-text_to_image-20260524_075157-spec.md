## Summary

This workflow generates images from natural-language text prompts by first optionally improving the prompt through an LLM before handing it off to an image backend (DALL-E 3 in the cloud, or Stable Diffusion locally). It bridges the gap between a user's rough idea and a polished image generation request, saving prompt-engineering effort. Content creators, researchers, and developers building multimodal pipelines are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality image from a user-supplied text prompt, with optional LLM-driven prompt enhancement, targeting DALL-E 3 (cloud) or Stable Diffusion (local) as the image backend.

---

### 2. High-level Description

`text_to_image` is a two-stage WORKFLOW that separates prompt refinement from image synthesis. In the first stage, an EVALUATE construct branches on the boolean `@enhance` flag: when true, a GENERATE call invokes the `enhance_prompt` function — a CREATE FUNCTION template that instructs an LLM to enrich the original prompt with lighting, camera angle, mood, and style keywords while staying under 200 words — and stores the result in `@final_prompt`; when false, `@final_prompt` is assigned the raw input directly. The workflow then RETURNs `@final_prompt` to the physical runner (`run.py`), which dispatches to the appropriate image backend and writes the output file. Actual image I/O is intentionally outside the SPL layer, following the DODA principle that the `.spl` spec never encodes physical backend decisions. An EXCEPTION handler catches `ModelUnavailable` (e.g. a missing `OPENAI_API_KEY`) and terminates with `status = 'failed'`, enabling callers to detect and recover from backend failures.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW text_to_image` | `WORKFLOW` | Top-level orchestration unit; declares `INPUT:` and `OUTPUT: @image_path IMAGE` |
| `CREATE FUNCTION enhance_prompt` | `CREATE FUNCTION` | Reusable prompt template with `{prompt}`, `{style}`, `{aspect}` slots; returns `TEXT` |
| `GENERATE enhance_prompt(...) INTO @final_prompt` | `GENERATE ... INTO @var` | LLM call capped at 512 output tokens; model resolved from `@llm_model` at runtime |
| `EVALUATE @enhance WHEN = TRUE THEN ... ELSE ... END` | `EVALUATE` | Semantic branch; true path invokes LLM enhancement, false path is a direct assignment |
| `@prompt, @style, @aspect, @enhance, ...` | SPL `@var` (shared state) | All INPUT variables; thread workflow state through all steps |
| `EXCEPTION WHEN ModelUnavailable THEN ...` | `EXCEPTION WHEN` | Typed handler; catches missing or unreachable image model |
| `RETURN ... WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial termination driven by exception; signals failure to the caller |
| `LOGGING ... LEVEL INFO/DEBUG/ERROR` | Side-effect statement | Observability; not a control-flow construct |

---

### 4. Logical Functions / Prompts

**`enhance_prompt(prompt TEXT, style TEXT, aspect TEXT)`**

- **Role:** Transforms a rough user prompt into a detailed, model-ready image generation prompt.
- **Key conventions:**
  - System persona: "professional prompt engineer for image generation models."
  - Accepts three slots: the original `{prompt}`, a `{style}` keyword (e.g. `photorealistic`, `oil painting`), and an `{aspect}` ratio hint (e.g. `landscape`, `portrait`).
  - Hard constraint: output must be under 200 words.
  - Sentinel convention: "Return ONLY the enhanced prompt, no explanation" — ensures the LLM output is directly usable as the image model's input without post-processing.
  - Output budget is enforced at the GENERATE call site: `WITH OUTPUT BUDGET 512 TOKENS`.

---

### 5. Control Flow

```
START
  │
  ├─ LOGGING entry (prompt, style)
  │
  ├─ EVALUATE @enhance
  │     WHEN = TRUE  →  GENERATE enhance_prompt(...) INTO @final_prompt
  │                      LOGGING 'enhanced prompt ready'
  │     ELSE         →  @final_prompt := @prompt  (direct assignment)
  │
  ├─ LOGGING 'generating image via {@model}'
  │
  ├─ RETURN @final_prompt          ← hands off to run.py (physical image backend)
  │
  └─ EXCEPTION WHEN ModelUnavailable
         LOGGING error
         RETURN '[ERROR] ...' WITH status = 'failed'   ← non-trivial exit
```

There is no WHILE loop; this is a single-pass, branch-and-return workflow. The only non-trivial RETURN is inside the exception handler; the normal exit simply delivers `@final_prompt` to the physical runner.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Generate a high-quality image from a user-supplied text prompt, with optional LLM-driven prompt enhancement, targeting DALL-E 3 (cloud) or Stable Diffusion (local) as the image backend." --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_image.spl --lang python/pocketflow
spl3 splc compile text_to_image.spl --lang python/langgraph
spl3 splc compile text_to_image.spl --lang go
```