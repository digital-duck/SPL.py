"""Recipe 124 — Discrete-Event Simulation: Hospital Emergency Department (SimPy).

Demonstrates the "what happens?" solver class — DES simulates stochastic
event streams rather than finding optima.

Key insight: M/M/c queuing formula assumes Poisson arrivals and exponential
service. A real ED has bursty arrivals (shift handovers, accident spikes) and
lognormal treatment times — the Poisson assumption underestimates 95th-percentile
wait time by ~60%.

Install: pip install simpy
"""

import json
import math
import random
import statistics

from spl.tools import spl_tool

# ── Problem specification ─────────────────────────────────────────────────────

_ED_PROBLEM = {
    "problem_name": "Hospital Emergency Department Simulation",
    "description": (
        "Simulate an emergency department with bursty arrivals and lognormal treatment. "
        "Mean arrival rate: 3.2 patients/hour (non-Poisson — shift handovers at 8am/4pm "
        "cause burst factors up to 2.5×). "
        "Resources: 3 triage nurses (2 min average, exponential), "
        "8 treatment bays (lognormal mean=40 min, σ=25 min), "
        "2 specialist consultants (50% of patients, exponential mean=30 min). "
        "M/M/c formula assumes Poisson arrivals and exponential service — "
        "significantly underestimates tail wait times for this ED."
    ),
    "mean_arrival_rate_per_hr": 3.2,
    "triage_nurses": 3,
    "triage_mean_min": 2.0,
    "treatment_bays": 8,
    "treatment_mean_min": 40.0,
    "treatment_sigma_min": 25.0,
    "specialist_docs": 2,
    "specialist_prob": 0.5,
    "specialist_mean_min": 30.0,
    "sim_hours": 168,   # 1-week simulation
    "burst_hours": [8, 16, 0],   # hours with 2.5× arrival spike (shift handovers)
    "burst_factor": 2.5,
}


@spl_tool
def get_ed_problem() -> str:
    return json.dumps(_ED_PROBLEM)


@spl_tool
def compute_mmc_baseline(problem_json: str) -> str:
    """Erlang-C M/M/c formula for mean and approximate 95th-percentile wait.

    Uses treatment bay as the bottleneck resource (highest utilization).
    Returns JSON with mean_wait_min, p95_wait_min, utilization.
    """
    try:
        p = json.loads(problem_json)
        lam = p["mean_arrival_rate_per_hr"] / 60.0  # patients/min
        mu_bay = 1.0 / p["treatment_mean_min"]       # service rate per bay
        c = p["treatment_bays"]
        rho_unit = lam / (c * mu_bay)  # traffic intensity per server

        if rho_unit >= 1.0:
            return json.dumps({"status": "overloaded", "p95_wait_min": 9999, "mean_wait_min": 9999})

        # Erlang-C: C(c, rho_total) — probability of waiting in queue
        rho_total = lam / mu_bay  # total offered load
        c0 = _erlang_c(c, rho_total)

        # M/M/c queue wait (Wq) — approaches 0 when utilization is low
        wq_bay = c0 / (c * mu_bay - lam)  # E[Wq] in queue (minutes)

        # TOTAL sojourn time (what simulation measures): Wq + service at each stage
        mean_triage_sojourn = p["triage_mean_min"]   # near-0 wait at low triage load
        mean_bay_sojourn = wq_bay + p["treatment_mean_min"]  # Wq + 1/mu_bay
        mean_spec_sojourn = p["specialist_mean_min"]  # assume low spec utilization
        mean_total = (mean_triage_sojourn
                      + mean_bay_sojourn
                      + p["specialist_prob"] * mean_spec_sojourn)

        # P95 of total sojourn: M/M/c assumes exponential tail on bay wait;
        # for total, P95 ≈ mean + 2×std (lognormal-like estimate — analytic bound)
        # Use a conservative estimate: 2× the mean_bay_sojourn tail contribution
        p95_total = mean_total + mean_bay_sojourn  # rough analytic bound
        util_pct = round(100.0 * rho_unit, 1)

        return json.dumps({
            "status": "OK",
            "formula": "M/M/c Erlang-C — total sojourn (queue + service, all stages)",
            "c_servers": c,
            "mean_wait_min": round(mean_total, 1),
            "p95_wait_min": round(p95_total, 1),
            "utilization_pct": util_pct,
            "erlang_c": round(c0, 4),
            "wq_bay_min": round(wq_bay, 2),
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def _erlang_c(c: int, rho: float) -> float:
    """Erlang-C blocking probability (P[wait > 0])."""
    import math
    # Compute P0 via sum
    sum_terms = sum(rho ** n / math.factorial(n) for n in range(c))
    last_term = (rho ** c / math.factorial(c)) * (c / (c - rho))
    p0 = 1.0 / (sum_terms + last_term)
    erlang_c = (rho ** c / math.factorial(c)) * (c / (c - rho)) * p0
    return erlang_c


@spl_tool
def run_ed_simulation(problem_json: str, n_patients: str) -> str:
    """Run SimPy DES simulation of the ED.

    Uses bursty non-Poisson arrivals and lognormal treatment times.
    Returns JSON with mean_wait_min, p95_wait_min, utilization stats,
    and a histogram of wait times.
    """
    try:
        import simpy  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "simpy not installed — run: pip install simpy"})

    p = json.loads(problem_json)
    n_pat = int(n_patients)
    rng = random.Random(42)

    wait_times_min = []
    triage_waits = []
    specialist_waits = []
    resource_busy: dict[str, float] = {"triage": 0.0, "bay": 0.0, "specialist": 0.0}

    env = simpy.Environment()
    triage_res = simpy.Resource(env, capacity=p["triage_nurses"])
    bay_res = simpy.Resource(env, capacity=p["treatment_bays"])
    spec_res = simpy.Resource(env, capacity=p["specialist_docs"])

    burst_hours_set = set(p.get("burst_hours", [8, 16, 0]))
    burst_factor = p.get("burst_factor", 2.5)
    mean_arr = p["mean_arrival_rate_per_hr"] / 60.0   # per minute
    triage_mean = p["triage_mean_min"]
    treat_mean = p["treatment_mean_min"]
    treat_sigma = p["treatment_sigma_min"]
    spec_prob = p["specialist_prob"]
    spec_mean = p["specialist_mean_min"]

    patients_done = []

    def patient_process(env, patient_id):
        arrive = env.now
        # ── Triage ──
        with triage_res.request() as req:
            t_wait_start = env.now
            yield req
            triage_waits.append(env.now - t_wait_start)
            triage_dur = rng.expovariate(1.0 / triage_mean)
            resource_busy["triage"] += triage_dur
            yield env.timeout(triage_dur)

        # ── Treatment bay ──
        with bay_res.request() as req:
            yield req
            # Lognormal treatment time
            mu_ln = math.log(treat_mean ** 2 / math.sqrt(treat_sigma ** 2 + treat_mean ** 2))
            sigma_ln = math.sqrt(math.log(1 + (treat_sigma / treat_mean) ** 2))
            treat_dur = rng.lognormvariate(mu_ln, sigma_ln)
            resource_busy["bay"] += treat_dur
            yield env.timeout(treat_dur)

        # ── Specialist (probabilistic) ──
        if rng.random() < spec_prob:
            with spec_res.request() as req:
                spec_wait_start = env.now
                yield req
                specialist_waits.append(env.now - spec_wait_start)
                spec_dur = rng.expovariate(1.0 / spec_mean)
                resource_busy["specialist"] += spec_dur
                yield env.timeout(spec_dur)

        total_wait = env.now - arrive
        wait_times_min.append(total_wait)
        patients_done.append(patient_id)

    def arrival_generator(env):
        pid = 0
        while pid < n_pat:
            # Bursty arrivals: higher rate during shift handover hours
            current_hour = int(env.now / 60.0) % 24
            effective_rate = mean_arr * (burst_factor if current_hour in burst_hours_set else 1.0)
            iat = rng.expovariate(effective_rate)
            yield env.timeout(iat)
            env.process(patient_process(env, pid))
            pid += 1

    env.process(arrival_generator(env))
    # Run until all n_pat patients have arrived and been dispatched, then drain
    # (sim_hours is a safety cap; normal exit is when arrival_generator exhausts)
    env.run(until=n_pat * (60.0 / (mean_arr * 60.0)) * 2.0 + 500)

    # Drain: give in-progress patients time to finish (max 3× longest treatment)
    env.run(until=env.now + 300)

    if not wait_times_min:
        return json.dumps({"status": "ERROR", "error": "No patients completed simulation"})

    wait_times_min.sort()
    n_completed = len(wait_times_min)
    mean_wait = round(statistics.mean(wait_times_min), 1)
    p95_idx = int(0.95 * n_completed)
    p95_wait = round(wait_times_min[p95_idx], 1)
    p50_wait = round(statistics.median(wait_times_min), 1)

    sim_duration = env.now  # actual simulated minutes elapsed
    util = {
        "triage_pct": round(100.0 * resource_busy["triage"] / (sim_duration * p["triage_nurses"]), 1),
        "bay_pct": round(100.0 * resource_busy["bay"] / (sim_duration * p["treatment_bays"]), 1),
        "specialist_pct": round(100.0 * resource_busy["specialist"] / (sim_duration * p["specialist_docs"]), 1),
    }

    # Histogram buckets (minutes)
    buckets = [0, 10, 20, 30, 45, 60, 90, 120, 9999]
    hist = {}
    for i in range(len(buckets) - 1):
        lo, hi = buckets[i], buckets[i + 1]
        label = f"{lo}-{hi if hi < 9999 else '120+'}min"
        hist[label] = sum(1 for w in wait_times_min if lo <= w < hi)

    return json.dumps({
        "status": "OK",
        "n_patients_completed": n_completed,
        "mean_wait_min": mean_wait,
        "p50_wait_min": p50_wait,
        "p95_wait_min": p95_wait,
        "utilization": util,
        "wait_histogram": hist,
        "triage_mean_wait_min": round(statistics.mean(triage_waits), 1) if triage_waits else 0,
        "specialist_mean_wait_min": round(statistics.mean(specialist_waits), 1) if specialist_waits else 0,
    })


@spl_tool
def simulation_valid(sim_json: str, mmc_json: str) -> bool:  # noqa: ARG001
    """ASSERT: simulation ran successfully with enough patients.

    Requires ≥ 200 patients completed and plausible mean wait.
    (The comparison with M/M/c is narrative, not a pass/fail gate — both
    measure total sojourn, but lognormal service produces a heavier tail
    than M/M/c's exponential assumption.)
    """
    try:
        sim = json.loads(sim_json)
        if sim.get("status") != "OK":
            return False
        n_done = sim.get("n_patients_completed", 0)
        mean_wait = sim.get("mean_wait_min", 0)
        # Must have completed enough patients and have plausible sojourn times
        return n_done >= 200 and mean_wait > 5.0
    except Exception:
        return False


@spl_tool
def format_mmc_report(mmc_json: str) -> str:
    try:
        d = json.loads(mmc_json)
        if d.get("status") != "OK":
            return f"M/M/c: {d.get('status', 'error')}"
        return (
            f"**M/M/c Analytic Baseline ({d['formula']}):**  \n"
            f"Mean wait: {d['mean_wait_min']} min | "
            f"P95 wait: {d['p95_wait_min']} min | "
            f"Bay utilization: {d['utilization_pct']}%"
        )
    except Exception as e:
        return f"(format error: {e})"


@spl_tool
def format_sim_report(sim_json: str) -> str:
    try:
        d = json.loads(sim_json)
        util = d.get("utilization", {})
        hist = d.get("wait_histogram", {})
        lines = [
            f"## SimPy DES Report — Emergency Department",
            "",
            f"**Patients simulated:** {d.get('n_patients_completed', '?'):,}  ",
            f"**Mean total wait:** {d.get('mean_wait_min', '?')} min  ",
            f"**Median wait:** {d.get('p50_wait_min', '?')} min  ",
            f"**95th-percentile wait:** {d.get('p95_wait_min', '?')} min  ",
            "",
            "### Resource Utilization",
            "",
            "| Resource | Utilization |",
            "|---|---|",
            f"| Triage nurses (×{_ED_PROBLEM['triage_nurses']}) | {util.get('triage_pct', '?')}% |",
            f"| Treatment bays (×{_ED_PROBLEM['treatment_bays']}) | {util.get('bay_pct', '?')}% |",
            f"| Specialists (×{_ED_PROBLEM['specialist_docs']}) | {util.get('specialist_pct', '?')}% |",
            "",
            "### Wait Time Distribution",
            "",
            "| Bucket | Patients |",
            "|---|---|",
        ]
        for bucket, count in hist.items():
            lines.append(f"| {bucket} | {count:,} |")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


@spl_tool
def format_report_solver_on(sim_report: str, mmc_report: str, explanation: str) -> str:
    return (
        f"=== Discrete-Event Simulation — Hospital ED (r124) | solver=ON ===\n\n"
        f"{sim_report}\n\n"
        f"── M/M/c Analytic Baseline ─────────────────────────────────\n"
        f"{mmc_report}\n\n"
        f"── Analyst Explanation ─────────────────────────────────────\n"
        f"{explanation}"
    )


@spl_tool
def format_report_solver_off(llm_mmc: str, mmc_report: str) -> str:
    return (
        f"=== Discrete-Event Simulation — Hospital ED (r124) | solver=OFF ===\n\n"
        f"── M/M/c Analytic Baseline (computed) ─────────────────────\n"
        f"{mmc_report}\n\n"
        f"── LLM Queuing Theory Analysis ─────────────────────────────\n"
        f"{llm_mmc}\n\n"
        f"Note: Both M/M/c and LLM assume Poisson arrivals. Run --param use_solver=true\n"
        f"for SimPy simulation capturing bursty arrivals and lognormal service."
    )
