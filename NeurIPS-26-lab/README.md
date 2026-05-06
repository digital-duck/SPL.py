
# experimental protocol for NeurIPS-2026 NDD round-trip closure test

see `/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab`

## Philosophy

- **Iterative and incremental** — not 1-shot. Expect issues; log them in `notes.md`, fix with Claude Code CLI, continue.
- **Human-in-the-loop** — explicit checkpoints at every stage where LLM output must be validated before it propagates to the next step.
- **Goal**: complete the NDD round-trip closure loop across 3 models × 5 recipes.

## Human Checkpoint Protocol

Every `[Human Checkpoint]` in this experiment follows the same three-step protocol — no exceptions:

```
1. REVIEW   — inspect the generated artifact (spec, diagram, .spl, .py, folder)
2. RUN      — execute / test the artifact with real inputs; work with AI assistant
              (Claude Code) to diagnose and fix all issues until the artifact is working
3. DOCUMENT — record every issue and its fix in $OUT/notes.md before proceeding
```

A checkpoint is only complete when the artifact passes step 2. Proceeding with a broken artifact causes LLM drift to compound silently through downstream steps.

## Experiment Plan

**Phase 1 (today):** 5 recipes × 3 models = **15 runs** via the full IR pipeline (S1→S6).

**Phase 2 (if time permits):** Ablation study — bypass the `.mmd` + `.spl` IR steps using `spl3 vibe` (text → target code directly), compare output quality against the full pipeline. This tests whether the intermediate representations add value.

| Phase | Pipeline | Steps | Hypothesis |
|-------|----------|-------|------------|
| 1 | Full IR | S1→S2→S3→S4→S5→S6 | IR steps improve round-trip fidelity |
| 2 (ablation) | Bypass IR | `spl3 vibe` (text→code) | Measure quality loss without .mmd/.spl |

## Model Selection

After initial experiments across gpt, deepseek, glm, gemma3, qwen, and gemini families,
**3 models** selected based on .spl code generation quality (ranked):

| Rank | ADAPTER | MODEL_ID | Alias | Assessment |
|------|---------|----------|-------|------------|
| 1 | `claude_cli`  | `claude-sonnet-4-6`             | `sonnet` | Strongest overall quality |
| 2 | `openrouter`  | `qwen/qwen3.6-plus`             | `qwen`   | Very good .spl quality |
| 3 | `openrouter`  | `google/gemini-3-flash-preview` | `gemini` | Reasonable quality; fast |

Models eliminated: gemma3 (not worthy), deepseek, gpt, glm — quality issues in generated .spl scripts.

If time permits, 1-2 additional models may be added (e.g. `qwen/qwen3.6-max-preview` or `anthropic/claude-opus-4.6`).

<details>
<summary>Full candidate model list (archive)</summary>

| ADAPTER | MODEL_ID |
|---------|----------|
| `ollama`     | `gemma3` |
| `openrouter` | `deepseek/deepseek-v4-flash` |
| `openrouter` | `anthropic/claude-sonnet-4.6` |
| `openrouter` | `anthropic/claude-opus-4.6` |
| `openrouter` | `openai/gpt-5.4` |
| `openrouter` | `qwen/qwen3.6-flash` |
| `openrouter` | `qwen/qwen3.6-35b-a3b` |
| `openrouter` | `qwen/qwen3.6-max-preview` |
| `openrouter` | `qwen/qwen3.6-27b` |
| `openrouter` | `z-ai/glm-5.1` |

</details>

## Recipes

5 Recipes:
```
R1: agent
R2: rag
R3: judge
R4: thinking
R5: research
```

stored in env var `RECIPE`. Sub-folders already created under each recipe dir:
```bash
mkdir -p src tests/claude_cli/sonnet \
    tests/openrouter/qwen tests/openrouter/gemini
```

## LLM Adapters

```
ADAPTER=claude_cli   MODEL_ID=claude-sonnet-4-6
ADAPTER=openrouter   MODEL_ID=qwen/qwen3.6-plus
ADAPTER=openrouter   MODEL_ID=google/gemini-3-flash-preview
```

see all available models in `shortlist-models.md`

## Pipeline: Full IR path (Phase 1)

7 steps with Human review touchpoints.

```
S1: spl3 splc describe
    - convert original pocketflow recipe to spec (--include-docs)
    - output: S1-<recipe>-<adapter>-<model>-1-spec.md

    [Human Checkpoint] (1) Review spec for completeness and fidelity to original code
                       (2) Re-run with stronger model or --include-docs if spec is thin
                       (3) Document in notes.md

S2: spl3 text2mmd
    - generate Mermaid chart from spec
    - output: S2-<recipe>-<adapter>-<model>.mmd

    [Human Checkpoint] (1) Review diagram: nodes, edges, loops, back-edges
                       (2) Fix topology errors directly in .mmd; re-run if diagram is broken
                       (3) Document in notes.md

S3: spl3 mmd2spl
    - convert Mermaid chart to SPL workflow script
    - output: S3-<recipe>-<adapter>-<model>.spl

    [Human Checkpoint] (1) Review .spl; run spl3 validate
                       (2) Run spl3 run with real inputs; work with AI to fix syntax/logic errors
                       (3) Document in notes.md

S4: spl3 splc compile --target python/pocketflow --llm
    - compile .spl → pocketflow python code
    - output: S4-<recipe>-<adapter>-<model>.py (+ readme.md)

    [Human Checkpoint] (1) Review generated .py; check imports and node wiring
                       (2) Run with real test inputs; work with AI to fix code errors until working
                       (3) Document in notes.md

S5: spl3 splc describe
    - convert generated python code back to spec
    - output: S5-<recipe>-<adapter>-<model>-2-spec.md
    - (automated — no checkpoint; quality depends on S4 being working)

S6: spl3 compare S1-1-spec.md S5-2-spec.md
    - semantic compare: original spec vs round-trip spec (judge: claude-opus-4-6)
    - output: S6-<recipe>-<adapter>-<model>-spec-diff.md

    [Human Checkpoint] (1) Review S6 diff report and score
                       (2) Trace any low scores back to S2 diagram or S3 SPL ambiguities
                       (3) Document findings in notes.md
```

## Pipeline: Ablation (Phase 2 — S7→S8→S9→S10)

Four additional steps appended to the Phase 1 pipeline. Same environment variables (`$OUT`, `$RECIPE`, `$ADAPTER`, `$MODEL`, `$MODEL_ID`).

| Phase | Pipeline | Steps | Key output |
|-------|----------|-------|------------|
| 1 | Full IR | S1→S2→S3→S4→S5→S6 | `S6-...-spec-diff.md` |
| 2 | Ablation (bypass IR) | S7→S8→S9→S10 | `S10-...-ablation.md` |

```
S7: spl3 vibe
    - generate code directly from S1 spec (bypass Mermaid + SPL IR)
    - output folder: vibe/python_pocketflow/  (model may generate .py, README, test data)

    [Human Checkpoint] (1) Review vibe/python_pocketflow/ — model may generate .py, README, test data
                       (2) Run generated code with same test inputs used in S4; work with AI to fix
                       (3) Document in notes.md

S8: spl3 splc describe
    - describe vibe-generated folder (same pattern as S1 which describes $SRC folder)
    - output: S8-<recipe>-<adapter>-<model>-3-spec.md
    - (automated — no checkpoint; quality depends on S7 being working)

S9: spl3 compare S1-1-spec.md S8-3-spec.md
    - compare original spec vs vibe spec (judge fixed at claude-opus-4-6)
    - output: S9-<recipe>-<adapter>-<model>-vibe-diff.md
    - (automated — no checkpoint)

S10: spl3 compare S6-spec-diff.md S9-vibe-diff.md
    - meta-comparison: full IR diff vs vibe diff
    - judge identifies ΔIR = S6 score − S9 score and qualitative IR value-add
    - output: S10-<recipe>-<adapter>-<model>-ablation.md

    [Human Checkpoint] (1) Review S10 ablation report: S6 score, S9 score, ΔIR commentary
                       (2) Verify ΔIR sign and magnitude are consistent with qualitative findings
                       (3) Document in notes.md; aggregate across all 15 runs → NeurIPS ablation table
```

## Issue Log

Issues encountered during experiments are logged in `notes.md`.
Fixed iteratively with Claude Code CLI.

