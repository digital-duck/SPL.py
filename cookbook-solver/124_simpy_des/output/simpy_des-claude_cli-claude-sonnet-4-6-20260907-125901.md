# SPL Run: simpy_des

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 300 in / 1286 out
- **Latency:** 144851ms
- **Timestamp:** 2026-09-07 12:59:01

## Output

```output
=== Discrete-Event Simulation — Hospital ED (r124) | solver=OFF ===

── M/M/c Analytic Baseline (computed) ─────────────────────
**M/M/c Analytic Baseline (M/M/c Erlang-C — total sojourn (queue + service, all stages)):**  
Mean wait: 57.0 min | P95 wait: 97.0 min | Bay utilization: 26.7%

── LLM Queuing Theory Analysis ─────────────────────────────
## ED Queuing Analysis — M/M/c / Erlang-C

---

### Setup: Parameters

| Subsystem | λ (arr/hr) | μ (srv/hr) | c (servers) | a = λ/μ |
|-----------|-----------|------------|-------------|---------|
| Triage | 3.2 | 30 (= 60/2 min) | 3 | 0.107 |
| Treatment bays | 3.2 | 1.5 (= 60/40 min) | 8 | 2.133 |
| Specialist | 1.6 (50% of λ) | 2.0 (= 60/30 min) | 2 | 0.800 |

---

### Step 1 — Erlang-C Formula

$$\rho = \frac{\lambda}{c\mu}, \quad a = \frac{\lambda}{\mu}$$

$$P_0 = \left[\sum_{n=0}^{c-1}\frac{a^n}{n!} + \frac{a^c}{c!\,(1-\rho)}\right]^{-1}$$

$$C(c,a) = \frac{a^c}{c!\,(1-\rho)} \cdot P_0 \quad \text{(prob. all servers busy)}$$

$$W_q = \frac{C(c,a)}{c\mu - \lambda}$$

---

#### 1a. Triage Nurses (M/M/3)

$$\rho_{\text{triage}} = \frac{3.2}{3 \times 30} = \boxed{0.036} \quad (3.6\%)$$

**P₀ sum (n = 0..2):** 1 + 0.107 + 0.0057 = 1.1124  
**Last term (n = c = 3):** a³/(3! × 0.964) = 0.001214/5.785 = **0.000210**  
**Denominator:** 1.1124 + 0.000210 = 1.1126 → **P₀ = 0.8988**

$$C(3,\,0.107) = \frac{0.000210}{1.1126} = 0.000189$$

$$W_q^{\text{triage}} = \frac{0.000189}{90 - 3.2} = \frac{0.000189}{86.8} = 2.2 \times 10^{-6}\,\text{hr} = \mathbf{0.008\,\text{sec}}$$

Negligible — triage is massively over-resourced at mean load.

---

#### 1b. Treatment Bays (M/M/8)

$$\rho_{\text{bay}} = \frac{3.2}{8 \times 1.5} = \boxed{0.267} \quad (26.7\%)$$

**P₀ sum (n = 0..7):**

| n | aⁿ/n! |
|---|-------|
| 0 | 1.000 |
| 1 | 2.133 |
| 2 | 2.274 |
| 3 | 1.617 |
| 4 | 0.862 |
| 5 | 0.368 |
| 6 | 0.131 |
| 7 | 0.040 |
| **Σ** | **8.425** |

**Last term:** a⁸/(8! × 0.733) = 428.5/29,568 = **0.01449**  
**Denominator:** 8.425 + 0.01449 = 8.440 → **P₀ = 0.1185**

$$C(8,\,2.133) = \frac{0.01449}{8.440} = 0.00172 \quad (0.17\%)$$

$$W_q^{\text{bay}} = \frac{0.00172}{12.0 - 3.2} = \frac{0.00172}{8.8} = 1.95\times10^{-4}\,\text{hr} = \mathbf{0.70\,\text{sec}}$$

Also negligible at mean load — 8 bays absorb 2.13 Erlangs easily.

---

#### 1c. Specialist Consultants (M/M/2) — the real bottleneck

$$\rho_{\text{spec}} = \frac{1.6}{2 \times 2.0} = 0.400 \quad (40\%)$$

**P₀:** 1/(1.000 + 0.800 + 0.64/1.2) = 1/(1.800 + 0.533) = **0.4286**

$$C(2,\,0.8) = \frac{0.533}{2.333} = 0.229$$

$$W_q^{\text{spec}} = \frac{0.229}{4.0 - 1.6} = \frac{0.229}{2.4} = 0.0952\,\text{hr} = \mathbf{5.7\,\text{min}}$$

---

### Step 2 — 95th-Percentile Wait

Using exponential tail: W₉₅ ≈ Wq × ln(20) = Wq × **2.996**

| Subsystem | Wq | W₉₅ |
|-----------|-----|------|
| Triage | 0.008 sec | 0.023 sec |
| Treatment bays (mean load) | 0.70 sec | 2.1 sec |
| Specialist | **5.7 min** | **17.1 min** |
| Treatment bays (**burst, λ=8.0/hr**) | **3.3 min** | **9.9 min** |

**Burst scenario** (λ_burst = 2.5 × 3.2 = 8.0/hr → ρ_bay = 0.667):

C(8, 5.333) requires summing to n=7 (sum = 171.76) + last term 48.66; P₀ = 0.00454, C = **0.221**

$$W_q^{\text{burst}} = \frac{0.221}{12.0 - 8.0} = 0.0552\,\text{hr} = \mathbf{3.3\,\text{min}}$$

The W₉₅ jump from **2 seconds → 10 minutes** during handover bursts is the operational danger M/M/c at mean load entirely misses.

---

### Step 3 — Utilization Summary

$$\boxed{\rho_{\text{triage}} = 0.036, \quad \rho_{\text{bay}} = 0.267, \quad \rho_{\text{specialist}} = 0.400}$$

None exceed 1.0, so the system is theoretically stable at mean λ — but burst ρ_bay = 0.667 is where queue buildup accelerates nonlinearly.

---

### Step 4 — When M/M/c Is Accurate, and Why EDs Violate It

**M/M/c is accurate when:**
- Arrivals are Poisson (memoryless, stationary, independent)
- Service times are exponential (coefficient of variation = 1)
- The system is in steady state (arrived long before we measure)
- All servers are identical and always available
- Queue discipline is FCFS with infinite capacity

**Why this ED violates the Poisson arrival assumption:**

Poisson requires that arrivals are **independent and stationary** — no clustering in time. ED arrivals violate this in at least three ways:

1. **Shift-handover bursts.** The 8am/4pm transitions cause 2.5× surges lasting 20–40 minutes. Poisson's intensity λ is constant; this ED's λ(t) is time-varying. The correct model is a **non-homogeneous Poisson process** (NHPP) or batch-arrival M[X]/M/c.

2. **Correlated arrivals.** Ambulance diversions, mass-casualty events, and seasonal flu all generate arrival clusters that are mutually dependent — violating the independence assumption. The inter-arrival variance exceeds what Poisson allows.

3. **Lognormal service times inflate tail waits.** The treatment bay distribution (mean=40 min, σ=25 min) has coefficient of variation CV = 25/40 = 0.625 < 1, which is actually *less* variable than exponential. But the Pollaczek–Khinchine formula for M/G/1 shows Wq scales with (1 + CV²)/2. For the specialist queue with unknown service distribution, CV > 1 is plausible, which inflates actual W₉₅ beyond the Erlang-C estimate.

**Net effect:** M/M/c underestimates peak wait times by potentially 3–5× during burst windows. A simulation (e.g., SimPy DES) or NHPP-based model is needed to capture tail behavior accurately — which is precisely what recipe 124 (`cookbook-solver/124_simpy_des/`) addresses.

Note: Both M/M/c and LLM assume Poisson arrivals. Run --param use_solver=true
for SimPy simulation capturing bursty arrivals and lognormal service.
```
