## 0. High-level Description

This workflow implements a multi-shot vibe coding ablation experiment that simulates iterative developer-LLM collaboration without any intermediate representation. Two actors alternate each shot. The **vibe_coder** (a configurable generator model — Claude, Gemini, or Qwen via OpenRouter) receives a prompt spec and synthesizes Python/PocketFlow code (`VibeCoder` GENERATE), then immediately describes what that code actually does (`Describer` GENERATE), producing `@code` and `@out_spec`. The **judge** (always GPT via OpenRouter) plays the role of the developer in current vibe-coding practice: it reviews the original spec, the generated code, and the code's self-description, then writes a refined prompt (`@next_spec`) for the next shot — exactly as a developer would rewrite their prompt after seeing the LLM's output miss the intent. The judge also records a numeric alignment score (`@score`) and brief notes (`@feedback`). On the first shot the vibe_coder receives only the original `@spec`; on subsequent shots it receives the judge's refined `@next_spec`. All outputs are persisted as named files indexed by shot number (`code-{shot_i}.md`, `out_spec-{shot_i}.md`, `score-{shot_i}.md`, `next_spec-{shot_i}.md`, `feedback-{shot_i}.md`) for manual review. After `@n_shots` iterations the convergence curve of scores quantifies how quickly each generator model approaches the original intent under GPT-simulated developer guidance, and the shot-N score is compared against the full IR pipeline's S6 score to measure the ΔS value-add of the Mermaid + SPL checkpoints.

## 1. Purpose

Establish the ΔS ablation baseline by simulating N-shot iterative vibe coding (developer-as-GPT refining the prompt, LLM generating code) across 3 generator models and 5 recipes — without using any structured IR (no Mermaid, no SPL). The convergence curve and final score are compared against the full NDD pipeline S6 scores to quantify what the S2 visual checkpoint and S3 SPL step contribute to intent preservation.

---

## 2. Two Actors

### Actor A — vibe_coder (generator model: claude / gemini / qwen via openrouter)

Simulates the LLM in a vibe-coding session. Receives a prompt and generates code.

| Step | SPL | Input | Output | File |
|------|-----|-------|--------|------|
| Generate code | `GENERATE VibeCoder(...)` | `@next_spec`, `@shot_i` | `@code` | `code-{shot_i}.md` |
| Describe code | `GENERATE Describer(...)` | `@code` | `@out_spec` | `out_spec-{shot_i}.md` |

### Actor B — judge (always GPT: openai/gpt-4o via openrouter)

Simulates the developer in a vibe-coding session. Reviews the output and writes a better prompt for the next shot.

| Step | SPL | Input | Output | File |
|------|-----|-------|--------|------|
| Score + refine | `CALL gpt_judge(...)` | `@spec`, `@code`, `@out_spec`, `@shot_i` | `@judgment` | — |
| Extract score | `CALL extract_field(...)` | `@judgment`, `"score"` | `@score` | `score-{shot_i}.md` |
| Extract next prompt | `CALL extract_field(...)` | `@judgment`, `"next_spec"` | `@next_spec` | `next_spec-{shot_i}.md` |
| Extract feedback | `CALL extract_field(...)` | `@judgment`, `"feedback"` | `@feedback` | `feedback-{shot_i}.md` |

---

## 3. Logical Functions / Prompts

### `VibeCoder(next_spec, shot_i)`
- **Role:** The LLM in a vibe-coding loop. Generates Python/PocketFlow code from the current prompt. Shot 1 receives the original `@spec`; shots 2+ receive the judge's refined `@next_spec`.
- **Output:** Complete runnable Python file using PocketFlow `Node`/`Flow` pattern.
- **Constraint:** No framework hints provided — the model infers architecture from the description alone.

### `Describer(code)`
- **Role:** Reverse-engineers a Section 0 style natural language description from the generated code, with no access to the original spec.
- **Output:** A single paragraph describing what the code does at the same abstraction level as the original Section 0.

### `gpt_judge` (CALL tool — always GPT)
- **Role:** Simulates the developer reviewing the LLM's output and rewriting the prompt. Receives the original reference spec, the generated code, and the code's self-description. Returns structured text with three fields.
- **Output format:**
  ```
  SCORE: [0-10]
  NEXT_SPEC: [rewritten prompt — a clearer version of the description that addresses what the code got wrong; this is what the developer would type for the next vibe-coding attempt]
  FEEDBACK: [one sentence explaining the primary gap between original intent and generated code]
  ```
- **Scoring rubric:** 10 = complete semantic match; ≥8 = NDD closure threshold; 6–7 = structural drift; <6 = paradigm divergence.

### `extract_field(text, field_name)` (CALL tool)
- Extracts value after `FIELD_NAME:` from structured judgment text.

---

## 4. Control Flow

```
INPUT @init_spec    TEXT   ← "## 0. High-level Description\n...\n## 1. Purpose\n..."
                              (Sections 0 and 1 only — the developer's initial vibe-coding prompt)
      @coder_model  TEXT   ← generator model ID, e.g. "anthropic/claude-sonnet-4-6"
      @judge_model  TEXT   ← judge model ID, e.g. "openai/gpt-4o"
      @n_shots      INT := 3
      @recipe       TEXT   ← e.g. "agent", "rag", "judge", "thinking", "research"

@shot_i    := 0
@next_spec := @init_spec   ← shot 1 uses the original prompt unchanged
@code      := ""
@out_spec  := ""

── WHILE @shot_i < @n_shots ─────────────────────────────────────────────────
│
│  @shot_i := @shot_i + 1
│
│  ── vibe_coder (generator model) ──────────────────────────────────────────
│  GENERATE VibeCoder(@next_spec, @shot_i) INTO @code
│  GENERATE Describer(@code)               INTO @out_spec
│  CALL write_file("code-"     + @shot_i + ".md", @code)     INTO @_;
│  CALL write_file("out_spec-" + @shot_i + ".md", @out_spec) INTO @_;
│
│  ── judge (GPT — uses @judge_model, independent of coder adapter) ─────────
│  CALL gpt_judge(@init_spec, @code, @out_spec, @shot_i, @judge_model) INTO @judgment;
│  CALL extract_field(@judgment, "score")            INTO @score;
│  CALL extract_field(@judgment, "next_spec")        INTO @next_spec;
│  CALL extract_field(@judgment, "feedback")         INTO @feedback;
│  CALL write_file("score-"     + @shot_i + ".md", @score)     INTO @_;
│  CALL write_file("next_spec-" + @shot_i + ".md", @next_spec) INTO @_;
│  CALL write_file("feedback-"  + @shot_i + ".md", @feedback)  INTO @_;
│
└─────────────────────────────────────────────────────────────────────────────

RETURN @out_spec WITH status = "complete";
```

---

## 5. File Outputs per Shot

All files written to `results/{recipe}-{model}/`:

| File | Content | Actor |
|------|---------|-------|
| `code-{shot_i}.md` | Generated Python/PocketFlow code | vibe_coder |
| `out_spec-{shot_i}.md` | Code's self-description (what it actually does) | vibe_coder |
| `score-{shot_i}.md` | Numeric alignment score 0–10 | judge |
| `next_spec-{shot_i}.md` | Judge's refined prompt for next shot | judge |
| `feedback-{shot_i}.md` | One-sentence primary gap note | judge |

---

## 6. Run Command

See `README.md` for full environment setup and per-recipe run commands.

Total: 5 recipes × 3 models × 3 shots = **45 vibe generations + 45 GPT judge calls**
