"""SageManifolds seed for the future `python/classical_mechanics` domain target.

This is milestone A-4's "one SageManifolds cell" (see
SPL.py/docs/DEV/sage_lean_integration_plan.md §A.3): the smallest computation
that proves the differential-geometry machinery the mechanics domain needs —
charts, metrics, curvature — runs in our environment (passagemath wheels,
same `spl123` interpreter as the SPL kernel).

The future `mechanics_graph.yaml` will declare nodes like `configuration_space`,
`lagrangian`, `geodesic`, `normal_modes` with `verifier: "sage"` — their worked
examples verify exactly the way `sphere_scalar_curvature` does below:
recompute the symbolic quantity on the manifold and compare exactly.

Run directly:  python classical_mechanics_seed.py
Run under SPL: CALL run_python('import classical_mechanics_seed as cm; ...')
               via `spl3 run --kernel-name sagemath`
"""

from __future__ import annotations


def sphere_scalar_curvature(radius=1):
    """Ricci scalar of the round 2-sphere of radius r — exactly 2/r².

    The "hello world" of SageManifolds: build S² with the round metric in
    spherical coordinates, compute the Ricci scalar symbolically, and return
    it simplified. A constant-curvature check like this is the verifier shape
    for every curvature/geodesic node in the future mechanics domain.
    """
    from sage.all import Manifold, var, sin, simplify

    r = var("r", domain="positive") if radius is None else radius
    S2 = Manifold(2, "S^2", structure="Riemannian")
    chart = S2.chart(r"th:(0,pi):\theta ph:(0,2*pi):\phi")

    th = chart[0]
    g = S2.metric("g")
    g[0, 0] = r**2
    g[1, 1] = (r * sin(th)) ** 2

    ricci_scalar = g.ricci_scalar()
    return simplify(ricci_scalar.expr())


def verify_sphere_curvature(radius=1) -> str:
    """graph_lib-shaped verifier: 'pass (sage)' iff Ricci scalar of S²_r == 2/r².

    Sage-only by nature (SymPy has no manifolds machinery) — this is exactly
    the kind of node the fallback policy marks `verifier: "sage"` (fail fast
    when Sage is absent) rather than `"sage|sympy"`.
    """
    try:
        from sage.all import QQ
        expected = QQ(2) / (QQ(radius) ** 2)
        actual = sphere_scalar_curvature(radius)
        if actual == expected:
            return "pass (sage)"
        return f"fail: Ricci scalar = {actual} != {expected} (sage)"
    except ImportError as exc:
        return f"fail: no verifier engine available ({exc})"


if __name__ == "__main__":
    print("S^2 (r=1) Ricci scalar:", sphere_scalar_curvature(1))
    print("S^2 (r=2) Ricci scalar:", sphere_scalar_curvature(2))
    print(verify_sphere_curvature(1))
