## Summary

This workflow implements a full audio-in / audio-out voice dialogue pipeline: it accepts a spoken question as an audio file, transcribes it to text using a lightweight on-device model, generates a spoken-natural text response through a configurable LLM, and returns the text for a downstream TTS stage to render as audio. It exists to enable an edge voice assistant that runs on ARM hardware or a laptop without cloud round-trips for every stage. Developers building offline or low-latency voice interfaces are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Convert a spoken audio question into a natural-language text response, optimized for subsequent text-to-speech playback, by chaining a transcription model with a persona-aware response model in a single linear workflow.

---

### 2. High-level Description

The `voice_dialogue` WORKFLOW implements a three-stage linear pipeline with no loops or conditional branches on the happy path. In the first stage, CREATE FUNCTION `transcribe_audio` provides a minimalist prompt template that instructs the model to return only the verbatim transcript and to mark uncertain audio segments with `[?]`; a GENERATE call executes this against the `liquid/lfm-2.5-1.2b-instruct:free` model (LFM-2.5 via OpenRouter), with a 1024-token output budget, storing the result in `@transcript`. In the second stage, CREATE FUNCTION `respond` provides a persona-injected prompt template that accepts `{transcript}`, `{context}`, and `{persona}` slots, explicitly instructs the model to avoid markdown and bullet points because the output will be read aloud, and targets a configurable model (defaulting to `gemma4:e4b`) via GENERATE into `@response`. The third stage — synthesizing `@response` to audio via OpenAI TTS or espeak — is a side-effect delegated entirely to the external `run.py` runner and is outside the SPL boundary; the workflow simply returns `@response` as its TEXT output. Multi-model design is intentional: LFM-2.5 is chosen for efficient audio transcription at the edge, while the response LLM is runtime-configurable to support swapping models without changing the workflow. An EXCEPTION handler catches `ModelUnavailable`, emits an error log, and terminates with `status = 'failed'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `WORKFLOW voice_dialogue` | Declares the named pipeline; inputs include typed defaults for audio path, persona, model names, and output directories |
| `CREATE FUNCTION` | `transcribe_audio(clip AUDIO)` | Prompt template: verbatim transcript with `[?]` for uncertain audio; returns TEXT |
| `CREATE FUNCTION` | `respond(transcript, context, persona)` | Prompt template: persona slot, context slot, spoken-language constraint; returns TEXT |
| `GENERATE … INTO @var` | `GENERATE transcribe_audio(@audio_in) … INTO @transcript` | LFM-2.5-1.2b-instruct:free; 1024-token budget; AUDIO→TEXT |
| `GENERATE … INTO @var` | `GENERATE respond(@transcript, @context, @persona) … INTO @response` | Model taken from `@llm_model` input; 1024-token budget; TEXT→TEXT |
| Shared state (`@var`) | `@transcript`, `@response` | Pipeline variables threaded between GENERATE calls |
| `EXCEPTION WHEN … THEN` | `WHEN ModelUnavailable THEN` | Catches unavailable model; logs error; terminates early |
| `RETURN … WITH status=` | `RETURN '[ERROR]…' WITH status='failed'` | Non-trivial: only appears in the exception handler to signal failure to the caller |
| `LOGGING` | Multiple `LOGGING … LEVEL INFO/ERROR` | Emits structured log lines at each stage boundary; error-level in exception handler |

---

### 4. Logical Functions / Prompts

**`transcribe_audio`**
- **Role:** Stage 1 — converts raw audio input to a clean text transcript.
- **Key prompt conventions:** Minimalist directive ("Return only the verbatim transcript"). Uses the sentinel token `[?]` to mark inaudible or ambiguous audio segments, enabling downstream handling of low-confidence text. No additional formatting instructions; output must be bare text.

**`respond`**
- **Role:** Stage 2 — generates the assistant's reply as natural spoken prose.
- **Key prompt conventions:** Three `{param}` slots: `{persona}` (controls voice and character), `{context}` (optional grounding information), `{transcript}` (the user's transcribed question). Explicit anti-markdown instruction ("avoid bullet points, markdown, or complex formatting") is a critical TTS-compatibility constraint — output is pipe-destined to a speech synthesizer. Tone guidance: helpful, concise, conversational.

---

### 5. Control Flow

Execution proceeds linearly through three stages with no looping or branching on the happy path:

1. **Transcription** — `GENERATE transcribe_audio(@audio_in)` executes against LFM-2.5 and writes to `@transcript`.
2. **Response generation** — `GENERATE respond(@transcript, @context, @persona)` executes against the configurable `@llm_model` and writes to `@response`.
3. **Return** — `@response` is returned as TEXT; TTS rendering is a side-effect outside the SPL boundary, performed by `run.py`.

The only non-linear path is the `EXCEPTION WHEN ModelUnavailable` handler, which short-circuits both GENERATE stages, logs an error, and issues `RETURN … WITH status='failed'` to signal failure to the caller. There are no WHILE loops and no EVALUATE branches.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Convert a spoken audio question into a natural-language text response, optimized for subsequent text-to-speech playback, by chaining a transcription model with a persona-aware response model in a single linear workflow." --mode workflow

# Step 2 — compile to any target
spl3 splc compile voice_dialogue.spl --lang python/liquid      # edge ARM / laptop (original target)
spl3 splc compile voice_dialogue.spl --lang python/pocketflow
spl3 splc compile voice_dialogue.spl --lang python/langgraph
spl3 splc compile voice_dialogue.spl --lang go
```