## Summary

This workflow converts text into natural-sounding speech and saves the result as an audio file. It optionally pre-processes the input text through an LLM to clean it for narration — expanding abbreviations, stripping markdown, and smoothing punctuation — before handing the script to a physical TTS engine (OpenAI or system `say`/`espeak`). It is useful for accessibility tooling, podcast narration, and generating spoken summaries of AI-generated content.

---

## Detailed Specification

### 1. Purpose

Convert arbitrary text into a saved audio file, with optional LLM-driven script cleaning to improve the naturalness of the resulting speech.

---

### 2. High-level Description

The `text_to_speech` WORKFLOW accepts a raw text string, a target voice, a tone instruction, a TTS model identifier, and a boolean `@prep` flag that governs whether LLM pre-processing runs. When `@prep` is TRUE, an EVALUATE branch invokes GENERATE with the `prep_script` function, which uses an LLM to expand abbreviations, strip markdown symbols, replace URLs with prose descriptions, and add natural pause punctuation — returning a cleaned script. When `@prep` is FALSE, the input text is assigned directly to `@script` with no LLM call. The workflow then emits the final script via RETURN so the physical runner (`run.py`) can dispatch it to either the OpenAI TTS API (cloud, requires `OPENAI_API_KEY`) or a local system TTS engine (`say` on macOS, `espeak` on Linux). An EXCEPTION handler for `ModelUnavailable` catches cases where the TTS backend or the LLM prep model is unreachable, logging the failure and returning with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION prep_script` | `CREATE FUNCTION` | Prompt template with `{raw_text}` and `{tone}` slots; returns cleaned narration-ready text |
| `WORKFLOW text_to_speech` | `WORKFLOW` | Top-level named workflow with `INPUT:` / `OUTPUT:` declarations |
| `GENERATE prep_script(...) INTO @script` | `GENERATE ... INTO @var` | Single LLM call, result bound to `@script`; budget-capped at 2 048 output tokens |
| `@script := @text` | `@var := value` | Direct assignment, bypasses LLM entirely when prep is off |
| `EVALUATE @prep WHEN = TRUE THEN ... ELSE ... END` | `EVALUATE` | Branches on a boolean input flag, not on LLM output; drives the prep/no-prep decision |
| `EXCEPTION WHEN ModelUnavailable THEN` | `EXCEPTION WHEN <Type>` | Catches unavailable TTS or LLM model; returns a sentinel error string |
| `RETURN ... WITH status = 'failed'` | `RETURN WITH status=` | Non-trivial status token; signals failure to the caller / physical runner |
| `LOGGING ... LEVEL INFO/DEBUG/ERROR` | `LOGGING` | Structured log emission at multiple verbosity levels throughout execution |
| `@script` (shared state) | `@var` | Single mutable variable threaded through EVALUATE and RETURN |

---

### 4. Logical Functions / Prompts

#### `prep_script(raw_text TEXT, tone TEXT)`

- **Role:** Pre-processing gate; transforms raw text into narration-optimised prose before it reaches the TTS engine.
- **Prompt conventions:**
  - Receives `{tone}` as a top-level style directive (e.g. `neutral`, `formal`, `friendly`).
  - Explicit cleaning rules are enumerated in the system prompt (abbreviation expansion, markdown stripping, URL replacement, pause punctuation).
  - Output format: raw cleaned text only — no explanation, no metadata, no wrapping.
  - Token budget: 2 048 output tokens, sufficient for long documents without runaway generation.

---

### 5. Control Flow

1. **Entry** — log voice, model, and character count at INFO level.
2. **EVALUATE `@prep`** — if TRUE, run GENERATE with `prep_script` and bind result to `@script`; log completion at DEBUG. If FALSE, assign `@text` directly to `@script` with no LLM call.
3. **Handoff** — log the synthesis target at INFO, then RETURN `@script` to the physical runner (`run.py`), which performs the actual TTS call and writes the audio file.
4. **Exception path** — if `ModelUnavailable` is raised at any point (LLM prep or TTS backend), log at ERROR and RETURN `status = 'failed'`, terminating the workflow without an audio file.

The only non-trivial RETURN is the `status = 'failed'` error exit; the happy-path RETURN is a simple scalar hand-off to the physical layer.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert arbitrary text into a saved audio file, with \
optional LLM-driven script cleaning to improve the naturalness of the resulting speech. \
When the prep flag is enabled, use a CREATE FUNCTION prompt to expand abbreviations, \
strip markdown, replace URLs with prose, and add pause punctuation before handing the \
cleaned script to the TTS engine. Handle ModelUnavailable exceptions by returning \
status=failed." --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_speech.spl --lang python/pocketflow
spl3 splc compile text_to_speech.spl --lang python/langgraph
spl3 splc compile text_to_speech.spl --lang go
```