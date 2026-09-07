"""
Independently computes 'expected' ground-truth answers for the 20 math
problems in cookbook/77_neurosymbolic/run_experiment.py, using SymPy
directly (not via any LLM or the SPL solver arm being evaluated).

This is a draft for Wen to review problem-by-problem before it is wired
into the experiment as a Pattern-2 verify() ground truth.
"""
import sympy as sp
from sympy import (
    symbols, diff, expand, factor, solve, simplify, exp, sin, cos, sqrt,
    limit, series, apart, integrate, Matrix, laplace_transform,
    inverse_laplace_transform, dsolve, Function, Eq, summation, oo, latex,
    Rational, S, roots, nsimplify
)

x, y, z, n, t, s = symbols('x y z n t s')
f = Function('f')

results = {}

# ---- T0 ----
results["p001"] = ("T0", "sympy",
    "differentiate x**4 - 2*x**2 + 1",
    diff(x**4 - 2*x**2 + 1, x))

results["p011"] = ("T0", "sympy",
    "simplify (x**2-1)/(x-1)",
    simplify((x**2 - 1) / (x - 1)))

# ---- T1 ----
results["p002"] = ("T1", "sympy",
    "expand (x+1)**2, then factor the expanded form",
    (expand((x+1)**2), factor(expand((x+1)**2))))

results["p003"] = ("T1", "sympy",
    "differentiate 3x^3-x, then factor if needed, finally solve for x",
    (diff(3*x**3 - x, x), factor(diff(3*x**3 - x, x)), solve(diff(3*x**3 - x, x), x)))

expr4 = expand((x - 2)**3)
d4 = diff(expr4, x)
s4 = simplify(d4)
f4 = factor(s4)
sol4 = solve(Eq(f4, 0), x)
results["p004"] = ("T1", "sympy",
    "expand (x-2)**3, differentiate, simplify, factor, solve for =0",
    (expr4, d4, s4, f4, sol4))

results["p012"] = ("T1", "sympy",
    "partial fraction decomposition of 1/(x**2-1)",
    apart(1/(x**2 - 1), x))

# ---- T2 ----
results["p005"] = ("T2", "sympy",
    "differentiate exp(x)",
    simplify(diff(exp(x), x)))

results["p006"] = ("T2", "sympy",
    "limit of sin(x)/x as x->0",
    limit(sin(x)/x, x, 0))

results["p013"] = ("T2", "sympy",
    "Taylor series of sin(x) around 0, degree 5",
    series(sin(x), x, 0, 6))

results["p014"] = ("T2", "sympy",
    "simplify sin(x)**2+cos(x)**2",
    simplify(sin(x)**2 + cos(x)**2))

# ---- T3 ----
results["p007"] = ("T3", "sage(sympy-equiv)",
    "integrate sqrt(4-x**2)",
    integrate(sqrt(4 - x**2), x))

results["p008"] = ("T3", "sage(sympy-equiv)",
    "integrate sin(x)*cos(x), simplify",
    simplify(integrate(sin(x)*cos(x), x)))

sysres = solve([Eq(x + y, 5), Eq(x - y, 1)], [x, y])
results["p015"] = ("T3", "sage(sympy-equiv)",
    "solve system x+y=5, x-y=1",
    sysres)

M = Matrix([[1, 2], [3, 4]])
results["p016"] = ("T3", "sage(sympy-equiv)",
    "eigenvalues of [[1,2],[3,4]]",
    M.eigenvals())

# ---- T4 ----
lap = laplace_transform(exp(-2*t), t, s, noconds=True)
results["p009"] = ("T4", "sage(sympy-equiv)",
    "Laplace transform of exp(-2t)",
    lap)

ode17 = dsolve(Eq(f(x).diff(x), f(x)), f(x), ics={f(0): 1})
results["p017"] = ("T4", "sage(sympy-equiv)",
    "solve y'(x)=y(x), y(0)=1",
    ode17)

results["p018"] = ("T4", "sage(sympy-equiv)",
    "sum 1/n**2 from n=1 to infinity",
    summation(1/n**2, (n, 1, oo)))

r19 = solve(Eq(x**4, 1), x)
results["p019"] = ("T4", "sage(sympy-equiv)",
    "roots of x**4-1",
    r19)

# ---- T5 ----
ode10 = dsolve(Eq(f(x).diff(x, 2) - 3*f(x).diff(x) + 2*f(x), 0), f(x))
results["p010"] = ("T5", "sage(sympy-equiv)",
    "general solution to y''-3y'+2y=0",
    ode10)

ilap = inverse_laplace_transform(s/(s**2+4), s, t)
lap_check = laplace_transform(ilap, t, s, noconds=True)
results["p020"] = ("T5", "sage(sympy-equiv)",
    "inverse Laplace of s/(s**2+4), verify by re-transforming",
    (ilap, lap_check))

for pid in ["p001","p011","p002","p003","p004","p012","p005","p006","p013","p014",
            "p007","p008","p015","p016","p009","p017","p018","p019","p010","p020"]:
    tier, backend, desc, val = results[pid]
    print(f"{pid} | {tier:>3} | {backend:<20} | {desc}")
    print(f"      => {val}")
    print()
