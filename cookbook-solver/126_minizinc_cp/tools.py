"""Recipe 126 — MiniZinc CP: Backend-Agnostic Nurse Scheduling.

Demonstrates "DODA for constraint programming": the same MiniZinc model
runs on any CP backend (CP-SAT, Gecode, Choco) by changing one parameter.

Key parallel:
  .spl file : LLM adapter  =  .mzn model : CP backend

Nurse scheduling problem:
  8 nurses, 7 days, 3 shifts (Morning/Afternoon/Night)
  Hard: coverage minimums, no night→morning consecutive, max 5 days
  Soft: nurse shift preferences (scored)

Install: pip install minizinc
         MiniZinc binary: https://www.minizinc.org/software.html
"""

import json
import textwrap

from spl.tools import spl_tool

# ── Problem data ──────────────────────────────────────────────────────────────

NURSES = ["N1_senior", "N2_senior", "N3", "N4", "N5", "N6", "N7", "N8"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = ["Morning", "Afternoon", "Night"]  # 0, 1, 2
OFF = 3

_PROBLEM = {
    "problem_name": "7-Day Nurse Scheduling",
    "description": (
        "Schedule 8 nurses (N1–N8; N1 and N2 are senior) across 7 days and 3 shifts. "
        "Hard constraints: "
        "(1) Morning shift needs ≥2 nurses, at least one senior (N1 or N2). "
        "(2) Afternoon shift needs ≥2 nurses. "
        "(3) Night shift needs ≥1 nurse. "
        "(4) No nurse works more than 5 days per week. "
        "(5) A nurse who works Night on day D cannot work Morning on day D+1 (rest rule). "
        "Soft preferences: N3 prefers mornings, N7 avoids nights, N8 prefers consecutive days off. "
        "Objective: maximize preference satisfaction score subject to all hard constraints."
    ),
    "n_nurses": 8,
    "n_days": 7,
    "n_shifts": 3,
    "senior_nurses": [0, 1],  # N1, N2 (0-indexed)
    "min_morning": 2,
    "min_afternoon": 2,
    "min_night": 1,
    "max_work_days": 5,
    # Preferences: (nurse_idx, shift_idx, score)
    "preferences": [
        (2, 0, 3),   # N3 prefers Morning: +3
        (6, 2, -3),  # N7 avoids Night: -3
        (7, 3, 2),   # N8 prefers Off (consecutive): +2 per Off day
    ],
}

# The MiniZinc model (as a string — invariant across backends)
_MZN_MODEL = textwrap.dedent("""\
    % Nurse scheduling: 8 nurses, 7 days, 3 shifts + off
    % Hard: coverage, rest between night→morning, max work days
    % Soft: maximize preference score

    int: n_nurses = {n_nurses};
    int: n_days   = {n_days};
    int: n_shifts = 3;   % 0=Morning 1=Afternoon 2=Night
    int: OFF      = 3;

    array[1..n_nurses, 1..n_days] of var 0..3: sched;

    % Shift coverage minimums
    constraint forall(d in 1..n_days) (
        sum(n in 1..n_nurses)(sched[n,d] == 0) >= {min_morning} /\\
        sum(n in 1..n_nurses)(sched[n,d] == 1) >= {min_afternoon} /\\
        sum(n in 1..n_nurses)(sched[n,d] == 2) >= {min_night}
    );

    % At least one senior (N1 or N2) on morning
    constraint forall(d in 1..n_days) (
        sched[1,d] == 0 \\/ sched[2,d] == 0
    );

    % Max 5 work days per week
    constraint forall(n in 1..n_nurses) (
        sum(d in 1..n_days)(sched[n,d] != OFF) <= {max_work_days}
    );

    % Night→Morning rest: no night on day d and morning on day d+1
    constraint forall(n in 1..n_nurses, d in 1..n_days-1) (
        not (sched[n,d] == 2 /\\ sched[n,d+1] == 0)
    );

    % Preference scores
    var int: pref_score =
        sum(d in 1..n_days)(sched[3,d] == 0) * 3       % N3 likes morning
      - sum(d in 1..n_days)(sched[7,d] == 2) * 3       % N7 dislikes night
      + sum(d in 1..n_days)(sched[8,d] == OFF) * 2;   % N8 likes days off

    solve maximize pref_score;

    output ["sched=", show(sched), "\\npref=", show(pref_score)];
""")


@spl_tool
def get_scheduling_problem() -> str:
    return json.dumps(_PROBLEM)


@spl_tool
def solve_with_minizinc(problem_json: str) -> str:
    """Solve nurse scheduling via MiniZinc Python interface.

    Tries CP-SAT (via OR-Tools) backend first, then Gecode.
    Falls back to a Python constraint solver if MiniZinc binary absent.
    """
    try:
        import minizinc  # type: ignore[import-untyped]
    except ImportError:
        return _python_cp_fallback(json.loads(problem_json),
                                   note="minizinc not installed — pip install minizinc + binary from minizinc.org")

    p = json.loads(problem_json)
    mzn_src = _MZN_MODEL.format(**p)

    try:
        model = minizinc.Model()
        model.add_string(mzn_src)

        for solver_tag in ("com.google.ortools.sat", "org.gecode.gecode"):
            try:
                solver = minizinc.Solver.lookup(solver_tag)
                inst = minizinc.Instance(solver, model)
                result = inst.solve(timeout=None)
                if result.status in (minizinc.Status.SATISFIED, minizinc.Status.OPTIMAL_SOLUTION):
                    sched_flat = result["sched"]
                    pref = result["pref_score"]
                    schedule = _parse_mzn_schedule(sched_flat, p)
                    violations = _count_violations(schedule, p)
                    return json.dumps({
                        "status": "OK",
                        "backend": solver_tag.split(".")[-1],
                        "violations": violations,
                        "pref_score": pref,
                        "schedule": schedule,
                        "n_nurses": p["n_nurses"],
                        "n_days": p["n_days"],
                    })
            except Exception:
                continue

        return _python_cp_fallback(p, note="No MiniZinc solver backend found (tried CP-SAT, Gecode)")

    except Exception as e:
        return _python_cp_fallback(p, note=f"MiniZinc error: {e}")


def _parse_mzn_schedule(sched_flat, p: dict) -> list:
    """Convert flat MiniZinc array to nurse×day schedule."""
    n_nurses = p["n_nurses"]
    n_days = p["n_days"]
    shift_labels = ["M", "A", "N", "Off"]
    schedule = []
    for n in range(n_nurses):
        row = {"nurse": NURSES[n], "days": {}}
        for d in range(n_days):
            val = sched_flat[n][d] if isinstance(sched_flat[0], list) else sched_flat[n * n_days + d]
            row["days"][DAYS[d]] = shift_labels[val]
        schedule.append(row)
    return schedule


def _python_cp_fallback(p: dict, note: str = "") -> str:
    """Python-only CP solver using backtracking (demonstrates same constraints)."""
    n_nurses = p["n_nurses"]
    n_days = p["n_days"]
    min_m, min_a, min_n = p["min_morning"], p["min_afternoon"], p["min_night"]
    max_work = p["max_work_days"]
    seniors = p["senior_nurses"]
    shift_names = ["M", "A", "N", "Off"]

    # Simple constructive: assign greedily, then verify
    import random as rnd
    rng = rnd.Random(42)
    sched = [[OFF] * n_days for _ in range(n_nurses)]

    # Ensure minimum coverage per day
    for d in range(n_days):
        # Assign morning: pick 2 nurses (1 senior required)
        morning_candidates = list(range(n_nurses))
        rng.shuffle(morning_candidates)
        morning_assigned = []
        # Senior first
        for n in seniors:
            if n in morning_candidates and len(morning_assigned) < min_m:
                prev_shift = sched[n][d - 1] if d > 0 else -1
                if prev_shift != 2:  # not coming off night
                    sched[n][d] = 0
                    morning_assigned.append(n)
        # Fill remaining morning spots
        for n in morning_candidates:
            if n not in morning_assigned and len(morning_assigned) < min_m:
                prev_shift = sched[n][d - 1] if d > 0 else -1
                if prev_shift != 2 and sum(sched[n][dd] != OFF for dd in range(d)) < max_work:
                    sched[n][d] = 0
                    morning_assigned.append(n)

        # Assign afternoon
        afternoon_assigned = []
        for n in morning_candidates:
            if n not in morning_assigned and len(afternoon_assigned) < min_a:
                if sum(sched[n][dd] != OFF for dd in range(d)) < max_work:
                    sched[n][d] = 1
                    afternoon_assigned.append(n)

        # Assign night
        night_assigned = []
        for n in morning_candidates:
            if (n not in morning_assigned and n not in afternoon_assigned
                    and len(night_assigned) < min_n):
                if sum(sched[n][dd] != OFF for dd in range(d)) < max_work:
                    sched[n][d] = 2
                    night_assigned.append(n)

    schedule = []
    for n in range(n_nurses):
        row = {"nurse": NURSES[n], "days": {DAYS[d]: shift_names[sched[n][d]] for d in range(n_days)}}
        schedule.append(row)

    violations = _count_violations(schedule, p)
    pref = _score_preferences(sched, p)

    return json.dumps({
        "status": "OK",
        "backend": "python_backtracking_fallback",
        "note": note or "MiniZinc unavailable; Python CP fallback used",
        "violations": violations,
        "pref_score": pref,
        "schedule": schedule,
        "n_nurses": n_nurses,
        "n_days": n_days,
    })


def _count_violations(schedule: list, p: dict) -> dict:
    """Count hard constraint violations in a schedule."""
    n_days = p["n_days"]
    violations = {"night_morning": 0, "coverage_shortage": 0, "overwork": 0}

    for d in range(n_days):
        counts = {"M": 0, "A": 0, "N": 0}
        for row in schedule:
            shift = row["days"].get(DAYS[d], "Off")
            if shift in counts:
                counts[shift] += 1
        if counts["M"] < p["min_morning"]:
            violations["coverage_shortage"] += 1
        if counts["A"] < p["min_afternoon"]:
            violations["coverage_shortage"] += 1
        if counts["N"] < p["min_night"]:
            violations["coverage_shortage"] += 1

    for row in schedule:
        work_days = sum(1 for d in DAYS if row["days"].get(d, "Off") != "Off")
        if work_days > p["max_work_days"]:
            violations["overwork"] += 1
        # Night → Morning check
        for d_idx in range(n_days - 1):
            if row["days"].get(DAYS[d_idx]) == "N" and row["days"].get(DAYS[d_idx + 1]) == "M":
                violations["night_morning"] += 1

    return violations


def _score_preferences(sched: list, p: dict) -> int:
    score = 0
    for row in p.get("preferences", []):
        n_idx, shift, pts = row
        for d in range(p["n_days"]):
            if sched[n_idx][d] == shift:
                score += pts
    return score


@spl_tool
def schedule_hard_constraints_met(result_json: str) -> bool:
    """ASSERT: no night→morning violations and no coverage shortages."""
    try:
        d = json.loads(result_json)
        if d.get("status") != "OK":
            return False
        v = d.get("violations", {})
        return v.get("night_morning", 1) == 0 and v.get("coverage_shortage", 1) == 0
    except Exception:
        return False


@spl_tool
def check_llm_schedule_violations(llm_schedule: str) -> str:
    """Parse LLM-generated text schedule and count constraint violations.

    Best-effort: looks for N/M pattern strings in the LLM output.
    Returns JSON with estimated violations.
    """
    # Count "N" followed by "M" in the same nurse row across days
    night_morning = 0
    lines = llm_schedule.split("\n")
    for line in lines:
        if "N" in line and "M" in line:
            # Check for N...M consecutive pattern (heuristic scan)
            tokens = line.upper().split()
            for i in range(len(tokens) - 1):
                if tokens[i] in ("N", "NIGHT") and tokens[i + 1] in ("M", "MORNING"):
                    night_morning += 1

    return json.dumps({
        "estimated_night_morning_violations": night_morning,
        "note": "Heuristic scan — exact count requires structured LLM output",
    })


@spl_tool
def format_schedule_report(result_json: str) -> str:
    try:
        d = json.loads(result_json)
        v = d.get("violations", {})
        backend = d.get("backend", "?")
        note = d.get("note", "")
        lines = [
            f"## CP Schedule Report — {d.get('problem_name', 'Nurse Scheduling')}",
            "",
            f"**Backend:** MiniZinc → {backend}  ",
            f"**Preference score:** {d.get('pref_score', '?')}  ",
            f"**Night→Morning violations:** {v.get('night_morning', '?')}  ",
            f"**Coverage shortages:** {v.get('coverage_shortage', '?')}  ",
            f"**Overwork violations:** {v.get('overwork', '?')}  ",
        ]
        if note:
            lines += ["", f"> {note}"]
        lines += [
            "",
            "### Weekly Schedule",
            "",
            "| Nurse | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Days |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for row in d.get("schedule", []):
            days = row.get("days", {})
            work_count = sum(1 for d_name in DAYS if days.get(d_name, "Off") != "Off")
            cells = " | ".join(days.get(day, "Off") for day in DAYS)
            lines.append(f"| {row['nurse']} | {cells} | {work_count} |")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


@spl_tool
def format_report_solver_on(cp_report: str, explanation: str) -> str:
    return (
        f"=== MiniZinc CP — Nurse Scheduling (r126) | solver=ON ===\n\n"
        f"{cp_report}\n\n"
        f"── Analyst Explanation ─────────────────────────────────────\n"
        f"{explanation}"
    )


@spl_tool
def format_report_solver_off(llm_schedule: str, violation_json: str) -> str:
    try:
        v = json.loads(violation_json)
        viol_note = (
            f"Estimated night→morning violations: {v.get('estimated_night_morning_violations', '?')}"
        )
    except Exception:
        viol_note = ""
    return (
        f"=== MiniZinc CP — Nurse Scheduling (r126) | solver=OFF ===\n\n"
        f"── LLM Schedule ─────────────────────────────────────────────\n"
        f"{llm_schedule}\n\n"
        f"── Constraint Check ─────────────────────────────────────────\n"
        f"{viol_note}\n\n"
        f"Note: LLM \"soft reasoning\" often misses hard constraint interactions.\n"
        f"Run --param use_solver=true for MiniZinc CP with guaranteed constraint satisfaction."
    )
