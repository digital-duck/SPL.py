"""Tools for Recipe 65: LLM-powered SPL Compiler (vibe-splc)"""

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
    import re
    code_exts = {".py", ".go", ".ts", ".js"}
    if os.path.splitext(path)[1] in code_exts:
        content = re.sub(r"^```[a-zA-Z0-9_]*\n?", "", content.strip())
        content = re.sub(r"\n?```$", "", content).strip()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content + "\n")
    return f"written: {path}"
