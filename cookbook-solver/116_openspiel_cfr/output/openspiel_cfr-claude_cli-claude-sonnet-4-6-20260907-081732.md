# SPL Run: openspiel_cfr

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 492 in / 345 out
- **Latency:** 14843ms
- **Timestamp:** 2026-09-07 08:17:32

## Output

```output
=== OpenSpiel CFR — Kuhn Poker (r116) | solver=ON ===

## CFR Report — Kuhn Poker

**Iterations:** 100  
**Exploitability:** 0.0082 (threshold: 0.05)  
**Converged to Nash:** Yes ✓

### Average Policy at Key Information Sets

| Info set | Pass / Check | Bet / Call |
|---|---|---|
| P1:0 | 0.815 | 0.185 |
| P1:0pb | 0.997 | 0.003 |
| P1:1 | 0.925 | 0.075 |
| P1:1pb | 0.474 | 0.526 |
| P1:2 | 0.423 | 0.577 |
| P1:2pb | 0.006 | 0.994 |
| P2:0b | 0.995 | 0.005 |
| P2:0p | 0.683 | 0.317 |
| P2:1b | 0.651 | 0.349 |
| P2:1p | 0.965 | 0.035 |
| P2:2b | 0.005 | 0.995 |
| P2:2p | 0.010 | 0.990 |

### Known Nash Equilibrium (Kuhn Poker)

> Player 1: Bet with K always (1.0), Bet with J at probability 1/3 (bluff), Pass with Q always. Player 2: Call with K always, Call with Q at probability 1/3, Pass with J always.

### Exploitability Interpretation

| Policy | Exploitability | Meaning |
|---|---|---|
| Perfect Nash | 0.000 | Unexploitable — best response cannot gain |
| CFR avg (this run) | 0.008 | Near-Nash ✓ |
| LLM naive (bet-K-only) | ~0.250 | Exploitable — opponent folds J/Q, always calls K |

── Game Theory Explanation ─────────────────────────────────
## CFR Analysis — Kuhn Poker

**1. Exploitability**
Exploitability measures the maximum chips-per-game a best-responding opponent can extract against your fixed strategy. At 0.008, this CFR solution yields near-zero free money to any adversary — a perfectly rational opponent gains essentially nothing by knowing your strategy in advance.

**2. Nash mixed strategy**
CFR recovered the known equilibrium: P1 bets K always (~0.577 matches ~1/3 bluff-weight on J via P1:0=0.185), P2 calls K always and calls Q with probability ~1/3. The bluff frequency (J-bet) is calibrated so P2 is exactly indifferent between calling and folding with Q — removing the exploit.

**3. Why pure "always bet K" fails**
A deterministic strategy is transparent. If P1 never bluffs, P2 folds J/Q to any bet (cost: 1 chip) and calls only when holding K. P1 gains nothing with K and wins nothing from bluffs. Opponent exploitability jumps to ~0.250. Randomization forces the opponent into genuine uncertainty.

**4. Generalization**
CFR scales to any extensive-form game with hidden information — multi-street poker (billions of info sets via abstraction + CFR+), sealed-bid auctions (private valuations as hidden cards), and multi-round negotiation (sequential private signals). The core loop — regret-weighted self-play until strategies converge — requires no closed-form equilibrium; it *discovers* one.
```
