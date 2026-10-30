"""spl2graph: lift an SPL workflow into a GraphLang graph IR (``*.graph.yaml``).

AST-direct (no LLM), sibling of spl3/spl2mmd.py.  Mapping:

    WORKFLOW inputs / outputs        -> INPUT node ``wf_entry`` / OUTPUT node ``wf_exit``
    GENERATE f(..) INTO @v           -> GENERATE   (config.function / arguments / model)
    CALL w(..) INTO @v               -> GENERATE   (config.procedure_ref = procedures.w)
    SOLVE @v := expr                 -> SOLVE      (config.expression)
    ASSERT expr [OTHERWISE ..]       -> ASSERT     (pass / fail), fail wired to the OTHERWISE body
    EVALUATE @x WHEN .. ELSE ..      -> chain of EVALUATE nodes (pass / fail)
    WHILE cond DO .. END             -> LOOP       (subgraph; unbound body inputs read the LOOP's inputs)
    CALL PARALLEL .. END             -> FORK, one GENERATE per branch, JOIN
    @v := expr                       -> CONTEXT    (action "set")
    RETRY / RAISE                    -> RECOVER    (action "retry" / "halt")
    COMMIT @v                        -> binds @v to wf_exit, triggers wf_exit
    LOGGING                          -> dropped (not part of the dataflow)

Control flow is explicit ``triggers`` edges, data flow is ``binds`` edges from the node that last
produced @var.  Anything the converter cannot map is skipped and reported in ``warnings``.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from dataclasses import dataclass, field

from spl.ast_nodes import (
    AssignmentStatement, CallStatement, CreateFunctionStatement, CompoundCondition as CompoundConditionV2, Condition, CommitStatement, DoBlock, EvaluateStatement, FStringLiteral,
    GenerateIntoStatement, ListLiteral, Literal, LoggingStatement, MapLiteral, ParamRef, ProcedureStatement, RaiseStatement,
    RetryStatement, SemanticCondition, StorageSubscript, WhileStatement, WorkflowStatement,
)
from spl3.ast_nodes import (
    AssertStatement, CallParallelStatement, ImportStatement, ToolAPINode, CompoundCondition, NoneLiteral, SetLiteral, SolveStatement, UnaryOp,
)

# The functions a GraphLang condition may call (graphlang/grafr/expr.py FUNCS). Any other call in an ASSERT condition is a
# Python tool and is lifted into its own SOLVE node. Kept as a copy so SPL.py does not import graflang.
_CONDITION_FUNCS = {"abs", "bool", "contains", "endswith", "float", "int", "is_empty", "json_get", "len", "lower", "max",
                    "min", "startswith", "str", "strip", "upper"}

GRAPH_VERSION = "1.0-graph"
_OUT_TYPES = {"TEXT": "TEXT", "STRING": "TEXT", "INTEGER": "INTEGER", "INT": "INTEGER", "NUMBER": "REAL", "FLOAT": "REAL",
              "REAL": "REAL", "BOOL": "BOOL", "BOOLEAN": "BOOL"}
_CALL = re.compile(r"\b([A-Za-z_]\w*)\(")
_SOLVE_MARK = re.compile(r"@@(\w+)@@")
_FSTR_VAR = re.compile(r"\{@(\w+)\}")


class NoWorkflowError(ValueError):
    """Raised when the script has no WORKFLOW to lift."""


# --------------------------------------------------------------------------- expressions

def expr_vars(obj) -> list[str]:
    """@variables referenced by an expression / condition, in first-use order."""
    found: list[str] = []

    def add(name):
        if name not in found:
            found.append(name)

    def walk(o):
        if isinstance(o, ParamRef):
            add(o.name.lstrip("@"))
        elif isinstance(o, FStringLiteral):
            for v in _FSTR_VAR.findall(o.template):
                add(v)
        elif isinstance(o, StorageSubscript):
            add(o.storage_var.lstrip("@"))
            walk(o.key)
        elif isinstance(o, str):
            for v in _SOLVE_MARK.findall(o):
                add(v)
        elif isinstance(o, (list, tuple)):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for x in o.values():
                walk(x)
        elif dataclasses.is_dataclass(o):
            for f in dataclasses.fields(o):
                walk(getattr(o, f.name))

    walk(obj)
    return found


_OPS = {"=": "==", "<>": "!="}


def _quote(text: str) -> str:
    """Quote with ' unless the text has a ' and no \"; then \" (else triple quotes)."""
    text = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    if "'" not in text:
        return "'" + text + "'"
    if '"' not in text:
        return '"' + text + '"'
    if "'''" not in text:
        return "'''" + text + "'''"
    return '"""' + text + '"""' 


def template(text: str) -> str:
    """SOLVE / ASSERT ``@@var@@`` markers -> GraphLang ``@in_var`` port references."""
    return _SOLVE_MARK.sub(lambda m: f"@in_{m.group(1)}", text)


def render(e, inport: bool = False) -> str:
    """Expression / condition -> GraphLang expression text.  ``inport`` writes ``@var`` as the node's
    own ``@in_var`` port (what EVALUATE / ASSERT / LOOP conditions read)."""
    if e is None:
        return ""
    if isinstance(e, ParamRef):
        return ("@in_" if inport else "@") + e.name.lstrip("@")
    if isinstance(e, Literal):
        if e.literal_type == "string":
            return _quote(str(e.value))
        if e.literal_type == "bool":
            return "TRUE" if e.value else "FALSE"
        return str(e.value)
    if isinstance(e, FStringLiteral):
        return "f" + _quote(e.template)
    if isinstance(e, NoneLiteral):
        return "NONE"
    if isinstance(e, StorageSubscript):
        return f"{'@in_' if inport else '@'}{e.storage_var.lstrip('@')}[{render(e.key, inport)}]"
    if isinstance(e, ListLiteral):
        return "[" + ", ".join(render(x, inport) for x in e.elements) + "]"
    if isinstance(e, SetLiteral):
        return "{" + ", ".join(render(x, inport) for x in e.elements) + "}"
    if isinstance(e, MapLiteral):
        return "{" + ", ".join(f"{render(k, inport)}: {render(v, inport)}" for k, v in e.pairs) + "}"
    if isinstance(e, CompoundConditionV2):
        parts = [render(e.conditions[0], inport)]
        for conj, c in zip(e.conjunctions, e.conditions[1:]):
            parts += [conj, render(c, inport)]
        return " ".join(parts)
    if isinstance(e, UnaryOp):
        return f"{e.operator} {render(e.operand, inport)}"
    if isinstance(e, CompoundCondition):
        return f"{render(e.left, inport)} {_OPS.get(e.operator, e.operator)} {render(e.right, inport)}"
    if isinstance(e, SemanticCondition):
        return e.semantic_value
    if getattr(e, "operator", None) == "IN" and getattr(e.right, "name", "") == "__in_list__":
        left = render(e.left, inport)  # no IN in GraphLang expressions: expand to ORs
        return "(" + " OR ".join(f"{left} == {render(a, inport)}" for a in e.right.arguments) + ")"
    if hasattr(e, "left") and hasattr(e, "operator") and hasattr(e, "right"):  # Condition / Comparison
        return f"{render(e.left, inport)} {_OPS.get(e.operator, e.operator)} {render(e.right, inport)}"
    if hasattr(e, "left") and hasattr(e, "op") and hasattr(e, "right"):        # BinaryOp
        return f"{render(e.left, inport)} {e.op} {render(e.right, inport)}"
    if hasattr(e, "arguments") and hasattr(e, "name"):                          # FunctionCall
        return f"{e.name}({', '.join(render(a, inport) for a in e.arguments)})"
    if hasattr(e, "name") and hasattr(e, "value"):                              # NamedArg
        return f"{e.name}={render(e.value, inport)}"
    if hasattr(e, "name"):                                                      # Identifier
        return str(e.name)
    if hasattr(e, "parts"):                                                     # DottedName
        return ".".join(e.parts)
    return str(e)


def _semantic(value: str) -> str:
    """SemanticCondition -> expression over the subject port (deterministic forms are expanded)."""
    q = lambda t: "'" + t.replace("'", "\\'") + "'"
    if value.startswith("contains:"):
        return " OR ".join(f"contains(@in_subject, {q(v)})" for v in value[len("contains:"):].split("|"))
    if value.startswith("startswith:"):
        return f"startswith(@in_subject, {q(value[len('startswith:'):])})"
    return f"@in_subject == {q(value)}"


# --------------------------------------------------------------------------- scope

@dataclass
class _Scope:
    """One node/edge list (the workflow, or a LOOP body) plus its control frontier."""
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    producers: dict = field(default_factory=dict)   # var -> ["node.out_var", ...] that may hold it here
    frontier: list = field(default_factory=list)    # [(node_id, control_port)] awaiting a successor
    used: list = field(default_factory=list)        # vars read here but not produced here


class SPLToGraphConverter:
    """Convert one ``WorkflowStatement`` to a GraphLang graph dict."""

    def __init__(self, workflows: set[str] | None = None, source_name: str = "", source_dir=None,
                 procedures: dict[str, str] | None = None, functions: dict | None = None,
                 tools: dict | None = None):
        self._workflows = workflows or set()   # workflows defined in the same .spl file
        self._warned_tools: set[str] = set()
        self._tools = tools or {}              # name -> CREATE TOOL_API in this file or an IMPORTed one
        self._functions = functions or {}      # name -> CREATE FUNCTION in the same file: its body is the prompt
        self._source_name = source_name
        self._known = procedures or {}         # name -> path, for callees that live outside this text
        self._source_dir = source_dir          # sibling <name>.spl files count as procedures too
        self.warnings: list[str] = []
        self._counters: dict[str, int] = {}
        self._procedures: dict[str, str] = {}
        self._wf: WorkflowStatement | None = None
        self._scope = _Scope()
        self._depth = 0                        # > 0 inside a LOOP body

    # -- helpers ------------------------------------------------------------
    def _id(self, prefix: str) -> str:
        n = self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}_{n}"

    def _warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def _add(self, node_id, ntype, ports, config=None, *, trigger=True) -> str:
        sc = self._scope
        node = {"id": node_id, "type": ntype}
        if config:
            node["config"] = config
        node["ports"] = list(ports)
        sc.nodes.append(node)
        if trigger:
            for src, port in sc.frontier:
                sc.edges.append({"source": f"{src}.{port}", "target": f"{node_id}.trigger", "type": "triggers"})
        return node_id

    def _bind_inputs(self, node_id: str, variables: list[str], renames: dict | None = None) -> list[str]:
        """Add in_<var> ports + binds edges from the producers; returns the in_ port names."""
        sc = self._scope
        node = next(n for n in sc.nodes if n["id"] == node_id)
        ports = []
        for v in variables:
            port = f"in_{(renames or {}).get(v, v)}"
            if port not in node["ports"]:
                node["ports"].append(port)
            ports.append(port)
            if v in sc.producers:
                for src in sc.producers[v]:
                    sc.edges.append({"source": src, "target": f"{node_id}.{port}", "type": "binds"})
            elif v not in sc.used:
                sc.used.append(v)
        return ports

    def _produce(self, node_id: str, var: str) -> None:
        node = next(n for n in self._scope.nodes if n["id"] == node_id)
        port = f"out_{var}"
        if port not in node["ports"]:
            node["ports"].append(port)
        self._scope.producers[var] = [f"{node_id}.{port}"]

    def _join_producers(self, before: dict, branches: list) -> None:
        """After branches meet, a variable may come from any branch that continues (phi)."""
        sc = self._scope
        merged: dict = {}
        for producers, continues in branches:
            if not continues:
                continue
            for var, srcs in producers.items():
                have = merged.setdefault(var, [])
                have += [x for x in srcs if x not in have]
        sc.producers = merged if merged else {k: list(v) for k, v in before.items()}

    def _step(self, node_id: str, port: str = "complete") -> None:
        self._scope.frontier = [(node_id, port)]

    # -- entry point --------------------------------------------------------
    def convert_workflow(self, wf: WorkflowStatement) -> dict:
        self._wf = wf
        sc = self._scope = _Scope()
        entry = "wf_entry"
        sc.nodes.append({"id": entry, "type": "INPUT",
                         "ports": ["entry"] + [f"out_{i.name.lstrip('@')}" for i in wf.inputs]})
        for i in wf.inputs:
            sc.producers[i.name.lstrip("@")] = [f"{entry}.out_{i.name.lstrip('@')}"]
        sc.frontier = [(entry, "entry")]

        self._exit_ports = [f"in_{o.name.lstrip('@')}" for o in wf.outputs] or ["in_result"]
        self._block(wf.body)

        exit_node = {"id": "wf_exit", "type": "OUTPUT", "ports": ["trigger", "exit"] + self._exit_ports}
        sc.nodes.append(exit_node)
        for src, port in sc.frontier:
            sc.edges.append({"source": f"{src}.{port}", "target": "wf_exit.trigger", "type": "triggers"})

        graph = {
            "version": GRAPH_VERSION,
            "workflow": {
                "name": wf.name,
                "inputs": [self._param(i) for i in wf.inputs],
                "outputs": [{"name": o.name.lstrip("@"), "type": o.param_type or "TEXT"} for o in wf.outputs],
            },
        }
        if self._procedures:
            graph["resources"] = {"procedures": dict(self._procedures)}
        graph["nodes"] = sc.nodes
        graph["edges"] = sc.edges
        return graph

    @staticmethod
    def _param(p) -> dict:
        d = {"name": p.name.lstrip("@"), "type": p.param_type or "TEXT"}
        if p.default_value is not None:
            dv = p.default_value
            d["default"] = dv.value if isinstance(dv, Literal) and dv.literal_type != "bool" else (bool(dv.value) if isinstance(dv, Literal) else render(dv))
        return d

    # -- statements ---------------------------------------------------------
    def _block(self, stmts) -> None:
        for s in stmts:
            sc = self._scope
            if not sc.frontier and sc.nodes and not isinstance(s, LoggingStatement):
                # nothing leads here (an earlier RETURN / RAISE ended every path)
                self._warn(f"unreachable {type(s).__name__} skipped")
                continue
            self._statement(s)

    def _statement(self, s) -> None:
        if isinstance(s, GenerateIntoStatement):
            self._generate(s)
        elif isinstance(s, CallStatement):
            self._call(s)
        elif isinstance(s, CallParallelStatement):
            self._call_parallel(s)
        elif isinstance(s, SolveStatement):
            nid = self._add(self._id("solve"), "SOLVE", ["trigger", "complete"],
                            {"expression": template(s.python_template), **({"type": s.target_type} if s.target_type else {})})
            self._bind_inputs(nid, expr_vars(s.python_template))
            self._produce(nid, s.target_variable.lstrip("@"))
            self._step(nid)
        elif isinstance(s, AssertStatement):
            self._assert(s)
        elif isinstance(s, EvaluateStatement):
            self._evaluate(s)
        elif isinstance(s, WhileStatement):
            self._while(s)
        elif isinstance(s, AssignmentStatement):
            nid = self._add(self._id("set"), "CONTEXT", ["trigger", "complete"],
                            {"action": "set", "expression": render(s.expression, True)})
            self._bind_inputs(nid, expr_vars(s.expression))
            self._produce(nid, s.variable.lstrip("@"))
            self._step(nid)
        elif isinstance(s, RetryStatement):
            nid = self._add(self._id("retry"), "RECOVER", ["trigger", "retry"], {"action": "retry"})
            self._step(nid, "retry")
        elif isinstance(s, RaiseStatement):
            nid = self._add(self._id("raise"), "RECOVER", ["trigger", "halt"],
                            {"action": "halt", "exception": s.exception_type,
                             **({"message": s.message} if s.message else {})})
            self._scope.frontier = []
        elif isinstance(s, CommitStatement):
            self._commit(s)
        elif isinstance(s, LoggingStatement):
            pass
        elif isinstance(s, DoBlock):
            self._block(s.statements)
            if s.exception_handlers:
                self._warn("EXCEPTION handlers in a DO block were dropped")
        else:
            self._warn(f"skipped unsupported statement {type(s).__name__}")

    def _generate(self, s: GenerateIntoStatement) -> None:
        gc = s.generate_clause
        nid = self._generate_node(gc.function_name, gc.arguments, s.target_variable, gc.model, gc.output_budget, gc.temperature)
        self._step(nid)

    def _generate_node(self, function: str, arguments: list, target: str, model=None, output_budget=None,
                       temperature=None) -> str:
        """GENERATE node for `function(args)`. A function defined in this file gives its body as the prompt, each
        `{param}` becoming the port `in_param`, fed by the argument (a plain @var is bound; a literal is written into
        the prompt; anything else is computed by a SOLVE node first). Else the call text itself is the prompt."""
        fn = self._functions.get(function)
        bindings: list[tuple[str, str]] = []                   # (variable, parameter) to bind once the node exists
        defaults: dict[str, object] = {}                       # parameter -> literal argument
        if fn is None:
            args = ", ".join(render(a) for a in arguments)
            cfg: dict = {"function": function, "prompt_inline": f"{function}({args})"}
            self._warn(f"function {function!r} is not defined in this file: its call text is used as the prompt")
        else:
            prompt = fn.body.strip()
            for param, arg in zip(fn.parameters, arguments):
                prompt = prompt.replace("{" + param.name + "}", "{{in_" + param.name + "}}")
                if isinstance(arg, ParamRef):
                    bindings.append((arg.name.lstrip("@"), param.name))
                elif isinstance(arg, Literal):
                    defaults[param.name] = arg.value
                else:
                    bindings.append((self._compute(render(arg), arg), param.name))
            cfg = {"function": function, "params": [p.name for p in fn.parameters], "prompt_inline": prompt}
        if arguments:
            cfg["arguments"] = [render(a) for a in arguments]
        if defaults:
            cfg["phases"] = {"pre": {"defaults": {f"in_{k}": v for k, v in defaults.items()}}}
        if model:
            cfg["model"] = model
        if output_budget is not None:
            cfg["output_budget"] = output_budget
        if temperature is not None:
            cfg["temperature"] = temperature
        nid = self._add(self._id("gen"), "GENERATE", ["trigger", "complete"], cfg)
        if fn is None:
            self._bind_inputs(nid, expr_vars([arguments, model, output_budget]))
        else:
            node = next(n for n in self._scope.nodes if n["id"] == nid)
            for param in defaults:
                node["ports"].append(f"in_{param}")
            for var, param in bindings:
                self._bind_inputs(nid, [var], {var: param})
            self._bind_inputs(nid, expr_vars([model, output_budget]))
        if target:
            self._produce(nid, target.lstrip("@"))
        return nid

    def _compute(self, expression: str, source) -> str:
        """A SOLVE node that evaluates `expression` first; returns the variable holding the result."""
        nid = self._add(self._id("calc"), "SOLVE", ["trigger", "complete"], {"expression": re.sub(r"@(\w+)", r"@in_\1", expression)})
        self._bind_inputs(nid, expr_vars(source))
        self._produce(nid, nid)
        self._step(nid)
        return nid

    def _tool_node(self, name: str, spl_args: list[str], py_args: list[str], trigger: bool, expression: str | None = None) -> str:
        """A call to a Python tool. If the tool's source is in the SPL (CREATE TOOL_API, here or in an IMPORTed file) the node
        is a `kernel` SOLVE that carries it, so the graph runs without SPL.py; else the call stays an `expression` SOLVE
        that only names the tool (it validates but cannot run: the source is registered elsewhere, e.g. a tools.py)."""
        local = Path(self._source_dir) / "tools.py" if self._source_dir is not None else None
        tool = (self._tools.get(name) or (local is not None and local.is_file() and _module_tool(name, local)) or _module_tool(name) or None)
        problem = "has no Python source in the SPL" if tool is None or tool.runtime != "PYTHON" else None
        if problem is None:
            try:
                compile(tool.python_body, f"<tool {name}>", "exec")
            except SyntaxError as e:
                problem = f"has Python source that does not compile ({e.msg}, line {e.lineno})"
        if problem:
            if name not in self._warned_tools:
                self._warned_tools.add(name)
                self._warn(f"tool {name!r} {problem}: the node names it but cannot run it")
            return self._add(self._id("tool"), "SOLVE", ["trigger", "complete"],
                             {"expression": expression or f"{name}({', '.join(spl_args)})", "tool": name}, trigger=trigger)
        call = f"{name}({', '.join(py_args)})"
        cfg = {"tool": name, "backend": "kernel", "arguments": spl_args,
               "code": tool.python_body.strip("\n") + f"\n_spl_result = {call}\n", "result": "_spl_result",
               "out_type": _OUT_TYPES.get(str(tool.return_type).upper(), "JSON"),
               "tool_params": [p.name for p in tool.parameters], "tool_returns": str(tool.return_type)}
        if getattr(tool, "builtin", False):
            cfg["tool_builtin"] = True
        return self._add(self._id("tool"), "SOLVE", ["trigger", "complete"], cfg, trigger=trigger)

    def _is_procedure(self, name: str) -> bool:
        sibling = self._source_dir is not None and (self._source_dir / f"{name}.spl").exists()
        return name in self._workflows or sibling or name in self._known

    def _call(self, s: CallStatement, *, trigger=True, workflow=False) -> str:
        name = s.procedure_name
        args = [render(a) for a in s.arguments]
        if workflow or self._is_procedure(name):
            default = f"./{self._source_name}" if name in self._workflows else f"./{name}.spl"
            self._procedures.setdefault(name, self._known.get(name, default))
            nid = self._add(self._id("call"), "GENERATE", ["trigger", "complete"],
                            {"procedure_ref": f"procedures.{name}", **({"arguments": args} if args else {})},
                            trigger=trigger)
        else:  # a Python tool (@spl_tool): deterministic, so SOLVE rather than GENERATE
            nid = self._tool_node(name, args, [re.sub(r"@(\w+)", r"\1", a) for a in args], trigger)
        self._bind_inputs(nid, expr_vars(s.arguments))
        if s.target_variable:
            self._produce(nid, s.target_variable.lstrip("@"))
        elif next(n for n in self._scope.nodes if n["id"] == nid).get("config", {}).get("backend"):
            self._produce(nid, name)                       # a kernel SOLVE must have exactly one result port
        if trigger:
            self._step(nid)
        return nid

    def _call_parallel(self, s: CallParallelStatement) -> None:
        sc = self._scope
        fork = self._add(self._id("fork"), "FORK", ["trigger"])
        join = self._id("join")
        branch_ids = []
        for b in s.branches:
            sc.frontier = [(fork, f"branch_{len(branch_ids) + 1}")]
            next(n for n in sc.nodes if n["id"] == fork)["ports"].append(f"branch_{len(branch_ids) + 1}")
            if b.workflow_name in self._functions and b.workflow_name not in self._workflows:
                branch_ids.append(self._generate_node(b.workflow_name, b.arguments, b.target_var))
            else:
                branch_ids.append(self._call(CallStatement(b.workflow_name, b.arguments, b.target_var or None),
                                             workflow=self._is_procedure(b.workflow_name) or any(type(a).__name__ == "NamedArg" for a in b.arguments)))
        sc.frontier = [(i, "complete") for i in branch_ids]
        self._add(join, "JOIN", ["trigger", "complete"])
        self._step(join)

    def _hoist_tool_calls(self, text: str) -> str:
        """A condition may only call the built-in functions. A call to anything else (a Python tool) becomes a SOLVE node
        that runs first; the condition reads its result instead."""
        out, pos = [], 0
        while True:
            m = next((m for m in _CALL.finditer(text, pos) if m.group(1) not in _CONDITION_FUNCS), None)
            if m is None:
                break
            depth, i = 0, m.end() - 1
            while i < len(text):
                depth += (text[i] == "(") - (text[i] == ")")
                i += 1
                if depth == 0:
                    break
            call = text[m.start():i]
            inner = call[call.index("(") + 1:-1]
            nid = self._tool_node(m.group(1), [re.sub(r"@in_(\w+)", r"@\1", inner)], [re.sub(r"@in_(\w+)", r"\1", inner)],
                                  True, expression=call)
            self._bind_inputs(nid, list(dict.fromkeys(re.findall(r"@in_(\w+)", call))))
            self._produce(nid, nid)
            self._step(nid)
            out.append(text[pos:m.start()] + f"@in_{nid}")
            pos = i
            self._hoisted.append(nid)
        return "".join(out) + text[pos:]

    def _assert(self, s: AssertStatement) -> None:
        self._hoisted: list[str] = []
        cond = self._hoist_tool_calls(template(s.python_template))
        nid = self._add(self._id("assert"), "ASSERT", ["trigger", "pass", "fail"], {"condition": cond})
        self._bind_inputs(nid, [*expr_vars(s.python_template), *self._hoisted])
        ends: list = [(nid, "pass")]
        if s.otherwise_body:
            before = {k: list(v) for k, v in self._scope.producers.items()}
            self._scope.frontier = [(nid, "fail")]
            self._block(s.otherwise_body)
            ends += self._scope.frontier
            self._join_producers(before, [(self._scope.producers, bool(self._scope.frontier)), (before, True)])
        else:
            ends.append((nid, "fail"))
        self._scope.frontier = ends

    def _evaluate(self, s: EvaluateStatement) -> None:
        sc = self._scope
        ends: list = []
        pending = list(sc.frontier)
        before = {k: list(v) for k, v in sc.producers.items()}
        outcomes: list = []
        for n_when, wc in enumerate(s.when_clauses, 1):
            sc.frontier = pending
            sc.producers = {k: list(v) for k, v in before.items()}
            c = wc.condition
            cfg: dict
            if isinstance(c, SemanticCondition):
                cond = True
                cfg = {"condition": _semantic(c.semantic_value)}
                if not c.semantic_value.startswith(("contains:", "startswith:")):
                    cfg["semantic"] = True
            else:
                cond = False
                if hasattr(c, "operator"):
                    cmp = Condition(s.expression, c.operator, c.right)
                    cfg = {"condition": render(cmp, True)}
                else:
                    cfg = {"condition": render(c, True)}
            cfg["branch"] = n_when  # 1-based WHEN index; graph2spl re-chains EVALUATE nodes by it
            nid = self._add(self._id("eval"), "EVALUATE", ["trigger", "pass", "fail"], cfg)
            vs = expr_vars(s.expression) + expr_vars(wc.condition)
            if cond:  # semantic: the subject is a single bound value
                self._bind_inputs(nid, expr_vars(s.expression), renames={v: "subject" for v in expr_vars(s.expression)})
            else:
                self._bind_inputs(nid, vs)
            sc.frontier = [(nid, "pass")]
            self._block(wc.statements)
            ends += sc.frontier
            outcomes.append((sc.producers, bool(sc.frontier)))
            pending = [(nid, "fail")]
        sc.frontier = pending
        sc.producers = {k: list(v) for k, v in before.items()}
        if s.else_statements:
            self._block(s.else_statements)
        outcomes.append((sc.producers, bool(sc.frontier)))
        sc.frontier = ends + sc.frontier
        self._join_producers(before, outcomes)

    def _while(self, s: WhileStatement) -> None:
        outer = self._scope
        body = self._scope = _Scope()
        self._depth += 1
        # Empty frontier: the body's first node has no trigger edge (LOOP starts nodes nothing triggers).
        self._block(s.body)
        self._scope = outer
        self._depth -= 1

        cond_vars = expr_vars(s.condition)
        produced = list(body.producers)
        cond = render(s.condition)
        first: list[str] = []
        state_ids: list[str] = []
        if any(m.group(1) not in _CONDITION_FUNCS for m in _CALL.finditer(cond)):
            cond, first, state_ids = self._loop_condition_calls(cond, body, outer)
            produced = list(body.producers)                        # now includes the results of the calls at the end of the body
        # A variable the body also produces has two values: the one it had before the loop (a LOOP input, read on the first
        # check) and the latest one (loop state, read on every later check). One only the body produces is state alone.
        initial = [v for v in cond_vars if v in produced and v in outer.producers and v != "cycle"]
        keeps = [v for v in produced if v in outer.producers]       # written in the body: its value before the loop is where it starts
        reads = [v for v in dict.fromkeys(body.used + first + initial + keeps + [v for v in cond_vars if v not in produced]) if v != "cycle"]
        lid = self._id("loop")

        def read(m: re.Match) -> str:
            v = m.group(1)
            if v == "cycle" or v.startswith("in_") or v in state_ids:
                return m.group(0)
            if v in initial:
                return f"latest(@in_{v}, @{v})"
            return m.group(0) if v in produced else f"@in_{v}"          # state stays bare, a plain input is read as @in_<var>

        cond = re.sub(r"@(\w+)", read, cond)
        cfg: dict = {"condition": cond}
        if s.max_iterations is not None:
            cfg["max_iterations"] = s.max_iterations
        cfg["outputs"] = {v: {"from": srcs[0] if len(srcs) == 1 else list(srcs)} for v, srcs in body.producers.items()}
        cfg["subgraph"] = {"nodes": body.nodes, "edges": body.edges}
        self._add(lid, "LOOP", ["trigger", "loop", "exit"], cfg)
        self._bind_inputs(lid, reads)
        for v in produced:
            self._produce(lid, v)
        self._step(lid, "exit")

    def _loop_condition_calls(self, cond: str, body: "_Scope", outer: "_Scope") -> tuple[str, list[str], list[str]]:
        """A WHILE condition that calls a Python tool. The condition is checked before every iteration, so the call runs
        twice as SOLVE nodes: once before the loop (its result enters the LOOP as an input, read on the first check) and
        once at the end of the body (its result is loop state, read on every later check). Returns the condition with each
        call replaced by that choice, the names of the loop inputs it reads, and the names of the loop-state results."""
        text = re.sub(r"@(\w+)", lambda m: m.group(0) if m.group(1) == "cycle" else f"@in_{m.group(1)}", cond)
        self._scope, self._hoisted = outer, []
        before_text = self._hoist_tool_calls(text)                 # in the outer scope, before the LOOP node
        before_ids = list(self._hoisted)
        self._scope, self._hoisted = body, []
        self._hoist_tool_calls(text)                               # again at the end of the body
        after_ids = list(self._hoisted)
        self._scope = outer
        for first, again in zip(before_ids, after_ids):
            before_text = before_text.replace(f"@in_{first}", f"latest(@in_{first}, @{again})")
        keep = set(before_ids)                                     # the pair stays in loop form; every other @in_x is a plain variable again
        before_text = re.sub(r"@in_(\w+)", lambda m: m.group(0) if m.group(1) in keep else f"@{m.group(1)}", before_text)
        return before_text, before_ids, after_ids

    def _commit(self, s: CommitStatement) -> None:
        sc = self._scope
        if self._depth:
            self._warn("COMMIT inside a WHILE body was skipped (a LOOP body cannot reach wf_exit)")
            return
        if not isinstance(s.expression, ParamRef):
            # a computed / literal value: build it in a node so wf_exit has one clear source
            out_name = self._exit_ports[0].removeprefix("in_")
            nid = self._add(self._id("set"), "CONTEXT", ["trigger", "complete"],
                            {"action": "set", "expression": render(s.expression, True)})
            self._bind_inputs(nid, expr_vars(s.expression))
            self._produce(nid, out_name)
            self._step(nid)
            names = [out_name]
        else:
            names = expr_vars(s.expression)
        for v in names:
            port = f"in_{v}" if f"in_{v}" in self._exit_ports else self._exit_ports[0]
            if v in sc.producers:
                for src in sc.producers[v]:
                    edge = {"source": src, "target": f"wf_exit.{port}", "type": "binds"}
                    if edge not in sc.edges:
                        sc.edges.append(edge)
        # RETURN leaves the workflow: wire this path to wf_exit and end it
        for src, port in sc.frontier:
            sc.edges.append({"source": f"{src}.{port}", "target": "wf_exit.trigger", "type": "triggers"})
        sc.frontier = []


# --------------------------------------------------------------------------- public API

def _parse(source: str):
    from spl.lexer import Lexer
    from spl3.parser import SPL3Parser

    return SPL3Parser(Lexer(source).tokenize()).parse().statements


def _module_tool(name: str, path=None):
    """A Python @spl_tool as a ToolAPINode: its source plus the imports and helpers it needs from the same module, so a
    graph that calls it runs without SPL.py. `path` is a tools.py next to the .spl; none means the built-in tools
    (spl/stdlib.py: write_file, ...)."""
    import ast

    try:
        from spl.ast_nodes import Parameter

        if path is None:
            import spl.stdlib as module
            path = module.__file__
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None
    top: dict[str, ast.stmt] = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module in ("__future__", "spl.tools"):
                continue
            for a in node.names:
                top[(a.asname or a.name).split(".")[0]] = node
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            top[node.name] = node
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    top[t.id] = node
    fn = top.get(name)
    if not isinstance(fn, ast.FunctionDef):
        return None
    needed, todo = {id(fn): fn}, [fn]
    while todo:
        for sub in ast.walk(todo.pop()):
            ident = sub.id if isinstance(sub, ast.Name) else None
            if ident in top and id(top[ident]) not in needed:
                needed[id(top[ident])] = top[ident]
                todo.append(top[ident])
    ordered = [n for n in tree.body if id(n) in needed]
    for n in ordered:
        if isinstance(n, ast.FunctionDef):
            n.decorator_list = []
    tool = ToolAPINode(name=name, parameters=[Parameter(name=a.arg) for a in fn.args.args], return_type="TEXT",
                       runtime="PYTHON", python_body="\n\n".join(ast.unparse(n) for n in ordered))
    tool.builtin = path is None or Path(path).name == "stdlib.py"
    return tool


def _definitions(statements, source_dir, seen=None) -> list:
    """The functions and tools of this file and of the files it IMPORTs (`IMPORT 'tools'` means tools.spl next to it)."""
    seen = seen if seen is not None else set()
    out = list(statements)
    for st in statements:
        if isinstance(st, ImportStatement) and source_dir is not None:
            base = Path(source_dir) / st.path
            path = next((c for c in (base, base.with_suffix(".spl"), Path(str(base) + ".spl")) if c.is_file()), None)
            if path is not None and path.resolve() not in seen:
                seen.add(path.resolve())
                try:
                    out += _definitions(_parse(path.read_text(encoding="utf-8")), path.parent, seen)
                except Exception:                                  # an unreadable import only costs its definitions
                    pass
    return out


def spl_to_graph(source: str, workflow: str | None = None, source_name: str = "", source_dir=None,
                 procedures: dict[str, str] | None = None) -> tuple[dict, list[str]]:
    """Parse SPL source; return (graph dict, warnings).  Default workflow: the last one defined
    (the entry point by SPL convention, callees come first)."""
    statements = _parse(source)
    wfs = [s for s in statements if isinstance(s, WorkflowStatement)]
    if not wfs:
        raise NoWorkflowError("no WORKFLOW found - spl2graph lifts agentic workflows only")
    if workflow:
        match = [w for w in wfs if w.name == workflow]
        if not match:
            raise NoWorkflowError(f"workflow {workflow!r} not found (have: {', '.join(w.name for w in wfs)})")
        wf = match[0]
    else:
        wf = wfs[-1]
    definitions = _definitions(statements, source_dir)
    functions = {s.name: s for s in definitions if isinstance(s, CreateFunctionStatement)}
    tools = {s.name: s for s in definitions if isinstance(s, ToolAPINode)}
    conv = SPLToGraphConverter({w.name for w in wfs}, source_name, source_dir, procedures, functions, tools)
    return conv.convert_workflow(wf), conv.warnings


def graph_to_yaml(graph: dict) -> str:
    import yaml
    return yaml.safe_dump(graph, sort_keys=False, default_flow_style=False, allow_unicode=True)
