# SPL Run: optuna_blackbox

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 319 in / 713 out
- **Latency:** 47729ms
- **Timestamp:** 2026-09-07 07:35:26

## Output

```output
=== Optuna Black-Box Optimization (r112) | solver=OFF ===

── LLM Heuristic Strategy ──────────────────────────────────
## Recommended Parameters

| Parameter | Recommended Value | Range |
|---|---|---|
| `monthly_price` | **$79** | $30–$120 |
| `annual_discount_pct` | **20%** | 0%–40% |
| `trial_days` | **14** | 3–30 |

---

## Reasoning

### monthly_price → $79

The LTV function has a nonlinear relationship with price. Too low ($30–$49) signals low value and leaves money on the table. Too high ($99+) triggers justification friction — prospects stall, require more touchpoints, and churn faster after converting.

$79 hits three practical sweet spots:
- Sits below the $80 psychological barrier (same effect as $99 but cheaper perception)
- Strong enough value signal to attract quality customers (low-price products attract high-churn bargain hunters)
- Revenue-per-user high enough to absorb a ~15–20% conversion rate and still generate meaningful LTV

At $49 with identical churn, you'd need ~60% more customers to match $79's LTV. That's a worse bet unless CAC is near zero.

### annual_discount_pct → 20%

Annual discount is the single highest-leverage LTV variable because it attacks churn directly.

Empirically, annual subscribers churn at roughly 1/3 the rate of monthly subscribers (monthly churn ~5% vs ~1.5–2% annualized). A 20% discount (the "2 months free" framing) shifts roughly 35–45% of converting users to annual plans.

LTV impact of moving a customer from monthly to annual at 20% discount:

- Monthly: $79 / 5% monthly churn = **$1,580 LTV**
- Annual (effective $63.20/mo): $63.20 / 1.7% monthly churn = **$3,718 LTV**

That's a **2.4× LTV multiplier** despite the 20% revenue haircut. At 40% discount the math still works, but you're leaving $15/mo on the table without proportional churn benefit — annual customers are committed regardless of whether the discount is 20% or 40%.

### trial_days → 14

Three-to-seven-day trials under-deliver: most SaaS products require 2–3 meaningful sessions before users internalize the core value loop. Cutting off at day 7 truncates the conversion funnel before it matures.

Thirty-day trials have the opposite problem: they attract tire-kickers, create "I'll decide later" behavior, and delay the cash-flow clock by 2–3 weeks per cohort.

Fourteen days is long enough to reach the activation milestone in most products (typically day 4–8), and short enough that the ending creates genuine urgency. Behavioral data from SaaS cohorts consistently shows day-11 through day-13 as the peak conversion window in 14-day trials — users are still engaged and feel the deadline.

---

## Expected LTV Estimate

Blended ARPU assuming 40% annual uptake: ~$72/month  
Blended monthly churn: ~2.8%  
**Estimated LTV: ~$2,570 per converted customer**

The biggest upside lever from here is pushing annual plan adoption above 40% — consider making the annual offer more prominent at trial end rather than adjusting prices.

Note: LLM guesses from intuition without exploring the search space.
Run --param use_solver=true to let Optuna TPE find the optimum in 50 trials.
```
