#!/usr/bin/env bash
# ============================================================
# Provision the Lean 4 toolchain for SPL's verifier ladder (B-1).
#
# Installs, idempotently:
#   1. elan       — Lean toolchain manager (into $ELAN_HOME, default ~/.elan)
#   2. repl       — leanprover-community/repl at the PINNED revision
#                   below, built with the toolchain named in its own
#                   lean-toolchain file (D2: the two move together)
#   3. spl_lean   — a minimal lake project for `lake env repl`
#   4. (optional) mathlib, with --with-mathlib  (~5 GB olean cache)
#
# Relocatable: all three land in-repo / in $HOME by default, but the
# same environment variables that spl3/lean_bridge.py reads at run time
# redirect the install — set them (and persist in ~/.bashrc) to keep the
# Lean stack on a big disk, e.g. /opt/lean:
#   ELAN_HOME             toolchains   (default: ~/.elan)
#   SPL_LEAN_REPL_DIR     repl checkout (default: <here>/repl)
#   SPL_LEAN_PROJECT_DIR  lake project + mathlib cache (default: <here>/spl_lean)
#
# The pin here must match REPL_REVISION in spl3/lean_bridge.py.
# ============================================================
set -euo pipefail

REPL_REVISION="v4.30.0"          # keep in sync with spl3/lean_bridge.py
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_MATHLIB=0
[[ "${1:-}" == "--with-mathlib" ]] && WITH_MATHLIB=1

export ELAN_HOME="${ELAN_HOME:-$HOME/.elan}"
REPL_DIR="${SPL_LEAN_REPL_DIR:-$HERE/repl}"
PROJECT_DIR="${SPL_LEAN_PROJECT_DIR:-$HERE/spl_lean}"

# ── 1. elan ──────────────────────────────────────────────────
if ! command -v elan >/dev/null 2>&1 && [[ ! -x "$ELAN_HOME/bin/elan" ]]; then
    echo "[setup_lean] installing elan (ELAN_HOME=$ELAN_HOME) ..."
    curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none
fi
export PATH="$ELAN_HOME/bin:$PATH"
echo "[setup_lean] elan: $(elan --version)"

# ── 2. repl at the pinned revision ──────────────────────────
if [[ ! -d "$REPL_DIR" ]]; then
    echo "[setup_lean] cloning leanprover-community/repl @ $REPL_REVISION ..."
    git clone --depth 1 --branch "$REPL_REVISION" \
        https://github.com/leanprover-community/repl.git "$REPL_DIR"
fi
echo "[setup_lean] building repl (toolchain: $(cat "$REPL_DIR/lean-toolchain")) ..."
( cd "$REPL_DIR" && lake build )
echo "[setup_lean] repl binary: $REPL_DIR/.lake/build/bin/repl"

# ── 3. spl_lean lake project ────────────────────────────────
# When redirected outside the repo, seed the project from the in-repo stub.
if [[ "$PROJECT_DIR" != "$HERE/spl_lean" && ! -f "$PROJECT_DIR/lakefile.toml" ]]; then
    echo "[setup_lean] seeding spl_lean project at $PROJECT_DIR ..."
    mkdir -p "$PROJECT_DIR"
    cp "$HERE/spl_lean/lean-toolchain" "$HERE/spl_lean/lakefile.toml" \
       "$HERE/spl_lean/SplLean.lean" "$PROJECT_DIR/"
fi
echo "[setup_lean] building spl_lean project ..."
( cd "$PROJECT_DIR" && lake build )

# ── 4. optional mathlib ─────────────────────────────────────
if [[ "$WITH_MATHLIB" == 1 ]]; then
    if ! grep -q '^\[\[require\]\]' "$PROJECT_DIR/lakefile.toml"; then
        echo "[setup_lean] enabling mathlib require (pinned $REPL_REVISION) ..."
        # Uncomment the pinned [[require]] block scaffolded in lakefile.toml
        sed -i 's/^# *\(\[\[require\]\]\)/\1/; s/^# *\(name = "mathlib"\)/\1/; s/^# *\(scope = "leanprover-community"\)/\1/; s/^# *\(rev = .*\)/\1/' \
            "$PROJECT_DIR/lakefile.toml"
    fi
    ( cd "$PROJECT_DIR" && lake update mathlib && lake exe cache get && lake build )
    echo "[setup_lean] mathlib ready — start the bridge with imports=['Mathlib']"
fi

echo "[setup_lean] done. Verify with:"
echo "  python -c \"from spl3.lean_bridge import repl_available; print(repl_available())\""
