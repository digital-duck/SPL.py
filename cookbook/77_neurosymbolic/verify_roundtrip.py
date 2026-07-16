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
"""
import sqlite3
import json
import re
import csv
from collections import defaultdict

import sympy as sp
from sympy import (
    symbols, Function, simplify, diff, sqrt, sin, cos, exp, pi, oo, I,
    laplace_transform, Matrix,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

DB_PATH = "experiment_results.db"

x, y, z, n, t, s = symbols("x y z n t s")
C1, C2, C3, C4 = symbols("C1 C2 C3 C4")
yf = Function("y")

TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
LOCAL_DICT = dict(
    x=x, y=y, z=z, n=n, t=t, s=s, C1=C1, C2=C2, C3=C3, C4=C4,
    I=I, pi=pi, oo=oo, E=sp.E, exp=exp, sin=sin, cos=cos, sqrt=sqrt,
    arcsin=sp.asin, arccos=sp.acos, arctan=sp.atan,
    arccot=sp.acot, arcsec=sp.asec, arccsc=sp.acsc,
)

PIDS = [
    "p001", "p011", "p002", "p003", "p004", "p012", "p005", "p006", "p013",
    "p014", "p007", "p008", "p015", "p016", "p009", "p017", "p018", "p019",
    "p010", "p020",
]


# ---------------------------------------------------------------- parsing --

def sanitize(expr_str: str) -> str:
    s_ = expr_str.strip().strip("`").strip()
    s_ = re.sub(r"\(already solved.*?\)\s*$", "", s_).strip()
    s_ = re.sub(r"\s*\+\s*C\s*$", "", s_)              # indefinite-integral constant
    s_ = re.sub(r"\s*\+\s*O\([^)]*\)\s*$", "", s_)     # truncated-series remainder
    s_ = re.sub(r"\be\^(\([^)]*\)|\w+)", r"exp(\1)", s_)  # sage e^x -> exp(x)
    return s_.strip()


def parse_sym(expr_str: str):
    return parse_expr(sanitize(expr_str), local_dict=LOCAL_DICT, transformations=TRANSFORMS)


def extract_final_line(decomposition_json):
    if not decomposition_json:
        return None
    try:
        dj = json.loads(decomposition_json)
        steps = dj.get("steps") or []
        ok_steps = [st for st in steps if st.get("ok")]
        if not ok_steps:
            return None
        return ok_steps[-1]["line"]
    except Exception:
        return None


def rhs_of(line: str):
    """Split on the spaced ' -> ' separator used between the kernel call and
    its result; a bare '->' with no surrounding spaces can appear inside a
    limit's point notation (e.g. 'x->0') and must not be treated as the
    separator. Falls back to the last '=' when no spaced arrow is present."""
    if line is None:
        return None
    if " -> " in line:
        return line.rsplit(" -> ", 1)[1].strip()
    if "=" in line:
        return line.rsplit("=", 1)[1].strip()
    return None


def strip_leading_var(rhs: str):
    """'x = [-1/3, 1/3]' -> '[-1/3, 1/3]'; 'y(x) = C1*exp(x)' left untouched."""
    m = re.match(r"^[a-zA-Z]\w*\s*=\s*(.+)$", rhs)
    return m.group(1).strip() if m else rhs


def parse_list_of(expr_str: str):
    """Parse a bracketed list of roots/eigenvalues into a Python list of sympy exprs."""
    body = sanitize(expr_str)
    body = body.strip()
    if body.startswith("[") and body.endswith("]"):
        body = body[1:-1]
    elif body.startswith("{") and body.endswith("}"):
        body = body[1:-1]
    if not body.strip():
        return []
    parts = []
    depth = 0
    cur = ""
    for ch in body:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return [parse_sym(p) for p in parts if p.strip()]


# --------------------------------------------------------- per-pid checks --
# Each check receives the raw `rhs` string (text after the last '->'/'=' in
# the final successful decomposition step) and returns True/False, or raises
# to signal UNPARSEABLE.

def check_p001(rhs):  # differentiate x**4 - 2x**2 + 1
    got = parse_sym(strip_leading_var(rhs))
    expected = diff(x**4 - 2*x**2 + 1, x)
    return simplify(got - expected) == 0


def check_p011(rhs):  # simplify (x**2-1)/(x-1) -- round trip: multiply back
    got = parse_sym(strip_leading_var(rhs))
    return simplify(sp.expand(got * (x - 1)) - (x**2 - 1)) == 0


def check_p002(rhs):  # expand (x+1)**2 then factor -- round trip: expand result back
    got = parse_sym(strip_leading_var(rhs))
    return simplify(sp.expand(got) - sp.expand((x + 1)**2)) == 0


def _roots_satisfy(root_exprs, univariate_expr, var=x):
    if not root_exprs:
        return False
    for r in root_exprs:
        residual = univariate_expr.subs(var, r)
        if simplify(residual) != 0:
            return False
    return True


def check_p003(rhs):  # diff 3x^3-x, factor, solve -- round trip: plug roots into derivative
    roots = parse_list_of(strip_leading_var(rhs))
    derivative = diff(3*x**3 - x, x)
    return _roots_satisfy(roots, derivative)


def check_p004(rhs):  # expand/diff/simplify/factor/solve chain -- plug root(s) into the derivative
    roots = parse_list_of(strip_leading_var(rhs))
    derivative = diff(sp.expand((x - 2)**3), x)
    return _roots_satisfy(roots, derivative)


def check_p012(rhs):  # partial fractions 1/(x**2-1) -- round trip: recombine and compare
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - 1/(x**2 - 1)) == 0


def check_p005(rhs):  # differentiate exp(x)
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - exp(x)) == 0


def check_p006(rhs):  # limit sin(x)/x as x->0
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - 1) == 0


def check_p013(rhs):  # Taylor series sin(x) deg 5 -- compare truncated polynomials
    got = parse_sym(strip_leading_var(rhs))
    expected = sp.series(sin(x), x, 0, 6).removeO()
    return simplify(sp.expand(got - expected)) == 0


def check_p014(rhs):  # simplify sin^2+cos^2
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - 1) == 0


def check_p007(rhs):  # integrate sqrt(4-x**2) -- round trip: differentiate result
    got = parse_sym(strip_leading_var(rhs))
    return simplify(diff(got, x) - sqrt(4 - x**2)) == 0


def check_p008(rhs):  # integrate sin(x)cos(x), simplify -- round trip: differentiate result
    got = parse_sym(strip_leading_var(rhs))
    return simplify(diff(got, x) - sin(x)*cos(x)) == 0


def _find_xy_pair(text):
    m = re.search(r"x\s*[:=]\s*(-?\d+/?\d*)\D+?y\s*[:=]\s*(-?\d+/?\d*)", text)
    if m:
        return parse_sym(m.group(1)), parse_sym(m.group(2))
    return None


def check_p015(rhs, output_text=None):  # solve x+y=5, x-y=1 -- round trip: substitute into both equations
    # The kernel decomposition trace for this problem is frequently
    # truncated at logging time (the multi-line solve_system(...) repr got
    # cut mid-render), so the visible x/y values are often only recoverable
    # from the workflow's final natural-language answer (`output`), not the
    # decomposition JSON. This falls back to that text when the trace
    # itself yields no usable value; the round-trip check performed is
    # still purely deterministic substitution once x, y are located.
    for source in (sanitize(strip_leading_var(rhs)), output_text or ""):
        pair = _find_xy_pair(source)
        if pair:
            xv, yv = pair
            return simplify(xv + yv - 5) == 0 and simplify(xv - yv - 1) == 0
    raise ValueError(f"cannot locate x,y in decomposition or output: {rhs!r}")


def check_p016(rhs):  # eigenvalues of [[1,2],[3,4]] -- round trip: det(A - lambda*I) == 0
    eigs = parse_list_of(strip_leading_var(rhs))
    A = Matrix([[1, 2], [3, 4]])
    lam = symbols("lam")
    charpoly = (A - lam*sp.eye(2)).det()
    if len(eigs) != 2:
        return False
    return all(simplify(charpoly.subs(lam, ev)) == 0 for ev in eigs)


def check_p009(rhs):  # Laplace transform of e^(-2t) -- unique closed form, direct compare
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - 1/(s + 2)) == 0


def _extract_yx_expr(rhs):
    """Pull the right-hand side of an Eq(y(x), ...) / 'y(x) = ...' final line,
    or accept a bare pass-through expression in x."""
    body = sanitize(rhs)
    m = re.match(r"^Eq\(y\(x\),\s*(.+)\)$", body)
    if m:
        return parse_sym(m.group(1))
    m = re.match(r"^y\(x\)\s*=\s*(.+)$", body)
    if m:
        return parse_sym(m.group(1))
    # bare expression, e.g. "(C1 + C2*exp(x))*exp(x)"
    return parse_sym(body)


def check_p017(rhs):  # solve y'=y, y(0)=1 -- round trip: substitute into the ODE
    # NOTE: the initial condition y(0)=1 is often resolved by the LLM's own
    # algebra (e.g. "so C1=1") outside any logged SOLVE/ASSERT call, so it is
    # not independently checkable from the decomposition trace alone. This
    # check validates the returned function satisfies the ODE itself; it
    # does not independently confirm the constant was resolved from the IC.
    expr = _extract_yx_expr(rhs)
    return simplify(diff(expr, x) - expr) == 0


def check_p018(rhs):  # sum 1/n**2 -- direct (no natural inverse for an infinite sum)
    got = parse_sym(strip_leading_var(rhs))
    return simplify(got - pi**2/6) == 0


def check_p019(rhs):  # roots of x**4-1 -- round trip: plug each root back in
    roots = parse_list_of(strip_leading_var(rhs))
    if len(set(sp.nsimplify(r) for r in roots)) != 4:
        return False
    return _roots_satisfy(roots, x**4 - 1)


CONST_SYMS = {C1, C2, C3, C4}


def check_p010(rhs):  # general solution y''-3y'+2y=0 -- substitute into the ODE
    expr = _extract_yx_expr(rhs)
    residual = simplify(sp.expand(diff(expr, x, 2) - 3*diff(expr, x) + 2*expr))
    if residual != 0:
        return False
    # A 2nd-order ODE's *general* solution needs two independent constants;
    # a particular solution (e.g. bare "exp(x)", missing the C2*exp(2x) term)
    # satisfies the ODE too but is not the general solution the problem asks
    # for, so require both degrees of freedom to be present.
    return len(expr.free_symbols & CONST_SYMS) == 2


def check_p020(rhs):  # inverse Laplace of s/(s**2+4) -- round trip: re-transform
    got = parse_sym(strip_leading_var(rhs))
    free = got.free_symbols
    if s in free and t not in free:
        # the logged final step is already the re-transform back to the
        # s-domain (the problem's own "verify by re-transforming" step) --
        # compare it directly to the original.
        return simplify(got - s/(s**2 + 4)) == 0
    # final step is still in the t-domain (e.g. cos(2*t)) -- perform the
    # round trip ourselves.
    back = laplace_transform(got, t, s, noconds=True)
    return simplify(back - s/(s**2 + 4)) == 0


CHECKS = {
    "p001": check_p001, "p011": check_p011, "p002": check_p002,
    "p003": check_p003, "p004": check_p004, "p012": check_p012,
    "p005": check_p005, "p006": check_p006, "p013": check_p013,
    "p014": check_p014, "p007": check_p007, "p008": check_p008,
    "p015": check_p015, "p016": check_p016, "p009": check_p009,
    "p017": check_p017, "p018": check_p018, "p019": check_p019,
    "p010": check_p010, "p020": check_p020,
}


# ------------------------------------------------------------------- main --

def classify(pid, status, decomposition, output_text=None):
    if status != "complete":
        return "NOT_EXECUTED", None
    line = extract_final_line(decomposition)
    rhs = rhs_of(line) if line else None
    if rhs is None and pid != "p015":
        return "UNPARSEABLE", f"no final line/rhs extractable ({line!r})"
    try:
        if pid == "p015":
            ok = check_p015(rhs or "", output_text)
        else:
            ok = CHECKS[pid](rhs)
    except Exception as e:
        return "UNPARSEABLE", f"{type(e).__name__}: {e} (rhs={rhs!r})"
    return ("ROUNDTRIP_PASS" if ok else "ROUNDTRIP_FAIL"), rhs


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    q = ",".join("?" * len(PIDS))
    cur.execute(
        f"""SELECT id, mid, label, pid, tier, backend, status, pass, decomposition, output
            FROM results
            WHERE pid IN ({q}) AND backend IN ('sympy','sage') AND solver = 'true'""",
        PIDS,
    )
    rows = cur.fetchall()

    out_rows = []
    tally = defaultdict(int)
    by_pid = defaultdict(lambda: defaultdict(int))
    by_model = defaultdict(lambda: defaultdict(int))
    by_backend = defaultdict(lambda: defaultdict(int))

    for rid, mid, label, pid, tier, backend, status, p1_pass, decomposition, output_text in rows:
        verdict, detail = classify(pid, status, decomposition, output_text)
        tally[verdict] += 1
        by_pid[pid][verdict] += 1
        by_model[label][verdict] += 1
        by_backend[backend][verdict] += 1
        out_rows.append(
            dict(
                id=rid, mid=mid, model=label, pid=pid, tier=tier, backend=backend,
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
