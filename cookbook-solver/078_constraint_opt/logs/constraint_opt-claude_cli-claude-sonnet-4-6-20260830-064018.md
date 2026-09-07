# SPL Run: constraint_opt

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 275 in / 760 out
- **Latency:** 45852ms
- **Timestamp:** 2026-08-30 06:40:18

## Output

```output
# Constraint Optimization Report

**Problem:** A factory makes chairs (2h labor, 4kg wood, $20 profit) and tables (4h labor, 3kg wood, $30 profit). Available: 20h labor, 24kg wood. Maximize profit.

## Solution

### 1. Decision Variables, Objective, and Constraints

Let **x** = chairs produced, **y** = tables produced.

**Objective:** Maximize Z = 20x + 30y

**Subject to:**
- Labor: 2x + 4y ≤ 20
- Wood: 4x + 3y ≤ 24
- Non-negativity: x ≥ 0, y ≥ 0

---

### 2. Feasible Region Corners

The boundary lines are:
- L₁: 2x + 4y = 20  (labor, full use)
- L₂: 4x + 3y = 24  (wood, full use)
- x = 0, y = 0

**Corner A — Origin:** (0, 0). Trivially feasible.

**Corner B — L₁ meets x-axis:** Set y = 0 in L₁: 2x = 20 → x = 10. Check L₂: 4(10) + 3(0) = 40 > 24. **Infeasible.**

**Corner C — L₂ meets x-axis:** Set y = 0 in L₂: 4x = 24 → x = 6. Check L₁: 2(6) + 4(0) = 12 ≤ 20. **Feasible** → **(6, 0)**.

**Corner D — L₁ meets y-axis:** Set x = 0 in L₁: 4y = 20 → y = 5. Check L₂: 4(0) + 3(5) = 15 ≤ 24. **Feasible** → **(0, 5)**.

**Corner E — L₂ meets y-axis:** Set x = 0 in L₂: 3y = 24 → y = 8. Check L₁: 4(8) = 32 > 20. **Infeasible.**

**Corner F — L₁ ∩ L₂ (both binding):** Solve the 2×2 system:
```
2x + 4y = 20   → x + 2y = 10   → x = 10 − 2y    … (i)
4x + 3y = 24                                       … (ii)
```
Substitute (i) into (ii):
```
4(10 − 2y) + 3y = 24
40 − 8y + 3y = 24
40 − 5y = 24
5y = 16
y = 3.2
x = 10 − 2(3.2) = 10 − 6.4 = 3.6
```
Check feasibility: both constraints are binding by construction. **Feasible** → **(3.6, 3.2)**.

**Feasible vertices: (0, 0), (6, 0), (3.6, 3.2), (0, 5).**

---

### 3. Objective at Each Corner

| Vertex | Z = 20x + 30y | Arithmetic |
|--------|--------------|------------|
| (0, 0) | $0 | 0 + 0 |
| (6, 0) | $120 | 20×6 + 30×0 |
| (3.6, 3.2) | **$168** | 20×3.6 + 30×3.2 = 72 + 96 |
| (0, 5) | $150 | 20×0 + 30×5 |

---

### 4. Optimal Solution

**LP relaxation optimum: x = 3.6 chairs, y = 3.2 tables, Z = $168.**

**Integrality note:** Chairs and tables are discrete items, so x and y must be non-negative integers. The LP vertex (3.6, 3.2) is non-integer, so we must search nearby integer points.

Round down: (3, 3) — Z = 20(3) + 30(3) = 60 + 90 = **$150**.

Check (2, 4): Labor: 2(2) + 4(4) = 4 + 16 = 20 ≤ 20 ✓. Wood: 4(2) + 3(4) = 8 + 12 = 20 ≤ 24 ✓. Z = 40 + 120 = **$160**.

Check (4, 3): Wood: 4(4) + 3(3) = 16 + 9 = 25 > 24. Infeasible.

Check (3, 4): Labor: 2(3) + 4(4) = 6 + 16 = 22 > 20. Infeasible.

For y = 5, x = 0: Z = $150. For y = 4, max feasible x: labor gives x ≤ 2, wood gives x ≤ 3; binding is x ≤ 2, already found (2, 4).

**Integer optimum: x = 2 chairs, y = 4 tables, Z = $160.**

---

## Verification

Plug in x = 2, y = 4:

**Labor constraint:**
2(2) + 4(4) = 4 + 16 = 20 ≤ 20 ✓ **Binding** (all 20 labor-hours used)

**Wood constraint:**
4(2) + 3(4) = 8 + 12 = 20 ≤ 24 ✓ **Slack of 4 kg** (only 20 of 24 kg used)

**Non-negativity:**
x = 2 ≥ 0 ✓, y = 4 ≥ 0 ✓

**Objective:**
2 chairs × $20 = $40
4 tables × $30 = $120
Total: $40 + $120 = **$160**

The LP relaxation bound of $168 is unattainable with integers. The integer-optimal plan — **produce 2 chairs and 4 tables for a profit of $160** — exhausts the full labor budget and leaves 4 kg of wood unused.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 1 |
| Stage 1 — direct LLM solve (s) | 44.70 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 45.20 |
| Input tokens | 275 |
| Output tokens | 760 |
| Total tokens | 1,035 |
```
