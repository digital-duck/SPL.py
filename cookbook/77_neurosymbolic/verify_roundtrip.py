"""
Round-trip / back-substitution verification for the solver arm of the
neurosymbolic experiment (cookbook/77_neurosymbolic).

Design (Wen, 2026-07-16): rather than compare the solver's final result
against a precomputed expected-answer table (form comparison), substitute
the result back into the *original problem's defining relation* and check
it holds -- the "check your work" method taught for exactly this class of
problem. This is deterministic (SymPy performs the substitution and
simplification itself) and sidesteps the comparison ambiguities a
precomputed-answer table runs into (free constants in indefinite
integrals/ODE solutions, root/eigenvalue ordering) because it checks a
*relation*, not a canonical *form*.

This script is a post-hoc check: it reads the already-logged
`decomposition` column in experiment_results.db (no LLM re-run) for the
20 T0-T5 math problems, backends sympy/sage, solver arm only
(solver = 'true'), and classifies each completed run as:

  ROUNDTRIP_PASS  -- final result satisfies the problem's defining relation
  ROUNDTRIP_FAIL  -- final result does not satisfy it (wrong answer,
                     wrong operation performed, or malformed final form)
  UNPARSEABLE     -- the logged final step could not be parsed into a
                     SymPy expression at all (logging/format artifact,
                     not a correctness judgment)

Rows where the Pattern-1 (kernel execution status) oracle already failed
(status != 'complete') are counted as NOT_EXECUTED and excluded from
round-trip checking -- there is no final result to check.

The ground-truth answers independently reviewed and confirmed correct by
Wen on 2026-07-16 (see expected_answers_DRAFT.md) are used where a problem
has no natural inverse operation (limits, sums, plain simplifications);
those checks reduce to direct symbolic-equality comparison, which is
unambiguous for this subset.

The 20 per-pid check functions themselves live in roundtrip_checks.py, so
this post-hoc re-check and symbolic_math.spl's own live `round_trip_check`
TOOL_API (called during the run itself, see sympolic_tools.spl) can never
silently diverge in what "round-trip verified" means for a given pid.

Since results.runtime distinguishes python (spl3) vs go (spl-go) rows in
the same table, verdicts are tallied per runtime as well as pooled --
pooling alone would hide a runtime-specific regression.
"""
import sqlite3
import csv
import sys
from collections import defaultdict

from roundtrip_checks import PIDS, classify

DB_PATH = "experiment_results.db"


def main():
    runtime_filter = sys.argv[1] if len(sys.argv) > 1 else None
    if runtime_filter not in (None, "python", "go"):
        raise SystemExit(f"usage: {sys.argv[0]} [python|go]  (default: both, tallied separately)")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    q = ",".join("?" * len(PIDS))
    sql = f"""SELECT id, mid, label, pid, tier, backend, status, pass, decomposition, output, runtime
              FROM results
              WHERE pid IN ({q}) AND backend IN ('sympy','sage') AND solver = 'true'"""
    params = list(PIDS)
    if runtime_filter:
        sql += " AND runtime = ?"
        params.append(runtime_filter)
    cur.execute(sql, params)
    rows = cur.fetchall()

    out_rows = []
    tally = defaultdict(int)
    tally_by_runtime = defaultdict(lambda: defaultdict(int))
    by_pid = defaultdict(lambda: defaultdict(int))
    by_model = defaultdict(lambda: defaultdict(int))
    by_backend = defaultdict(lambda: defaultdict(int))

    for rid, mid, label, pid, tier, backend, status, p1_pass, decomposition, output_text, runtime in rows:
        verdict, detail = classify(pid, status, decomposition, output_text)
        tally[verdict] += 1
        tally_by_runtime[runtime][verdict] += 1
        by_pid[pid][verdict] += 1
        by_model[label][verdict] += 1
        by_backend[backend][verdict] += 1
        out_rows.append(
            dict(
                id=rid, mid=mid, model=label, pid=pid, tier=tier, backend=backend,
                runtime=runtime,
                pattern1_status=status, pattern1_pass=p1_pass,
                roundtrip_verdict=verdict,
                deterministically_verified={
                    "ROUNDTRIP_PASS": True,
                    "ROUNDTRIP_FAIL": False,
                    "UNPARSEABLE": None,
                    "NOT_EXECUTED": None,
                }[verdict],
                detail=detail,
            )
        )

    if not out_rows:
        print("No matching rows.")
        return

    with open("roundtrip_verification_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    total = len(rows)
    print(f"Total solver-arm rows checked (20 problems, sympy+sage): {total}")
    print()
    print("Overall verdict tally:")
    for k in ("ROUNDTRIP_PASS", "ROUNDTRIP_FAIL", "UNPARSEABLE", "NOT_EXECUTED"):
        n_ = tally.get(k, 0)
        print(f"  {k:16s} {n_:5d}  ({100*n_/total:5.1f}%)")

    print()
    print("Verdict tally by runtime:")
    for rt in sorted(tally_by_runtime.keys()):
        sub_total = sum(tally_by_runtime[rt].values())
        print(f"  runtime={rt} (n={sub_total}):")
        for k in ("ROUNDTRIP_PASS", "ROUNDTRIP_FAIL", "UNPARSEABLE", "NOT_EXECUTED"):
            n_ = tally_by_runtime[rt].get(k, 0)
            print(f"    {k:16s} {n_:5d}  ({100*n_/sub_total:5.1f}%)")

    p1_pass_total = sum(1 for r in out_rows if r["pattern1_pass"] == 1)
    both_pass = sum(1 for r in out_rows if r["pattern1_pass"] == 1 and r["roundtrip_verdict"] == "ROUNDTRIP_PASS")
    p1_pass_rt_fail = sum(1 for r in out_rows if r["pattern1_pass"] == 1 and r["roundtrip_verdict"] == "ROUNDTRIP_FAIL")
    p1_pass_unparse = sum(1 for r in out_rows if r["pattern1_pass"] == 1 and r["roundtrip_verdict"] == "UNPARSEABLE")

    print()
    print("Of rows where Pattern 1 (kernel execution) already said 'pass':")
    print(f"  total Pattern-1 pass                         : {p1_pass_total}")
    print(f"  also round-trip verified (ROUNDTRIP_PASS)     : {both_pass}  ({100*both_pass/p1_pass_total:5.1f}%)")
    print(f"  round-trip FAILS despite Pattern-1 pass       : {p1_pass_rt_fail}  ({100*p1_pass_rt_fail/p1_pass_total:5.1f}%)")
    print(f"  unparseable final result (excluded)           : {p1_pass_unparse}  ({100*p1_pass_unparse/p1_pass_total:5.1f}%)")

    print()
    print("Per-pid breakdown (Pattern-1-pass rows only):")
    for pid in PIDS:
        sub = [r for r in out_rows if r["pid"] == pid and r["pattern1_pass"] == 1]
        if not sub:
            continue
        n_rt_pass = sum(1 for r in sub if r["roundtrip_verdict"] == "ROUNDTRIP_PASS")
        n_rt_fail = sum(1 for r in sub if r["roundtrip_verdict"] == "ROUNDTRIP_FAIL")
        n_unparse = sum(1 for r in sub if r["roundtrip_verdict"] == "UNPARSEABLE")
        print(f"  {pid}: n={len(sub):4d}  rt_pass={n_rt_pass:4d}  rt_fail={n_rt_fail:4d}  unparseable={n_unparse:4d}")

    print()
    print("Per-model breakdown (Pattern-1-pass rows only):")
    for label in sorted(by_model.keys()):
        sub = [r for r in out_rows if r["model"] == label and r["pattern1_pass"] == 1]
        if not sub:
            continue
        n_rt_pass = sum(1 for r in sub if r["roundtrip_verdict"] == "ROUNDTRIP_PASS")
        print(f"  {label:16s} n={len(sub):4d}  round-trip-verified={n_rt_pass:4d} ({100*n_rt_pass/len(sub):5.1f}%)")

    print()
    print("Wrote per-row detail to roundtrip_verification_results.csv")


if __name__ == "__main__":
    main()
