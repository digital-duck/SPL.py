"""
Recipe 98 — Job-shop scheduling via OR-Tools CP-SAT.
TOOL_APIs called from job_shop.spl.
"""

import json
from typing import Any


def is_scheduled(solution_json: str) -> bool:
    """Return True when CP-SAT status is OPTIMAL or FEASIBLE."""
    import json
    try:
        data = json.loads(solution_json)
        return data.get("status", "") in ("OPTIMAL", "FEASIBLE")
    except Exception:
        return "OPTIMAL" in solution_json or "FEASIBLE" in solution_json


def json_get_field(data_json: str, field: str) -> str:
    """Extract a top-level field from a JSON object; return empty string on failure."""
    import json
    try:
        data = json.loads(data_json)
        return str(data.get(field, ""))
    except Exception:
        return ""


def parse_job_shop_problem(problem: str) -> str:
    """
    Parse a natural-language job-shop problem description into structured JSON.
    Expected JSON output:
    {
      "jobs": [
          {"name": "Job1", "operations": [{"machine": "M1", "duration": 3}, ...]},
          ...
      ],
      "machines": ["M1", "M2", "M3"],
      "deadline": null   // or an integer makespan deadline
    }
    This is a passthrough — the LLM produces the JSON in extract_job_shop_json step.
    Here we just validate and normalise it.
    """
    try:
        data = json.loads(problem)
        jobs = data.get("jobs", [])
        if not jobs:
            return json.dumps({"error": "no jobs found in parsed data"})
        machines: list[str] = []
        for job in jobs:
            for op in job.get("operations", []):
                m = op.get("machine", "")
                if m and m not in machines:
                    machines.append(m)
        data.setdefault("machines", machines)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"parse_error: {e}", "raw": problem[:200]})


def solve_job_shop(problem_json: str) -> str:
    """
    Solve a job-shop scheduling problem using OR-Tools CP-SAT.
    Input: JSON string with keys: jobs, machines, deadline (optional)
    Returns: JSON with keys: status, makespan, schedule, solver_log
    """
    from ortools.sat.python import cp_model

    try:
        data = json.loads(problem_json)
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    jobs_data: list[dict[str, Any]] = data.get("jobs", [])
    deadline: int | None = data.get("deadline")

    if not jobs_data:
        return json.dumps({"status": "INVALID_INPUT", "error": "no jobs"})

    model = cp_model.CpModel()

    # Compute horizon = sum of all durations (loose upper bound for makespan)
    horizon = sum(
        op["duration"]
        for job in jobs_data
        for op in job.get("operations", [])
    )

    all_tasks: dict[tuple[int, int], dict] = {}
    machine_to_intervals: dict[str, list] = {}

    for job_id, job in enumerate(jobs_data):
        for task_id, op in enumerate(job.get("operations", [])):
            machine = op["machine"]
            duration = int(op["duration"])

            suffix = f"_j{job_id}_t{task_id}"
            start_var = model.NewIntVar(0, horizon, f"start{suffix}")
            end_var = model.NewIntVar(0, horizon, f"end{suffix}")
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f"interval{suffix}")

            all_tasks[(job_id, task_id)] = {
                "start": start_var,
                "end": end_var,
                "interval": interval_var,
                "machine": machine,
                "duration": duration,
            }

            if machine not in machine_to_intervals:
                machine_to_intervals[machine] = []
            machine_to_intervals[machine].append(interval_var)

    # No-overlap on each machine
    for machine, intervals in machine_to_intervals.items():
        model.AddNoOverlap(intervals)

    # Precedence within each job (operations must follow in order)
    for job_id, job in enumerate(jobs_data):
        ops = job.get("operations", [])
        for task_id in range(len(ops) - 1):
            model.Add(
                all_tasks[(job_id, task_id + 1)]["start"]
                >= all_tasks[(job_id, task_id)]["end"]
            )

    # Makespan variable
    makespan_var = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(
        makespan_var,
        [all_tasks[(job_id, len(job["operations"]) - 1)]["end"]
         for job_id, job in enumerate(jobs_data)
         if job.get("operations")],
    )

    if deadline is not None:
        model.Add(makespan_var <= deadline)

    model.Minimize(makespan_var)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status_code = solver.Solve(model)
    status_name = solver.StatusName(status_code)

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return json.dumps({
            "status": status_name,
            "makespan": None,
            "schedule": [],
            "solver_log": f"CP-SAT returned {status_name}",
        })

    makespan = solver.ObjectiveValue()
    schedule = []
    for job_id, job in enumerate(jobs_data):
        for task_id, op in enumerate(job.get("operations", [])):
            t = all_tasks[(job_id, task_id)]
            schedule.append({
                "job": job.get("name", f"Job{job_id + 1}"),
                "operation": task_id + 1,
                "machine": op["machine"],
                "start": solver.Value(t["start"]),
                "end": solver.Value(t["end"]),
                "duration": t["duration"],
            })

    schedule.sort(key=lambda x: (x["machine"], x["start"]))

    return json.dumps({
        "status": status_name,
        "makespan": int(makespan),
        "schedule": schedule,
        "solver_log": f"CP-SAT {status_name}; makespan={int(makespan)}",
    })


def verify_job_shop(problem_json: str, solution_json: str) -> str:
    """
    Back-substitution verifier for solver=OFF path.
    Checks: precedence constraints, no-overlap on machines, correct makespan.
    """
    try:
        problem = json.loads(problem_json)
        sol = json.loads(solution_json)
    except Exception as e:
        return json.dumps({"verdict": "UNPARSEABLE", "notes": str(e)})

    schedule: list[dict] = sol.get("schedule", [])
    if not schedule:
        return json.dumps({"verdict": "UNPARSEABLE", "notes": "empty schedule"})

    jobs_data = problem.get("jobs", [])
    notes: list[str] = []
    ok = True

    # Check no-overlap on each machine
    machine_ops: dict[str, list[dict]] = {}
    for entry in schedule:
        m = entry["machine"]
        machine_ops.setdefault(m, []).append(entry)

    for machine, ops in machine_ops.items():
        ops_sorted = sorted(ops, key=lambda x: x["start"])
        for i in range(len(ops_sorted) - 1):
            a, b = ops_sorted[i], ops_sorted[i + 1]
            if a["end"] > b["start"]:
                notes.append(f"overlap on {machine}: {a['job']}[{a['start']},{a['end']}) vs {b['job']}[{b['start']},{b['end']})")
                ok = False

    # Check precedence within each job
    for job in jobs_data:
        job_name = job.get("name", "")
        job_ops = [e for e in schedule if e["job"] == job_name]
        job_ops.sort(key=lambda x: x["operation"])
        for i in range(len(job_ops) - 1):
            if job_ops[i]["end"] > job_ops[i + 1]["start"]:
                notes.append(f"precedence violated for {job_name}: op{i+1} ends {job_ops[i]['end']} > op{i+2} starts {job_ops[i+1]['start']}")
                ok = False

    claimed_makespan = sol.get("makespan")
    actual_makespan = max((e["end"] for e in schedule), default=0)
    if claimed_makespan is not None and int(claimed_makespan) != actual_makespan:
        notes.append(f"makespan mismatch: claimed={claimed_makespan}, actual={actual_makespan}")
        ok = False

    return json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "claimed_makespan": claimed_makespan,
        "actual_makespan": actual_makespan,
        "notes": "; ".join(notes) if notes else "all constraints satisfied",
    })


def format_gantt(solution_json: str) -> str:
    """
    Render a simple ASCII Gantt chart from the CP-SAT solution.
    """
    try:
        sol = json.loads(solution_json)
    except Exception:
        return "Could not parse solution for Gantt chart."

    schedule: list[dict] = sol.get("schedule", [])
    if not schedule:
        return "No schedule to render."

    makespan = sol.get("makespan", max(e["end"] for e in schedule))
    width = min(makespan, 60)
    scale = width / makespan if makespan > 0 else 1.0

    machines = sorted({e["machine"] for e in schedule})
    lines = [f"Makespan = {makespan} time units", ""]
    header = "Machine  |" + "".join(str(t % 10) for t in range(width + 1))
    lines.append(header)
    lines.append("-" * len(header))

    for machine in machines:
        row = ["."] * (width + 1)
        ops = [e for e in schedule if e["machine"] == machine]
        for op in ops:
            s = int(op["start"] * scale)
            e = int(op["end"] * scale)
            label = op["job"][0] if op["job"] else "?"
            for i in range(s, min(e, width + 1)):
                row[i] = label
        lines.append(f"{machine:<9}|{''.join(row)}")

    return "\n".join(lines)
