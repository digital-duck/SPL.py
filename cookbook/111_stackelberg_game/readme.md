# Recipe 111 — Stackelberg Sequential Game (Backward Induction)

**The key story:** A market leader sets subscription price first; the follower observes and responds. The LLM's unconstrained first-pass intuition: "price High ($100) to signal quality" — wrong. Backward induction proves (Low, Low) is the SPNE: the follower always undercuts regardless of the leader's move, so the leader's best response is also Low ($28K vs $12K). When solver=OFF is explicitly prompted to trace backward induction step by step, it also reaches the correct answer — but the LLM's spontaneous qualitative reasoning would mislead.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | Backward induction (pure Python) | LLM explicit backward induction trace |
| Structure | Extensive form: leader moves first, follower observes | Correctly traces 2-level subgames when prompted |
| LLM first-pass | Captured: "Leader should price High to signal quality" (wrong) | — |
| Output | SPNE: (Low, Low) → $28K/$22K + gap from LLM prediction | (Low, Low) → $28K/$22K — same result via verbal reasoning |
| Verification | `ASSERT spne_solved` (C1) | — |
| Solver class | C1 (categorical: SPNE found) | — |

## The game tree

```
Leader chooses:
├── High ($100)
│   └── Follower responds:
│       ├── High ($100) → Leader=$38K, Follower=$38K
│       └── Low  ($70)  → Leader=$12K, Follower=$52K  ← follower best-response
└── Low ($70)
    └── Follower responds:
        ├── High ($100) → Leader=$50K, Follower=$14K
        └── Low  ($70)  → Leader=$28K, Follower=$22K  ← follower best-response
```

**Backward induction**:
1. If leader plays High: follower chooses Low ($52K > $38K) → leader gets $12K
2. If leader plays Low: follower chooses Low ($22K > $14K) → leader gets $28K
3. Leader compares: $28K (play Low) > $12K (play High) → **leader plays Low**

**SPNE**: (Low, Low) → Leader=$28K, Follower=$22K

## Simultaneous vs Sequential (r110 vs r111)

| | r110 (Nash, simultaneous) | r111 (SPNE, sequential) |
|---|---|---|
| Game structure | Both choose at same time | Leader commits first |
| Solution concept | Nash equilibrium | Subgame-perfect Nash equilibrium |
| Outcome | (Low, Low) = ($25K, $25K) | (Low, Low) = ($28K, $22K) |
| Leader advantage | None (symmetric) | +$3K from first-mover anticipation |

## Run results — solver=ON vs solver=OFF

Both runs: `claude_cli` / `claude-sonnet-4-6`, default Stackelberg pricing duopoly.

| Metric | solver=ON | solver=OFF |
|---|---|---|
| Timestamp | 2026-09-07 07:16:20 | 2026-09-07 07:16:56 |
| Tokens in | 433 | 394 |
| Tokens out | 389 | 660 |
| Total tokens | 822 | 1,054 (+28%) |
| Latency | 30.7s | 34.9s (+14%) |
| LLM first-pass intuition | "Price High to signal quality" ✗ | — |
| Final SPNE verdict | (Low, Low): Leader $28K, Follower $22K ✓ | (Low, Low): Leader $28K, Follower $22K ✓ |
| LLM calls | 2 | 3 |

### The two-stage reveal in solver=ON

The solver=ON workflow makes the LLM's reasoning failure explicit. It runs in two stages:

1. **LLM prediction (unconstrained):** "Leader should price High ($100) to signal quality" — qualitative branding intuition, not game-theoretic reasoning.
2. **Backward induction:** Follower always plays Low (dominant strategy); leader anticipates this and plays Low → SPNE = (Low, Low). The prediction was wrong.

The explanation LLM is then anchored to the verified SPNE and correctly traces the backward induction proof, including the counter-intuitive finding that first-mover advantage does not exist here.

### solver=OFF succeeded — with the right prompt

Solver=OFF explicitly prompted the LLM to trace each subgame ("work backwards from the follower's best response"). Under that framing the LLM correctly computed:

| Leader's choice | Follower best response | Leader payoff |
|---|---|---|
| High | Low ($52K > $38K) | **$12K** |
| Low | Low ($22K > $14K) | **$28K** |

→ Leader plays Low. SPNE correct.

**The trap:** If the LLM were asked casually — "what price should a Stackelberg leader set?" — it defaults to "High, to signal quality." That's the answer from branding/reputation theory, not game theory. The solver=ON workflow catches this by capturing the LLM's unanchored first guess before any structured reasoning. Solver=OFF only succeeds because the prompt scaffolds the backward induction argument.

### Contrast with r110 (simultaneous Nash)

In r110 (simultaneous Prisoner's Dilemma), solver=OFF succeeded without explicit scaffolding — the LLM found the dominant strategy on its own. Here, the game is sequential (extensive form), which requires backward induction rather than dominance reasoning. That extra step is where LLM intuition slips into qualitative heuristics ("signal quality"). The backward induction solver is the corrective.

### Key takeaway

solver=ON is 22% cheaper and reveals the LLM's first-pass error explicitly. The backward induction algorithm is not complicated — but it is a formal fixed procedure that doesn't drift toward branding intuition. The solver=OFF LLM is correct only when the prompt forces it into the backward induction frame; unanchored, it would give the wrong answer.

## Run commands

```bash
# solver=ON — backward induction
spl3 run cookbook/111_stackelberg_game/stackelberg_game.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM sequential reasoning
spl3 run cookbook/111_stackelberg_game/stackelberg_game.spl \
    --adapter ollama -m gemma3 --param use_solver=false
```

## Install

```bash
conda activate spl123
# No additional install — pure Python backward induction
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_game()` | Returns Stackelberg game tree JSON |
| `solve_stackelberg(game_json)` | Backward induction → SPNE path + payoffs |
| `spne_solved(result_json)` | ASSERT gate: status OK |
| `format_stackelberg_report(result_json)` | Markdown: SPNE path table + LLM comparison |

## Related recipes

- r110: Nash equilibrium (simultaneous game — no time structure)
- r112: Optuna black-box (no strategic interaction, just parameter optimization)
- r102: Z3 SMT (logical constraint satisfiability, not game equilibria)
