"""AST-direct Mermaid diagram generator for SPL scripts.

Converts a parsed SPL Program to a Mermaid flowchart without any LLM call.
The output faithfully mirrors the source workflow structure: assignments,
GENERATE (LLM) calls, CALL (procedure) dispatches, WHILE loops, EVALUATE
branches, exception handlers, and RETURN/RAISE terminals.

Node shapes by type:
  rectangle    — assignment, SELECT, generic
  parallelogram — GENERATE (LLM call)
  subroutine   — CALL (procedure)
  diamond      — WHILE / EVALUATE / exception
  cylinder     — STORE / storage assign
  stadium      — Start / End / RETURN / RAISE
  flag         — LOG
"""

from __future__ import annotations
from typing import Optional

from spl.ast_nodes import (
    Program, WorkflowStatement, ProcedureStatement, CreateFunctionStatement,
    AssignmentStatement, GenerateIntoStatement, CallStatement,
    WhileStatement, EvaluateStatement, DoBlock,
    CommitStatement, RaiseStatement, LoggingStatement,
    SelectIntoStatement, StorageAssignStatement, StoreStatement,
    ExceptionHandler, WhenClause, CTEClause,
    Literal, ParamRef, Identifier, DottedName, FunctionCall, BinaryOp,
    FStringLiteral, NamedArg, StorageSubscript, ListLiteral, MapLiteral,
    Condition, SemanticCondition, ComparisonCondition, CompoundCondition,
)


# ---------------------------------------------------------------------------
# Expression / condition → short string helpers
# ---------------------------------------------------------------------------

def _expr_str(expr, max_len: int = 35) -> str:
    s = _expr_raw(expr)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _expr_raw(expr) -> str:
    if expr is None:
        return ""
    if isinstance(expr, Literal):
        v = expr.value
        if isinstance(v, str):
            short = v[:20] + ("..." if len(v) > 20 else "")
            return repr(short)
        return str(v)
    if isinstance(expr, ParamRef):
        return f"@{expr.name}"
    if isinstance(expr, Identifier):
        return expr.name
    if isinstance(expr, DottedName):
        return expr.full_name
    if isinstance(expr, FunctionCall):
        args = ", ".join(_expr_str(a, 12) for a in expr.arguments[:2])
        sfx = ", ..." if len(expr.arguments) > 2 else ""
        return f"{expr.name}({args}{sfx})"
    if isinstance(expr, BinaryOp):
        return f"{_expr_str(expr.left, 12)} {expr.op} {_expr_str(expr.right, 12)}"
    if isinstance(expr, FStringLiteral):
        t = expr.template[:18] + ("..." if len(expr.template) > 18 else "")
        return f'f"{t}"'
    if isinstance(expr, NamedArg):
        return f"{expr.name}={_expr_str(expr.value, 12)}"
    if isinstance(expr, StorageSubscript):
        return f"@{expr.storage_var}[{_expr_str(expr.key, 12)}]"
    if isinstance(expr, ListLiteral):
        return f"[{len(expr.elements)} items]"
    if isinstance(expr, MapLiteral):
        return f"{{{len(expr.pairs)} pairs}}"
    return type(expr).__name__


def _cond_str(cond, max_len: int = 40) -> str:
    s = _cond_raw(cond)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _cond_raw(cond) -> str:
    if isinstance(cond, SemanticCondition):
        return cond.semantic_value
    if isinstance(cond, ComparisonCondition):
        return f"{cond.operator} {_expr_str(cond.right, 20)}"
    if isinstance(cond, Condition):
        return f"{_expr_str(cond.left, 15)} {cond.operator} {_expr_str(cond.right, 15)}"
    if isinstance(cond, CompoundCondition):
        parts: list[str] = []
        for i, c in enumerate(cond.conditions):
            parts.append(_cond_raw(c))
            if i < len(cond.conjunctions):
                parts.append(cond.conjunctions[i])
        return " ".join(parts)
    return _expr_str(cond, 40)


def _mmd_label(text: str) -> str:
    """Escape text for use inside a Mermaid quoted label."""
    text = text.replace('"', "'")
    text = text.replace("{", "(").replace("}", ")")
    text = text.replace("[", "(").replace("]", ")")
    text = text.replace("\n", " ")
    return text


def _mmd_edge_label(text: str) -> str:
    """Escape text for use inside a Mermaid edge label (between pipes).

    All bracket/paren chars are parsed as node-shape delimiters by Mermaid
    and must be stripped from edge labels.
    """
    text = text.replace('"', "'")
    text = text.replace("\n", " ")
    # Remove all shape-delimiter characters — they break Mermaid edge parsing
    for ch in "()[]{}":
        text = text.replace(ch, "")
    return text


def _is_terminal(stmt) -> bool:
    return isinstance(stmt, (CommitStatement, RaiseStatement))


def _last_is_terminal(stmts: list) -> bool:
    """True when the last non-logging statement is a terminal."""
    for s in reversed(stmts):
        if isinstance(s, LoggingStatement):
            continue
        return _is_terminal(s)
    return False


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

_STYLE_DEFS = {
    "llm":    "fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f",
    "proc":   "fill:#fef3c7,stroke:#f59e0b,color:#78350f",
    "ctrl":   "fill:#ede9fe,stroke:#8b5cf6,color:#3b0764",
    "store":  "fill:#dcfce7,stroke:#22c55e,color:#14532d",
    "term":   "fill:#fce7f3,stroke:#ec4899,color:#831843",
    "log":    "fill:#f8fafc,stroke:#94a3b8,color:#64748b",
    "fn":     "fill:#f0fdf4,stroke:#86efac,color:#166534",
    "assign": "fill:#f8fafc,stroke:#64748b,color:#1e293b",
}

_IND = "    "


class ASTToMermaid:
    """Walk a parsed SPL Program and produce a Mermaid flowchart string."""

    def __init__(self):
        self._n: int = 0
        self._lines: list[str] = []
        self._class_assigns: list[str] = []  # deferred, emitted outside subgraphs
        self._used_classes: set[str] = set()

    # ── ID / node / edge helpers ────────────────────────────────────────────

    def _id(self, prefix: str = "N") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def _node(self, nid: str, shape: str, label: str, cls: str) -> tuple[str, str]:
        safe = _mmd_label(label)
        if shape == "rect":
            self._lines.append(f'{_IND}{nid}["{safe}"]')
        elif shape == "stadium":
            self._lines.append(f'{_IND}{nid}(["{safe}"])')
        elif shape == "diamond":
            self._lines.append(f'{_IND}{nid}{{"{safe}"}}')
        elif shape == "para":
            self._lines.append(f'{_IND}{nid}[/"{safe}"/]')
        elif shape == "subroutine":
            self._lines.append(f'{_IND}{nid}[["{safe}"]]')
        elif shape == "cylinder":
            self._lines.append(f'{_IND}{nid}[("{safe}")]')
        elif shape == "flag":
            self._lines.append(f'{_IND}{nid}>"{safe}"]')
        else:
            self._lines.append(f'{_IND}{nid}["{safe}"]')
        self._class_assigns.append(f"{_IND}class {nid} {cls}")
        self._used_classes.add(cls)
        return nid, nid

    def _edge(self, src: str, dst: str, lbl: str = ""):
        if lbl:
            self._lines.append(f"{_IND}{src} -->|{_mmd_edge_label(lbl)}| {dst}")
        else:
            self._lines.append(f"{_IND}{src} --> {dst}")

    def _back_edge(self, src: str, dst: str):
        self._lines.append(f"{_IND}{src} -.-> {dst}")

    # ── Top-level entry ─────────────────────────────────────────────────────

    def convert(self, program: Program) -> str:
        self._n = 0
        self._lines = ["flowchart TD"]
        self._class_assigns = []
        self._used_classes = set()

        for stmt in program.statements:
            if isinstance(stmt, (WorkflowStatement, ProcedureStatement)):
                self._top_def(stmt)
            elif isinstance(stmt, CreateFunctionStatement):
                nid = self._id("FN")
                self._node(nid, "rect", f"FUNCTION {stmt.name}()", "fn")

        # Class assignments and defs go outside any subgraph
        self._lines.extend(self._class_assigns)
        for cls, style in _STYLE_DEFS.items():
            if cls in self._used_classes:
                self._lines.append(f"{_IND}classDef {cls} {style}")

        return "\n".join(self._lines)

    # ── Workflow / Procedure subgraph ────────────────────────────────────────

    def _top_def(self, stmt: WorkflowStatement | ProcedureStatement):
        kind = "WORKFLOW" if isinstance(stmt, WorkflowStatement) else "PROCEDURE"
        name = stmt.name
        body = stmt.body
        exc = stmt.exception_handlers

        sg = f"SG_{name}"
        self._lines.append(f'{_IND}subgraph {sg}["{kind}: {name}"]')
        self._lines.append(f"{_IND}direction TB")

        start = self._id("START")
        self._node(start, "stadium", "Start", "term")

        entry, exit_ = self._stmts(body)
        if entry:
            self._edge(start, entry)

        end = self._id("END")
        self._node(end, "stadium", "End", "term")
        if exit_ and not _last_is_terminal(body):
            self._edge(exit_, end)

        for h in exc:
            h_id = self._id("EXC")
            self._node(h_id, "diamond", f"EXCEPTION {h.exception_type}", "ctrl")
            if h.statements:
                h_entry, h_exit = self._stmts(h.statements)
                if h_entry:
                    self._edge(h_id, h_entry)
                if h_exit and not _last_is_terminal(h.statements):
                    self._edge(h_exit, end)

        self._lines.append(f"{_IND}end")

    # ── Statement sequence ──────────────────────────────────────────────────

    def _stmts(self, stmts: list) -> tuple[Optional[str], Optional[str]]:
        first: Optional[str] = None
        prev: Optional[str] = None
        for stmt in stmts:
            entry, exit_ = self._stmt(stmt)
            if entry is None:
                continue
            if first is None:
                first = entry
            if prev is not None:
                self._edge(prev, entry)
            prev = exit_
            if _is_terminal(stmt):
                break
        return first, prev

    # ── Individual statements ───────────────────────────────────────────────

    def _stmt(self, stmt) -> tuple[Optional[str], Optional[str]]:
        if isinstance(stmt, AssignmentStatement):
            nid = self._id("A")
            return self._node(nid, "rect", f"@{stmt.variable} := {_expr_str(stmt.expression)}", "assign")

        if isinstance(stmt, GenerateIntoStatement):
            gc = stmt.generate_clause
            args = ", ".join(_expr_str(a, 12) for a in gc.arguments[:2])
            sfx = ", ..." if len(gc.arguments) > 2 else ""
            target = f" -> @{stmt.target_variable}" if stmt.target_variable else ""
            nid = self._id("GEN")
            return self._node(nid, "para", f"GENERATE {gc.function_name}({args}{sfx}){target}", "llm")

        if isinstance(stmt, CallStatement):
            args = ", ".join(_expr_str(a, 12) for a in stmt.arguments[:2])
            sfx = ", ..." if len(stmt.arguments) > 2 else ""
            target = f" -> @{stmt.target_variable}" if stmt.target_variable and stmt.target_variable != "NONE" else ""
            nid = self._id("SUB")
            return self._node(nid, "subroutine", f"CALL {stmt.procedure_name}({args}{sfx}){target}", "proc")

        if isinstance(stmt, WhileStatement):
            return self._while(stmt)

        if isinstance(stmt, EvaluateStatement):
            return self._evaluate(stmt)

        if isinstance(stmt, DoBlock):
            return self._do(stmt)

        if isinstance(stmt, CommitStatement):
            opts = ""
            if stmt.options:
                parts = [f"{k}={_expr_str(v, 8)}" for k, v in list(stmt.options.items())[:2]]
                opts = " [" + ", ".join(parts) + "]"
            nid = self._id("RET")
            return self._node(nid, "stadium", f"RETURN {_expr_str(stmt.expression)}{opts}", "term")

        if isinstance(stmt, RaiseStatement):
            msg = f": {stmt.message[:20]}" if stmt.message else ""
            nid = self._id("RAISE")
            return self._node(nid, "stadium", f"RAISE {stmt.exception_type}{msg}", "term")

        if isinstance(stmt, LoggingStatement):
            nid = self._id("LOG")
            return self._node(nid, "flag", f"LOG[{stmt.level}] {_expr_str(stmt.expression)}", "log")

        if isinstance(stmt, SelectIntoStatement):
            targets = ", ".join(
                f"@{v}" for v in (
                    stmt.target_variables or ([stmt.target_variable] if stmt.target_variable else [])
                )
            )
            sync_label = f"SELECT -> {targets}" if targets else "SELECT"
            if stmt.ctes:
                return self._fan_out(stmt.ctes, sync_label)
            nid = self._id("SEL")
            return self._node(nid, "rect", sync_label, "assign")

        if isinstance(stmt, StorageAssignStatement):
            key = _expr_str(stmt.key)
            val = _expr_str(stmt.value)
            nid = self._id("STA")
            return self._node(nid, "cylinder", f"@{stmt.storage_var}[{key}] := {val}", "store")

        if isinstance(stmt, StoreStatement):
            nid = self._id("ST")
            return self._node(nid, "cylinder", f"STORE @{stmt.variable} -> memory.{stmt.key}", "store")

        nid = self._id("S")
        return self._node(nid, "rect", type(stmt).__name__, "assign")

    # ── Control-flow nodes ──────────────────────────────────────────────────

    def _while(self, stmt: WhileStatement) -> tuple[str, str]:
        cond_id = self._id("WHILE")
        self._node(cond_id, "diamond", f"WHILE: {_cond_str(stmt.condition)}", "ctrl")

        b_entry, b_exit = self._stmts(stmt.body)
        if b_entry:
            self._edge(cond_id, b_entry, "True")
        if b_exit:
            self._back_edge(b_exit, cond_id)

        # Exit from WHILE (False branch) is the condition node itself;
        # the parent _stmts will connect it to the next statement.
        return cond_id, cond_id

    def _evaluate(self, stmt: EvaluateStatement) -> tuple[str, str]:
        eval_id = self._id("EVAL")
        self._node(eval_id, "diamond", f"EVALUATE: {_expr_str(stmt.expression)}", "ctrl")

        merge_id = self._id("MERGE")
        needs_merge = False

        for wc in stmt.when_clauses:
            lbl = f"WHEN {_cond_str(wc.condition)}"
            w_entry, w_exit = self._stmts(wc.statements)
            if w_entry:
                self._edge(eval_id, w_entry, lbl)
                if w_exit and not _last_is_terminal(wc.statements):
                    self._lines.append(f"{_IND}{w_exit} --> {merge_id}")
                    needs_merge = True
            else:
                self._edge(eval_id, merge_id, lbl)
                needs_merge = True

        if stmt.else_statements:
            e_entry, e_exit = self._stmts(stmt.else_statements)
            if e_entry:
                self._edge(eval_id, e_entry, "ELSE")
                if e_exit and not _last_is_terminal(stmt.else_statements):
                    self._lines.append(f"{_IND}{e_exit} --> {merge_id}")
                    needs_merge = True
            else:
                self._edge(eval_id, merge_id, "ELSE")
                needs_merge = True
        else:
            self._edge(eval_id, merge_id, "ELSE")
            needs_merge = True

        if needs_merge:
            self._lines.append(f'{_IND}{merge_id}[" "]')
            return eval_id, merge_id

        return eval_id, eval_id

    def _do(self, stmt: DoBlock) -> tuple[Optional[str], Optional[str]]:
        entry, exit_ = self._stmts(stmt.body)
        for h in stmt.exception_handlers:
            h_id = self._id("EXC")
            self._node(h_id, "diamond", f"EXCEPTION {h.exception_type}", "ctrl")
            if h.statements:
                h_entry, _ = self._stmts(h.statements)
                if h_entry:
                    self._edge(h_id, h_entry)
        return entry, exit_

    def _fan_out(self, ctes: list, sync_label: str) -> tuple[str, str]:
        """Render a WITH-block CTE fan-out followed by a SELECT sync node."""
        fork_id = self._id("FORK")
        self._lines.append(f'{_IND}{fork_id}[" "]')
        self._class_assigns.append(f"{_IND}class {fork_id} assign")
        self._used_classes.add("assign")

        sync_id = self._id("SYNC")
        self._lines.append(f'{_IND}{sync_id}["{_mmd_label(sync_label)}"]')
        self._class_assigns.append(f"{_IND}class {sync_id} assign")

        for cte in ctes:
            cte_id = self._id("CTE")
            gc = cte.nested_prompt.generate_clause if cte.nested_prompt else None
            if gc:
                args = ", ".join(_expr_str(a, 12) for a in gc.arguments[:2])
                sfx = ", ..." if len(gc.arguments) > 2 else ""
                model = f" [{gc.model}]" if gc.model else ""
                label = f"GENERATE {gc.function_name}({args}{sfx}){model}"
                self._lines.append(f'{_IND}{cte_id}[/"{_mmd_label(label)}"/]')
                self._class_assigns.append(f"{_IND}class {cte_id} llm")
                self._used_classes.add("llm")
            else:
                label = cte.name
                self._lines.append(f'{_IND}{cte_id}["{_mmd_label(label)}"]')
                self._class_assigns.append(f"{_IND}class {cte_id} assign")
            self._edge(fork_id, cte_id)
            self._lines.append(f"{_IND}{cte_id} --> {sync_id}")

        return fork_id, sync_id


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class NoWorkflowError(ValueError):
    """Raised when no WORKFLOW or PROCEDURE is found (PROMPT-only SPL 1.0 script)."""


def spl_to_mermaid(source: str) -> str:
    """Parse SPL source and return a Mermaid flowchart string (no LLM).

    Raises NoWorkflowError if the script contains only SPL 1.0 PROMPT/SELECT/GENERATE
    statements with no WORKFLOW or PROCEDURE definitions.
    """
    from spl.lexer import Lexer
    from spl3.parser import SPL3Parser

    tokens = Lexer(source).tokenize()
    ast = SPL3Parser(tokens).parse()

    if not any(isinstance(s, (WorkflowStatement, ProcedureStatement)) for s in ast.statements):
        raise NoWorkflowError(
            "no WORKFLOW or PROCEDURE found — script uses PROMPT/SELECT/GENERATE (SPL 1.0). "
            "spl2mmd renders agentic workflow logic only."
        )

    return ASTToMermaid().convert(ast)
