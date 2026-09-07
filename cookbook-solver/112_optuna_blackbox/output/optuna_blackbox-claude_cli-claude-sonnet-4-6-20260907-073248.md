# SPL Run: optuna_blackbox

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 391 in / 408 out
- **Latency:** 23298ms
- **Timestamp:** 2026-09-07 07:32:48

## Output

```output
=== Optuna Black-Box Optimization (r112) | solver=ON ===

## Optuna Black-Box Optimization — SaaS Pricing Strategy Optimization

**Trials:** 50  
**Best LTV:** $246.05/customer  
**Naive LTV:** $166.05/customer  
**Improvement:** +48.2%

| Parameter | Naive (LLM guess) | Optuna Best |
|---|---|---|
| monthly_price | $50 | $45.7 |
| annual_discount_pct | 20% | 3.6% |
| trial_days | 14 days | 30 days |

### Top 5 Trials

| Rank | Price | Discount | Trial Days | LTV |
|---|---|---|---|---|
| 1 | $45.7 | 3.6% | 30 days | $246.05 |
| 2 | $45.6 | 3.0% | 26 days | $241.01 |
| 3 | $44.3 | 2.5% | 26 days | $240.12 |
| 4 | $50.6 | 2.0% | 24 days | $234.73 |
| 5 | $38.9 | 3.3% | 27 days | $228.15 |

── Analytics Explanation ───────────────────────────────────
## Optuna Findings: SaaS Pricing Optimization

**1. What Optuna found:** The optimizer discovered a $246.05/customer LTV — a 48% lift over the naive $166.05 guess — by systematically exploring the 3D parameter space across 50 trials, converging on price~$45, discount~3%, trial~27 days.

**2. Why lower price wins:** Conversion is nonlinear. Dropping from $50→$45 likely crosses a psychological threshold, pulling in a larger cohort. The volume × retention gain outweighs the per-seat revenue loss — classic elasticity dominating margin.

**3. Why longer trial helps:** The naive 14-day trial underestimates activation time. Users who reach the "aha moment" by day 26–30 convert at higher rates *and* churn less, because they've internalized the product. Trial length buys retention quality, not just sign-ups.

**4. Non-convex objective:** The LTV surface has multiple local peaks (e.g., high-price/low-volume vs. low-price/high-volume regimes). Gradient descent gets trapped in whichever basin it starts in. TPE explores globally before exploiting, so it can jump between basins.

**5. Optuna vs. analytical model:**

| Use Optuna | Use Analytical |
|---|---|
| Black-box simulator or A/B data | Clean closed-form demand curve |
| Churn depends on usage patterns | Price elasticity is known/estimated |
| >3 interacting parameters | 1–2 parameters, smooth objective |
| Rapid experimentation needed | Stakeholder needs explainable formula |

The key signal here: the optimal annual discount (3.6%) is near-zero, suggesting customers aren't price-sensitive to commitment discounts — they just need time (trial days) to self-select.
```
