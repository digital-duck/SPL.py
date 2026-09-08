# SPL Run: stackelberg_game

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 433 in / 738 out
- **Latency:** 35904ms
- **Timestamp:** 2026-09-07 07:13:52

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
## Why Backward Induction Overrules the LLM

### 1. Why Low despite (High, High) being Pareto-superior?

The leader cannot *enforce* (High, High). If the leader prices High, the follower earns $52K by undercutting vs $38K by matching — so the follower *always* defects. The leader anticipates this: High yields $12K, not $38K. Low guarantees $28K. The cooperative outcome collapses because there is no binding commitment mechanism.

---

### 2. Backward Induction — step by step

**Stage 2 — Follower's subgame (given each possible leader action):**

| Leader's price | Follower plays High | Follower plays Low | Follower's choice |
|---|---|---|---|
| High ($100) | $38K | **$52K** | **Low** |
| Low ($70) | $14K | **$22K** | **Low** |

Follower has a **dominant strategy: always price Low**, regardless of what the leader does.

**Stage 1 — Leader anticipates the follower's response:**

| Leader's price | Follower's response | Leader's payoff |
|---|---|---|
| High ($100) | Low | $12K |
| Low ($70) | Low | **$28K** ← choose this |

Leader's best response, given the follower will always undercut: **price Low**.

SPNE: **(Low, Low) → $28K / $22K**.

---

### 3. First-mover advantage — and does it exist here?

In classical Stackelberg *quantity* competition (Cournot), the leader commits to a large output, forcing the follower into a smaller residual market — a genuine first-mover advantage.

Here, **there is no first-mover advantage**. The follower's dominant strategy (Low) is independent of the leader's choice. The leader's "commitment power" buys nothing because the follower's best reply is the same regardless. The leader observes this and also plays Low — ending up at $28K, identical to what they'd earn in the simultaneous game (see §4).

The LLM's "signal quality" intuition would only be valid in a **repeated game** with reputation effects — irrelevant in this single-shot structure.

---

### 4. How this differs from the simultaneous Nash (r110)

In r110 (simultaneous play), both players choose without observing each other. The equilibrium is computed by checking dominant strategies:

- Follower: Low dominates regardless (same table as above).
- Leader: Low dominates regardless ($28K > $12K if follower is Low; $50K > $38K if follower is High, but follower never plays High).

**Simultaneous Nash equilibrium: (Low, Low) = $28K / $22K** — identical to the SPNE.

This is a degenerate case: when the follower has a **dominant strategy**, sequential and simultaneous play yield the same outcome. The leader's extra information (seeing the follower's decision rule in advance) is worthless here because that rule doesn't depend on the leader's action.

> **The structural reason:** First-mover advantage in Stackelberg pricing requires the follower's best response to be *responsive* to the leader's price. When the follower has a dominant strategy (Low always), the leader's commitment is inert — there is nothing to exploit.
```
