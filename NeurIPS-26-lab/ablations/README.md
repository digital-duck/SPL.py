# Ablation: Multi-Shot Vibe Coding — NeurIPS-26 Phase 2

Ablation experiment for the NeurIPS-26 paper. Tests whether iterative vibe coding
(developer-as-GPT refining prompts, LLM generating code) can converge to the same
intent fidelity as the full SPL IR pipeline (Mermaid + SPL checkpoints).

---

## Hypothesis

ΔS_ablation = S6_pipeline − A3_vibe(shot_N) > 0

If positive: the S2 Mermaid checkpoint and S3 SPL step add measurable intent
preservation that iterative prompt refinement alone cannot recover.

---

## Experiment Design

- **5 recipes**: agent, rag, judge, thinking, research (R1–R5)
- **3 coder models**: Claude Sonnet, Gemini Flash, Qwen 3.6 Plus (all via openrouter)
- **1 judge model**: GPT-4o via openrouter (neutral, independent of coder)
- **3 shots** per (recipe × coder model) = 45 vibe generations + 45 GPT judge calls
- **Input**: Sections 0–1 of the S1 spec only (the developer's initial natural-language prompt)

---

## Pipeline (mirrors S1→S6, but uses `spl3 vibe` instead of `spl3 text2mmd` + `spl3 mmd2spl`)

```
S1-ablation-1-spec.md    ← spec for this workflow (already written)
      ↓ spl3 text2mmd
S2-ablation-1.mmd        ← Mermaid diagram   [human review]
      ↓ spl3 mmd2spl
S3-ablation-1.spl        ← SPL script        [spl3 validate]
      ↓ spl3 run
results/{recipe}-{model}/
  code-{1,2,3}.md        ← generated code per shot
  out_spec-{1,2,3}.md    ← code's self-description per shot
  score-{1,2,3}.md       ← GPT alignment score per shot
  next_spec-{1,2,3}.md   ← GPT's refined prompt for next shot
  feedback-{1,2,3}.md    ← GPT's one-sentence gap note per shot
```

---

## S2 — Generate Mermaid diagram

```bash
cd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/ablation
conda activate spl123

spl3 text2mmd S1-ablation-1-spec.md \
  --adapter claude_cli \
  -o S2-ablation-1.mmd
```

**⚠️ HUMAN CHECKPOINT** — open `S2-ablation-1.mmd` and verify:
- Two actor subgraphs (vibe_coder, judge) are present and correctly bounded
- Shot loop back-edge is present
- `@init_spec → @next_spec` handoff across loop iterations is visible
- File-write nodes appear after each actor's outputs

---

## S3 — Generate SPL script

```bash
spl3 mmd2spl S2-ablation-1.mmd \
  --adapter claude_cli \
  -o S3-ablation-1.spl

spl3 validate S3-ablation-1.spl
```

---

## Environment

```bash
conda activate spl123
export OPENROUTER_API_KEY=<your-key>    # required for all 3 coder models + GPT judge

# Coder model configs
export CLAUDE_MODEL=anthropic/claude-sonnet-4-6
export GEMINI_MODEL=google/gemini-3-flash-preview
export QWEN_MODEL=qwen/qwen3.6-plus

# Judge — always GPT, never the coder model
export JUDGE_MODEL=openai/gpt-4o

# Common
export ADAPTER=openrouter
```

---

## Extract Section 0+1 from S1 spec

The input to each run is only Sections 0 and 1 of the recipe's S1 spec
(the developer's initial natural-language prompt — not the full technical spec).

```bash
# Helper: extract "## 0." and "## 1." sections from a spec file
python3 -c "
import sys, re
text = open(sys.argv[1]).read()
m = re.search(r'(## 0\..*?)(?=^## [2-9]\.|\Z)', text, re.S | re.M)
m1 = re.search(r'(## 1\..*?)(?=^---|\n## [2-9]\.|\Z)', text, re.S | re.M)
print((m.group(1) if m else '') + '\n' + (m1.group(1) if m1 else ''))
" \$SPEC_FILE
```

Or use the provided helper:

```bash
INIT_SPEC=$(python3 extract_sec0.py \$SPEC_FILE)
```

---

## Run — per recipe × coder model

Set `RECIPE`, `CODER_MODEL`, and `SPEC_FILE`, then run:

```bash
# ── R1: agent ────────────────────────────────────────────────────────────────
export RECIPE=agent
export SPEC_FILE=../R1-agent/tests/claude_cli/claude/S1-agent-claude_cli-claude-1-spec.md

# Claude coder
export CODER_MODEL=$CLAUDE_MODEL
mkdir -p results/${RECIPE}-claude
spl3 vibe \
  --description "$INIT_SPEC" \
  --adapter $ADAPTER --model $CODER_MODEL \
  --tools tools.py \
  --param coder_model=$CODER_MODEL \
  --param judge_model=$JUDGE_MODEL \
  --param init_spec="$INIT_SPEC" \
  --param n_shots=3 \
  --param recipe=$RECIPE \
  -o results/${RECIPE}-claude/vibe-$(date +%Y%m%d_%H%M%S).py \
  2>&1 | tee results/${RECIPE}-claude/run-$(date +%Y%m%d_%H%M%S).log

# Gemini coder
export CODER_MODEL=$GEMINI_MODEL
mkdir -p results/${RECIPE}-gemini
spl3 vibe \
  --description "$INIT_SPEC" \
  --adapter $ADAPTER --model $CODER_MODEL \
  --tools tools.py \
  --param coder_model=$CODER_MODEL \
  --param judge_model=$JUDGE_MODEL \
  --param init_spec="$INIT_SPEC" \
  --param n_shots=3 \
  --param recipe=$RECIPE \
  -o results/${RECIPE}-gemini/vibe-$(date +%Y%m%d_%H%M%S).py \
  2>&1 | tee results/${RECIPE}-gemini/run-$(date +%Y%m%d_%H%M%S).log

# Qwen coder
export CODER_MODEL=$QWEN_MODEL
mkdir -p results/${RECIPE}-qwen
spl3 vibe \
  --description "$INIT_SPEC" \
  --adapter $ADAPTER --model $CODER_MODEL \
  --tools tools.py \
  --param coder_model=$CODER_MODEL \
  --param judge_model=$JUDGE_MODEL \
  --param init_spec="$INIT_SPEC" \
  --param n_shots=3 \
  --param recipe=$RECIPE \
  -o results/${RECIPE}-qwen/vibe-$(date +%Y%m%d_%H%M%S).py \
  2>&1 | tee results/${RECIPE}-qwen/run-$(date +%Y%m%d_%H%M%S).log
```

Repeat with `RECIPE` set to `rag`, `judge`, `thinking`, `research` and corresponding `SPEC_FILE`.

---

## Recipe → SPEC_FILE mapping

| RECIPE | SPEC_FILE |
|--------|-----------|
| agent | `../R1-agent/tests/claude_cli/claude/S1-agent-claude_cli-claude-1-spec.md` |
| rag | `../R2-rag/tests/claude_cli/sonnet/S1-rag-claude_cli-sonnet-1-spec.md` |
| judge | `../R3-judge/tests/claude_cli/sonnet/S1-judge-claude_cli-sonnet-1-spec.md` |
| thinking | `../R4-thinking/tests/claude_cli/sonnet/S1-thinking-claude_cli-sonnet-1-spec.md` |
| research | `../R5-research/tests/claude_cli/sonnet/S1-research-claude_cli-sonnet-1-spec.md` |

---

## Output files per shot

All written to `results/{recipe}-{model}/`:

| File | Content |
|------|---------|
| `code-1.md` … `code-3.md` | Generated Python/PocketFlow code |
| `out_spec-1.md` … `out_spec-3.md` | Code's self-description |
| `score-1.md` … `score-3.md` | GPT alignment score (0–10) |
| `next_spec-1.md` … `next_spec-3.md` | GPT's refined prompt for next shot |
| `feedback-1.md` … `feedback-3.md` | GPT's one-sentence gap note |

---

## Convergence analysis (post-run)

Compare `score-{1,2,3}.md` across shots and models.
Compare `score-3.md` against the full-pipeline S6 score for the same recipe.

ΔS = S6 − score-3  →  positive means IR pipeline preserves more intent than vibe + GPT guidance.

Results feed into §7.10 Ablation section of `neurips26-beyond-vibe-coding-v0.4.3.md`.
