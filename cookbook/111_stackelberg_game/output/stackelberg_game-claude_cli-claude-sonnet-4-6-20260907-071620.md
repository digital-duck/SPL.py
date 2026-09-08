# SPL Run: stackelberg_game

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 433 in / 389 out
- **Latency:** 30676ms
- **Timestamp:** 2026-09-07 07:16:20

## Output

```output
=== Stackelberg Game (r111) | solver=ON ===

## Stackelberg Game Report — Stackelberg Pricing Duopoly

### Subgame-Perfect Nash Equilibrium (backward induction)

| Step | Player | Action |
|---|---|---|
| 1 | Leader | Low ($70) |
| 2 | Follower | Low ($70) |

**Outcome:** (Low, Low) -> Leader=$28K, Follower=$22K
**Leader payoff (SPNE):** $28K/mo
**Follower payoff (SPNE):** $22K/mo

### LLM Prediction vs SPNE

- **LLM:** Leader should price High ($100) to signal quality
- **SPNE:** SPNE: Leader plays 'Low ($70)' (earns $28K) vs LLM: 'Leader should price High ($100) to signal quality'

── Explanation ─────────────────────────────────────────────
## Stackelberg Pricing Game — Analysis

**1. Why Low despite (High, High) being jointly better?**
The follower has a dominant strategy: undercutting always pays more (High→52K vs 38K; Low→22K vs 14K). The leader cannot trust the follower to hold High, so (High, High) is not self-enforcing — it collapses the moment the follower defects.

**2. Backward induction, step by step**
- *Follower's subgame if Leader=High:* 52K (Low) > 38K (High) → Follower plays **Low**
- *Follower's subgame if Leader=Low:* 22K (Low) > 14K (High) → Follower plays **Low**
- Follower plays Low regardless. Leader now chooses: High→12K vs Low→28K → Leader plays **Low**
- SPNE: **(Low, Low)**

**3. First-mover "advantage"?**
There is none here. Classical Stackelberg quantity games give the leader an advantage because committing to a large output *shifts* the follower's best response downward. In this pricing game, the follower's best response is constant (always Low), so commitment buys nothing. The leader is actually worse off than (High, High) = 38K — they earn only 28K.

**4. Difference from simultaneous Nash (r110)**
In the simultaneous game, Low is still the follower's dominant strategy, so the NE is also (Low, Low). The outcome is identical. The distinction is *reasoning path*: the simultaneous game finds a fixed point (no player wants to deviate); the Stackelberg game uses backward induction over the game tree. When the follower has a dominant strategy, sequential structure adds no strategic leverage — both solution concepts converge to the same outcome.
```
