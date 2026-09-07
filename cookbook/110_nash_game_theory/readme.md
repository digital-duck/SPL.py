# Recipe 110 — Nash Equilibrium Game Theory

**The key story:** Two SaaS firms choose simultaneously between High (\$100/mo) and Low (\$70/mo) pricing. nashpy proves (Low, Low) is the unique Nash equilibrium via support enumeration — a Prisoner's Dilemma where each firm earns \$25K/mo instead of the cooperative \$40K/mo. Unusually, solver=OFF was also correct: the LLM correctly traced the dominant-strategy argument (Low beats High in both scenarios) and reached the same verdict. The gap between nashpy and LLM emerges only in games without dominant strategies — mixed-strategy equilibria, 3+ players, or multiple equilibria — where the LLM's combinatorial intuition breaks down.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | nashpy support enumeration | LLM dominant-strategy reasoning |
| Output | All Nash equilibria + Prisoner's Dilemma gap | Correctly identifies Low as dominant; reaches (Low, Low) Nash |
| Guarantee | Mathematically verified (no profitable unilateral deviation) | Correct on this 2×2 dominant-strategy case; fails on mixed-strategy games |
| Verification | `ASSERT nash_found` (C1) | — |
| Solver class | C1 (categorical: equilibrium found / not found) | — |

## The payoff matrix (profits in \$K/month)

|  | **B: High** | **B: Low** |
|---|---|---|
| **A: High** | (40, 40) ← joint optimum | (10, 55) |
| **A: Low** | (55, 10) | **(25, 25) ← Nash** |

**Why (Low, Low) is Nash**: If B plays High, A earns 55 by playing Low vs 40 by playing High → A defects. If B plays Low, A earns 25 by playing Low vs 10 by playing High → A still defects. Low is a dominant strategy for A (and by symmetry, for B). The Nash equilibrium is where both dominant strategies intersect.

**Prisoner's Dilemma gap**: Each firm earns \$25K/mo at Nash vs \$40K/mo at the joint optimum — \$15K/mo per firm, \$30K/mo combined, is destroyed by rational self-interest.

## Run results — solver=ON vs solver=OFF

Both runs: `claude_cli` / `claude-sonnet-4-6`, default SaaS pricing duopoly (2 players, 2 strategies each).

| Metric | solver=ON | solver=OFF |
|---|---|---|
| Timestamp | 2026-09-07 06:55:09 | 2026-09-07 06:55:24 |
| Tokens in | 387 | 292 |
| Tokens out | 239 | 754 |
| Total tokens | 626 | 1,046 (+67%) |
| Latency | 13.7s | 36.5s (2.7×) |
| Nash equilibrium found | (Low, Low) ✓ | (Low, Low) ✓ |
| PD gap identified | \$15K/firm, \$30K combined ✓ | \$15K/firm, \$30K combined ✓ |
| Dominant strategy traced | ✓ (algebraic) | ✓ (verbal reasoning) |
| Defection mechanisms listed | grim-trigger, price-signaling, contracts | repeated interaction, transparent pricing, signaling, differentiation |

### Both correct — but for different reasons

solver=ON ran nashpy support enumeration over the 2×2 payoff matrix and returned the unique Nash equilibrium as a formal result with no profitable unilateral deviation. solver=OFF traced the dominant-strategy argument verbally: "Low beats High in both scenarios, therefore Low dominates" — the same mathematical logic, expressed in prose.

The solver=OFF LLM did **not** fall into the cooperative reasoning trap ("both should price High for mutual benefit"). It correctly prioritized individual rationality over collective optimality and recognized the Prisoner's Dilemma structure.

### Why solver=OFF succeeded here — and where it would fail

This game has a **dominant strategy**: Low beats High for every possible opponent move. Dominant-strategy games are LLM-friendly because the argument is a simple case analysis (2 scenarios × 2 options = 4 cells). The LLM only needs to compare payoffs cell-by-cell, which is within its arithmetic reach.

Solver=OFF breaks down in:

| Game type | Problem | nashpy |
|---|---|---|
| **Mixed-strategy Nash** | No dominant strategy; equilibrium is a probability distribution (e.g., Rock-Paper-Scissors) | ✓ computes exact mixing probabilities |
| **Multiple equilibria** | Equilibrium selection; LLM picks one arbitrarily or picks the cooperative optimum | ✓ enumerates all equilibria |
| **3-player games** | Combinatorial argument has 3×N²×M cells; LLM loses track | ✓ (see r115 pygambit) |
| **Non-symmetric payoffs** | Small asymmetries change equilibrium; LLM anchors on symmetry | ✓ exact |

### Key takeaway

solver=ON is 2.7× faster and 40% cheaper. Both are correct on this canonical Prisoner's Dilemma because dominant-strategy reasoning is the simplest case in game theory. The value of nashpy is not demonstrated here — it becomes decisive when the game lacks a dominant strategy, has mixed-strategy equilibria, or involves 3+ players (see r115 pygambit for a 3-player case where the LLM fails).

## Run commands

```bash
# solver=ON — nashpy Nash equilibrium
spl3 run cookbook/110_nash_game_theory/nash_game_theory.spl \
    --llm claude_cli --param use_solver=true

# solver=OFF — LLM strategic reasoning
spl3 run cookbook/110_nash_game_theory/nash_game_theory.spl \
    --llm claude_cli --param use_solver=false
```

## Install

```bash
conda activate spl123
pip install nashpy
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_game()` | Returns SaaS pricing duopoly game JSON (payoff matrices) |
| `find_nash_equilibria(game_json)` | nashpy support enumeration → all equilibria + PD gap |
| `nash_found(result_json)` | ASSERT gate: at least 1 equilibrium found |
| `format_nash_report(result_json)` | Markdown tables: equilibria + joint optimum + gap |

## Game theory concepts

- **Normal-form game**: players choose strategies simultaneously (no time structure)
- **Nash equilibrium**: no player can improve payoff by changing their strategy unilaterally
- **Dominant strategy**: a strategy that is best regardless of what the opponent does
- **Prisoner's Dilemma**: dominant-strategy Nash is Pareto-inferior (everyone worse off than cooperation)
- **Support enumeration**: nashpy's algorithm finds all Nash equilibria by iterating over support pairs

## Related recipes

- r111: Stackelberg sequential game (extensive form — leader goes first)
- r102: Z3 eligibility rules (constraint satisfiability, not game equilibria)
- r107: workforce multi-objective (Pareto — tradeoffs without strategic interaction)
