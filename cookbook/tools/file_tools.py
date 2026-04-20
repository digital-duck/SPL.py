"""cookbook/tools/file_tools.py — File I/O tools for SPL recipes."""

import os
from spl.tools import spl_tool


@spl_tool
def load_file(path: str) -> str:
    """Load a file and return its contents."""
    path = path.strip()
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@spl_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return f"written: {path}"
