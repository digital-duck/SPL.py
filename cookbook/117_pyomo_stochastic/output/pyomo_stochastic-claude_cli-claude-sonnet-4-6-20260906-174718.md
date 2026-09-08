# SPL Run: pyomo_stochastic

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 64 in / 0 out
- **Latency:** 96340ms
- **Timestamp:** 2026-09-06 17:47:18

## Output

```output
=== Two-Stage Stochastic Programming (r117) | solver=OFF ===

── LLM Reasoning Under Uncertainty ─────────────────────────
## Step-by-Step Reasoning

### 1. Should you order exactly 190?

No. The expected value tells you where demand *averages*, not where costs balance. Ordering 190 exposes you to shortages in both the nominal scenario (200 − 190 = 10 units short, probability 50%) and the high scenario (110 units short, probability 20%). Those shortfalls are costly, and averaging demand doesn't account for *what it costs when you're wrong*.

### 2. How does cost asymmetry affect the decision?

Shortage costs $15/unit; excess costs $2/unit. Running short is **7.5× more expensive per unit** than overstocking. This means the cost of guessing low is far more damaging than the cost of guessing high. The rational response is to bias your order *above* the expected demand to insure against the expensive shortage outcome.

### 3. Downside risk of each error

| Mistake | Worst-case exposure | Probability |
|---|---|---|
| Order too little (e.g., 100) | 200-unit shortage = $3,000 penalty | 20% (high demand) |
| Order too much (e.g., 300) | 200-unit overstock = $400 holding cost | 30% (low demand) |

The overstock downside is capped and cheap. The shortage downside is open-ended and expensive. Asymmetric costs create asymmetric risk.

### 4. Recommendation: Order **200 units**

Work through the three candidate quantities:

**Q = 190 (expected demand)**
- Low: 90 excess × $2 = $180 holding; order cost $950 → $1,130
- Nominal: 10 shortage × $15 = $150; order cost $950 → $1,100
- High: 110 shortage × $15 = $1,650; order cost $950 → $2,600
- **Expected cost: 0.3(1,130) + 0.5(1,100) + 0.2(2,600) = $1,409**

**Q = 200 (nominal scenario)**
- Low: 100 excess × $2 = $200; order cost $1,000 → $1,200
- Nominal: exact fit, no penalty → $1,000
- High: 100 shortage × $15 = $1,500; order cost $1,000 → $2,500
- **Expected cost: 0.3(1,200) + 0.5(1,000) + 0.2(2,500) = $1,360**

**Q = 300 (full coverage)**
- Low: 200 excess × $2 = $400 holding; order cost $1,500 → $1,900
- Nominal: 100 excess × $2 = $200; order cost $1,500 → $1,700
- High: exact fit → $1,500
- **Expected cost: 0.3(1,900) + 0.5(1,700) + 0.2(1,500) = $1,720**

**Order 200.** It covers the most likely scenario exactly (50% probability), accepts the one costly shortage risk only in the 20%-probability high case, and avoids the heavy holding costs of full coverage. Moving from 190 → 200 saves $49 in expected cost. Moving from 200 → 300 *adds* $360 in holding costs while only saving $100 in expected shortage costs — a losing trade.

The principle at work: when shortage is far more expensive than overstock, you hedge upward — but only until the marginal holding cost of one more unit exceeds the marginal shortage savings it prevents. That crossover happens at 200 in this discrete demand structure.

Note: LLM applies intuition but typically defaults to ordering the expected
demand (Q=190, cost=$1,409). Run --param use_solver=true to see Pyomo's
stochastic optimum (Q=200, cost=$1,360 — VSS=$49 improvement).
```
