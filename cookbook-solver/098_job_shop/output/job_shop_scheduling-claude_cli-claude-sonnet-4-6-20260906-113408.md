# SPL Run: job_shop_scheduling

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 541 in / 506 out
- **Latency:** 39758ms
- **Timestamp:** 2026-09-06 11:34:08

## Output

```output
=== Job-Shop Scheduling (solver=ON / OR-Tools CP-SAT) ===

Problem:
3 jobs, 3 machines. Job1: M1(3)→M2(2)→M3(2). Job2: M2(2)→M1(3)→M3(1). Job3: M3(2)→M2(1)→M1(2). Minimize makespan.

CP-SAT Solution (JSON):
{"status": "OPTIMAL", "makespan": 8, "schedule": [{"job": "Job1", "operation": 1, "machine": "M1", "start": 0, "end": 3, "duration": 3}, {"job": "Job2", "operation": 2, "machine": "M1", "start": 3, "end": 6, "duration": 3}, {"job": "Job3", "operation": 3, "machine": "M1", "start": 6, "end": 8, "duration": 2}, {"job": "Job2", "operation": 1, "machine": "M2", "start": 0, "end": 2, "duration": 2}, {"job": "Job3", "operation": 2, "machine": "M2", "start": 2, "end": 3, "duration": 1}, {"job": "Job1", "operation": 2, "machine": "M2", "start": 3, "end": 5, "duration": 2}, {"job": "Job3", "operation": 1, "machine": "M3", "start": 0, "end": 2, "duration": 2}, {"job": "Job1", "operation": 3, "machine": "M3", "start": 5, "end": 7, "duration": 2}, {"job": "Job2", "operation": 3, "machine": "M3", "start": 7, "end": 8, "duration": 1}], "solver_log": "CP-SAT OPTIMAL; makespan=8"}

Gantt Chart:
Makespan = 8 time units

Machine  |012345678
-------------------
M1       |JJJJJJJJ.
M2       |JJJJJ....
M3       |JJ...JJJ.

Interpretation:
## Job-Shop Schedule Interpretation

### 1. Optimal Makespan
The solver found the **provably best possible answer: 8 time units**. "OPTIMAL" means no rearrangement of jobs can finish faster — this is a mathematical guarantee, not just a good guess.

### 2. Bottleneck: Machine 1 (M1)
M1 runs at **100% utilization** — it processes Job1, then Job2, then Job3 back-to-back with zero gaps (0→3→6→8). M2 and M3 are only ~63% busy. M1 is the constraint: adding capacity there (a faster machine or a second one) would directly shrink the total time.

### 3. Schedule in Plain Language

| Time | M1 | M2 | M3 |
|------|----|----|-----|
| 0–2  | Job1 | Job2 | Job3 |
| 2–3  | Job1 | Job3 | — |
| 3–5  | Job2 | Job1 | — |
| 5–7  | Job3 running on M1 (6–8) | — | Job1 |
| 7–8  | Job3 | — | Job2 |

- **Job1** flows smoothly: M1 → M2 → M3, no waiting.
- **Job2** starts immediately on M2, waits 1 unit for M1, then finishes on M3.
- **Job3** starts on M3, does a quick M2 step, then waits **3 units** for M1 to clear.

### 4. Waiting Time
All waiting is caused by M1 being fully booked. Job3 is the most affected — it finishes its M2 step at t=3 but can't get onto M1 until t=6, sitting idle for 3 units. This is unavoidable: M1 has 8 total units of work to do, and the schedule delivers exactly that with no waste.

### 5. Practical Takeaway
**M1 is your factory floor's single bottleneck** — every minute you reduce M1's processing time (faster tooling, parallel station, reduced setup) translates directly into a shorter total runtime; improvements elsewhere won't help until M1 is no longer the constraint.

LLM calls: 2
```
