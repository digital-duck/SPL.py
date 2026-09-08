# SPL Run: openspiel_cfr

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 251 in / 739 out
- **Latency:** 48749ms
- **Timestamp:** 2026-09-07 08:04:57

## Output

```output
=== OpenSpiel CFR — Kuhn Poker (r116) | solver=OFF ===

── LLM Strategic Reasoning ─────────────────────────────────
## Kuhn Poker Strategy Analysis

### 1. When Should Player 1 Bet vs Pass?

**With K (strongest card):** Always bet. You win every showdown, so you want the pot as large as possible. Passing K is leaving money on the table.

**With Q (middle card):** Lean toward passing. Betting K is value-betting. Betting Q is betting into a range that folds everything you beat (J) and calls everything that beats you (K). The math doesn't work.

**With J (weakest card):** This is the critical decision. You *cannot* win a showdown, so your only path to profit is making P2 fold. Bet sometimes — but not always.

---

### 2. When Should Player 2 Call vs Fold?

| P2's Card | P1 Bet | Reasoning |
|-----------|--------|-----------|
| K | Always call | Best hand, can't lose |
| Q | Call sometimes | Beats J-bluffs, loses to K — decision depends on P1's bluff frequency |
| J | Always fold | Loses to everything |

The Q decision is the crux. If P1 *never* bluffs with J, P2 can safely fold Q to any bet — P1 only bets K and P2 can't beat K. But that lets P1 bluff for free.

---

### 3. Why Pure Strategy Fails

Suppose P1 plays purely: **always bet K, never bet J.**

P2 learns this pattern. When P1 bets, P2 knows it's K — so P2 folds Q every time. P1 with K wins only the antes (+1 chip), never the bet.

Now P1 passes K trying to trap. P2 with Q bets into P1's range. P1 calls... but P2 has already extracted the same information from the pass pattern.

**Any pure, predictable strategy leaks information.** Once P2 maps P1's action to a card, P2 plays perfectly against it. P1 gets no value from K bets and no steals from J.

---

### 4. Why Randomizing (Bluffing Sometimes with J) Is Better

When P1 occasionally bets J, P2 facing a bet now holds two possible worlds:

```
P1 bets → {K (value) or J (bluff)}
```

P2 with Q can beat a J-bluff but loses to K. P2 *cannot* fold all bets (P1 profits on every J-bluff) and *cannot* call all bets (P1 profits on every K value-bet). P2 is forced into a mixed response.

This is the key insight: **bluffing doesn't work because the bluff succeeds — it works because it makes your value bets harder to read.** A K-bet that P2 can't confidently fold to is worth far more than a K-bet P2 always folds to.

---

### Concrete Recommendations

**Player 1:**
- K → always bet
- Q → pass (fold equity doesn't justify the risk)
- J → bluff-bet roughly 1 in 3 times; pass the rest

**Player 2 (after P1 bets):**
- K → always call
- Q → call roughly 1 in 3 times (just enough that P1 can't bluff J profitably without risk)
- J → always fold

**Player 2 (after P1 passes):**
- K or Q → bet (either you're ahead or you can make P1 fold)
- J → pass (showdown is a losing proposition)

The equilibrium is stable precisely because neither player can unilaterally improve by shifting to a pure strategy — any pure deviation is exploitable by the other player adjusting. The randomization isn't indecision; it's what makes you unexploitable.

Note: LLM gives intuitive strategy (~0.25 exploitability).
Run --param use_solver=true to compute the Nash equilibrium
mixed strategy via CFR (converges to <0.05 exploitability).
```
