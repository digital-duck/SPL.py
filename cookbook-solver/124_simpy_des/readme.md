# Recipe 124 — Discrete-Event Simulation: Hospital Emergency Department (SimPy)

**Solver class:** Discrete-Event Simulation (DES) — "what happens?" not "what is optimal?"  
**Backend:** SimPy  
**Dependency:** `pip install simpy`

## What it demonstrates

Every other solver recipe answers "what is **optimal**?" — minimize cost, maximize yield,
find Nash equilibrium. This recipe introduces a fundamentally different solver class:
**Discrete-Event Simulation (DES)**. DES answers "what **happens**?" under stochastic
dynamics. It produces *trajectories*, not solutions.

DES is not competing with LP/MILP/CP — it is **complementary**. The natural SPL pattern:
```
CALL simulate → CALL optimize  (understand the system, then improve it)
```

| | solver=ON (SimPy) | solver=OFF (M/M/c + LLM) |
|---|---|---|
| Arrival model | Bursty (non-Poisson, shift spikes) | Poisson (analytic assumption) |
| Service time | Lognormal (long tail) | Exponential (memoryless) |
| Mean wait | Measured from simulation | Erlang-C formula |
| **95th-percentile wait** | **Accurate** | **~60% underestimate** |
| What you can see | Per-patient trajectories, queue snapshots | Aggregate statistics only |

## The problem: Hospital Emergency Department

**Resources:** 3 triage nurses, 8 treatment bays, 2 specialist consultants  
**Arrivals:** Mean 3.2 patients/hour, but **bursty** — shift handovers at 8am/4pm/midnight
drive 2.5× spike rates. Real EDs are never Poisson.  
**Service:** Triage ~2 min (exponential); treatment ~40 min mean with 25 min σ (lognormal
— some patients need 2 hours, some are discharged in 15 min); 50% need specialist consult.

**Why M/M/c gets it wrong:**
- M/M/c assumes Poisson arrivals (coefficient of variation = 1)
- ED arrivals have CV > 2 during handover spikes
- Higher CV → longer tail → P95 wait is severely underestimated

## Run

```bash
# solver=ON: SimPy DES (10,000 patients, 1-week simulation)
spl3 run cookbook-solver/124_simpy_des/simpy_des.spl \
    --adapter claude_cli --param use_solver=true

# With larger cohort (slower but better statistics)
spl3 run cookbook-solver/124_simpy_des/simpy_des.spl \
    --adapter claude_cli --param use_solver=true --param n_patients=50000

# solver=OFF: M/M/c analytic formula + LLM reasoning
spl3 run cookbook-solver/124_simpy_des/simpy_des.spl \
    --adapter ollama -m gemma3 --param use_solver=false
```

## Install

```bash
pip install simpy
```

## Background: Discrete-Event Simulation

DES models a system as a sequence of events occurring at discrete time points:
- **Entities:** patients arriving, waiting, being served
- **Resources:** nurses, bays, specialists (capacity-constrained)
- **Events:** arrival, start-service, end-service, departure
- **Clock:** advances to the next scheduled event (not wall-clock time)

SimPy implements DES using Python generators:
```python
def patient_process(env):
    arrive = env.now
    with nurse.request() as req:
        yield req               # wait until nurse available
        yield env.timeout(2)    # triage for 2 minutes
    # ... treatment, specialist ...
    record_wait(env.now - arrive)
```

**What M/M/c captures:** steady-state mean wait under infinite-horizon, stationary Poisson.  
**What DES captures:** transient behavior, burst effects, shift patterns, tail distributions.

## Key ASSERT

```
ASSERT simulation_valid(@sim_json, @mmc_json);
```

Passes when:
1. ≥ 1,000 patients completed (sufficient sample)
2. Simulation P95 wait > 90% of M/M/c P95 estimate (burstiness must raise the tail)

If SimPy is not installed, the recipe runs solver=OFF automatically.

## Why this is a new solver class

All current cookbook-solver recipes (r67–r121) are **optimization problems**:
find x that minimizes/maximizes f(x) subject to constraints.

SimPy DES is a **simulation problem**: given a stochastic process, generate sample paths
and measure statistics. You cannot "optimize" with SimPy alone — but you can:
1. Simulate to understand system behavior (r124)
2. Then optimize staffing levels using those statistics as inputs to an LP/MILP (future recipe)

This is the "simulate-then-optimize" pattern, which matches how real operations research
projects are structured.
