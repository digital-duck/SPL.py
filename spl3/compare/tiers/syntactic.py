"""Syntactic comparison using AST-diff logic."""

from __future__ import annotations
import re as _re

def compare_syntactic(content1: str, content2: str, ext1: str, ext2: str) -> dict:
    def _ast_inventory(text: str, ext: str) -> dict:
        if ext == ".py":
            import ast as _ast
            try:
                tree = _ast.parse(text)
                return {
                    "classes":    [n.name for n in _ast.walk(tree) if isinstance(n, _ast.ClassDef)],
                    "functions":  [n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)],
                    "async_fns":  [n.name for n in _ast.walk(tree) if isinstance(n, _ast.AsyncFunctionDef)],
                }
            except SyntaxError as exc:
                return {"error": str(exc)}
        elif ext == ".spl":
            try:
                from spl.lexer import Lexer as _Lex
                from spl3.parser import SPL3Parser as _P3
                from spl.ast_nodes import WorkflowStatement as _WS, ProcedureStatement as _PS
                _tokens = _Lex(text).tokenize()
                _tree   = _P3(_tokens).parse()
                return {
                    "workflows":  [s.name for s in _tree.statements if isinstance(s, _WS)],
                    "procedures": [s.name for s in _tree.statements if isinstance(s, _PS)],
                    "generates":  _re.findall(r'\bGENERATE\s+(\w+)\s*\(', text, _re.IGNORECASE),
                    "calls":      _re.findall(r'\bCALL\s+(\w+)\s*\(',      text, _re.IGNORECASE),
                }
            except Exception as exc:
                return {"error": str(exc)}
        else:
            return {"note": f"ast-diff not supported for {ext}"}

    inv1 = _ast_inventory(content1, ext1)
    inv2 = _ast_inventory(content2, ext2)

    ast_diff_result: dict[str, dict] = {}
    keys = (set(inv1) | set(inv2)) - {"error", "note"}
    for key in sorted(keys):
        v1 = sorted(set(inv1.get(key, [])))
        v2 = sorted(set(inv2.get(key, [])))
        ast_diff_result[key] = {
            "common":  sorted(set(v1) & set(v2)),
            "removed": sorted(set(v1) - set(v2)),
            "added":   sorted(set(v2) - set(v1)),
        }
    
    if "error" in inv1: ast_diff_result["error1"] = inv1["error"]
    if "error" in inv2: ast_diff_result["error2"] = inv2["error"]
    
    return ast_diff_result
