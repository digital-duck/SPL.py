"""SPL 3.0 semantic linter — static analysis passes on the AST.

Checks beyond parse-level correctness:
  1. Undefined variable reference  — @x used before any assignment/input
  2. Unreachable code after RETURN  — statements following CommitStatement
  3. Potential infinite WHILE loop  — no exit-capable statement inside body
  4. Undefined CALL target         — procedure not in CREATE FUNCTION / TOOL_API / workflows / stdlib

Usage::

    from spl3.linter import lint_program
    issues = lint_program(ast)
    for issue in issues:
        print(issue)  # "ERROR [workflow] message" or "WARN [workflow] message"
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

# ── SPL 2.0 nodes ─────────────────────────────────────────────────────────────
from spl.ast_nodes import (
    WorkflowStatement,
    CreateFunctionStatement,
    GenerateIntoStatement,
    CallStatement,
    SelectIntoStatement,
    AssignmentStatement,
    CommitStatement,
    WhileStatement,
    EvaluateStatement,
    ParamRef,
    Parameter,
)

# ── SPL 3.0 nodes ─────────────────────────────────────────────────────────────
from spl3.ast_nodes import (
    ImportStatement,
    CallParallelStatement,
    ToolAPINode,
)

# stdlib tools that are always valid CALL targets
_STDLIB_TOOLS = {
    "web_search", "web_fetch", "read_file", "write_file", "shell",
    "python", "sql", "memory_get", "memory_set", "sleep", "log",
    "http_get", "http_post", "duckduckgo_search", "arxiv_search",
}


@dataclass
class LintIssue:
    level: str        # "ERROR" | "WARN"
    workflow: str     # workflow name or "<top-level>"
    message: str

    def __str__(self) -> str:
        return f"{self.level} [{self.workflow}] {self.message}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_paramsrefs(node: Any) -> list[str]:
    """Recursively collect all ParamRef names in an expression tree."""
    refs: list[str] = []
    if isinstance(node, ParamRef):
        refs.append(node.name)
    elif hasattr(node, "__dict__"):
        for v in vars(node).values():
            if isinstance(v, list):
                for item in v:
                    refs.extend(_collect_paramsrefs(item))
            else:
                refs.extend(_collect_paramsrefs(v))
    return refs


def _stmt_defines(stmt: Any) -> list[str]:
    """Return variable names that this statement defines (writes to)."""
    if isinstance(stmt, GenerateIntoStatement):
        return [stmt.target_variable] if stmt.target_variable else []
    if isinstance(stmt, CallStatement):
        return [stmt.target_variable] if stmt.target_variable else []
    if isinstance(stmt, SelectIntoStatement):
        targets = list(stmt.target_variables or [])
        if stmt.target_variable and stmt.target_variable not in targets:
            targets.append(stmt.target_variable)
        return targets
    if isinstance(stmt, AssignmentStatement):
        return [stmt.variable]
    if isinstance(stmt, CallParallelStatement):
        return [b.target_var for b in stmt.branches if b.target_var]
    return []


def _stmt_uses(stmt: Any) -> list[str]:
    """Return ParamRef names read by this statement (not counting defines)."""
    refs: list[str] = []
    if isinstance(stmt, GenerateIntoStatement):
        refs.extend(_collect_paramsrefs(stmt.generate_clause))
    elif isinstance(stmt, CallStatement):
        for a in stmt.arguments:
            refs.extend(_collect_paramsrefs(a))
    elif isinstance(stmt, SelectIntoStatement):
        refs.extend(_collect_paramsrefs(stmt.from_clause))
        refs.extend(_collect_paramsrefs(stmt.where_clause))
    elif isinstance(stmt, AssignmentStatement):
        refs.extend(_collect_paramsrefs(stmt.expression))
    elif isinstance(stmt, CommitStatement):
        refs.extend(_collect_paramsrefs(stmt.expression))
    elif isinstance(stmt, EvaluateStatement):
        refs.extend(_collect_paramsrefs(stmt.expression))
    elif isinstance(stmt, WhileStatement):
        refs.extend(_collect_paramsrefs(stmt.condition))
    elif isinstance(stmt, CallParallelStatement):
        for b in stmt.branches:
            for a in b.arguments:
                refs.extend(_collect_paramsrefs(a))
    return refs


def _has_exit(body: list) -> bool:
    """Return True if body contains any CommitStatement at the top level."""
    for stmt in body:
        if isinstance(stmt, CommitStatement):
            return True
        if isinstance(stmt, EvaluateStatement):
            for wc in stmt.when_clauses:
                if any(isinstance(s, CommitStatement) for s in wc.statements):
                    return True
            if any(isinstance(s, CommitStatement) for s in stmt.else_statements):
                return True
    return False


def _body_statements(stmt: Any) -> list:
    """Flatten nested bodies for reachability: return all child statement lists."""
    children = []
    if isinstance(stmt, WhileStatement):
        children.extend(stmt.body)
    if isinstance(stmt, EvaluateStatement):
        for wc in stmt.when_clauses:
            children.extend(wc.statements)
        children.extend(stmt.else_statements)
    return children


# ── Per-workflow checks ───────────────────────────────────────────────────────

def _lint_workflow(wf: WorkflowStatement, known_fns: set[str]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    name = wf.name

    # Seed defined variables from workflow INPUTs
    defined: set[str] = {p.name.lstrip("@") for p in wf.inputs}

    def _check_body(stmts: list, context_defined: set[str]) -> bool:
        """Walk statements linearly. Returns True if a CommitStatement was seen."""
        saw_return = False
        for stmt in stmts:
            if saw_return:
                issues.append(LintIssue(
                    "WARN", name,
                    f"unreachable statement after RETURN: {type(stmt).__name__}"
                ))
                continue

            # Check 1: undefined variable reads
            for ref in _stmt_uses(stmt):
                clean = ref.lstrip("@")
                if clean and clean not in context_defined:
                    issues.append(LintIssue(
                        "WARN", name,
                        f"@{clean} used before assignment (may be undefined)"
                    ))

            # Check 4: undefined CALL target
            if isinstance(stmt, CallStatement):
                proc = stmt.procedure_name
                if proc not in known_fns and proc not in _STDLIB_TOOLS:
                    issues.append(LintIssue(
                        "WARN", name,
                        f"CALL target '{proc}' not found in CREATE FUNCTION declarations "
                        f"or stdlib tools"
                    ))

            # Check 3: WHILE with no exit
            if isinstance(stmt, WhileStatement):
                if not _has_exit(stmt.body) and stmt.max_iterations is None:
                    issues.append(LintIssue(
                        "WARN", name,
                        "WHILE loop has no RETURN inside body and no max_iterations — "
                        "potential infinite loop"
                    ))
                # Recurse into WHILE body with a copy of current defined set
                inner_defined = set(context_defined)
                _check_body(stmt.body, inner_defined)
                # Variables defined inside WHILE body are available after it
                for s in stmt.body:
                    for v in _stmt_defines(s):
                        context_defined.add(v.lstrip("@"))

            elif isinstance(stmt, EvaluateStatement):
                for wc in stmt.when_clauses:
                    _check_body(wc.statements, set(context_defined))
                _check_body(stmt.else_statements, set(context_defined))

            else:
                # Record definitions
                for v in _stmt_defines(stmt):
                    context_defined.add(v.lstrip("@"))

            if isinstance(stmt, CommitStatement):
                saw_return = True

        return saw_return

    _check_body(wf.body, defined)
    return issues


# ── Top-level entry point ─────────────────────────────────────────────────────

def lint_program(program: Any) -> list[LintIssue]:
    """Run all semantic checks on a parsed SPL program.

    ``program`` is the object returned by ``SPL3Parser(...).parse()``.
    Returns a list of LintIssue objects (empty = no issues found).
    """
    issues: list[LintIssue] = []

    statements = getattr(program, "statements", [])

    # Collect all declared function names (CREATE FUNCTION)
    known_fns: set[str] = set()
    for stmt in statements:
        if isinstance(stmt, CreateFunctionStatement):
            known_fns.add(stmt.name)

    # Collect all CREATE TOOL_API names — deterministic Python tools,
    # valid CALL targets registered at executor load time
    known_tool_apis: set[str] = set()
    for stmt in statements:
        if isinstance(stmt, ToolAPINode):
            known_tool_apis.add(stmt.name)

    # Collect all declared workflow names (for CALL workflow cross-refs)
    known_workflows: set[str] = set()
    for stmt in statements:
        if isinstance(stmt, WorkflowStatement):
            known_workflows.add(stmt.name)

    # Also load stdlib tool names at lint time so we don't hard-code a partial list
    try:
        from spl.tools import get_global_tools
        runtime_stdlib: set[str] = set(get_global_tools().keys())
    except Exception:
        runtime_stdlib = set()

    # CALL targets can be: TOOL_API, CREATE FUNCTION, other workflows, or stdlib
    all_known = known_fns | known_tool_apis | known_workflows | _STDLIB_TOOLS | runtime_stdlib

    # Per-workflow passes
    for stmt in statements:
        if isinstance(stmt, WorkflowStatement):
            issues.extend(_lint_workflow(stmt, all_known))

    return issues
