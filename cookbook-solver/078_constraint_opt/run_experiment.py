#!/usr/bin/env python3
"""
run_experiment.py — CLI for the Recipe-78 constraint optimization experiment.

Axes:
  Axis 1: Recipe      (r78a constraint_opt LP, r78b supply_chain LP,
                        r78c staff_scheduling ILP, r78d resource_allocation BILP)
  Axis 2: Model       (m001 sonnet-4-6, m002 gemma3, m003 gemma4:e2b, ...)
  Axis 3: Scale       (n05 = default, n10 = scaled, n20 = large)
  Axis 4: Solver arm  (true = PuLP+ASSERT, false = LLM only)
  Axis 5: Runs/cell

Must be run from the SPL.py repo root:
  cd ~/projects/digital-duck/SPL.py

Quick start:
  python cookbook/78_constraint_opt/run_experiment.py --list
  python cookbook/78_constraint_opt/run_experiment.py -r r78d -m m001 -n n05 -s true
  python cookbook/78_constraint_opt/run_experiment.py -r r78d -m m001 -n n10 -s false
  python cookbook/78_constraint_opt/run_experiment.py -r r78a,r78b,r78c,r78d -m m001 -n n05,n10,n20
  python cookbook/78_constraint_opt/run_experiment.py --dry-run
"""

import re
import socket
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

import click

# ── SQLite persistence ────────────────────────────────────────────────────────
DB_PATH_DEFAULT = "cookbook/78_constraint_opt/experiment_results.db"


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id           TEXT UNIQUE,
            hostname         TEXT,
            recipe_id        TEXT NOT NULL,
            recipe_name      TEXT NOT NULL,
            model_id         TEXT NOT NULL,
            model_label      TEXT NOT NULL,
            n_size           TEXT NOT NULL,
            solver           TEXT NOT NULL,
            run              INTEGER NOT NULL DEFAULT 1,
            problem          TEXT,
            -- outcomes
            status           TEXT,
            pass             INTEGER,
            objective_claimed REAL,
            correct          INTEGER,
            verify_status    TEXT,
            -- performance
            llm_calls        INTEGER,
            input_tokens     INTEGER,
            output_tokens    INTEGER,
            latency_ms       INTEGER,
            -- content
            output           TEXT,
            spl_log          TEXT,
            imported_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            source_id      TEXT PRIMARY KEY,
            hostname       TEXT,
            rows_total     INTEGER,
            rows_inserted  INTEGER DEFAULT 0,
            log_path       TEXT,
            started_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def write_cell(conn, source_id, recipe_id, recipe_name, model_id, model_label,
               n_size, solver, run_no, problem, metrics, hostname=""):
    run_id = f"{recipe_id}-{model_id}-{n_size}-{'T' if solver == 'true' else 'F'}-{run_no}"
    status = metrics["status"]
    passed = int(status in {"complete"})

    obj_raw = metrics.get("objective")
    try:
        obj = float(obj_raw) if obj_raw else None
    except (TypeError, ValueError):
        obj = None

    lat = metrics.get("latency_ms")
    try:
        lat = int(lat) if lat and lat != "?" else None
    except (TypeError, ValueError):
        lat = None

    llm = metrics.get("llm_calls")
    try:
        llm = int(llm) if llm and llm != "?" else None
    except (TypeError, ValueError):
        llm = None

    tok_in  = metrics.get("input_tokens")
    tok_out = metrics.get("output_tokens")
    try:
        tok_in  = int(tok_in)  if tok_in  and tok_in  != "?" else None
        tok_out = int(tok_out) if tok_out and tok_out != "?" else None
    except (TypeError, ValueError):
        tok_in = tok_out = None

    verify_raw = metrics.get("verify", "")
    verify_status = verify_raw if verify_raw and verify_raw != "N/A" else None

    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO results
                (run_id, hostname, recipe_id, recipe_name, model_id, model_label,
                 n_size, solver, run, problem,
                 status, pass, objective_claimed, verify_status,
                 llm_calls, input_tokens, output_tokens, latency_ms,
                 output, spl_log)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (run_id, hostname, recipe_id, recipe_name, model_id, model_label,
             n_size, solver, run_no, problem[:500] if problem else "",
             status, passed, obj, verify_status,
             llm, tok_in, tok_out, lat,
             metrics.get("output", "")[:4000],
             metrics.get("spl_log", "")),
        )
        conn.execute(
            "UPDATE runs SET rows_inserted = rows_inserted + 1 WHERE source_id = ?",
            (source_id,)
        )
        conn.commit()
    except Exception as exc:
        click.echo(f"\n  [DB WARNING] {exc}", err=True)


# ── Ground-truth back-fill: mark solver=OFF rows as correct/incorrect ─────────
def backfill_correct(conn):
    """After each run, update `correct` for solver=OFF rows using solver=ON ground truth."""
    rows = conn.execute("""
        SELECT recipe_id, model_id, n_size, objective_claimed
        FROM results
        WHERE solver = 'true' AND objective_claimed IS NOT NULL
    """).fetchall()
    for recipe_id, model_id, n_size, gt in rows:
        conn.execute("""
            UPDATE results
            SET correct = CASE
                WHEN objective_claimed IS NULL THEN 0
                WHEN ABS(objective_claimed - ?) < MAX(0.01 * ABS(?), 0.5) THEN 1
                ELSE 0
            END
            WHERE recipe_id = ? AND model_id = ? AND n_size = ? AND solver = 'false'
        """, (gt, gt, recipe_id, model_id, n_size))
    conn.commit()


# ── Axis 2: Model roster ─────────────────────────────────────────────────────
MODELS = {
    "m001": ("sonnet-4-6",      "claude_cli",          "claude_cli"),
    "m002": ("gemma3",          "ollama:gemma3",        "ollama"),
    "m003": ("gemma4:e2b",      "ollama:gemma4:e2b",    "ollama"),
    "m004": ("qwen2.5",         "ollama:qwen2.5",       "ollama"),
    "m005": ("deepseek-v2:16b", "ollama:deepseek-v2:16b", "ollama"),
    "m006": ("phi4",            "ollama:phi4",          "ollama"),
    "m007": ("llama3.2",        "ollama:llama3.2",      "ollama"),
    "m008": ("qwen3",           "ollama:qwen3",         "ollama"),
    "m009": ("gemma3:27b",      "ollama:gemma3:27b",    "ollama"),
}

# ── Axis 1 × 3: Recipes × Scale ──────────────────────────────────────────────
# n05 = default problem in the .spl file (hand-verifiable)
# n10, n20 = H2 scale problems from experiment_H2_scale_sensitivity.md
RECIPES = {
    "r78a": {
        "name":   "constraint_opt",
        "label":  "LP (production)",
        "script": "cookbook/78_constraint_opt/constraint_opt.spl",
        "problems": {
            "n05": (
                "A furniture workshop produces chairs and tables. Each chair requires 2 hours of "
                "labor and 3 kg of wood, earning $20 profit. Each table requires 4 hours of labor "
                "and 5 kg of wood, earning $30 profit. The workshop has 24 hours of labor and 30 kg "
                "of wood available per day. Both quantities must be non-negative. Maximize daily profit."
            ),
            "n10": (
                "A furniture factory produces 10 product lines. Each unit requires labor (hours), "
                "lumber (kg), upholstery fabric (m²), and steel (kg), and earns a fixed profit. "
                "Product specifications per unit: Dining Chair needs 2.0h labor, 3.0kg lumber, 0.8m² "
                "fabric, 0.0kg steel, profit $25. Dining Table needs 4.0h labor, 8.0kg lumber, 0.0m² "
                "fabric, 0.0kg steel, profit $55. Office Desk needs 3.5h labor, 5.0kg lumber, 0.0m² "
                "fabric, 1.5kg steel, profit $45. Bookcase needs 5.0h labor, 9.0kg lumber, 0.0m² "
                "fabric, 0.5kg steel, profit $58. Wardrobe needs 7.0h labor, 14.0kg lumber, 0.0m² "
                "fabric, 0.5kg steel, profit $85. Armchair needs 3.0h labor, 2.0kg lumber, 1.5m² "
                "fabric, 0.0kg steel, profit $48. Bed Frame needs 5.0h labor, 10.0kg lumber, 0.0m² "
                "fabric, 2.0kg steel, profit $72. Coffee Table needs 2.0h labor, 4.0kg lumber, 0.0m² "
                "fabric, 0.0kg steel, profit $28. Storage Cabinet needs 4.0h labor, 7.0kg lumber, "
                "0.0m² fabric, 1.0kg steel, profit $52. Lounge Sofa needs 4.0h labor, 3.0kg lumber, "
                "2.5m² fabric, 0.0kg steel, profit $68. Available daily: 120 labor hours, 150 kg "
                "lumber, 15 m² upholstery fabric, 12 kg steel. Production quantities are continuous "
                "(fractional units allowed). Maximize total daily profit."
            ),
            "n20": (
                "A furniture factory produces 20 product lines. Each unit requires labor (hours), "
                "lumber (kg), upholstery fabric (m²), steel (kg), and finishing time (hours). "
                "Product specifications per unit: Dining Chair 2.0h/3.0kg/0.8m²/0.0kg/0.5h $25. "
                "Dining Table 4.0h/8.0kg/0.0m²/0.0kg/1.0h $55. Office Desk 3.5h/5.0kg/0.0m²/"
                "1.5kg/0.8h $45. Bookcase 5.0h/9.0kg/0.0m²/0.5kg/1.0h $58. Wardrobe 7.0h/14.0kg/"
                "0.0m²/0.5kg/1.5h $85. Armchair 3.0h/2.0kg/1.5m²/0.0kg/0.5h $48. Bed Frame "
                "5.0h/10.0kg/0.0m²/2.0kg/1.2h $72. Coffee Table 2.0h/4.0kg/0.0m²/0.0kg/0.4h "
                "$28. Storage Cabinet 4.0h/7.0kg/0.0m²/1.0kg/0.8h $52. Lounge Sofa 4.0h/3.0kg/"
                "2.5m²/0.0kg/0.6h $68. Nightstand 1.5h/2.5kg/0.0m²/0.0kg/0.3h $20. Dresser "
                "4.5h/8.0kg/0.0m²/0.5kg/1.0h $62. Vanity Table 3.0h/4.5kg/0.0m²/1.0kg/0.7h "
                "$42. Ottoman 2.0h/1.0kg/1.2m²/0.0kg/0.3h $35. Side Table 1.5h/2.0kg/0.0m²/"
                "0.0kg/0.3h $18. Media Console 3.5h/6.0kg/0.0m²/0.5kg/0.7h $48. Hall Tree "
                "3.0h/5.0kg/0.0m²/1.0kg/0.6h $40. Shoe Rack 2.0h/3.5kg/0.0m²/0.5kg/0.4h "
                "$24. Bar Cart 2.5h/1.5kg/0.0m²/2.5kg/0.5h $38. Rocking Chair 3.5h/4.0kg/"
                "0.5m²/0.0kg/0.7h $44. Available daily: 200 labor hours, 250 kg lumber, 20 m² "
                "fabric, 18 kg steel, 30 finishing hours. Fractional units allowed. Maximize profit."
            ),
        },
        "known_optimal": {"n05": 200.0, "n10": None, "n20": None},
    },
    "r78b": {
        "name":   "supply_chain",
        "label":  "LP (transportation)",
        "script": "cookbook/78_constraint_opt/supply_chain.spl",
        "problems": {
            "n05": (
                "A company has two warehouses and three retail stores. Warehouse W1 has 80 units of "
                "inventory; Warehouse W2 has 60 units. Store S1 needs 50 units, Store S2 needs 40 units, "
                "Store S3 needs 50 units. Shipping costs per unit: W1 to S1 costs $2, W1 to S2 costs $3, "
                "W1 to S3 costs $1; W2 to S1 costs $5, W2 to S2 costs $4, W2 to S3 costs $8. All store "
                "demand must be met exactly. Minimize total shipping cost."
            ),
            "n10": (
                "A regional distributor has 4 warehouses and 5 retail stores. Warehouse W1 holds 90 units, "
                "W2 holds 70 units, W3 holds 80 units, W4 holds 60 units (total supply 300). Store S1 "
                "needs 60 units, S2 needs 55 units, S3 needs 70 units, S4 needs 50 units, S5 needs 65 "
                "units (total demand 300). Shipping cost per unit: W1 to S1 $3, W1 to S2 $2, W1 to S3 $5, "
                "W1 to S4 $8, W1 to S5 $4. W2 to S1 $6, W2 to S2 $4, W2 to S3 $3, W2 to S4 $5, W2 to "
                "S5 $7. W3 to S1 $4, W3 to S2 $7, W3 to S3 $2, W3 to S4 $6, W3 to S5 $3. W4 to S1 $8, "
                "W4 to S2 $5, W4 to S3 $6, W4 to S4 $2, W4 to S5 $9. All store demand must be exactly "
                "met. Minimize total shipping cost."
            ),
            "n20": (
                "A national distributor operates 8 warehouses and 5 regional distribution centers. "
                "Warehouse capacities: W1=100, W2=80, W3=90, W4=70, W5=60, W6=85, W7=75, W8=65 (total "
                "supply 625). DC requirements: D1=120, D2=110, D3=130, D4=140, D5=125 (total demand 625). "
                "Shipping cost per unit: W1: D1 $4, D2 $2, D3 $6, D4 $9, D5 $5. W2: D1 $7, D2 $5, D3 "
                "$3, D4 $6, D5 $8. W3: D1 $3, D2 $8, D3 $2, D4 $7, D5 $4. W4: D1 $9, D2 $4, D3 $7, D4 "
                "$2, D5 $10. W5: D1 $5, D2 $3, D3 $8, D4 $4, D5 $6. W6: D1 $6, D2 $7, D3 $4, D4 $5, "
                "D5 $2. W7: D1 $8, D2 $6, D3 $5, D4 $3, D5 $7. W8: D1 $2, D2 $9, D3 $7, D4 $8, D5 $3. "
                "All DC demand must be exactly met. Minimize total shipping cost."
            ),
        },
        "known_optimal": {"n05": None, "n10": None, "n20": None},
    },
    "r78c": {
        "name":   "staff_scheduling",
        "label":  "ILP (scheduling)",
        "script": "cookbook/78_constraint_opt/staff_scheduling.spl",
        "problems": {
            "n05": (
                "A clinic needs to staff one day with 3 shifts: Morning, Afternoon, and Night. Minimum "
                "nurse coverage required: Morning needs at least 2 nurses, Afternoon needs at least 2 "
                "nurses, Night needs at least 1 nurse. Five nurses are available (Nurse1 through Nurse5). "
                "Each nurse can work at most 1 shift today. Wage per nurse-shift: Morning costs $200, "
                "Afternoon costs $180, Night costs $320. Assign nurses to shifts to meet all minimum "
                "coverage requirements at minimum total wage cost."
            ),
            "n10": (
                "A hospital clinic needs to staff one day with 4 shifts: Early Morning (5am-1pm), Day "
                "(9am-5pm), Evening (1pm-9pm), and Night (9pm-5am). Minimum nurse coverage: Early Morning "
                "needs at least 2 nurses, Day needs at least 3 nurses, Evening needs at least 3 nurses, "
                "Night needs at least 2 nurses (total minimum 10 slots). Ten nurses are available: Nurse1 "
                "through Nurse10. Each nurse can work at most 1 shift today. Wage per nurse-shift: Early "
                "Morning costs $280, Day costs $220, Evening costs $240, Night costs $350. Assign nurses "
                "to shifts to meet all minimum coverage requirements at minimum total wage cost."
            ),
            "n20": (
                "A regional hospital needs to staff one day with 5 shifts: Night (11pm-7am), Early Morning "
                "(6am-2pm), Day (10am-6pm), Evening (2pm-10pm), and Late Night (8pm-4am). Minimum nurse "
                "coverage: Night needs at least 3 nurses, Early Morning needs at least 4 nurses, Day needs "
                "at least 5 nurses, Evening needs at least 4 nurses, Late Night needs at least 3 nurses "
                "(total minimum 19 slots). Twenty nurses are available: Nurse1 through Nurse20. Each nurse "
                "can work at most 1 shift today. Wage per nurse-shift: Night costs $380, Early Morning "
                "costs $260, Day costs $200, Evening costs $230, Late Night costs $310. Assign nurses to "
                "shifts to meet all minimum coverage requirements at minimum total wage cost. Note: total "
                "nurse capacity (20) exceeds minimum demand (19), so exactly one nurse will not be "
                "assigned to any shift."
            ),
        },
        "known_optimal": {"n05": 1080.0, "n10": 2640.0, "n20": 5030.0},
    },
    "r78d": {
        "name":   "resource_allocation",
        "label":  "Binary ILP (portfolio)",
        "script": "cookbook/78_constraint_opt/resource_allocation.spl",
        "problems": {
            "n05": (
                "An IT department must select a portfolio of projects for next quarter. Six candidate "
                "projects are available. Project P1 costs $120K and requires 3 developer-months, "
                "delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, "
                "delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering "
                "value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. "
                "Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 "
                "costs $90K and requires 2 developer-months, delivering value 6. The total budget is "
                "$500K and the team has 10 developer-months available. Each project is either fully "
                "funded or not funded - no partial investment. Select which projects to fund to maximize "
                "total strategic value."
            ),
            "n10": (
                "An IT department must select a portfolio of projects for next quarter. Ten candidate "
                "projects are available. Project P1 costs $80K and requires 2 developer-months, "
                "delivering strategic value 6. Project P2 costs $120K and requires 3 developer-months, "
                "delivering value 9. Project P3 costs $60K and requires 2 developer-months, delivering "
                "value 5. Project P4 costs $150K and requires 4 developer-months, delivering value 11. "
                "Project P5 costs $200K and requires 5 developer-months, delivering value 12. Project P6 "
                "costs $90K and requires 2 developer-months, delivering value 7. Project P7 costs $110K "
                "and requires 3 developer-months, delivering value 8. Project P8 costs $70K and requires "
                "2 developer-months, delivering value 5. Project P9 costs $180K and requires 4 "
                "developer-months, delivering value 13. Project P10 costs $100K and requires 3 "
                "developer-months, delivering value 6. The total budget is $600K and the team has 15 "
                "developer-months available. Each project is either fully funded or not - no partial "
                "investment. Select which projects to fund to maximize total strategic value."
            ),
            "n20": (
                "An IT department must select a portfolio of projects for next year. Twenty candidate "
                "projects are available. Project P1 costs $80K/2mo/value 6. Project P2 costs "
                "$120K/3mo/value 9. Project P3 costs $60K/2mo/value 5. Project P4 costs $150K/4mo/"
                "value 11. Project P5 costs $200K/5mo/value 12. Project P6 costs $90K/2mo/value 7. "
                "Project P7 costs $110K/3mo/value 8. Project P8 costs $70K/2mo/value 5. Project P9 "
                "costs $180K/4mo/value 13. Project P10 costs $100K/3mo/value 6. Project P11 costs "
                "$130K/3mo/value 10. Project P12 costs $85K/2mo/value 6. Project P13 costs $160K/4mo/"
                "value 12. Project P14 costs $75K/2mo/value 5. Project P15 costs $220K/5mo/value 14. "
                "Project P16 costs $95K/3mo/value 7. Project P17 costs $140K/4mo/value 10. Project P18 "
                "costs $65K/2mo/value 5. Project P19 costs $170K/4mo/value 12. Project P20 costs "
                "$115K/3mo/value 8. Total budget $1000K, team capacity 25 developer-months. Each "
                "project fully funded or not. Maximize total strategic value."
            ),
        },
        "known_optimal": {"n05": 28.0, "n10": 45.0, "n20": None},
    },
}

N_SIZES  = ("n05", "n10", "n20")
SOLVERS  = ("true", "false")
SCRIPT_DEFAULT = "cookbook/78_constraint_opt/constraint_opt.spl"
LOG_DIR_DEFAULT = "cookbook/78_constraint_opt/logs"
OUT_DIR         = "cookbook/78_constraint_opt/output"


# ── Output parser ─────────────────────────────────────────────────────────────
def stream_run(cmd: list, log_file) -> tuple:
    """Run cmd, stream stdout+stderr to console and log. Returns (rc, metrics)."""
    metrics = {
        "status": "unknown", "llm_calls": "?", "latency_ms": "?",
        "objective": None, "verify": None,
        "input_tokens": None, "output_tokens": None,
        "output": "", "output_preview": "?", "spl_log": "?",
    }
    status_priority = 0
    in_output = False
    output_lines: list[str] = []

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
            s = line.strip()

            if in_output and (
                s.startswith("LLM calls:") or s.startswith("Log:")
                or s.startswith("Status:") or s.startswith("====")
            ):
                full = "\n".join(output_lines).strip()
                metrics["output"] = full
                metrics["output_preview"] = full[:120]
                in_output = False

            if s.startswith("Status:") and status_priority < 1:
                metrics["status"] = s.split(":", 1)[1].strip()
                status_priority = 1

            elif s.startswith("Output:"):
                first_line = s.split(":", 1)[1].strip()
                output_lines = [first_line]
                in_output = True

            elif in_output:
                output_lines.append(line.rstrip("\n"))

            elif s.startswith("LLM calls:"):
                m = re.search(r"LLM calls:\s*(\d+)\s+Latency:\s*(\d+)ms", s)
                if m:
                    metrics["llm_calls"] = m.group(1)
                    metrics["latency_ms"] = m.group(2)

            elif s.startswith("Log:"):
                metrics["spl_log"] = s.split(":", 1)[1].strip()

            elif "RETURN:" in s and status_priority < 2:
                m_st  = re.search(r"\bstatus=(\w+)", s)
                m_obj = re.search(r"\bobjective=([\d.]+)", s)
                m_ver = re.search(r"\bverify=(\w+)", s)
                if m_st:
                    metrics["status"] = m_st.group(1)
                    status_priority = 2
                if m_obj:
                    metrics["objective"] = m_obj.group(1)
                if m_ver:
                    metrics["verify"] = m_ver.group(1)

            # Parse token counts from LOGGING lines emitted by the .spl
            elif "tokens_in=" in s:
                m_in  = re.search(r"tokens_in=(\d+)", s)
                m_out = re.search(r"tokens_out=(\d+)", s)
                if m_in:
                    metrics["input_tokens"] = m_in.group(1)
                if m_out:
                    metrics["output_tokens"] = m_out.group(1)

            # Parse objective from LOGGING when not in RETURN line
            elif "objective_claimed=" in s:
                m_obj = re.search(r"objective_claimed=([\d.]+)", s)
                if m_obj and not metrics["objective"]:
                    metrics["objective"] = m_obj.group(1)

    proc.wait()
    if in_output and output_lines:
        full = "\n".join(output_lines).strip()
        metrics["output"] = full
        metrics["output_preview"] = full[:120]

    return proc.returncode, metrics


def parse_ids(values: tuple) -> list:
    ids = []
    for v in values:
        ids.extend(p for p in re.split(r"[,\s]+", v) if p)
    return ids


# ── CLI ───────────────────────────────────────────────────────────────────────
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--recipe",  "-r", "recipe_ids",   multiple=True,
              help="Recipe ID(s): r78a r78b r78c r78d (default: all)")
@click.option("--model",   "-m", "model_ids",    multiple=True,
              help="Model ID(s): m001 m002 ... (default: all)")
@click.option("--size",    "-n", "n_sizes",      multiple=True,
              default=("n05",), show_default=True,
              help="Scale(s): n05 n10 n20")
@click.option("--solver",  "-s", "solver_modes", multiple=True,
              default=("true", "false"), show_default=True,
              help='Solver arm: "true" (PuLP+ASSERT) or "false" (LLM only)')
@click.option("--runs",        "-k", default=1,    show_default=True,
              help="Repetitions per cell")
@click.option("--llm-timeout", "-t", "llm_timeout", default=None, type=int,
              help="Per-call LLM timeout in seconds (passed as --llm-timeout to spl3 run). "
                   "Defaults to adapter built-in (1200s for claude_cli).")
@click.option("--db",      default=DB_PATH_DEFAULT, show_default=True,
              help="SQLite database path")
@click.option("--log-dir", default=LOG_DIR_DEFAULT, show_default=True)
@click.option("--list",    "show_list", is_flag=True)
@click.option("--dry-run", is_flag=True)
def main(recipe_ids, model_ids, n_sizes, solver_modes, runs, llm_timeout, db, log_dir,
         show_list, dry_run):
    """Run the Recipe-78 constraint optimization ablation experiment."""

    if show_list:
        click.echo("\nRecipe IDs  (use with -r):")
        for rid, info in RECIPES.items():
            click.echo(f"  {rid:<8}  {info['label']:<28}  {info['script']}")
        click.echo("\nModel IDs  (use with -m):")
        for mid, (label, adapter, _) in MODELS.items():
            click.echo(f"  {mid:<8}  {label:<20}  {adapter}")
        click.echo("\nSize IDs  (use with -n):")
        for n in N_SIZES:
            click.echo(f"  {n}")
        return

    recipe_ids   = parse_ids(recipe_ids)   or list(RECIPES.keys())
    model_ids    = parse_ids(model_ids)    or list(MODELS.keys())
    n_sizes      = parse_ids(n_sizes)
    solver_modes = parse_ids(solver_modes)

    for rid in recipe_ids:
        if rid not in RECIPES:
            raise click.BadParameter(f"'{rid}' not found. Run --list.", param_hint="-r")
    for mid in model_ids:
        if mid not in MODELS:
            raise click.BadParameter(f"'{mid}' not found. Run --list.", param_hint="-m")
    for n in n_sizes:
        if n not in N_SIZES:
            raise click.BadParameter(f"'{n}' must be one of {N_SIZES}", param_hint="-n")

    sel_recipes = {k: v for k, v in RECIPES.items() if k in recipe_ids}
    sel_models  = {k: v for k, v in MODELS.items()  if k in model_ids}
    total = len(sel_recipes) * len(sel_models) * len(n_sizes) * len(solver_modes) * runs

    hostname  = socket.gethostname()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path  = Path(log_dir) / f"recipe-78-log-{timestamp}.md"
    source_id = f"exp-{timestamp}"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    click.echo(f"\nRecipes  ({len(sel_recipes)}): {list(sel_recipes.keys())}")
    click.echo(f"Models   ({len(sel_models)}): {list(sel_models.keys())}")
    click.echo(f"Sizes    : {n_sizes}")
    click.echo(f"Solver   : {solver_modes}")
    click.echo(f"Runs/cell: {runs}")
    click.echo(f"Total    : {total} cells")

    if dry_run:
        click.echo(f"\n--- DRY RUN ---")
        for rid, rinfo in sel_recipes.items():
            for mid, (label, adapter, _) in sel_models.items():
                for n in n_sizes:
                    problem = rinfo["problems"].get(n, "")
                    for solver_mode in solver_modes:
                        click.echo(
                            f"  [{rid}/{mid}/{n}/solver={solver_mode}] "
                            f"spl3 run {rinfo['script']} --llm {adapter} "
                            f"--param use_solver={solver_mode} "
                            f"--param problem=\"{problem[:60]}...\""
                        )
        return

    db_conn = init_db(db)
    db_conn.execute(
        "INSERT OR IGNORE INTO runs (source_id, hostname, rows_total, log_path) VALUES (?,?,?,?)",
        (source_id, hostname, total, str(log_path))
    )
    db_conn.commit()

    click.echo(f"Hostname : {hostname}")
    click.echo(f"Log      : {log_path}")
    click.echo(f"DB       : {db}  (source={source_id})\n")

    with open(log_path, "w") as log:
        log.write(f"# Recipe-78 experiment run {timestamp}\n\nDB source: `{source_id}`\n\n")

        completed = 0
        for rid, rinfo in sel_recipes.items():
            for mid, (label, adapter, _) in sel_models.items():
                for n in n_sizes:
                    problem = rinfo["problems"].get(n, "")
                    known = rinfo["known_optimal"].get(n)
                    for solver_mode in solver_modes:
                        for run_no in range(1, runs + 1):
                            cell = f"[{rid}/{mid}/{n}] solver={solver_mode} run={run_no}"
                            click.echo(f"\n{'='*56}")
                            click.echo(f" {cell}")
                            click.echo(f" {label} ({rinfo['label']})")
                            click.echo(f" Problem: {problem[:70]}")
                            if known is not None:
                                click.echo(f" Known optimal: {known}")
                            click.echo(f"{'='*56}")

                            cmd = [
                                "spl3", "run", rinfo["script"],
                                "--llm", adapter,
                                "--param", f"problem={problem}",
                                "--param", f"use_solver={solver_mode}",
                                "--param", f"out_dir={OUT_DIR}",
                            ]
                            if llm_timeout is not None:
                                cmd += ["--llm-timeout", str(llm_timeout)]

                            log.write(
                                f"\n## {label} — {rid} {n} solver={solver_mode} run={run_no}\n\n"
                                f"_Host: `{hostname}` | Problem: {problem[:80]}_\n\n"
                                f"```bash\n$ {' '.join(cmd[:6])} ...\n```\n\n```output\n"
                            )
                            log.flush()

                            _, metrics = stream_run(cmd, log)
                            log.write("```\n\n")
                            log.flush()

                            write_cell(
                                db_conn, source_id,
                                rid, rinfo["name"], mid, label,
                                n, solver_mode, run_no, problem, metrics,
                                hostname=hostname,
                            )

                            completed += 1
                            passed = metrics["status"] == "complete"
                            outcome = "✓" if passed else "✗"
                            obj_str = f"  obj={metrics['objective']}" if metrics["objective"] else ""
                            ver_str = f"  verify={metrics['verify']}" if metrics["verify"] else ""
                            click.echo(
                                f"\n  [{completed}/{total}] {cell}"
                                f" → {outcome} {metrics['status']}"
                                f"  llm_calls={metrics['llm_calls']}"
                                f"  latency={metrics['latency_ms']}ms"
                                f"{obj_str}{ver_str}"
                            )

        backfill_correct(db_conn)
        db_conn.close()

    click.echo(f"\n{'='*56}")
    click.echo(f" Done — {completed}/{total} cells.")
    click.echo(f" Log: {log_path}")
    click.echo(f" DB : {db}  (source={source_id})")
    click.echo(f"{'='*56}")


if __name__ == "__main__":
    main()
