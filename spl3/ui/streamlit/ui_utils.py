"""Shared utilities for all SPL Studio Streamlit pages."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def parse_run_output(stdout: str) -> dict:
    """Extract metrics and LLM output from spl3 run stdout."""
    lines = stdout.splitlines()
    meta: dict[str, str] = {}
    output_lines: list[str] = []
    in_output = False

    for line in lines:
        s = line.strip()
        if s and all(c == "=" for c in s) and len(s) >= 20:
            if in_output:
                in_output = False
            continue
        if s and all(c == "-" for c in s) and len(s) >= 20:
            in_output = True
            continue
        if s.startswith("```"):
            continue
        if in_output:
            output_lines.append(line)
        elif s.startswith("Model: "):
            meta["model"] = s[7:]
        elif s.startswith("Tokens: "):
            parts = s[8:].split(" in / ")
            meta["tokens_in"] = parts[0]
            meta["tokens_out"] = parts[1].replace(" out", "") if len(parts) > 1 else ""
        elif s.startswith("Latency: "):
            meta["latency"] = s[9:]
        elif s.startswith("Cost: "):
            meta["cost"] = s[6:]
        elif s.startswith("LLM Calls: "):
            meta["llm_calls"] = s[11:]
        elif s.startswith("Status: "):
            meta["status"] = s[8:]

    return {"meta": meta, "output": "\n".join(output_lines).strip()}


def extract_compare_score(text: str) -> float | None:
    """Extract the numeric similarity score from a spl3 compare output file.

    Looks for patterns like:
      Score: 0.82
      **Score:** 0.82
      Overall score: 0.82 / 1.0
      similarity_score: 0.82
    Returns None if no score found.
    """
    patterns = [
        r"[Ss]core[:\s*_]+([0-9]\.[0-9]+)",
        r"[Ss]imilarity[_\s]+[Ss]core[:\s*]+([0-9]\.[0-9]+)",
        r"\*\*[Ss]core\*\*[:\s]+([0-9]\.[0-9]+)",
        r"([0-9]\.[0-9]+)\s*/\s*1\.0",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def run_spl3(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a spl3 CLI command and return the CompletedProcess result."""
    return subprocess.run(
        ["spl3"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


def find_step_file(out_dir: Path, pattern: str) -> Path | None:
    """Find a step output file matching a glob pattern, newest first."""
    matches = sorted(out_dir.glob(pattern), reverse=True)
    return matches[0] if matches else None
