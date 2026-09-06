# SPL Run: supply_sourcing

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 507 in / 465 out
- **Latency:** 32036ms
- **Timestamp:** 2026-09-06 11:54:41

## Output

```output
=== Supply Sourcing (solver=ON / PuLP ε-constraint) ===

Problem:
A manufacturer needs 1000 units from 3 suppliers. S1: $10/unit, 95% fill rate, capacity 400 units. S2: $7/unit, 80% fill rate, capacity 500 units. S3: $5/unit, 60% fill rate, capacity 400 units. Find allocations that minimize cost and maximize fill rate.

Pareto Front (8 points):
| Cost ($) | Fill rate (%) | S1  |  S2  |  S3 |
|---|---|---|---|---|
| 6,500.00 | 73.5 | 100  |  500  |  400 |
| 6,714.30 | 75.0 | 142  |  500  |  357 |
| 6,928.55 | 76.5 | 185  |  500  |  314 |
| 7,142.85 | 78.0 | 228  |  500  |  271 |
| 7,357.15 | 79.5 | 271  |  500  |  228 |
| 7,571.45 | 81.0 | 314  |  500  |  185 |
| 7,785.70 | 82.5 | 357  |  500  |  142 |
| 8,000.00 | 84.0 | 400  |  500  |  100 |

Interpretation:
## Pareto Front Interpretation: Supply Sourcing

### What the Curve Tells You

**S2 is fully committed in every single solution** (always 500 units). The entire tradeoff is a substitution game between S3 (cheap/unreliable) and S1 (expensive/reliable) for the remaining 500 units. Each step along the curve shifts ~43 units from S3 to S1, costing **~$214 more** to gain **~1.5% fill rate** — roughly **$143 per percentage point of service level**.

The maximum achievable fill rate with these suppliers is only **84%** even at maximum spend, because S2's 80% rate is a structural ceiling on the blended result.

---

### Recommended Operating Points

| Point | Row | Cost | Fill Rate | S1 | S2 | S3 | Use When |
|---|---|---|---|---|---|---|---|
| **Low-cost anchor** | 1 | $6,500 | 73.5% | 100 | 500 | 400 | Commodity items, buffer stock available, elastic demand |
| **Balanced midpoint** | 4 | $7,143 | 78.0% | 228 | 500 | 271 | Standard operations, moderate SLA requirements |
| **High-fill anchor** | 8 | $8,000 | 84.0% | 400 | 500 | 100 | Critical launches, contractual penalty clauses, thin inventory |

**Who dominates each point:**
- **Low-cost**: S3 dominates volume (400 units); S1 is a token hedge (100 units)
- **Balanced**: S1 and S3 split evenly (~228/271); S2 unchanged
- **High-fill**: S1 maxed out (400 units); S3 reduced to minimum (100 units)

---

### Practical Takeaway

**Max out S2 first** (it's your best price-to-reliability ratio at $7/unit, 80%), then use the S1/S3 split as a service-level dial — paying ~$143 per point of fill rate you need above the baseline 73.5%.

LLM calls: 2
```
