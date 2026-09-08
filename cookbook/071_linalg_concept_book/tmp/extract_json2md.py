#!/usr/bin/env python3
"""Extract a JSON-encoded string of raw streamed terminal output into clean markdown.

The captured `*_output-*.json` files here hold a single JSON string containing
raw streamed LLM output, complete with ANSI escape codes (cursor-back, clear-
line, etc.) emitted as the terminal progressively redrew lines while streaming.
A naive `json.load` + write would leave those control codes embedded as garbage
in the markdown. This replays them through a small terminal emulator to
reconstruct the final visible text, then writes that to a sibling `.md` file.

Usage:
    python3 extract_json2md.py FILE.json [FILE2.json ...]

Each FILE.json produces FILE.md alongside it.
"""

from __future__ import annotations

import json
import os
import re
import sys

ANSI_RE = re.compile(r"\x1b\[(\d*)([A-Za-z])")


def render_terminal(text: str) -> str:
    """Replay cursor-movement / line-clear escape codes to get the final visible text."""
    lines: list[str] = []
    buf: list[str] = []
    cursor = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\x1b":
            m = ANSI_RE.match(text, i)
            if m:
                num_s, code = m.group(1), m.group(2)
                num = int(num_s) if num_s else 1
                if code == "D":  # cursor back
                    cursor = max(0, cursor - num)
                elif code == "C":  # cursor forward
                    cursor = cursor + num
                elif code == "K":  # clear from cursor to end of line
                    buf = buf[:cursor]
                # other escape codes (color, etc.) are dropped
                i = m.end()
                continue
            i += 1
            continue
        elif ch == "\n":
            lines.append("".join(buf))
            buf = []
            cursor = 0
            i += 1
        elif ch == "\r":
            cursor = 0
            i += 1
        else:
            if cursor < len(buf):
                buf[cursor] = ch
            else:
                buf.append(ch)
            cursor += 1
            i += 1
    lines.append("".join(buf))
    return "\n".join(lines)


def convert(src_path: str) -> str:
    with open(src_path) as fh:
        data = json.load(fh)
    if not isinstance(data, str):
        raise TypeError(f"{src_path}: expected a JSON string, got {type(data).__name__}")
    rendered = render_terminal(data)
    dst_path = os.path.splitext(src_path)[0] + ".md"
    with open(dst_path, "w") as fh:
        fh.write(rendered)
    return dst_path


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    for src_path in argv:
        dst_path = convert(src_path)
        print(f"{src_path} -> {dst_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
