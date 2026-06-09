#!/usr/bin/env python3
"""
run_experiment.py — CLI for the Recipe-67 symbolic-math experiment.

Must be run from the SPL.py repo root:
  cd ~/projects/digital-duck/SPL.py

Requires: conda activate spl123   (spl3 must be on PATH)

Quick start:
  python cookbook/67_symbolic_math/run_experiment.py --list
  python cookbook/67_symbolic_math/run_experiment.py -m m001 -p p003          # smoke test
  python cookbook/67_symbolic_math/run_experiment.py -m "m006,m007" -p "p003 p005" --dry-run
  python cookbook/67_symbolic_math/run_experiment.py -m m001 -m m007 -p p003  # repeated flags
  python cookbook/67_symbolic_math/run_experiment.py                           # all 9 models
  python cookbook/67_symbolic_math/run_experiment.py -s true -s false -r 3    # both solver arms
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

import click


def parse_ids(values: tuple) -> list:
    """Expand comma/space-delimited strings from click multiple options.

    All three call styles produce the same result:
      -m m001 -m m007
      -m "m001,m007"
      -m "m001 m007"
      -m "m001, m007" -m m009
    """
    ids = []
    for v in values:
        ids.extend(part for part in re.split(r"[,\s]+", v) if part)
    return ids

# ── Axis 2: Model roster ─────────────────────────────────────────────────────
# id → (label, adapter, provider)
# IDs use zero-padded m001–m999 so alphabetical order == numerical order,
# making log filenames and automated parsing unambiguous at any scale.
MODELS = {
    "m001": ("sonnet-4-6",  "claude_cli",         "claude_cli"),
    "m002": ("gemma3",      "ollama:gemma3",       "ollama"),
    "m003": ("gemma4:12b",  "ollama:gemma4:12b",   "ollama"),
    "m004": ("qwen2.5",     "ollama:qwen2.5",      "ollama"),
    "m005": ("qwen3",       "ollama:qwen3",        "ollama"),
    "m006": ("phi3",        "ollama:phi3",         "ollama"),
    "m007": ("phi4",        "ollama:phi4",         "ollama"),
    "m008": ("deepseek-r1", "ollama:deepseek-r1",  "ollama"),
    "m009": ("lfm2.5",      "ollama:lfm2.5",       "ollama"),
}

# ── Axis 1: Problem battery (ordered easy → hard, Tier 0–5) ──────────────────
# id → (tier, problem-text)
# IDs use zero-padded p001–p999; current p001–p010 match the numbered table
# in case-2-hackernews.md § Axis 1.
PROBLEMS = {
    "p001": ("T0", "differentiate x**4 - 2*x**2 + 1"),
    "p002": ("T1", "expand (x+1)**2, then factor the expanded form"),
    "p003": ("T1", "differentiate 3*x**3-x, then factor if needed, finally solve for x"),
    "p004": ("T1", "expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0"),
    "p005": ("T2", "differentiate e**x and simplify it if necessary"),
    "p006": ("T2", "First, differentiate e**x. Then simplify the result."),
    "p007": ("T3", "integrate the square root of (4 minus x squared)"),
    "p008": ("T3", "find the integral of sin(x) times cos(x), then simplify the result"),
    "p009": ("T4", "find the Laplace transform of e to the power of negative 2t"),
    "p010": ("T5", "simplify the expression and tell me what x equals"),
}

SCRIPT_DEFAULT = "cookbook/67_symbolic_math/sympy_math_multi_step.spl"
LOG_DIR_DEFAULT = "cookbook/67_symbolic_math/logs-spl"


def stream_run(cmd: list, log_file) -> tuple:
    """Run cmd, streaming stdout+stderr to console and log_file.

    Returns (returncode, metrics) where metrics is a dict with keys:
      status, llm_calls, latency_ms, steps
    parsed from spl3's standard output lines.
    """
    metrics = {
        "status": "unknown", "llm_calls": "?",
        "latency_ms": "?", "steps": "?", "spl_log": "?",
        "output_preview": "?",
    }
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
            s = line.strip()
            if s.startswith("Status:"):
                metrics["status"] = s.split(":", 1)[1].strip()
            elif s.startswith("Output:"):
                preview = s.split(":", 1)[1].strip()
                metrics["output_preview"] = preview[:80]
                # (no COMMIT) means spl3 ran but nothing was verified/committed —
                # status=complete is misleading; reclassify as silent_failure
                if preview == "(no COMMIT)":
                    metrics["status"] = "silent_failure"
            elif s.startswith("LLM calls:"):
                m = re.search(r"LLM calls:\s*(\d+)\s+Latency:\s*(\d+)ms", s)
                if m:
                    metrics["llm_calls"] = m.group(1)
                    metrics["latency_ms"] = m.group(2)
            elif s.startswith("Log:"):
                metrics["spl_log"] = s.split(":", 1)[1].strip()
            elif "| status=" in s and "steps=" in s:
                m = re.search(r"steps=(\d+)", s)
                if m:
                    metrics["steps"] = m.group(1)
    proc.wait()
    # steps=0 + complete + non-empty output → pipeline was bypassed entirely;
    # the LLM free-formed a correct-looking answer without SymPy verification.
    if (metrics["status"] == "complete"
            and metrics["steps"] == "0"
            and metrics["output_preview"] not in ("?", "(no COMMIT)")):
        metrics["status"] = "unverified_success"
    return proc.returncode, metrics


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--model",   "-m", "model_ids",    multiple=True,
              help="Model ID(s) — comma/space-delimited or repeatable: "
                   '-m "phi3,phi4"  or  -m phi3 -m phi4  (default: all). '
                   "Run --list to see IDs.")
@click.option("--problem", "-p", "problem_ids",  multiple=True,
              help="Problem ID(s) — comma/space-delimited or repeatable: "
                   '-p "p1a p1b"  or  -p p1a -p p1b  (default: all). '
                   "Run --list to see IDs.")
@click.option("--solver",  "-s", "solver_modes", multiple=True,
              default=("true",), show_default=True,
              help='Solver arm(s): "true" (SymPy kernel on) or "false" (LLM only). '
                   'Only applied when --script points to sympy_llm.spl.')
@click.option("--runs",    "-r", default=1,      show_default=True,
              help="Repetitions per (model × problem × solver) cell.")
@click.option("--script",  default=SCRIPT_DEFAULT, show_default=True,
              help="SPL script to execute.")
@click.option("--log-dir", default=LOG_DIR_DEFAULT, show_default=True,
              help="Directory for the markdown log output.")
@click.option("--list",    "show_list", is_flag=True,
              help="Print all available model and problem IDs, then exit.")
@click.option("--dry-run", is_flag=True,
              help="Show the commands that would run without executing them.")
def main(model_ids, problem_ids, solver_modes, runs, script, log_dir,
         show_list, dry_run):
    """Run the Recipe-67 symbolic-math experiment across up to 4 axes:
    problems (Axis 1), models (Axis 2), solver on/off (Axis 3), repetitions (Axis 4).
    """
    if show_list:
        click.echo("\nModel IDs  (use with -m):")
        for mid, (label, adapter, _) in MODELS.items():
            click.echo(f"  {mid:<12}  {label:<14}  {adapter}")
        click.echo("\nProblem IDs  (use with -p):")
        for pid, (tier, text) in PROBLEMS.items():
            click.echo(f"  {pid:<6}  [{tier}]  {text[:72]}")
        return

    # Expand comma/space-delimited input before any validation or selection
    model_ids   = parse_ids(model_ids)
    problem_ids = parse_ids(problem_ids)

    # Validate IDs early so the error message is clean
    for mid in model_ids:
        if mid not in MODELS:
            raise click.BadParameter(
                f"'{mid}' not found. Run --list to see available model IDs.",
                param_hint="--model")
    for pid in problem_ids:
        if pid not in PROBLEMS:
            raise click.BadParameter(
                f"'{pid}' not found. Run --list to see available problem IDs.",
                param_hint="--problem")

    # Resolve selections (preserve declaration order)
    sel_models   = {k: v for k, v in MODELS.items()
                    if not model_ids   or k in model_ids}
    sel_problems = {k: v for k, v in PROBLEMS.items()
                    if not problem_ids or k in problem_ids}

    use_solver_param = "sympy_llm" in script
    total = len(sel_models) * len(sel_problems) * len(solver_modes) * runs

    click.echo(f"\nModels   ({len(sel_models)}): {list(sel_models.keys())}")
    click.echo(f"Problems ({len(sel_problems)}): {list(sel_problems.keys())}")
    click.echo(f"Solver modes : {list(solver_modes)}"
               + ("" if use_solver_param else "  [ignored — not sympy_llm.spl]"))
    click.echo(f"Runs/cell    : {runs}")
    click.echo(f"Total cells  : {total}")

    if dry_run:
        click.echo("\n--- DRY RUN ---")
        for pid, (tier, problem) in sel_problems.items():
            for mid, (label, adapter, _) in sel_models.items():
                for solver_mode in solver_modes:
                    for run_no in range(1, runs + 1):
                        extra = (f" --param enable_solver={solver_mode}"
                                 if use_solver_param else "")
                        click.echo(
                            f"  [{tier}/{pid}] [{mid}] run={run_no} solver={solver_mode}\n"
                            f"    spl3 run {script} --llm {adapter}"
                            f" --param problem=\"{problem[:55]}...\"{extra}"
                        )
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path  = Path(log_dir) / f"case-2-log-rerun-{timestamp}.md"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    click.echo(f"Log          : {log_path}\n")

    with open(log_path, "w") as log:
        log.write(f"# The experimental logs for Recipe #67 (rerun {timestamp})\n\n")

        completed = 0
        for pid, (tier, problem) in sel_problems.items():
            for mid, (label, adapter, provider) in sel_models.items():
                for solver_mode in solver_modes:
                    for run_no in range(1, runs + 1):

                        cell = (f"[{pid}/{mid}] solver={solver_mode} run={run_no}")
                        click.echo(f"\n{'='*54}")
                        click.echo(f" {cell}")
                        click.echo(f" {label} ({provider})")
                        click.echo(f" Problem ({tier}): {problem[:65]}")
                        click.echo(f"{'='*54}")

                        cmd = ["spl3", "run", script,
                               "--llm", adapter,
                               "--param", f"problem={problem}"]
                        if use_solver_param:
                            cmd += ["--param", f"enable_solver={solver_mode}"]

                        extra_md = (f" \\\n   --param enable_solver={solver_mode}"
                                    if use_solver_param else "")
                        log.write(
                            f"\n## {label} ({provider})"
                            f" — solver={solver_mode} — run {run_no}\n\n"
                            f"_Tier: {tier} | Problem ID: `{pid}`_\n\n"
                            f"```bash\n"
                            f"(spl123) $ spl3 run {script} --llm {adapter} \\\n"
                            f'   --param problem="{problem}"{extra_md}\n'
                            f"```\n\n\n```output\n"
                        )
                        log.flush()

                        _rc, metrics = stream_run(cmd, log)
                        log.write("```\n\n")
                        # Normalize preview: replace ALL whitespace (incl. Unicode)
                        # with underscores so the space-delimited RESULT tag stays parseable.
                        ws_re = re.compile(r"\s")
                        preview_slug = ws_re.sub("_", metrics["output_preview"]) or "(empty)"
                        # Structured result tag — parsed by run_analysis.py
                        log.write(
                            f"<!-- RESULT"
                            f" pid={pid} mid={mid} label={label} tier={tier}"
                            f" solver={solver_mode} run={run_no}"
                            f" status={metrics['status']}"
                            f" llm_calls={metrics['llm_calls']}"
                            f" latency_ms={metrics['latency_ms']}"
                            f" steps={metrics['steps']}"
                            f" spl_log={metrics['spl_log']}"
                            f" output_preview={preview_slug}"
                            f" -->\n\n"
                        )
                        log.flush()

                        completed += 1
                        outcome = "✓" if metrics["status"] == "complete" else "✗"
                        click.echo(
                            f"\n  [{completed}/{total}] {cell}"
                            f" → {outcome} {metrics['status']}"
                            f"  llm_calls={metrics['llm_calls']}"
                            f"  latency={metrics['latency_ms']}ms"
                        )

    click.echo(f"\n{'='*54}")
    click.echo(f" Done — {completed}/{total} run(s) completed.")
    click.echo(f" Log: {log_path}")
    click.echo(f"{'='*54}")


if __name__ == "__main__":
    main()
