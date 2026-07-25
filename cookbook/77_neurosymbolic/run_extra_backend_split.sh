#!/usr/bin/env bash
# run_extra_backend_split.sh — Extra repetitions (+3 runs/cell, r=3 -> r=6)
# for all 11 models (m001-m011, deepseek-r1/m012 excluded), split into two
# sequential batches by backend: SymPy (T0-T2) then Sage (T3-T5).
#
# Designed to run unattended for a long stretch (many hours): launch with
# nohup + setsid + disown so it survives the parent shell/session closing,
# and wrap in systemd-inhibit so the machine doesn't suspend mid-run (a
# GNOME idle-suspend killed nothing outright the one time it happened, but
# it silently pauses the run for however long the machine stays asleep).
#
#   nohup setsid systemd-inhibit --what=sleep:idle \
#       --who="SPL-experiment" --why="Long-running unattended experiment batch" \
#       --mode=block \
#       bash cookbook/77_neurosymbolic/run_extra_backend_split.sh \
#       > cookbook/77_neurosymbolic/logs-spl/extra-backend-split-driver.log 2>&1 < /dev/null &
#   disown
#
# Progress/results land in the normal places:
#   - per-cell markdown logs: cookbook/77_neurosymbolic/logs-spl/recipe-77-log-<ts>.md
#   - DB rows: cookbook/77_neurosymbolic/experiment_results.db (new source_file per phase)
#   - this driver's own stdout/stderr: whatever path you redirect to above

set -uo pipefail

source /home/gongai/anaconda3/etc/profile.d/conda.sh
conda activate spl123

cd "$(dirname "${BASH_SOURCE[0]}")/../.."   # SPL.py repo root

MODELS="m001,m002,m003,m004,m005,m006,m007,m008,m009,m010,m011"
N_RUNS=3

SYMPY_PROBLEMS="p001 p002 p003 p004 p005 p006 p011 p012 p013 p014"
SAGE_PROBLEMS="p007 p008 p009 p010 p015 p016 p017 p018 p019 p020"

STAMP="$(date +%Y%m%d-%H%M%S)"
echo "=== run_extra_backend_split.sh starting at ${STAMP} ==="
echo "Models : ${MODELS}"
echo "Extra runs/cell: ${N_RUNS} (existing r=3 + this batch => r=6 total)"

echo
echo "--- Phase 1/2: SymPy backend (T0-T2), problems: ${SYMPY_PROBLEMS} ---"
MODELS="${MODELS}" PROBLEMS="${SYMPY_PROBLEMS}" N_RUNS="${N_RUNS}" \
    bash cookbook/77_neurosymbolic/run_experiment.sh
SYMPY_STATUS=$?
echo "--- Phase 1/2 (SymPy) exit code: ${SYMPY_STATUS} ---"

echo
echo "--- Phase 2/2: Sage backend (T3-T5), problems: ${SAGE_PROBLEMS} ---"
MODELS="${MODELS}" PROBLEMS="${SAGE_PROBLEMS}" N_RUNS="${N_RUNS}" \
    bash cookbook/77_neurosymbolic/run_experiment.sh
SAGE_STATUS=$?
echo "--- Phase 2/2 (Sage) exit code: ${SAGE_STATUS} ---"

echo
echo "=== run_extra_backend_split.sh finished at $(date +%Y%m%d-%H%M%S) ==="
echo "SymPy phase exit: ${SYMPY_STATUS}  |  Sage phase exit: ${SAGE_STATUS}"

if [[ ${SYMPY_STATUS} -ne 0 || ${SAGE_STATUS} -ne 0 ]]; then
    exit 1
fi
