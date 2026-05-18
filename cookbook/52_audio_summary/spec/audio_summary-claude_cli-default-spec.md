## Summary

This workflow transcribes, summarizes, or extracts key points from an audio clip using a speech-capable multimodal language model (Liquid AI LFM-2.5). It exists to give teams a single, configurable entry point for audio intelligence—replacing manual note-taking after meetings or calls. Product managers, analysts, and developers who need structured insight from recorded audio benefit most.

---

## Detailed Specification

### 1. Purpose

Process an audio clip through a speech-capable LLM to produce a verbatim transcript, a prose summary, or a structured set of key points and action items, depending on a caller-supplied mode.

---

### 2. High-level Description

The WORKFLOW `audio_summary` accepts an audio file path, an operating mode, a summary style, a model identifier, an output token budget, and a log directory as inputs. It logs the incoming parameters, then uses a single EVALUATE branch to route execution: when `@mode` equals `transcribe`, it invokes the GENERATE function `transcribe` to produce a verbatim, speaker-aware transcript; when `@mode` equals `key_points`, it invokes the GENERATE function `key_points` to produce structured Markdown covering agenda, decisions, and action items; in all other cases (the default being `summary`), it invokes the GENERATE function `summarise` with a caller-controlled `@style` string to produce a concise prose summary. All three GENERATE calls target the same model (`@model`, defaulting to Liquid AI LFM-2.5) and respect a shared `@output_budget` token ceiling. After the EVALUATE block resolves, a second log entry records the output length before the workflow RETURNs `@result`. An EXCEPTION handler catches `ModelUnavailable` errors—most likely caused by a missing `OPENROUTER_API_KEY` or an offline Ollama instance—logs an error message, and RETURNs a sentinel error string with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW audio_summary` | `WORKFLOW` | Named entry point; declares typed INPUTs and a single TEXT OUTPUT |
| `CREATE FUNCTION transcribe` | `CREATE FUNCTION` | Prompt template for verbatim speech-to-text; takes `clip AUDIO` |
| `CREATE FUNCTION summarise` | `CREATE FUNCTION` | Prompt template for prose summary; takes `clip AUDIO` + `style TEXT` |
| `CREATE FUNCTION key_points` | `CREATE FUNCTION` | Prompt template for structured Markdown extraction; takes `clip AUDIO` |
| `GENERATE transcribe(@clip) INTO @result` | `GENERATE` | Multimodal LLM call; result stored in shared state variable `@result` |
| `GENERATE key_points(@clip) INTO @result` | `GENERATE` | Same pattern; branches based on EVALUATE |
| `GENERATE summarise(@clip, @style) INTO @result` | `GENERATE` | Passes two params including the style hint |
| `EVALUATE @mode WHEN = '...' THEN ... ELSE ... END` | `EVALUATE` | Mode-dispatch branch; three arms: `transcribe`, `key_points`, else `summary` |
| `@clip`, `@result`, `@mode`, `@style`, `@model` | Shared state `@vars` | Workflow-scoped variables; `@result` is written by every GENERATE branch |
| `WITH OUTPUT BUDGET @output_budget TOKENS` | GENERATE option | Caps token generation; controlled by caller |
| `USING MODEL @model` | GENERATE option | Model is parameterized, not hard-coded |
| `EXCEPTION WHEN ModelUnavailable THEN ... RETURN ... WITH status='failed'` | `EXCEPTION` + `RETURN WITH` | Non-trivial status token `'failed'` signals downstream callers of hard failure |
| `LOGGING ... LEVEL INFO / ERROR` | `LOGGING` | Structured log entries at workflow entry and exit, and in exception handler |

---

### 4. Logical Functions / Prompts

**`transcribe`**
- **Role:** Converts raw audio into a verbatim text transcript.
- **Key conventions:** Instructs the model to act as a "speech transcription engine"; requests plain text output; mandates speaker turn separation via new lines when distinguishable; uses `[?]` as the sentinel token for uncertain words. No scoring or JSON required.

**`summarise`**
- **Role:** Produces a concise, readable prose summary of the audio content.
- **Key conventions:** Takes a `{style}` parameter slot (e.g., `"concise paragraph"`, `"bullet list"`) that the caller controls at runtime, making the prompt tone and format configurable without rewriting the function. Instructs the model to preserve names, dates, figures, and decisions verbatim while omitting filler. No sentinel tokens or structured output format enforced.

**`key_points`**
- **Role:** Extracts structured meeting intelligence: main topic, key points, decisions, and action items with owners.
- **Key conventions:** Numbered extraction schema hard-coded in the prompt (items 1–4); output format is structured Markdown. Designed for meeting recordings where action tracking matters. No scoring or loop-back required.

---

### 5. Control Flow

1. **Entry:** Workflow begins by logging clip path, mode, and model at `INFO` level.
2. **Branch (EVALUATE):** `@mode` is evaluated against three cases:
   - `= 'transcribe'` → GENERATE `transcribe(@clip)` INTO `@result`
   - `= 'key_points'` → GENERATE `key_points(@clip)` INTO `@result`
   - `ELSE` (including the default `'summary'`) → GENERATE `summarise(@clip, @style)` INTO `@result`
3. **No loop:** There is no WHILE construct; execution is strictly linear within each branch.
4. **Exit:** After the EVALUATE block, output length is logged at `INFO` and `@result` is returned.
5. **Exception path:** If `ModelUnavailable` is raised at any point, execution jumps to the EXCEPTION handler, which logs at `ERROR` level and terminates with `RETURN ... WITH status='failed'`, signaling failure to any caller inspecting the status token.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Process an audio clip through a speech-capable LLM to produce a verbatim transcript, a prose summary, or a structured set of key points and action items, depending on a caller-supplied mode." --mode workflow

# Step 2 — compile to any target
spl3 splc compile audio_summary.spl --lang python/pocketflow
spl3 splc compile audio_summary.spl --lang python/langgraph
spl3 splc compile audio_summary.spl --lang go
```