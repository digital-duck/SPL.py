## Summary

The Audio Summary workflow accepts an audio clip and produces one of three outputs — a verbatim transcript, a structured meeting analysis, or a prose summary — depending on a caller-supplied mode. It is designed for anyone who needs to convert spoken recordings into actionable text: teams processing meeting recordings, researchers transcribing interviews, or developers building audio-first pipelines. The workflow targets Liquid AI's LFM-2.5 multimodal model, which can ingest raw audio directly without a separate speech-to-text step.

---

## Detailed Specification

### 1. Purpose

Process an audio clip through a speech-capable multimodal LLM and return either a verbatim transcript, a structured key-points breakdown, or a concise prose summary, selected by a single `mode` parameter.

---

### 2. High-level Description

The `audio_summary` WORKFLOW accepts an `AUDIO`-typed input variable (`@clip`) alongside three control parameters — `@mode`, `@style`, and `@model` — and routes execution through one of three CREATE FUNCTIONs via an EVALUATE branch. When `@mode` equals `'transcribe'`, the `transcribe` function instructs the model to produce a verbatim, line-by-line transcript with uncertainty markers (`[?]`) for unclear audio. When `@mode` equals `'key_points'`, the `key_points` function instructs the model to extract agenda items, bullet-point key points, decisions, and action items formatted as structured Markdown. In all other cases (including the default `'summary'`), the `summarise` function generates a style-controlled prose summary (style is caller-specified, defaulting to `'concise paragraph'`) that preserves names, dates, and decisions while discarding filler. All three branches issue a GENERATE call against the same `@model` (defaulting to Liquid AI LFM-2.5) with a shared `@output_budget` token ceiling and store their result into `@result`. The AUDIO input is encoded by `spl/codecs/audio_codec.py` into `AudioPart` dicts before being passed to `generate_multimodal()`, keeping the `.spl` source hardware-agnostic per the DODA principle. An EXCEPTION handler for `ModelUnavailable` logs a diagnostic hint about API keys or Ollama availability and RETURNs a sentinel error string with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `PocketFlow Node` | `CREATE FUNCTION` | Each logical prompt template (`transcribe`, `summarise`, `key_points`) maps to one CREATE FUNCTION |
| `Flow` / pipeline | `WORKFLOW audio_summary` | Single named workflow; INPUT/OUTPUT declarations replace constructor args |
| `node._exec()` call | `GENERATE <fn>(...) INTO @result` | Dispatches to `generate_multimodal()` because input carries AUDIO type |
| Conditional routing | `EVALUATE @mode WHEN = '...' THEN ... ELSE ... END` | Three-way branch on the `mode` string; no LLM judge needed — equality check suffices |
| Shared state dict | `@clip`, `@mode`, `@style`, `@model`, `@result` | SPL `@var` bindings replace a mutable shared-state dictionary |
| `output_budget` cap | `WITH OUTPUT BUDGET @output_budget TOKENS` | Applied identically across all three GENERATE calls |
| Model selection | `USING MODEL @model` | Single parameter fans out to any audio-capable provider at runtime |
| Error node / fallback | `EXCEPTION WHEN ModelUnavailable THEN ... END` | Catches provider failures; RETURN with `status = 'failed'` signals the caller |
| `RETURN` (non-trivial) | `RETURN @result WITH status = 'failed'` | Only in the exception path; normal path is implicit linear return |

---

### 4. Logical Functions / Prompts

**`transcribe(clip AUDIO)`**
- **Role:** Verbatim speech-to-text. Converts the raw audio into a plain-text transcript with no paraphrasing.
- **Key conventions:** Speaker changes placed on new lines when distinguishable; uncertain words wrapped in `[?]`; no editorial interpretation.

**`summarise(clip AUDIO, style TEXT)`**
- **Role:** Prose summarisation. Condenses the audio into a caller-controlled writing style (e.g., `'concise paragraph'`, `'executive brief'`).
- **Key conventions:** `{style}` slot injected from `@style`; preserves proper nouns, dates, figures, and decisions verbatim; drops filler and off-topic content.

**`key_points(clip AUDIO)`**
- **Role:** Structured meeting analysis. Extracts agenda, key points, decisions, and action items with owners.
- **Key conventions:** Output formatted as structured Markdown with four numbered sections; action items include named owners when mentioned in audio.

---

### 5. Control Flow

1. **Entry:** WORKFLOW receives `@clip` (AUDIO), `@mode`, `@style`, `@model`, `@output_budget`, `@log_dir`; logs clip path, mode, and model at INFO level.
2. **Branch:** EVALUATE inspects `@mode`:
   - `= 'transcribe'` → GENERATE via `transcribe(@clip)` → `@result`
   - `= 'key_points'` → GENERATE via `key_points(@clip)` → `@result`
   - ELSE (any other value, including `'summary'`) → GENERATE via `summarise(@clip, @style)` → `@result`
3. **Termination (happy path):** Logs output length at INFO level, returns `@result` implicitly.
4. **Termination (error path):** EXCEPTION catches `ModelUnavailable`; logs an actionable hint (API key / Ollama check); RETURN `'[ERROR] Audio model unavailable.'` WITH `status = 'failed'`.

There is no WHILE loop — this is a single-pass, single-GENERATE workflow.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Process an audio clip through a speech-capable multimodal LLM and return either a verbatim transcript, a structured key-points breakdown, or a concise prose summary, selected by a single mode parameter." --mode workflow

# Step 2 — compile to any target
spl3 splc compile audio_summary.spl --lang python/pocketflow
spl3 splc compile audio_summary.spl --lang python/langgraph
spl3 splc compile audio_summary.spl --lang go
```