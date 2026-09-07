# SPL Run: openspiel_cfr

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 492 in / 464 out
- **Latency:** 17172ms
- **Timestamp:** 2026-09-07 08:04:45

## Output

```output
=== OpenSpiel CFR — Kuhn Poker (r116) | solver=ON ===

## CFR Report — Kuhn Poker

**Iterations:** 1000  
**Exploitability:** 0.0009 (threshold: 0.05)  
**Converged to Nash:** Yes ✓

### Average Policy at Key Information Sets

| Info set | Pass / Check | Bet / Call |
|---|---|---|
| P1:0 | 0.806 | 0.194 |
| P1:0pb | 1.000 | 0.000 |
| P1:1 | 0.993 | 0.007 |
| P1:1pb | 0.469 | 0.531 |
| P1:2 | 0.416 | 0.584 |
| P1:2pb | 0.001 | 0.999 |
| P2:0b | 1.000 | 0.000 |
| P2:0p | 0.667 | 0.333 |
| P2:1b | 0.664 | 0.336 |
| P2:1p | 0.996 | 0.004 |
| P2:2b | 0.000 | 1.000 |
| P2:2p | 0.001 | 0.999 |

### Known Nash Equilibrium (Kuhn Poker)

> Player 1: Bet with K always (1.0), Bet with J at probability 1/3 (bluff), Pass with Q always. Player 2: Call with K always, Call with Q at probability 1/3, Pass with J always.

### Exploitability Interpretation

| Policy | Exploitability | Meaning |
|---|---|---|
| Perfect Nash | 0.000 | Unexploitable — best response cannot gain |
| CFR avg (this run) | 0.001 | Near-Nash ✓ |
| LLM naive (bet-K-only) | ~0.250 | Exploitable — opponent folds J/Q, always calls K |

── Game Theory Explanation ─────────────────────────────────
## CFR Analysis: Kuhn Poker Nash Equilibrium

**1. Exploitability**
Exploitability measures how many chips per game a best-responding opponent can extract against your fixed strategy. At 0.001, an optimal adversary gains essentially nothing — your strategy is a near-perfect Nash equilibrium. A player wants this near zero because any exploitable pattern (always bluff, never bluff) becomes a free money pump once the opponent detects it.

**2. CFR's Mixed Strategy and Why Bluffing is Optimal**
CFR converged to: bet K always (0.584), bluff J ~19% of the time, check Q always. Bluffing with J at ~1/3 frequency is optimal because it keeps Player 2 *indifferent* between calling and folding when facing a bet. If P2 can't distinguish a J-bluff from a K-value-bet, calling yields the same EV as folding — P1 captures maximum value with K without being exploited.

**3. Pure Strategy Fails**
If P1 never bluffs, P2 folds everything except K to any bet. P1's K-bets win only 1 chip instead of 2 (when P2 would have called a bluff-protected bet). The threat of the bluff is what makes P2 call — remove it and P1 leaves chips on the table.

**4. Generalization**
CFR solves any finite extensive-form game with imperfect information by iteratively minimizing regret across every decision node. In no-limit Hold'em (Libratus/Pluribus), the same principle scales via abstraction: group similar hands into buckets, run CFR, then map solutions back. In sealed auctions, private valuations play the role of hole cards — bidding slightly above true value is the bluff analog. In multi-round negotiation, CFR handles sequential private signals (e.g., budget constraints) by building a strategy *tree* where each node's mixed action prevents the opponent from reverse-engineering your position — exploitability becomes the negotiation analog of leaving money on the table.
```
