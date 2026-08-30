#!/usr/bin/env bash
# Driver for the Recipe-78 constraint optimization experiment.
#
# Usage:
#   bash cookbook/78_constraint_opt/run_experiment.sh --list
#   bash cookbook/78_constraint_opt/run_experiment.sh -r r78d -m m001 -n n05
#   bash cookbook/78_constraint_opt/run_experiment.sh -r r78d -m m001 -n n10,n20
#   bash cookbook/78_constraint_opt/run_experiment.sh -r r78a,r78b,r78c,r78d -m m001
#   bash cookbook/78_constraint_opt/run_experiment.sh --dry-run
#
# Env-var presets (comma-separated or space-separated):
#   RECIPES="r78a r78d"   bash .../run_experiment.sh
#   MODELS="m001 m002"    bash .../run_experiment.sh
#   SIZES="n05 n10 n20"   bash .../run_experiment.sh   (default: n05)
#   SOLVERS="true false"  bash .../run_experiment.sh   (default: both)
#   N_RUNS=3              bash .../run_experiment.sh
#
# DB: cookbook/78_constraint_opt/experiment_results.db
# Log: cookbook/78_constraint_opt/logs/recipe-78-log-<timestamp>.md

set -uo pipefail

source /home/papagame/anaconda3/etc/profile.d/conda.sh 2>/dev/null || \
source /home/gongai/anaconda3/etc/profile.d/conda.sh   2>/dev/null || \
true

conda activate spl123 2>/dev/null || true

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

ARGS=()
[[ -n "${RECIPES:-}"  ]] && for r in $RECIPES;  do ARGS+=(-r "$r"); done
[[ -n "${MODELS:-}"   ]] && for m in $MODELS;   do ARGS+=(-m "$m"); done
[[ -n "${SIZES:-}"    ]] && for n in $SIZES;    do ARGS+=(-n "$n"); done
[[ -n "${SOLVERS:-}"  ]] && for s in $SOLVERS;  do ARGS+=(-s "$s"); done
[[ -n "${N_RUNS:-}"     ]] && ARGS+=(-k "$N_RUNS")
[[ -n "${LLM_TIMEOUT:-}" ]] && ARGS+=(-t "$LLM_TIMEOUT")

exec python cookbook/78_constraint_opt/run_experiment.py "${ARGS[@]}" "$@"
