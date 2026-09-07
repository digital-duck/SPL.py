# SPL Run: gambit_3player

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 507 in / 462 out
- **Latency:** 15242ms
- **Timestamp:** 2026-09-07 07:52:29

## Output

```output
=== Gambit 3-Player Game Theory (r115) | solver=ON ===

## 3-Player Nash Equilibrium Report — 3-Firm SaaS Pricing Triopoly

**Solver:** pygambit  
**Players:** Firm A, Firm B, Firm C  
**Nash equilibria found:** 1

### Nash Equilibria

| # | Firm A | Firm B | Firm C | Payoff A | Payoff B | Payoff C |
|---|---|---|---|---|---|---|
| 1 | Standard | Standard | Standard | $120.0K | $120.0K | $120.0K |

### Cooperative Optimum (NOT a Nash equilibrium)

| Firm A | Firm B | Firm C | Payoff A | Payoff B | Payoff C |
|---|---|---|---|---|---|
| Premium | Premium | Premium | $200K | $200K | $200K |

> *Collective optimum is unstable: every firm can unilaterally*
> *gain by defecting to Standard, making Premium unsustainable.*

### Prisoner's Dilemma Gap

Nash ['Standard', 'Standard', 'Standard'] → each earns $120.0K; cooperative ['Premium', 'Premium', 'Premium'] → each earns $200K; gap = $80.0K/firm

── Business Explanation ────────────────────────────────────
## Nash Equilibrium Analysis — 3-Firm SaaS Pricing Triopoly

**1. The Nash Equilibrium**
All three firms price at Standard ($120K/mo each). No firm can unilaterally improve its outcome — switching to Premium while rivals stay Standard drops your payoff to $80K. In business terms: a race-to-the-bottom where rational individual decisions destroy collective value.

**2. Why Standard Dominates**
Compare any firm's options holding rivals fixed: if rivals play (P,P), defecting to S pays $300K vs $200K. If rivals play (S,P), defecting to S pays $260K vs $80K. If rivals play (S,S), S still pays $120K vs $80K. Standard strictly dominates in every scenario — it's the safe move regardless of what competitors do.

**3. The Prisoner's Dilemma Gap**
Nash outcome: $120K/firm. Cooperative optimum: $200K/firm. **Gap = $80K/firm/month** — $240K in monthly industry value destroyed by rational self-interest.

**4. Harder Than 2-Player**
With two firms, a single defection breaks the cartel. With three, there are more potential defectors and fewer bilateral trust relationships to maintain. Coordination requires unanimous discipline across all three — one weak link collapses the Premium equilibrium for everyone.

**5. Real-World Escape Mechanisms**
- **Signaling/price leadership**: one firm publicly anchors at Premium, signaling intent before others move
- **Product differentiation**: make Premium genuinely incomparable (features, brand) so Standard isn't a true substitute
- **Contractual lock-in**: annual contracts reduce the tempo of defection opportunities
- **Regulatory floors**: industry minimum pricing agreements (legally constrained in most markets)
- **Reputation/repeated game**: if firms interact indefinitely, future retaliation threats (tit-for-tat) can sustain cooperation — but this requires low discount rates and no exit threat
```
