# R1-agent / openrouter — Ablation: One-Shot Vibe Coding

One-shot vibe coding test for R1-agent across 3 openrouter models.
The same enhanced prompt (`A1-agent-openrouter-init-spec.md`) is used for all three
models; only `--model` and the output filename change.

Compare generated files against the claude_cli reference:
`../claude_cli/A1-agent-claude_cli-vibe.py`

---

## Environment

```bash
conda activate spl123
# export OPENROUTER_API_KEY=<your-key>

export INIT_SPEC=/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/ablations/R1-agent/tests/openrouter/A1-agent-openrouter-init-spec.md
export OUT_DIR=/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/ablations/R1-agent/tests/openrouter
```

---

## Run — one command per model

```bash
# Claude Sonnet 4.6
spl3 vibe \
  --description $INIT_SPEC \
  --adapter openrouter --model anthropic/claude-sonnet-4-6 \
  -o $OUT_DIR/claude/A1-agent-openrouter-claude-vibe.py

# Gemini 3 Flash
spl3 vibe \
  --description $INIT_SPEC \
  --adapter openrouter --model google/gemini-3-flash-preview \
  -o $OUT_DIR/gemini/A1-agent-openrouter-gemini-vibe.py

# Qwen 3.6 Plus
spl3 vibe \
  --description $INIT_SPEC \
  --adapter openrouter --model qwen/qwen3.6-plus \
  -o $OUT_DIR/qwen/A1-agent-openrouter-qwen-vibe.py
```

---

## Output files

| Model | Output file |
|-------|------------|
| Claude Sonnet 4.6 | `claude/A1-agent-openrouter-claude-vibe.py` |
| Gemini 3 Flash | `gemini/A1-agent-openrouter-gemini-vibe.py` |
| Qwen 3.6 Plus | `qwen/A1-agent-openrouter-qwen-vibe.py` |

---

## Next step — describe and score each output

```bash
# Describe each vibe-coded file (A2 step)
for MODEL in claude gemini qwen; do
  spl3 splc describe $OUT_DIR/$MODEL/A1-agent-openrouter-${MODEL}-vibe.py \
    --adapter openrouter \
    -o $OUT_DIR/$MODEL/A2-agent-openrouter-${MODEL}-vibe-spec.md
done

# Compare against original S1 spec (A3 step) — judge fixed at claude-opus-4-6
S1_SPEC=/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S1-agent-claude_cli-claude-1-spec.md

for MODEL in claude gemini qwen; do
  spl3 compare \
    $S1_SPEC \
    $OUT_DIR/$MODEL/A2-agent-openrouter-${MODEL}-vibe-spec.md \
    --adapter claude_cli --model claude-opus-4-6 \
    -o $OUT_DIR/$MODEL/A3-agent-openrouter-${MODEL}-vibe-diff.md
done
```
