# SPL Run: materials_crystal

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 640 in / 307 out
- **Latency:** 15999ms
- **Timestamp:** 2026-09-05 20:18:07

## Output

```output
# Crystal Structure Check Report

**Problem:** Silicon has a cubic diamond structure with a = 5.431 Angstrom, Z = 8, molar mass 28.09 g/mol. What is its theoretical density in g/cm^3?

**Verifier status:** `OK`
**Theoretical density:** `2.3294 g/cm^3`
**Crystal system:** `cubic` (symmetry_ok=True)
**Unit cell volume:** `160.191 Å³`
**Round-trip check:** `match`

## Interpretation

Silicon adopts a **cubic diamond structure** with a unit-cell volume of **160.19 Å³** containing 8 atoms. The theoretical density is **2.3294 g/cm³**, in excellent agreement with the experimentally accepted value (~2.329 g/cm³). The dual cross-check — verifying cubic symmetry constraints alongside an independent density recomputation from raw lattice parameters — ensures no transcription errors or symmetry misassignments have corrupted the result, which is critical when materials databases feed directly into device simulations or property predictions.

Final answer: 2.3294

## Solver Code (LLM-generated, Python)

```python
a = 5.431
b = 5.431
c = 5.431
alpha = 90.0
beta = 90.0
gamma = 90.0
Z = 8
molar_mass = 28.09

alpha_r = math.radians(alpha)
beta_r = math.radians(beta)
gamma_r = math.radians(gamma)

V = a * b * c * math.sqrt(
    1
    - math.cos(alpha_r)**2
    - math.cos(beta_r)**2
    - math.cos(gamma_r)**2
    + 2 * math.cos(alpha_r) * math.cos(beta_r) * math.cos(gamma_r)
)

N_A = 6.02214076e23
V_cm3 = V * 1e-24
density = Z * molar_mass / (N_A * V_cm3)
density = float(f"{density:.4g}")

_result = {
    "system": "cubic",
    "a": a, "b": b, "c": c,
    "alpha": alpha, "beta": beta, "gamma": gamma,
    "Z": Z, "molar_mass": molar_mass,
    "density": density
}
```
```
