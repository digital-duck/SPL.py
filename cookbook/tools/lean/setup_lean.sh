#!/usr/bin/env bash
# ============================================================
# Provision the Lean 4 toolchain for SPL's verifier ladder (B-1).
#
# Installs, idempotently:
#   1. elan       — Lean toolchain manager (user-space, ~/.elan)
#   2. repl       — leanprover-community/repl at the PINNED revision
#                   below, built with the toolchain named in its own
#                   lean-toolchain file (D2: the two move together)
#   3. spl_lean   — a minimal lake project for `lake env repl`
#   4. (optional) mathlib, with --with-mathlib  (~5 GB olean cache)
#
# The pin here must match REPL_REVISION in spl3/lean_bridge.py.
# ============================================================
set -euo pipefail

REPL_REVISION="v4.30.0"          # keep in sync with spl3/lean_bridge.py
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_MATHLIB=0
[[ "${1:-}" == "--with-mathlib" ]] && WITH_MATHLIB=1

# ── 1. elan ──────────────────────────────────────────────────
if ! command -v elan >/dev/null 2>&1 && [[ ! -x "$HOME/.elan/bin/elan" ]]; then
    echo "[setup_lean] installing elan ..."
    curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none
fi
export PATH="$HOME/.elan/bin:$PATH"
echo "[setup_lean] elan: $(elan --version)"

# ── 2. repl at the pinned revision ──────────────────────────
if [[ ! -d "$HERE/repl" ]]; then
    echo "[setup_lean] cloning leanprover-community/repl @ $REPL_REVISION ..."
    git clone --depth 1 --branch "$REPL_REVISION" \
        https://github.com/leanprover-community/repl.git "$HERE/repl"
fi
echo "[setup_lean] building repl (toolchain: $(cat "$HERE/repl/lean-toolchain")) ..."
( cd "$HERE/repl" && lake build )
echo "[setup_lean] repl binary: $HERE/repl/.lake/build/bin/repl"

# ── 3. spl_lean lake project ────────────────────────────────
echo "[setup_lean] building spl_lean project ..."
( cd "$HERE/spl_lean" && lake build )

# ── 4. optional mathlib ─────────────────────────────────────
if [[ "$WITH_MATHLIB" == 1 ]]; then
    if ! grep -q '^\[\[require\]\]' "$HERE/spl_lean/lakefile.toml"; then
        echo "[setup_lean] enabling mathlib require (pinned $REPL_REVISION) ..."
        # Uncomment the pinned [[require]] block scaffolded in lakefile.toml
        sed -i 's/^# *\(\[\[require\]\]\)/\1/; s/^# *\(name = "mathlib"\)/\1/; s/^# *\(scope = "leanprover-community"\)/\1/; s/^# *\(rev = .*\)/\1/' \
            "$HERE/spl_lean/lakefile.toml"
    fi
    ( cd "$HERE/spl_lean" && lake update mathlib && lake exe cache get && lake build )
    echo "[setup_lean] mathlib ready — start the bridge with imports=['Mathlib']"
fi

echo "[setup_lean] done. Verify with:"
echo "  python -c \"from spl3.lean_bridge import repl_available; print(repl_available())\""
