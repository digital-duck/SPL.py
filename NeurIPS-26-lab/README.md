
# experimental protocol for NeurIPS-2026 NDD round-trip closure test

see `/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab`

## Philosophy

- **Iterative and incremental** — not 1-shot. Expect issues; log them in `notes.md`, fix with Claude Code CLI, continue.
- **Human-in-the-loop** — explicit review touchpoints to catch LLM drift before it propagates.
- **Goal**: complete the NDD round-trip closure loop across 3 models × 5 recipes.

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
    - output: S1-<recipe>-<model>-spec.md

    [Human] review spec

S2: spl3 text2mmd
    - generate Mermaid chart from Section 0 of spec
    - output: S2-<recipe>-<model>.mmd

    [Human] review workflow chart

S3: spl3 mmd2spl
    - convert Mermaid chart to SPL workflow script
    - output: S3-<recipe>-<model>.spl

    [Human] spl3 validate + spl3 run

S4: spl3 splc --target python/pocketflow --llm
    - compile .spl → pocketflow python code
    - output: S4-<recipe>-<model>.py (+ readme.md)

    [Human] validate .py with real test-cases

S5: spl3 splc describe
    - convert generated python code back to spec
    - output: S5-<recipe>-<model>-spec.md

S6: spl3 compare S1-spec.md S5-spec.md
    - semantic compare: input spec vs round-trip spec
    - output: S6-<recipe>-<model>-diff.md

    [Human] review diff; choose --mode per file type:
      --mode ged        → best for .mmd (topological)
      --mode llm,git-diff → best for .spl
      --mode llm        → best for -spec.md
```

## Pipeline: Bypass IR / Ablation (Phase 2)

```
A1: spl3 vibe
    - generate target code directly from recipe description (no .mmd/.spl IR)
    - output: A1-<recipe>-<model>.py

    [Human] validate .py with same test-cases as S4

A2: spl3 splc describe
    - convert vibe-generated python to spec
    - output: A2-<recipe>-<model>-spec.md

A3: spl3 compare S1-spec.md A2-spec.md
    - compare full-pipeline spec vs bypass spec
    - output: A3-<recipe>-<model>-ablation-diff.md

    [Human] compare A3 vs S6 to quantify IR value-add
```

## Issue Log

Issues encountered during experiments are logged in `notes.md`.
Fixed iteratively with Claude Code CLI.

