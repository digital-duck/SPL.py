# Recipe 125 — Progressive Hedging: Battery Storage Investment

**Solver class:** Parallel Stochastic Programming (Two-Stage SP, Scenario Decomposition)  
**Backend:** Progressive Hedging (custom Python PH loop over Pyomo/HiGHS subproblems)  
**Dependency:** `pip install pyomo highspy`

## What it demonstrates

Extends r117 (3-scenario monolithic stochastic LP) to **30-scenario** two-stage stochastic
programming via **Progressive Hedging (PH)** decomposition. PH solves each scenario as
an independent subproblem and enforces non-anticipativity via a quadratic penalty term.
This is how real stochastic programs scale: not by building a giant monolithic model,
but by decomposing by scenario and coordinating with a penalty.

| | r117 (3 scenarios) | r125 (30 scenarios) |
|---|---|---|
| Method | Monolithic extensive form | Progressive Hedging decomposition |
| Stage 1 vars | 1 (capacity) | 1 (capacity) |
| Stage 2 vars | 3×24 = 72 | 30×24 = 720 |
| Memory | Scales with scenarios | Bounded (one subproblem at a time) |
| Parallelism | None (monolithic) | Each scenario independent |
| Convergence | Immediate (LP) | PH iterations until residual < 0.5 MW |

## The problem: battery storage investment

**Stage 1 (here-and-now):** Choose `capacity_MW ∈ [0, 100]` before knowing which demand
scenario will occur. Capital cost: $150,000/MW.

**Stage 2 (recourse):** Given the realized scenario (demand + price profile), choose hourly
`charge[t]` and `discharge[t]` to maximize arbitrage revenue.

**30 scenarios:** Random demand scaling factors (0.7×–1.4×) and correlated electricity
prices. Each scenario has a 24-hour demand/price profile.

**Non-anticipativity:** All scenarios must use the *same* Stage 1 decision. You cannot
invest differently in different scenarios — you commit to one capacity before the scenario
is revealed. PH enforces this by penalizing scenario-specific capacity decisions that
deviate from the consensus.

## Run

```bash
# solver=ON: Progressive Hedging across 30 scenarios
spl3 run cookbook-solver/125_progressive_hedging/progressive_hedging.spl \
    --adapter claude_cli --param use_solver=true

# More scenarios (slower, better convergence demo)
spl3 run cookbook-solver/125_progressive_hedging/progressive_hedging.spl \
    --adapter claude_cli --param use_solver=true --param n_scenarios=50

# solver=OFF: deterministic EV (mean scenario) + LLM reasoning
spl3 run cookbook-solver/125_progressive_hedging/progressive_hedging.spl \
    --adapter ollama -m gemma3 --param use_solver=false
```

## Install

```bash
pip install pyomo highspy
# HiGHS is the LP/MIP solver used for each scenario subproblem.
# For MPI-based PH at scale: pip install mpi4py mpi-sppy
```

## Background: Progressive Hedging algorithm

Given scenarios S with probabilities p_s and shared first-stage variable x:

```
1. Initialize: solve each scenario independently → x_s^0
2. Compute consensus: x̄ = Σ p_s · x_s
3. Update multipliers: w_s += ρ · (x_s - x̄)
4. Re-solve each scenario with augmented cost: min c(x,y) + w_s·x + (ρ/2)·‖x - x̄‖²
5. Repeat from 2 until max|x_s - x̄| < tolerance
```

The penalty ρ pulls scenario solutions toward the consensus. As ρ → ∞, all scenarios
converge to the same x (perfect non-anticipativity). The algorithm is guaranteed to
converge for convex problems.

## Value of Stochastic Solution (VSS)

```
VSS = EV_cost − RP_cost
```

- **RP (Recourse Problem):** optimal cost when solving with all 30 scenarios (PH result)
- **EV (Expected Value):** cost when solving with the mean scenario and applying that
  decision to all actual scenarios
- **VSS > 0** means knowing the scenario distribution is worth something — risk-averse
  investors should solve with scenarios, not with means

Typical VSS for storage investment: 3–12% of total cost, representing $45K–$180K/MW
in avoided over/under-investment.

## Key ASSERT

```
ASSERT ph_converged(@result_json);
```

Passes when `rp_cost ≤ ev_cost` (stochastic solution is no worse than EV). In practice,
VSS should be positive; the ASSERT allows tie (within numerical tolerance).

## Connection to Momagrid

PH's scenario subproblems are embarrassingly parallel — each scenario is fully
independent within each iteration. On Momagrid, 30 scenario subproblems would
route to 30 different nodes, completing in parallel. The coordinator (PH multiplier
update) runs centrally. This is the natural distributed pattern for large SP problems
and is a direct application of DODA: the `.spl` workflow is identical whether running
locally (ThreadPoolExecutor) or on Momagrid (node dispatch).
