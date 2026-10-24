#!/usr/bin/env python3
"""Measure the three engines of recipe 127 on this machine: import time, install size, check latency, agreement.

    python cookbook-solver/127_pii_compliance/bench_engines.py [--repeat N] [--json]

Prints a Markdown table with the package versions and the Python version, so the numbers in readme.md can be
reproduced and dated. Nothing here is quoted from anywhere else.
"""
import argparse
import importlib.metadata as md
import importlib.util
import itertools
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPORTS = {
    "stdlib": "pass",
    "sympy": "from sympy import And, Not, Symbol; from sympy.logic.inference import satisfiable",
    "z3": "import z3; z3.Solver()",
}
PACKAGES = {"stdlib": [], "sympy": ["sympy", "mpmath"], "z3": ["z3-solver"]}


def load_tools():
    spec = importlib.util.spec_from_file_location("recipe127_tools", HERE / "tools.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_seconds(statement: str, repeat: int) -> float:
    """Median wall time of a fresh interpreter doing `statement`, minus the bare interpreter start-up."""
    def run(code: str) -> float:
        t0 = time.perf_counter()
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)
        return time.perf_counter() - t0
    base = statistics.median(run("pass") for _ in range(repeat))
    return max(statistics.median(run(statement) for _ in range(repeat)) - base, 0.0)


def installed_mb(packages: list) -> float:
    total = 0
    for name in packages:
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            return float("nan")
        for f in dist.files or []:
            path = dist.locate_file(f)
            if path.is_file():
                total += path.stat().st_size
    return total / 1e6


def version(packages: list) -> str:
    out = []
    for name in packages:
        try:
            out.append(f"{name} {md.version(name)}")
        except md.PackageNotFoundError:
            out.append(f"{name} (not installed)")
    return ", ".join(out) or "standard library"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeat", type=int, default=7, help="fresh-interpreter runs per import timing")
    ap.add_argument("--checks", type=int, default=200, help="timed passes over all fact assignments per engine")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = ap.parse_args()

    tools = load_tools()
    rules = tools.DEFAULT_RULES
    names = rules["variables"]
    assignments = [dict(zip(names, v)) for v in itertools.product([False, True], repeat=len(names))]

    rows, verdicts = {}, {}
    for engine in tools.ENGINES:
        ok, why = tools.engine_available(engine)
        if not ok:
            rows[engine] = {"available": False, "why": why}
            continue
        verdicts[engine] = [tuple(tools.check(f, rules, engine)["violated"]) for f in assignments]
        tools.check(assignments[0], rules, engine)                        # warm up
        per_check = []
        for _ in range(args.checks):
            t0 = time.perf_counter()
            for f in assignments:
                tools.check(f, rules, engine)
            per_check.append((time.perf_counter() - t0) / len(assignments))
        t0 = time.perf_counter()
        tools.consistent(rules, engine)
        search_ms = (time.perf_counter() - t0) * 1000
        rows[engine] = {"available": True, "import_ms": import_seconds(IMPORTS[engine], args.repeat) * 1000,
                        "installed_mb": installed_mb(PACKAGES[engine]), "check_ms_median": statistics.median(per_check) * 1000,
                        "consistency_search_ms": search_ms, "versions": version(PACKAGES[engine])}
    agree = len({tuple(v) for v in verdicts.values()}) <= 1
    result = {"python": platform.python_version(), "platform": platform.platform(), "assignments": len(assignments),
              "engines_agree_on_every_assignment": agree, "engines": rows}
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Python {result['python']} on {result['platform']}")
    print(f"{len(assignments)} fact assignments, {len(rules['rules'])} rules; engines agree on every assignment: {agree}\n")
    print("| Engine | Packages | Import (ms) | Installed (MB) | One check (ms, median) | Consistency search (ms) |")
    print("|---|---|---|---|---|---|")
    for engine, r in rows.items():
        if not r["available"]:
            print(f"| {engine} | {r['why']} | | | | |")
        else:
            print(f"| {engine} | {r['versions']} | {r['import_ms']:.0f} | {r['installed_mb']:.0f} | {r['check_ms_median']:.3f} | {r['consistency_search_ms']:.2f} |")


if __name__ == "__main__":
    main()
