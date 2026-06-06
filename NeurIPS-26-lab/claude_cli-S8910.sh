# conda activate spl123
# S8: spl3 splc describe vibe/python_pocketflow → S8-*-3-spec.md
# S9: spl3 compare S1-*-1-spec.md S8-*-3-spec.md → S9-*-vibe-diff.md
# S10: spl3 compare S6-*-spec-diff.md S9-*-vibe-diff.md → S10-*-ablation.md  (only where S6 exists)
# Judge for S9/S10 is fixed at claude-opus-4-6 via openrouter

# ── R1-agent ──────────────────────────────────────────────────────────────────
export ADAPTER=claude_cli
export MODEL=claude
export MODEL_ID=claude-sonnet-4-6
export RECIPE=agent
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S8
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9
spl3 compare \
  $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
  --adapter openrouter --model anthropic/claude-opus-4-6 \
  -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 (S6 exists for R1 claude_cli/claude)
spl3 compare \
  $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff.md \
  $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md \
  --adapter openrouter --model anthropic/claude-opus-4-6 \
  -o $OUT/S10-$RECIPE-$ADAPTER-$MODEL-ablation.md


# ── R2-rag ────────────────────────────────────────────────────────────────────
export ADAPTER=claude_cli
export MODEL=claude
export MODEL_ID=claude-sonnet-4-6
export RECIPE=rag
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S8
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9 — NOTE: no S1 for claude_cli/claude R2; skip or provide path manually
# spl3 compare \
#   $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
#   $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
#   --adapter openrouter --model anthropic/claude-opus-4-6 \
#   -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 — skipped (no S6 for claude_cli/claude R2)


# ── R3-judge ──────────────────────────────────────────────────────────────────
export ADAPTER=claude_cli
export MODEL=claude
export MODEL_ID=claude-sonnet-4-6
export RECIPE=judge
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S8
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9 — NOTE: no S1 for claude_cli/claude R3; skip or provide path manually
# spl3 compare \
#   $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
#   $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
#   --adapter openrouter --model anthropic/claude-opus-4-6 \
#   -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 — skipped (no S6 for claude_cli/claude R3)


# ── R4-thinking ───────────────────────────────────────────────────────────────
export ADAPTER=claude_cli
export MODEL=claude
export MODEL_ID=claude-sonnet-4-6
export RECIPE=thinking
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S8
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9 — NOTE: no S1 for claude_cli/claude R4; skip or provide path manually
# spl3 compare \
#   $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
#   $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
#   --adapter openrouter --model anthropic/claude-opus-4-6 \
#   -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 — skipped (no S6 for claude_cli/claude R4)


# ── R5-research ───────────────────────────────────────────────────────────────
export ADAPTER=claude_cli
export MODEL=claude
export MODEL_ID=claude-sonnet-4-6
export RECIPE=research
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S8
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md

# S9 — NOTE: no S1 for claude_cli/claude R5; skip or provide path manually
# spl3 compare \
#   $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
#   $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
#   --adapter openrouter --model anthropic/claude-opus-4-6 \
#   -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md

# S10 — skipped (no S6 for claude_cli/claude R5)
