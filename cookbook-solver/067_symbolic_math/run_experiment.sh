#!/usr/bin/env bash
# Runs the symbolic-math experiment across the 4 axes defined in
# case-2-hackernews.md.  Run from the repo root:
#
#   bash cookbook/67_symbolic_math/run_experiment.sh
#
# Selective run — override any axis at the command line:
#   MODELS="sonnet-4-6 phi4" bash .../run_experiment.sh
#   PROBLEMS="0 2"           bash .../run_experiment.sh   (by index)
#   SOLVER_MODES="true"      bash .../run_experiment.sh
#   N_RUNS=3                 bash .../run_experiment.sh
#
# Output: cookbook/67_symbolic_math/logs-spl/case-2-log-rerun-<timestamp>.md

set -uo pipefail

# ── Axis 1: Problem battery (ordered easy → hard, Tier 0–5) ──────────────────
# Format: "tier|problem-text"
# Indices 0-9 match the numbered table in case-2-hackernews.md § Axis 1.
ALL_PROBLEMS=(
    "T0|differentiate x**4 - 2*x**2 + 1"
    "T1|expand (x+1)**2, then factor the expanded form"
    "T1|differentiate 3*x**3-x, then factor if needed, finally solve for x"
    "T1|expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0"
    "T2|differentiate e**x and simplify it if necessary"
    "T2|First, differentiate e**x. Then simplify the result."
    "T3|integrate the square root of (4 minus x squared)"
    "T3|find the integral of sin(x) times cos(x), then simplify the result"
    "T4|find the Laplace transform of e to the power of negative 2t"
    "T5|simplify the expression and tell me what x equals"
)

# ── Axis 2: Model roster (label|adapter|provider) ────────────────────────────
ALL_MODELS=(
    "sonnet-4-6|claude_cli|claude_cli"
    "gemma3|ollama:gemma3|ollama"
    "gemma4|ollama:gemma4|ollama"
    "qwen2.5|ollama:qwen2.5|ollama"
    "qwen3|ollama:qwen3|ollama"
    "phi3|ollama:phi3|ollama"
    "phi4|ollama:phi4|ollama"
    "deepseek-r1|ollama:deepseek-r1:8b|ollama"
    "lfm2.5|ollama:lfm2.5|ollama"
    "rnj-1|ollama:rnj-1|ollama"
)

# ── Axis 3: Solver toggle (requires sympy_llm.spl) ───────────────────────────
# "true"  → ARM A: LLM plans, SymPy computes, LLM explains (verified chain)
# "false" → ARM B: LLM solves the whole problem unaided, one shot
ALL_SOLVER_MODES=("true" "false")

# ── Axis 4: Repetitions ──────────────────────────────────────────────────────
ALL_N_RUNS=1

# ── Active selections (override via env, or edit here for a saved preset) ────
# For MODELS/SOLVER_MODES: space-separated label list; empty = run all.
# For PROBLEMS: space-separated index list (0-based); empty = run all.
MODELS="${MODELS:-}"
PROBLEMS="${PROBLEMS:-}"
SOLVER_MODES="${SOLVER_MODES:-true}"   # default: solver-on only (matches case-2)
N_RUNS="${N_RUNS:-$ALL_N_RUNS}"

# ── Script + log setup ───────────────────────────────────────────────────────
# Switch to sympy_llm.spl to activate the solver toggle (Axis 3).
# Use sympy_math_multi_step.spl for a plain rerun without the toggle.
SCRIPT="cookbook/67_symbolic_math/sympy_math_multi_step.spl"
LOG_DIR="cookbook/67_symbolic_math/logs-spl"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/case-2-log-rerun-${TIMESTAMP}.md"

source /home/gongai/anaconda3/etc/profile.d/conda.sh
conda activate spl123

mkdir -p "$LOG_DIR"
printf "# The experimental logs for Recipe #67 (rerun %s)\n\n" "$TIMESTAMP" > "$LOG_FILE"
echo "Logging to: $LOG_FILE"

# ── Helpers ──────────────────────────────────────────────────────────────────

is_selected() {
    # is_selected <value> <space-separated allowlist>
    # Returns 0 (true) if allowlist is empty OR value is in the list.
    local val="$1" list="$2"
    [[ -z "$list" ]] && return 0
    for item in $list; do [[ "$item" == "$val" ]] && return 0; done
    return 1
}

run_one() {
    local label="$1" adapter="$2" provider="$3"
    local problem="$4" solver_mode="$5" run_no="$6" tier="$7"

    local heading="${label} / solver=${solver_mode} / run ${run_no}"
    echo ""
    echo "=============================="
    echo " ${heading}"
    echo " Problem (${tier}): ${problem}"
    echo "=============================="

    local extra_params=""
    if [[ "$SCRIPT" == *"sympy_llm"* ]]; then
        extra_params="--param enable_solver=${solver_mode}"
    fi

    {
        printf "\n## %s (%s) — solver=%s — run %s\n\n" \
            "$label" "$provider" "$solver_mode" "$run_no"
        printf "_Tier: %s | Problem: %s_\n\n" "$tier" "$problem"
        printf '```bash\n'
        printf '(spl123) $ spl3 run %s --llm %s \\\n' "$SCRIPT" "$adapter"
        printf '   --param problem="%s"' "$problem"
        [[ -n "$extra_params" ]] && printf ' \\\n   %s' "$extra_params"
        printf '\n```\n\n\n```output\n'
    } >> "$LOG_FILE"

    spl3 run "$SCRIPT" --llm "$adapter" \
        --param problem="$problem" \
        ${extra_params} 2>&1 | tee -a "$LOG_FILE" || true

    printf '```\n\n' >> "$LOG_FILE"
}

# ── Main loop: Axis 1 × Axis 2 × Axis 3 × Axis 4 ────────────────────────────

total=0
p_idx=0
for problem_entry in "${ALL_PROBLEMS[@]}"; do
    IFS='|' read -r tier problem <<< "$problem_entry"

    if ! is_selected "$p_idx" "$PROBLEMS"; then
        (( p_idx++ )) || true
        continue
    fi

    for model_entry in "${ALL_MODELS[@]}"; do
        IFS='|' read -r label adapter provider <<< "$model_entry"

        if ! is_selected "$label" "$MODELS"; then
            continue
        fi

        for solver_mode in $SOLVER_MODES; do
            for run_no in $(seq 1 "$N_RUNS"); do
                run_one "$label" "$adapter" "$provider" \
                        "$problem" "$solver_mode" "$run_no" "$tier"
                (( total++ )) || true
            done
        done
    done

    (( p_idx++ )) || true
done

echo ""
echo "=============================="
echo " Done — ${total} run(s) completed."
echo " Log: $LOG_FILE"
echo "=============================="
