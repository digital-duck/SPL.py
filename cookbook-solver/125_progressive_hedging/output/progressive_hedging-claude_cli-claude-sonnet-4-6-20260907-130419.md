# SPL Run: progressive_hedging

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 454 in / 342 out
- **Latency:** 15057ms
- **Timestamp:** 2026-09-07 13:04:19

## Output

```output
=== Progressive Hedging — Battery Storage (r125) | solver=ON ===

## Progressive Hedging Report — Battery Storage Investment

**Scenarios:** 30  
**PH iterations:** 1  
**Converged:** Yes ✓  
**Primal residual:** 0.0 MW  
**Solve time:** 0.0s  

### Investment Decision

| | PH (stochastic) | EV (mean scenario) |
|---|---|---|
| Capacity (MW) | **100.0** | 100.0 |
| Capital cost ($/yr) | $800,000.0 | — |
| Annual net value (profit − capital, $) | **$2,252,629.0** | $2,252,629.0 |
| **Value of Stochastic Solution (VSS)** | **$0.0** | baseline |

VSS = RP_profit − EV_profit: the annual dollar gain from solving with
all 30 scenarios vs. optimizing on the mean alone.
Positive VSS means the stochastic solution earns more than the EV policy.

── Analyst Explanation ─────────────────────────────────────
## Progressive Hedging: Conceptual Breakdown

**1. Non-Anticipativity**
Stage 1 (capacity investment) must be decided *before* any scenario reveals itself. Non-anticipativity means all scenarios must share the same Stage 1 decision — you cannot invest 60 MW "in scenario 7" and 100 MW "in scenario 12." The constraint x₁(ω) = x̄ for all ω ∈ Ω enforces this.

**2. PH Penalty Mechanism**
PH adds a quadratic penalty `(ρ/2)||x₁(ω) − x̄||²` to each scenario subproblem, where x̄ is the current consensus (scenario-average) capacity. Each subproblem is solved independently, then x̄ is updated. As ρ → ∞, deviating from consensus becomes infinitely costly, forcing all scenarios to agree on identical Stage 1 decisions — non-anticipativity is recovered in the limit.

**3. VSS = $0 Here**
The battery hit the 100 MW cap under *every* scenario and the mean scenario alike. When the optimal decision is corner-pinned by a binding constraint, stochastic information adds no value — the EV policy already finds the global optimum.

**4. PH vs. Extensive Form**
Solve the full extensive form when scenario count is small (< a few hundred) and the joint problem fits in memory. Use PH when scenarios number in the thousands, subproblems are large MIPs (parallelism across nodes), or the extensive form exceeds solver memory limits — PH trades iteration count for decomposability.
```
