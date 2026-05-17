## Summary

This workflow converts text into natural-sounding speech by optionally cleaning a raw script with an LLM before handing it off to a TTS engine. It supports both cloud-based synthesis (OpenAI TTS) and local system TTS tools, making it useful for accessibility, podcast narration, and spoken document summaries. Content creators and developers building voice-enabled applications are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Convert an input text string into a synthesized audio file, with an optional LLM-powered script-cleaning step that makes the text more natural for spoken delivery.

---

### 2. High-level Description

The `text_to_speech` WORKFLOW accepts a text string along with synthesis parameters (voice, TTS model, tone, and an output directory) and produces an AUDIO output representing the saved file path. At the start, it logs the invocation context including voice, model, and character count. The workflow branches on a boolean `@prep` flag using EVALUATE: when `@prep` is TRUE, it calls the `prep_script` CREATE FUNCTION via GENERATE — using a local LLM (defaulting to `gemma4:e4b`) with a 2048-token output budget — to expand abbreviations, strip markdown symbols, replace URLs with descriptions, and add natural pause punctuation, storing the result in `@script`; when FALSE, `@script` is assigned directly from the raw `@text` input. After the branch resolves, the workflow logs the chosen TTS model and voice, then RETURNs `@script` to the physical runner (`run.py`), which handles the actual audio synthesis and file saving — this separation allows the SPL layer to remain engine-agnostic, supporting both OpenAI TTS and system-level tools like `say` (macOS) or `espeak` (Linux). An EXCEPTION handler catches `ModelUnavailable` errors (missing API key or absent `espeak`), logs an error message, and RETURNs with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW text_to_speech` | `WORKFLOW text_to_speech` | Top-level orchestration unit with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION prep_script` | `CREATE FUNCTION prep_script(raw_text, tone)` | Reusable prompt template with `{raw_text}` and `{tone}` slots |
| `GENERATE prep_script(...) INTO @script` | `GENERATE <fn>(...) INTO @<var>` | LLM call with `WITH OUTPUT BUDGET` and `USING MODEL` modifiers |
| `EVALUATE @prep WHEN = TRUE THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Binary branch on the boolean prep flag |
| `@script := @text` | Inline assignment in ELSE branch | Bypasses LLM; passes raw text directly |
| `RETURN @script` | `RETURN @<var>` | Hands cleaned script to physical runner for synthesis |
| `RETURN '[ERROR]...' WITH status = 'failed'` | `RETURN @<var> WITH status=<value>` | Non-trivial status token; signals failure to the caller |
| `EXCEPTION WHEN ModelUnavailable THEN` | `EXCEPTION WHEN <Type> THEN` | Named handler for missing TTS engine or API key |
| `LOGGING ... LEVEL INFO/DEBUG/ERROR` | `LOGGING` | Structured log emission at multiple severity levels |
| `@text`, `@script`, `@audio_path` | SPL `@<var>` shared state | Typed workflow variables threaded through all steps |

---

### 4. Logical Functions / Prompts

**`prep_script`**

- **Role:** Pre-processing gate — transforms raw input text into TTS-ready prose before synthesis.
- **Key prompt conventions:**
  - Parameterised by `{raw_text}` (the source content) and `{tone}` (e.g., "neutral", "warm", "formal") to allow caller-controlled register.
  - Explicit cleaning rules listed as instructions: expand abbreviations, strip markdown symbols (`**`, `#`, `-`), replace URLs with brief descriptions, insert natural pause punctuation.
  - Strict output contract: "Return ONLY the cleaned script, no explanation." — no sentinel tokens needed because the entire response is consumed as the script.
  - Output budget capped at 2048 tokens to bound latency and cost.
  - Runs on a local LLM (`@llm_model`, default `gemma4:e4b`), keeping this preprocessing step zero-cost and offline-capable.

---

### 5. Control Flow

1. **Entry** — log invocation metadata (voice, model, character count).
2. **EVALUATE branch on `@prep`:**
   - `TRUE` → GENERATE `prep_script(@text, @tone)` using the local LLM → store in `@script` → log "script prep done".
   - `FALSE` (ELSE) → assign `@script := @text` directly; no LLM call.
3. **Post-branch** — log the TTS synthesis intent (model, voice).
4. **RETURN `@script`** — passes the (optionally cleaned) script to the external `run.py` runner, which performs audio synthesis and file saving; `@audio_path` is populated by the runner.
5. **EXCEPTION `ModelUnavailable`** — if either the local LLM or the TTS engine is unreachable, log at ERROR level and RETURN with `status = 'failed'`, terminating the workflow abnormally.

There is no WHILE loop; the workflow is a single conditional pass.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert an input text string into a synthesized audio file, \
  with an optional LLM-powered script-cleaning step that makes the text more natural \
  for spoken delivery." --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_speech.spl --lang python/pocketflow
spl3 splc compile text_to_speech.spl --lang python/langgraph
spl3 splc compile text_to_speech.spl --lang go
```