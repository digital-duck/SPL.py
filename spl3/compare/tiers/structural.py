"""Structural comparison using skeleton extractors."""

from __future__ import annotations
import re as _re

def compare_structural(content1: str, content2: str, ext1: str, ext2: str) -> dict:
    def _extract_structure(text: str, ext: str) -> dict:
        if ext == ".md":
            headings = _re.findall(r'^(#{1,6})\s+(.+)$', text, _re.MULTILINE)
            return {"type": "markdown", "headings": [(len(h), t.strip()) for h, t in headings]}
        elif ext == ".py":
            import ast as _ast
            try:
                tree = _ast.parse(text)
                return {
                    "type":      "python",
                    "classes":   [n.name for n in _ast.walk(tree) if isinstance(n, _ast.ClassDef)],
                    "functions": [n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)],
                }
            except SyntaxError as exc:
                return {"type": "python", "error": str(exc)}
        elif ext in (".js", ".ts"):
            fns = _re.findall(
                r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', text
            )
            return {
                "type":      ext[1:],
                "classes":   _re.findall(r'class\s+(\w+)', text),
                "functions": [f[0] or f[1] for f in fns],
            }
        elif ext == ".spl":
            return {
                "type":       "spl",
                "workflows":  _re.findall(r'^\s*WORKFLOW\s+(\w+)',  text, _re.MULTILINE | _re.IGNORECASE),
                "procedures": _re.findall(r'^\s*PROCEDURE\s+(\w+)', text, _re.MULTILINE | _re.IGNORECASE),
            }
        elif ext == ".mmd":
            node_classes = _re.findall(r'^\s+class\s+\w+\s+(\w+)\s*$', text, _re.MULTILINE)
            type_counts: dict[str, int] = {}
            for t in node_classes:
                if t in ("llm", "ctrl", "term", "assign", "proc", "log"):
                    type_counts[t] = type_counts.get(t, 0) + 1
            return {
                "type":       "mermaid",
                "workflows":  _re.findall(r'subgraph\s+SG_\w+\["(?:WORKFLOW|PROCEDURE):\s+(\w+)"\]', text),
                "node_types": type_counts,
            }
        else:
            lines = text.splitlines()
            return {"type": "text", "lines": len(lines), "chars": len(text)}

    s1 = _extract_structure(content1, ext1)
    s2 = _extract_structure(content2, ext2)
    return {"file1": s1, "file2": s2}
