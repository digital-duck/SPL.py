## Summary

`voice_dialogue` is a full audio-in / audio-out pipeline that accepts a spoken question and returns both a text answer and a synthesized speech file. It exists to enable natural voice-based interaction with any LLM by separating transcription, reasoning, and speech synthesis into discrete, swappable stages. Product teams and edge-device developers benefit by getting a clean logical specification that compiles to voice assistants running on ARM hardware, laptops, or cloud backends.

---

## Detailed Specification

### 1. Purpose

Convert a user's spoken audio question into a coherent spoken audio response by chaining automatic speech recognition, LLM reasoning, and text-to-speech synthesis.

---

### 2. High-level Description

The `voice_dialogue` WORKFLOW implements a three-stage multimodal pipeline: AUDIO → TEXT → TEXT → AUDIO. It accepts a WAV audio clip as its primary INPUT variable (`@audio_in`) along with optional TEXT inputs for conversational context, a persona string, and runtime configuration parameters (model names, TTS voice, output directories).

Stage 1 uses `CREATE FUNCTION transcribe_audio`, which instructs a multimodal LLM (defaulting to `liquid/lfm-2.5-1.2b-instruct:free` via OpenRouter) to produce a verbatim transcript of the audio, marking unclear segments with `[?]`; the result is captured via `GENERATE ... INTO @transcript`. Stage 2 uses `CREATE FUNCTION respond`, a persona-aware prompt template that injects `@transcript`, `@context`, and `@persona` into a system-style instruction that explicitly requests spoken-register output (no markdown, no bullet points); the result is captured via `GENERATE ... INTO @response` using a configurable `@llm_model`. Stage 3 (TEXT → AUDIO via TTS) is a physical side-effect delegated to `run.py` rather than expressed in the `.spl` logical spec, consistent with the DODA principle. An `EXCEPTION WHEN ModelUnavailable` handler catches provider failures and issues a `RETURN WITH status='failed'`, terminating the workflow cleanly with a sentinel error string rather than propagating a hard crash.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `voice_dialogue` pipeline | `WORKFLOW voice_dialogue` | Named, parameterized orchestration unit |
| Transcription prompt template | `CREATE FUNCTION transcribe_audio(clip AUDIO)` | AUDIO-typed parameter triggers multimodal dispatch |
| Response generation template | `CREATE FUNCTION respond(transcript, context, persona)` | Three TEXT params; persona injected via `{persona}` slot |
| ASR call | `GENERATE transcribe_audio(@audio_in) ... INTO @transcript` | Routes to `generate_multimodal()` due to AUDIO input |
| LLM reasoning call | `GENERATE respond(...) ... INTO @response` | Uses runtime-configurable `@llm_model` |
| Per-call token cap | `WITH OUTPUT BUDGET 1024 TOKENS` | Applied to both GENERATE calls |
| Model selection | `USING MODEL 'liquid/lfm-2.5-1.2b-instruct:free'` / `USING MODEL @llm_model` | Stage 1 pinned; Stage 2 parameterized |
| Shared pipeline state | `@transcript`, `@response` | SPL `@var` bindings passed between stages |
| Provider failure guard | `EXCEPTION WHEN ModelUnavailable THEN ... RETURN WITH status='failed'` | Non-trivial status drives early termination |
| TTS side-effect | Delegated to `run.py` (outside SPL) | Intentional DODA separation; no SPL construct needed |
| Observability | `LOGGING ... LEVEL INFO / ERROR` | Emitted at each stage boundary and on exception |

---

### 4. Logical Functions / Prompts

**`transcribe_audio`**
- **Role:** ASR stage — converts raw AUDIO input to plain TEXT transcript.
- **Key conventions:** Instruction-only prompt (no few-shot examples); uncertainty sentinel `[?]` for inaudible segments; output is verbatim transcript only, no commentary. Routed to a multimodal-capable model via the AUDIO-typed parameter.

**`respond`**
- **Role:** Reasoning stage — generates a contextually appropriate, voice-ready reply.
- **Key conventions:** Three injected slots: `{persona}` (system identity), `{context}` (optional background), `{transcript}` (user utterance). Explicit negative constraints against markdown and bullet points enforce spoken-register output suitable for TTS. Model is runtime-swappable via `@llm_model`.

---

### 5. Control Flow

The pipeline is strictly linear with a single error exit:

1. **Entry** — WORKFLOW binds all INPUT variables (audio file path, context, persona, model names, directories).
2. **Stage 1** — `GENERATE transcribe_audio(@audio_in) INTO @transcript` using the pinned multimodal model.
3. **Stage 2** — `GENERATE respond(@transcript, @context, @persona) INTO @response` using the configurable `@llm_model`.
4. **Stage 3** — `@response` (TEXT) is returned to the caller; TTS synthesis happens outside SPL in `run.py`.
5. **Normal exit** — `RETURN @response` (no status token; clean completion is implicit).
6. **Error exit** — `EXCEPTION WHEN ModelUnavailable` fires if either GENERATE call cannot reach its model; issues `RETURN WITH status='failed'` and an error string, terminating the workflow early.

There are no WHILE loops and no EVALUATE branches — the control graph is a straight line with one guarded early-exit path.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 1 above as text2spl input)
spl3 text2spl \
  --description "Convert a user's spoken audio question into a coherent spoken audio response by chaining automatic speech recognition, LLM reasoning, and text-to-speech synthesis." \
  --mode workflow \
  --adapter ollama -m gemma3

# Step 2 — compile to a target runtime
spl3 splc compile voice_dialogue.spl --lang python/pocketflow   # edge/ARM voice assistant
spl3 splc compile voice_dialogue.spl --lang python/langgraph    # LangGraph orchestration
spl3 splc compile voice_dialogue.spl --lang go                  # Go microservice
```