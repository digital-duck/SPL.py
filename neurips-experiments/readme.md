# NeurIPS Experiments — NDD Round-Trip Closure

## Hypothesis

A high-fidelity NDD (Natural-language Driven Design) pipeline should produce a Python/PocketFlow implementation whose *observable specification* is semantically indistinguishable from the specification of the original, expert-written implementation. The round-trip closure score — measured by `spl3 compare` on two independently generated specs — quantifies how much semantic information is lost or distorted across the pipeline.

---

## Evaluation Protocol

Starting point: an existing PocketFlow Python recipe written by the repo owner (not vibe-coded). Each recipe includes a `README.md` with the original functional intent; use `--include-docs` at step 1 so the LLM has that context when generating spec1. Step 5 does **not** use `--include-docs` — the reconstructed code has no README, and adding one would contaminate the round-trip measurement.

> **Command distinction:** `spl3 splc describe` operates on target/framework-specific implementations (Python, TypeScript, Go). `spl3 describe` operates on `.spl` workflow scripts.

```
Step 1   original code  →  spl3 splc describe --include-docs  →  spec1.md
Step 2   spec1.md       →  spl3 text2mmd                      →  diagram.mmd
Step 3   diagram.mmd    →  spl3 mmd2spl                       →  workflow.spl
Step 4   workflow.spl   →  spl3 splc --llm --lang python/pocketflow  →  reconstructed code
Step 5   reconstructed  →  spl3 splc describe                 →  spec2.md
Step 6   spec1.md vs spec2.md  →  spl3 compare                →  closure score (0–10)
```

**Closure score** = `spl3 compare spec1.md spec2.md --adapter claude_cli` output (Structure / Logic / Quality / Overall).

### Ceiling Baseline

Run `spl3 splc describe --include-docs` on the **original code** twice (with two different models, e.g. claude_cli and gemini_cli), then compare the two specs. This gives the "same-code similarity ceiling" — the maximum achievable score when both specs describe identical implementations. A round-trip score near the ceiling means near-lossless closure.

```
original code  →  spl3 splc describe --include-docs (model A)  →  spec_a.md
original code  →  spl3 splc describe --include-docs (model B)  →  spec_b.md
spl3 compare spec_a.md spec_b.md  →  ceiling score
```

---

## Models Under Test

All models are used for **both** spec generation (steps 1, 5) and pipeline generation (steps 2, 3, 4). The judge for `spl3 compare` (step 6) is fixed at `claude_cli / claude-opus-4-6` for consistency — Opus provides deeper reasoning for evaluation than Sonnet.

| # | Model | Adapter | Model ID |
|---|-------|---------|----------|
| 1 | Claude Sonnet 4.6 | `claude_cli` | `claude-sonnet-4-6` |
| 2 | Gemini 3 Flash | `openrouter` | `google/gemini-3-flash-preview` |
| 3 | DeepSeek v4 Flash | `openrouter` | `deepseek/deepseek-v4-flash` |
| 4 | Gemma3 (local) | `ollama` | `gemma3` |

---

## Recipes (5 PocketFlow)

| Recipe | Description |
|--------|-------------|
| `pocketflow-agent` | ReAct research agent with iterative web search |
| `pocketflow-deep-research` | Multi-step deep research workflow |
| `pocketflow-judge` | LLM-as-judge evaluation pattern |
| `pocketflow-rag` | Retrieval-augmented generation pipeline |
| `pocketflow-thinking` | Chain-of-thought / thinking loop pattern |

Source: `~/projects/wgong/PocketFlow/cookbook/`

---

## Output File Convention

All outputs are written under `neurips-experiments/<adapter>/<recipe>/targets/python_pocketflow/`:

```
spec1.md       →  <recipe>-<adapter>-<model_slug>-spec.md          (step 1)
spec2.md       →  <recipe>-<adapter>-<model_slug>-spec2.md         (step 5)
compare        →  <recipe>-compare-<model_slug>-closure.md          (step 6)
ceiling        →  <recipe>-compare-ceiling-<modelA>-vs-<modelB>.md
```

---

## Run Commands (per recipe × model)

```bash
ADAPTER="claude_cli"
MODEL="claude-sonnet-4-6"
MODEL_JUDGE="claude-opus-4-6"
RECIPE=pocketflow-agent
SRC=~/projects/wgong/PocketFlow/cookbook/$RECIPE
OUT=~/projects/digital-duck/SPL.py/neurips-experiments/$ADAPTER/$RECIPE/targets/python_pocketflow

# Step 1 — describe original code (--include-docs pulls in README.md for intent context)
spl3 splc describe $SRC --include-docs \
  --adapter $ADAPTER -m $MODEL \
  --spec-dir $OUT

# Step 2 — spec → Mermaid
spl3 text2mmd $OUT/${RECIPE}-${ADAPTER}-$MODEL-spec.md \
  --adapter $ADAPTER -m $MODEL \
  -o $OUT/${RECIPE}.mmd

# *** HUMAN CHECKPOINT: open $OUT/${RECIPE}.mmd and visually review the diagram ***
# Correct any mis-wired edges or missing nodes before proceeding.

# Step 3 — Mermaid → SPL
spl3 mmd2spl $OUT/${RECIPE}.mmd \
  --adapter $ADAPTER -m $MODEL \
  -o $OUT/${RECIPE}.spl

# Step 4 — SPL → Python/PocketFlow  (--llm: use LLM transpiler, not deterministic)
spl3 splc $OUT/${RECIPE}.spl --target python/pocketflow \
  --llm --adapter $ADAPTER -m $MODEL \
  --output $OUT/${RECIPE}_recon.py

# Step 5 — describe reconstructed code (no --include-docs: reconstructed dir has no README)
spl3 splc describe $OUT/${RECIPE}_recon.py \
  --adapter $ADAPTER -m $MODEL \
  --spec-dir $OUT

# Step 6 — compare (judge always claude_cli / opus-4-6)
spl3 compare \
  $OUT/${RECIPE}-claude_cli-claude-sonnet-4-6-spec.md \
  $OUT/${RECIPE}-claude_cli-claude-sonnet-4-6-spec2.md \
  --adapter $ADAPTER --model $MODEL_JUDGE \
  -o $OUT/${RECIPE}-compare-claude-sonnet-4-6-closure.md
```

---

## Scoring Sheet

| Recipe | Model | Structure | Logic | Quality | Overall |
|--------|-------|-----------|-------|---------|---------|
| pocketflow-agent | claude-sonnet-4-6 | | | | |
| pocketflow-agent | gemini-3.1-flash | | | | |
| pocketflow-agent | gemma3 | | | | |
| pocketflow-agent | deepseek-v3.1 | | | | |
| pocketflow-deep-research | claude-sonnet-4-6 | | | | |
| pocketflow-deep-research | gemini-3.1-flash | | | | |
| pocketflow-deep-research | gemma3 | | | | |
| pocketflow-deep-research | deepseek-v3.1 | | | | |
| pocketflow-judge | claude-sonnet-4-6 | | | | |
| pocketflow-judge | gemini-3.1-flash | | | | |
| pocketflow-judge | gemma3 | | | | |
| pocketflow-judge | deepseek-v3.1 | | | | |
| pocketflow-rag | claude-sonnet-4-6 | | | | |
| pocketflow-rag | gemini-3.1-flash | | | | |
| pocketflow-rag | gemma3 | | | | |
| pocketflow-rag | deepseek-v3.1 | | | | |
| pocketflow-thinking | claude-sonnet-4-6 | | | | |
| pocketflow-thinking | gemini-3.1-flash | | | | |
| pocketflow-thinking | gemma3 | | | | |
| pocketflow-thinking | deepseek-v3.1 | | | | |
| **Ceiling** | claude vs gemini | | | | |
| **Ceiling** | claude vs gemma3 | | | | |

---

## Notes

- `spl3 splc describe` — operates on target/framework implementations (Python/PocketFlow, TypeScript, Go). `spl3 describe` — operates on `.spl` workflow scripts. These are distinct commands; do not confuse them.
- Judge model is fixed at `claude_cli / claude-opus-4-6` across all comparisons to avoid cross-judge variance. Opus is used (not Sonnet) for deeper reasoning in evaluation. The 2026-05-01 pilot (pocketflow-agent) confirmed claude produces precise, falsifiable verdicts with named technical gaps rather than vague assessments.
- The weakest link is `text2mmd → mmd2spl`. A **human visual review of the .mmd diagram** (between steps 2 and 3) is the mitigation — check for mis-wired edges or missing nodes before proceeding. This is the only manual step in the protocol.
- `spl3 splc` uses `--llm` (LLM-assisted transpiler) rather than the deterministic transpiler, which is not yet reliable enough for novel SPL patterns.
- Gemma3-as-judge (pilot run) scored Claude 9.5 vs Gemma3 8.6; Claude-as-judge scored 9/10 vs 6/10 — cross-model judging is more discriminating. The fixed-judge design avoids this variance for the scoring sheet.
