"""Character-level comparison using git-diff (difflib)."""

from __future__ import annotations
import difflib
import sys
from pathlib import Path

def compare_character(
    content1: str, 
    content2: str, 
    path1: Path, 
    path2: Path, 
    diff_style: str = "unified",
    no_color: bool = False,
    output_format: str = "markdown",
    is_terminal: bool = False
) -> str:
    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)
    mechanical_diff = ""

    if diff_style == "unified":
        diff_lines = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=f"a/{path1.name}",
            tofile=f"b/{path2.name}",
            lineterm=""
        ))

        if not no_color and is_terminal:
            # Add ANSI color codes for terminal output
            colored_diff = []
            for line in diff_lines:
                if line.startswith('+++') or line.startswith('---'):
                    colored_diff.append(f"\033[1m{line}\033[0m")
                elif line.startswith('@@'):
                    colored_diff.append(f"\033[36m{line}\033[0m")
                elif line.startswith('+'):
                    colored_diff.append(f"\033[32m{line}\033[0m")
                elif line.startswith('-'):
                    colored_diff.append(f"\033[31m{line}\033[0m")
                else:
                    colored_diff.append(line)
            mechanical_diff = "\n".join(colored_diff)
        else:
            mechanical_diff = "\n".join(diff_lines)

    elif diff_style == "context":
        diff_lines = list(difflib.context_diff(
            lines1, lines2,
            fromfile=f"a/{path1.name}",
            tofile=f"b/{path2.name}",
            lineterm=""
        ))
        mechanical_diff = "\n".join(diff_lines)

    elif diff_style == "side-by-side":
        if output_format == "markdown":
            side_by_side_lines = []
            side_by_side_lines.append(f"| {path1.name} | {path2.name} |")
            side_by_side_lines.append("|---|---|")

            for l1, l2 in zip(lines1, lines2):
                l1_clean = l1.rstrip('\n\r').replace('|', '\\|')
                l2_clean = l2.rstrip('\n\r').replace('|', '\\|')
                if l1 != l2:
                    side_by_side_lines.append(f"| **{l1_clean}** | **{l2_clean}** |")
                else:
                    side_by_side_lines.append(f"| {l1_clean} | {l2_clean} |")

            max_len = max(len(lines1), len(lines2))
            for i in range(min(len(lines1), len(lines2)), max_len):
                if i < len(lines1):
                    l1_clean = lines1[i].rstrip('\n\r').replace('|', '\\|')
                    side_by_side_lines.append(f"| **{l1_clean}** | *[missing]* |")
                else:
                    l2_clean = lines2[i].rstrip('\n\r').replace('|', '\\|')
                    side_by_side_lines.append(f"| *[missing]* | **{l2_clean}** |")

            mechanical_diff = "\n".join(side_by_side_lines)
        else:
            # Fallback to unified
            diff_lines = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=f"a/{path1.name}",
                tofile=f"b/{path2.name}",
                lineterm=""
            ))
            mechanical_diff = "\n".join(diff_lines)

    if not mechanical_diff.strip():
        return "No mechanical differences found - files are identical."
    
    return mechanical_diff
