# SPL Run: simpy_des

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 369 in / 353 out
- **Latency:** 12611ms
- **Timestamp:** 2026-09-07 12:58:47

## Output

```output
=== Discrete-Event Simulation — Hospital ED (r124) | solver=ON ===

## SimPy DES Report — Emergency Department

**Patients simulated:** 10,000  
**Mean total wait:** 62.0 min  
**Median wait:** 50.6 min  
**95th-percentile wait:** 145.6 min  

### Resource Utilization

| Resource | Utilization |
|---|---|
| Triage nurses (×3) | 1.8% |
| Treatment bays (×8) | 13.4% |
| Specialists (×2) | 19.9% |

### Wait Time Distribution

| Bucket | Patients |
|---|---|
| 0-10min | 45 |
| 10-20min | 700 |
| 20-30min | 1,451 |
| 30-45min | 2,157 |
| 45-60min | 1,624 |
| 60-90min | 2,062 |
| 90-120min | 1,000 |
| 120-120+min | 961 |

── M/M/c Analytic Baseline ─────────────────────────────────
**M/M/c Analytic Baseline (M/M/c Erlang-C — total sojourn (queue + service, all stages)):**  
Mean wait: 57.0 min | P95 wait: 97.0 min | Bay utilization: 26.7%

── Analyst Explanation ─────────────────────────────────────
## Simulation vs. M/M/c Analysis

**1. Bursty arrivals and the P95 gap**
M/M/c assumes Poisson arrivals (coefficient of variation = 1 exactly). Real ED arrivals are bursty — CV > 1 means the variance in inter-arrival times exceeds the mean, so clusters of simultaneous arrivals periodically overwhelm capacity. These surges drive the tail: simulation P95 is 145.6 min vs. M/M/c's 97.0 min, a 50% underestimate from the analytic model.

**2. Inspection paradox**
A patient arriving at a random moment is more likely to land during a *long* busy period than a short one — long intervals are sampled with higher probability. So perceived wait exceeds what average utilization (13–20%) would suggest. The "average" hides the experience of patients who arrive into backlogs.

**3. Highest-leverage operational change**
Specialists at 19.9% utilization are the binding constraint — the highest-utilized resource. Adding a third specialist or implementing fast-track protocols for non-specialist cases would most directly flatten the P95 tail.

**4. Simulation → optimization gap**
Simulation tells you *what happens*; it cannot tell you *what to do*. You need an objective function (minimize P95 subject to cost), a decision space (staffing levels, schedules), and a search algorithm — stochastic optimization, response surface methods, or Bayesian optimization — to turn scenario replay into a staffing recommendation.
```
