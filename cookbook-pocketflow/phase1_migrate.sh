#!/usr/bin/env bash
# Phase 1 migration — Tier 1 remaining recipes (001, 002, 003, 006, 008)
#
# Runs fully automated: S1 (splc describe) → S2 (text2mmd) → S3 (mmd2spl).
# No human checkpoints. Review generated artifacts afterward:
#   spl3 validate cookbook-pocketflow/<NNN_name>/<name>.spl
#   spl3 run     cookbook-pocketflow/<NNN_name>/<name>.spl ...
#
# Usage:
#   conda activate spl123
#   cd ~/projects/digital-duck/SPL.py
#   bash cookbook-pocketflow/phase1_migrate.sh
#
#   # Override adapter/model:
#   ADAPTER=openrouter MODEL_ID=qwen/qwen3.6-plus bash cookbook-pocketflow/phase1_migrate.sh

set -uo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

ADAPTER="${ADAPTER:-claude_cli}"
MODEL_ID="${MODEL_ID:-claude-sonnet-4-6}"
MODEL="${MODEL_ID##*/}"   # strip adapter prefix for filenames (e.g. qwen/qwen3.6-plus → qwen3.6-plus)

SPL_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # ~/projects/digital-duck/SPL.py
PF_BASE="${PF_BASE:-$HOME/projects/wgong/PocketFlow/cookbook}"
CB="$SPL_DIR/cookbook-pocketflow"
LOG_DIR="$CB/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP="$(date +%Y%m%dT%H%M%S)"
SUMMARY_LOG="$LOG_DIR/phase1-$TIMESTAMP.log"

# ── Recipe table: "NUM:NAME:PF_SUBDIR:DIFFICULTY" ───────────────────────────

RECIPES=(
  "001:chat:pocketflow-chat:☆☆☆"
  "002:structured_output:pocketflow-structured-output:☆☆☆"
  "003:workflow:pocketflow-workflow:☆☆☆"
  "006:map_reduce:pocketflow-map-reduce:☆☆☆"
  "008:chat_guardrail:pocketflow-chat-guardrail:☆☆☆"
)

# ── Helpers ──────────────────────────────────────────────────────────────────

log() { echo "$*" | tee -a "$SUMMARY_LOG"; }
step() { log ""; log "  [$RECIPE] $*"; }
ok()   { log "  ✓ $*"; }
fail() { log "  ✗ $*"; }

run_step() {
  local label="$1"; shift
  local logfile="$1"; shift
  if "$@" >> "$logfile" 2>&1; then
    ok "$label"
    return 0
  else
    fail "$label (exit $?)"
    log "    see $logfile"
    return 1
  fi
}

write_readme() {
  local dest="$1" num="$2" name="$3" pf_sub="$4" diff="$5"
  local spl_name="${name}.spl"
  cat > "$dest/README.md" <<EOF
# ${num} — ${name//_/ }  *(migrated from PocketFlow)*

**Source:** [${pf_sub}](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/${pf_sub})
**Difficulty:** ${diff}
**Migrated by:** phase1_migrate.sh — adapter=${ADAPTER} model=${MODEL_ID}

## Run

\`\`\`bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/${num}_${name}/${spl_name} \\
    --tools cookbook/tools/ \\
    --llm ${ADAPTER}:${MODEL_ID}
\`\`\`

## Migrate artifacts

\`\`\`
migrate/
├── S1-${name}-${MODEL}-spec.md   # splc describe output
├── S2-${name}-${MODEL}.mmd       # text2mmd Mermaid diagram
└── S3-${name}-${MODEL}.spl       # raw mmd2spl output (= ${spl_name})
\`\`\`

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Phase-1 recipes only wrap call_llm in utils.py, so no tools.spl needed.

> TODO: enrich this README — describe SPL pattern, key constructs, tool dependencies.
EOF
}

# ── Main loop ────────────────────────────────────────────────────────────────

log "========================================================"
log "  Phase 1 migration — $(date)"
log "  adapter : $ADAPTER"
log "  model   : $MODEL_ID"
log "  spl_dir : $SPL_DIR"
log "  pf_base : $PF_BASE"
log "  summary : $SUMMARY_LOG"
log "========================================================"

PASS=0
FAIL=0
FAILED_RECIPES=()

for ENTRY in "${RECIPES[@]}"; do
  IFS=':' read -r NUM NAME PF_SUB DIFF <<< "$ENTRY"
  RECIPE="${NUM}_${NAME}"
  SRC="$PF_BASE/$PF_SUB"
  DEST="$CB/$RECIPE"
  OUT="$DEST/migrate"
  RECIPE_LOG="$LOG_DIR/${RECIPE}-$TIMESTAMP.log"

  log ""
  log "── $RECIPE ──────────────────────────────────────────"

  # Guard: PocketFlow source must exist
  if [[ ! -d "$SRC" ]]; then
    fail "source not found: $SRC — skipping"
    FAIL=$((FAIL + 1))
    FAILED_RECIPES+=("$RECIPE (source missing)")
    continue
  fi

  mkdir -p "$OUT"

  S1="$OUT/S1-${NAME}-${MODEL}-spec.md"
  S2="$OUT/S2-${NAME}-${MODEL}.mmd"
  S3="$OUT/S3-${NAME}-${MODEL}.spl"
  CANONICAL="$DEST/${NAME}.spl"

  RECIPE_OK=true

  # S1 — describe Python source
  step "S1: splc describe → spec"
  run_step "S1 splc describe" "$RECIPE_LOG" \
    spl3 splc describe "$SRC" \
      --include-docs \
      --adapter "$ADAPTER" --model "$MODEL_ID" \
      -o "$S1" \
    || { RECIPE_OK=false; }

  # S2 — spec → Mermaid
  if $RECIPE_OK; then
    step "S2: text2mmd → Mermaid"
    run_step "S2 text2mmd" "$RECIPE_LOG" \
      spl3 text2mmd "$S1" \
        --adapter "$ADAPTER" --model "$MODEL_ID" \
        --no-defaults \
        -o "$S2" \
      || { RECIPE_OK=false; }
  fi

  # S3 — Mermaid → SPL
  if $RECIPE_OK; then
    step "S3: mmd2spl → SPL"
    run_step "S3 mmd2spl" "$RECIPE_LOG" \
      spl3 mmd2spl "$S2" \
        --adapter "$ADAPTER" --model "$MODEL_ID" \
        --validate \
        -o "$S3" \
      || { RECIPE_OK=false; }
  fi

  # Promote + write README
  if $RECIPE_OK; then
    cp "$S3" "$CANONICAL"
    write_readme "$DEST" "$NUM" "$NAME" "$PF_SUB" "$DIFF"
    ok "promoted → $CANONICAL"
    PASS=$((PASS + 1))
  else
    fail "$RECIPE — one or more steps failed; artifacts in $OUT/"
    FAIL=$((FAIL + 1))
    FAILED_RECIPES+=("$RECIPE")
  fi
done

# ── Summary ──────────────────────────────────────────────────────────────────

log ""
log "========================================================"
log "  Phase 1 complete — $(date)"
log "  passed : $PASS"
log "  failed : $FAIL"
if [[ ${#FAILED_RECIPES[@]} -gt 0 ]]; then
  log "  failed recipes:"
  for r in "${FAILED_RECIPES[@]}"; do log "    - $r"; done
fi
log ""
log "  Next steps:"
log "    Validate each .spl:"
log "    for f in cookbook-pocketflow/0{01,02,03,06,08}_*/migrate/S3-*.spl; do"
log "      echo \"\$f\"; spl3 validate \"\$f\"; done"
log ""
log "  Full logs: $LOG_DIR/"
log "========================================================"
