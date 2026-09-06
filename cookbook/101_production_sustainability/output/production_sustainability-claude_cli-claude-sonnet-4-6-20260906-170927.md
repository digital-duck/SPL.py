# SPL Run: production_sustainability

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 1028 in / 587 out
- **Latency:** 56079ms
- **Timestamp:** 2026-09-06 17:09:27

## Output

```output
=== Production Sustainability (solver=OFF / LLM heuristic) ===

Problem:
A factory produces standard product A and green product B. A: $10 profit, 3 kg CO₂, uses 2 hr labor and 3 kg material. B: $6 profit, 1 kg CO₂, uses 1 hr labor and 2 kg material. Available: 20 labor-hours, 30 kg material. Find production plans that maximize profit and minimize carbon footprint.

Extracted Problem Data (JSON):
```json
{
  "products": [
    {"name": "A", "profit": 10.0, "carbon": 3.0, "labor": 2.0, "material": 3.0},
    {"name": "B", "profit": 6.0,  "carbon": 1.0, "labor": 1.0, "material": 2.0}
  ],
  "resources": {"labor": 20.0, "material": 30.0}
}
```

LLM Proposed Solution:
## Feasible Region Analysis

**Corner points** of the feasible region (intersections of constraint boundaries):

| Point | Labor check | Material check | Feasible? |
|-------|------------|----------------|-----------|
| (0, 0) | 0 ≤ 20 ✓ | 0 ≤ 30 ✓ | Yes |
| (10, 0) | 20 ≤ 20 ✓ | 30 ≤ 30 ✓ | Yes |
| (0, 15) | 15 ≤ 20 ✓ | 30 ≤ 30 ✓ | Yes |
| (0, 20) | 20 ≤ 20 ✓ | 40 > 30 ✗ | **No** |

The two constraints (2x+y=20 and 3x+2y=30) intersect at (10, 0), so the feasible region is a **triangle** with vertices (0,0), (10,0), (0,15).

---

## Objective Values at Each Vertex

| (x, y) | Profit = 10x+6y | Carbon = 3x+y | Notes |
|--------|-----------------|---------------|-------|
| (0, 0) | $0 | 0 kg | Trivial — no production |
| (10, 0) | **$100** | 30 kg | Max profit, max carbon |
| (0, 15) | $90 | **15 kg** | Near-max profit, half the carbon |

---

## Trade-off Reasoning

Moving from (0,15) → (10,0):
- Profit gain: +$10 (+11%)
- Carbon cost: +15 kg (+100%)

Paying **15 extra kg CO₂** for only **$10 more profit** is a poor trade. **(0, 15)** dominates as the balanced plan: it captures **90% of maximum profit** while producing only **50% of the carbon** of the pure-profit solution. It is Pareto-superior on the carbon axis with minimal profit sacrifice.

---

## Verification for (x=0, y=15)

- Labor: 2(0) + 15 = **15 ≤ 20** ✓
- Material: 3(0) + 2(15) = **30 ≤ 30** ✓
- Profit: 10(0) + 6(15) = **$90**
- Carbon: 3(0) + 1(15) = **15 kg**

---

```json
{
  "x": 0.0,
  "y": 15.0,
  "profit": 90.0,
  "carbon": 15.0,
  "reasoning": "Producing only Product B (15 units) captures 90% of maximum profit ($90 vs $100) while cutting carbon footprint in half (15 kg vs 30 kg) compared to the pure-profit plan, making it the dominant balanced choice on the Pareto frontier."
}
```

Extracted Solution (JSON):
```json
{
  "x": 0.0,
  "y": 15.0,
  "profit": 90.0,
  "carbon": 15.0,
  "reasoning": "Producing only Product B (15 units) captures 90% of maximum profit ($90 vs $100) while cutting carbon footprint in half (15 kg vs 30 kg) compared to the pure-profit plan, making it the dominant balanced choice on the Pareto frontier."
}
```

Verification:
{"verdict": "PASS", "x": 0.0, "y": 15.0, "actual_profit": 90.0, "actual_carbon": 15.0, "notes": "all checks passed"}

LLM calls: 3
```
