#!/usr/bin/env bash
# Driver for the Recipe-77 neurosymbolic experiment — activates the
# spl123 env, moves to the repo root, and forwards to run_experiment.py
# (which owns the problem battery, model roster, and SQLite persistence).
#
#   bash cookbook/77_neurosymbolic/run_experiment.sh --list
#   bash cookbook/77_neurosymbolic/run_experiment.sh -m m001 -p p021
#   bash cookbook/77_neurosymbolic/run_experiment.sh -m m001 -p p003 --backend sympy
#
# Recipe-67-style env-var presets still work (mapped to CLI flags;
# anything passed on the command line is appended after them):
#
#   MODELS="m001 m010"  bash .../run_experiment.sh
#   PROBLEMS="p021 p025" bash .../run_experiment.sh
#   SOLVER_MODES="true"  bash .../run_experiment.sh   (default: both arms)
#   BACKEND=sympy        bash .../run_experiment.sh   (override the rung)
#   N_RUNS=3             bash .../run_experiment.sh
#
# Output: cookbook/77_neurosymbolic/logs-spl/recipe-77-log-<timestamp>.md
#         cookbook/77_neurosymbolic/experiment_results.db

set -uo pipefail

source /home/gongai/anaconda3/etc/profile.d/conda.sh
conda activate spl123

# run_experiment.py expects the SPL.py repo root as the working directory
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

ARGS=()
[[ -n "${MODELS:-}"   ]] && ARGS+=(-m "$MODELS")
[[ -n "${PROBLEMS:-}" ]] && ARGS+=(-p "$PROBLEMS")
if [[ -n "${SOLVER_MODES:-}" ]]; then
    for mode in $SOLVER_MODES; do ARGS+=(-s "$mode"); done
fi
[[ -n "${BACKEND:-}" ]] && ARGS+=(--backend "$BACKEND")
[[ -n "${N_RUNS:-}"  ]] && ARGS+=(-r "$N_RUNS")

exec python cookbook/77_neurosymbolic/run_experiment.py "${ARGS[@]}" "$@"
