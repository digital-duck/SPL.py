"""
splc — deterministic SPL 3.0 → Python/PocketFlow transpiler.

No LLM required. Converts a .spl logical view to a Python/PocketFlow
physical implementation using rule-based AST traversal.

PocketFlow maps cleanly to SPL via the ETL analogy:
  prep(shared)                → Extract  — read @variables from shared store
  exec(prep_res)              → Transform — GENERATE / LLM call
  post(shared, prep_res, res) → Load     — write results back to shared store

Pattern detection (inspects AST — no heuristics):
  react:       WHILE + EVALUATE + CALL (non-write_file) in ELSE branch
  self_refine: WHILE + EVALUATE + GENERATE in ELSE branch (default)
  linear:      no WHILE loop

Phase 1 scope (self_refine pattern):
  draft → critique → ([APPROVED]? commit : refine → critique)

  Handles:
    CREATE FUNCTION  → PROMPT = '''...''' string constants
    WORKFLOW INPUT   → shared dict initial values + @click.option
    GENERATE INTO    → Node.exec() calling call_llm(model, prompt)
    CALL write_file  → _write(path, content) in post()
    LOGGING          → print(...) in post()
    EVALUATE WHEN contains(...) THEN → post() returns action string
    WHILE cond DO    → critique.post() returns "refine" / "commit"
    EXCEPTION WHEN MaxIterationsReached → handled via WHILE guard in post()
    EXCEPTION WHEN BudgetExceeded      → Node.exec_fallback() override

Phase 2 scope (react pattern):
  decide → ([action: answer]? answer : search → update_context → decide)

  Handles:
    GENERATE DecideAction INTO @decision   → DecideNode
    EVALUATE WHEN contains(...) THEN       → DecideNode.post() routing
    CALL tool INTO @results  (ELSE branch) → SearchNode.exec() inline
    Context/iteration update (ELSE stmts)  → SearchNode.post()
    GENERATE AnswerQuestion INTO @answer   → AnswerNode
    RETURN WITH status/iterations          → AnswerNode.post()
    EXCEPTION WHEN BudgetExceeded          → AnswerNode fallback
"""

from __future__ import annotations

import re

from spl.ast_nodes import (
    AssignmentStatement,
    CallStatement,
    CommitStatement,
    CreateFunctionStatement,
    EvaluateStatement,
    FStringLiteral,
    GenerateIntoStatement,
    Literal,
    LoggingStatement,
    ParamRef,
    SemanticCondition,
    WhileStatement,
    WorkflowStatement,
)
from spl3.ast_nodes import CompoundCondition, NoneLiteral, UnaryOp


class PocketFlowTranspiler:
    """Deterministic SPL 3.0 → Python/PocketFlow transpiler.

    Usage::

        from spl.lexer import Lexer
        from spl3.parser import SPL3Parser
        from spl3.splc.transpiler_pocketflow import PocketFlowTranspiler

        tokens = Lexer(src).tokenize()
        program = SPL3Parser(tokens).parse()
        code = PocketFlowTranspiler("react_research").transpile(program)
    """

    def __init__(self, recipe_name: str):
        self.recipe_name = recipe_name
        self.prompts: dict[str, str] = {}       # fn_name → prompt body
        self.fn_params: dict[str, list] = {}    # fn_name → [Parameter]
        self.sub_workflows: dict[str, WorkflowStatement] = {}
        self.pattern: str = "self_refine"       # detected in transpile()

    # ── Public entry point ────────────────────────────────────────────────────

    def transpile(self, program) -> str:
        """Return full Python/PocketFlow source as a string."""
        # Pass 1: collect CREATE FUNCTION definitions
        for stmt in program.statements:
            if isinstance(stmt, CreateFunctionStatement):
                self.prompts[stmt.name] = stmt.body
                self.fn_params[stmt.name] = stmt.parameters

        # Pass 2: collect workflow definitions
        workflows = [s for s in program.statements if isinstance(s, WorkflowStatement)]
        for wf in workflows:
            self.sub_workflows[wf.name] = wf

        main_wf = workflows[-1]
        self.pattern = self._detect_pattern(main_wf)

        parts = [
            self._gen_header(main_wf),
            self._gen_prompts(),
            self._gen_helpers(),
            self._gen_nodes(main_wf),
            self._gen_build_flow(main_wf),
            self._gen_main(main_wf),
        ]
        return "\n\n".join(p for p in parts if p)

    # ── Pattern detection ─────────────────────────────────────────────────────

    def _detect_pattern(self, wf: WorkflowStatement) -> str:
        """Detect workflow pattern from AST structure.

        react:       WHILE + EVALUATE + CALL (non-write_file) in ELSE branch
        self_refine: WHILE + EVALUATE + GENERATE in ELSE branch (default)
        linear:      no WHILE loop
        """
        while_stmt = self._find_while(wf)
        if while_stmt is None:
            return "linear"
        eval_stmt = next(
            (s for s in while_stmt.body if isinstance(s, EvaluateStatement)), None
        )
        if eval_stmt is None:
            return "self_refine"
        if eval_stmt.else_statements:
            for s in eval_stmt.else_statements:
                if isinstance(s, CallStatement) and s.procedure_name not in ("write_file",):
                    return "react"
        return "self_refine"

    def _extract_contains_strs(self, condition) -> list[str]:
        """Recursively extract all 'contains:...' strings from a condition tree."""
        if isinstance(condition, SemanticCondition):
            sem = condition.semantic_value
            if sem.startswith("contains:"):
                return [sem[len("contains:"):]]
            return []
        if isinstance(condition, CompoundCondition):
            return (
                self._extract_contains_strs(condition.left)
                + self._extract_contains_strs(condition.right)
            )
        return []

    # ── Code section generators ───────────────────────────────────────────────

    def _gen_header(self, wf: WorkflowStatement) -> str:
        name = wf.name
        pattern_descs = {
            "self_refine": "draft → critique → ([APPROVED]? commit : refine → critique)",
            "react":       "decide → ([action: answer]? answer : search → update_context → decide)",
            "linear":      "step1 → step2 → ... → output",
        }
        pattern_desc = pattern_descs.get(self.pattern, self.pattern)
        return f'''\
"""
{name} — generated by splc (deterministic Python/PocketFlow transpiler)

PocketFlow pattern: prep(shared) → exec(prep_res) → post(shared, prep_res, exec_res)
                    Extract       → Transform        → Load
                    (ETL applied to LLM orchestration)

Pattern: {pattern_desc}

Usage:
    pip install pocketflow click
    python {name}_python_pocketflow.py --task "Your task here"
"""

from pathlib import Path

import click
from pocketflow import Flow, Node'''

    def _gen_prompts(self) -> str:
        lines = [
            "# ── Prompts (mirrors CREATE FUNCTION blocks in .spl) "
            "──────────────────────────"
        ]
        for name, body in self.prompts.items():
            const = name.upper() + "_PROMPT"
            body_clean = body.strip("\n")
            lines.append(f'\n{const} = """\\\n{body_clean}"""')
        return "\n".join(lines)

    def _gen_helpers(self) -> str:
        base = '''\
# ── Helpers ───────────────────────────────────────────────────────────────────

def _call_llm(model: str, prompt: str) -> str:
    """Call the LLM via Ollama REST API. Replace with your preferred adapter."""
    import urllib.request, json
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["response"].strip()


def _write(path: str, content: str) -> None:
    """Write content to a file, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")'''
        if self.pattern == "react":
            base += "\n\n\n" + self._gen_web_search_helper()
        return base

    def _gen_web_search_helper(self) -> str:
        """Generate _web_search() helper — inlined DuckDuckGo search for ReAct."""
        lines = [
            "def _web_search(query: str, max_results: int = 5) -> str:",
            '    """Search the web via DuckDuckGo — auto-extracts search_query from YAML."""',
            "    import re",
            "    try:",
            "        from ddgs import DDGS",
            "    except ImportError:",
            "        from duckduckgo_search import DDGS",
            "    m = re.search(r'search_query:\\s*(.+)', query)",
            "    if m:",
            "        query = m.group(1).strip().strip('\"').strip(\"'\")",
            "    try:",
            "        results = DDGS().text(query.strip(), max_results=max_results)",
            "        if not results:",
            '            return f"No results for: {query}"',
            "        lines = []",
            "        for i, r in enumerate(results, 1):",
            '            title = r.get("title", "")',
            '            url   = r.get("href", "")',
            '            body  = r.get("body", "")',
            '            lines.append(f"[{i}] {title}\\n    URL: {url}\\n    {body}")',
            '        return "\\n\\n".join(lines)',
            "    except Exception as e:",
            '        return f"Search error: {e}"',
        ]
        return "\n".join(lines)

    def _gen_nodes(self, wf: WorkflowStatement) -> str:
        if self.pattern == "react":
            return self._gen_nodes_react(wf)
        if self.pattern == "linear":
            return self._gen_nodes_linear(wf)
        # self_refine (default)
        segs = self._segment_body(wf)
        parts = [
            "# ── Nodes  (each mirrors one GENERATE / EVALUATE block) "
            "──────────────────────"
        ]
        parts.append(self._gen_node_draft(segs["init"], wf))
        parts.append(self._gen_node_critique(segs["pre_eval"], wf))
        parts.append(self._gen_node_refine(segs["else_stmts"], wf))
        parts.append(self._gen_node_commit(segs["when_stmts"], segs["post"], wf))
        return "\n\n".join(parts)

    def _gen_build_flow(self, wf: WorkflowStatement) -> str:
        if self.pattern == "react":
            return self._gen_build_flow_react(wf)
        if self.pattern == "linear":
            return self._gen_build_flow_linear(wf)
        # self_refine (default)
        return '''\
# ── Flow wiring  (mirrors WORKFLOW control flow) ─────────────────────────────
# SPL:  draft → WHILE loop → EVALUATE → commit or refine → critique
#
# PocketFlow conditional edges via post() return value (action string):
#   critique.post() → "commit"  (EVALUATE [APPROVED] or max_iterations)
#   critique.post() → "refine"  (else branch)
#   refine.post()   → "critique" (loop back)
#   draft.post()    → "critique" (initial transition)

def build_flow() -> Flow:
    draft   = DraftNode()
    critique = CritiqueNode()
    refine  = RefineNode()
    commit  = CommitNode()

    # SPL: initial draft → critique
    draft   - "critique" >> critique

    # SPL: EVALUATE + WHILE guard → commit or refine
    critique - "commit"  >> commit
    critique - "refine"  >> refine

    # SPL: WHILE back-edge — refine → critique
    refine  - "critique" >> critique

    return Flow(start=draft)'''

    # ── Linear pattern generators ─────────────────────────────────────────────

    def _gen_nodes_linear(self, wf: WorkflowStatement) -> str:
        """Generate one Node per GENERATE/CALL statement in the workflow body.

        Linear pipeline: StepNode1 → StepNode2 → ... → OutputNode
        Each node does exactly one LLM call or sub-workflow CALL.
        """
        # Collect all actionable statements (skip pure assignments)
        steps = [
            s for s in wf.body
            if isinstance(s, (GenerateIntoStatement, CallStatement))
        ]
        # Find the RETURN target variable
        from spl.ast_nodes import CommitStatement
        ret_stmt = next((s for s in wf.body if isinstance(s, CommitStatement)), None)
        out_var = self._key(ret_stmt.expression.name) if (
            ret_stmt and isinstance(ret_stmt.expression, ParamRef)
        ) else (self._key(wf.outputs[0].name) if wf.outputs else "result")

        inp_keys = [self._key(p.name) for p in wf.inputs]

        parts = [
            "# ── Nodes  (each mirrors one GENERATE / CALL statement) "
            "────────────────────"
        ]

        node_names: list[str] = []
        for idx, stmt in enumerate(steps):
            is_last = (idx == len(steps) - 1)
            next_action = "output" if is_last else f"step{idx + 2}"

            if isinstance(stmt, GenerateIntoStatement):
                gc = stmt.generate_clause
                fn = gc.function_name
                target = self._key(stmt.target_variable) if stmt.target_variable else f"out{idx}"
                class_name = f"Step{idx + 1}_{fn.capitalize()}Node"
                node_names.append(class_name)

                # Build argument locals for exec()
                arg_locals = [
                    self._key(a.name) if isinstance(a, ParamRef) else self._expr_local(a)
                    for a in gc.arguments
                ]
                # All vars needed for this step — inputs + any previously computed vars
                all_prior = inp_keys + [
                    self._key(s.target_variable)
                    for s in steps[:idx]
                    if isinstance(s, (GenerateIntoStatement, CallStatement))
                    and s.target_variable
                ]
                needed = [v for v in all_prior if v in arg_locals]

                lines = [
                    f"class {class_name}(Node):",
                    f'    # SPL: GENERATE {fn}(...) INTO @{target}',
                    "",
                    "    def prep(self, shared):",
                    "        # Extract — pull required vars from shared store",
                ]
                for v in needed:
                    lines.append(f'        {v} = shared["{v}"]')
                if needed:
                    lines.append(f'        return {", ".join(needed)}')
                else:
                    lines.append('        return None')

                lines += [
                    "",
                    "    def exec(self, prep_res):",
                    f"        # Transform — LLM call: {fn}",
                ]
                if needed:
                    if len(needed) == 1:
                        lines.append(f"        {needed[0]} = prep_res")
                    else:
                        lines.append(f"        {', '.join(needed)} = prep_res")
                lines.append(f'        print("Running {fn} ...")')
                lines.append(
                    f"        return _call_llm({self._model_expr_local(gc.model)}, "
                    f"{self._prompt_fmt(fn, gc.arguments, arg_locals)})"
                )

                lines += [
                    "",
                    "    def post(self, shared, prep_res, exec_res):",
                    "        # Load — store result",
                    f'        shared["{target}"] = exec_res',
                ]

            elif isinstance(stmt, CallStatement):
                fn = stmt.procedure_name
                target = self._key(stmt.target_variable) if stmt.target_variable else f"out{idx}"
                class_name = f"Step{idx + 1}_{fn.capitalize()}Node"
                node_names.append(class_name)

                arg_locals = [
                    self._key(a.name) if isinstance(a, ParamRef) else self._expr_local(a)
                    for a in stmt.arguments
                ]
                all_prior = inp_keys + [
                    self._key(s.target_variable)
                    for s in steps[:idx]
                    if isinstance(s, (GenerateIntoStatement, CallStatement))
                    and s.target_variable
                ]
                needed = [v for v in all_prior if v in arg_locals]

                lines = [
                    f"class {class_name}(Node):",
                    f'    # SPL: CALL {fn}(...) INTO @{target}',
                    "",
                    "    def prep(self, shared):",
                    "        # Extract — pull required vars from shared store",
                ]
                for v in needed:
                    lines.append(f'        {v} = shared["{v}"]')
                if needed:
                    lines.append(f'        return {", ".join(needed)}')
                else:
                    lines.append('        return None')

                lines += [
                    "",
                    "    def exec(self, prep_res):",
                    f"        # Transform — sub-workflow call: {fn}",
                    f"        # NOTE: In standalone mode this calls the LLM to simulate {fn}.",
                    f"        # For production, replace with a direct function call.",
                ]
                if needed:
                    if len(needed) == 1:
                        lines.append(f"        {needed[0]} = prep_res")
                    else:
                        lines.append(f"        {', '.join(needed)} = prep_res")
                lines.append(f'        print("Calling {fn} ...")')
                # Fall back to LLM simulation for sub-workflow calls
                first_arg = arg_locals[0] if arg_locals else '""'
                lines.append(f'        return _call_llm("llama3.2", f"Execute {fn}: {{{first_arg}}}")')

                lines += [
                    "",
                    "    def post(self, shared, prep_res, exec_res):",
                    "        # Load — store result",
                    f'        shared["{target}"] = exec_res',
                ]

            # Route to next step or output
            if is_last:
                lines += [
                    f'        shared["status"] = "complete"',
                    f'        print(f"\\nStatus:  complete")',
                    f'        print(f"\\n{{shared.get({repr(out_var)}, exec_res)}}")',
                    '        return None',
                ]
            else:
                lines.append(f'        return "{next_action}"')

            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    def _gen_build_flow_linear(self, wf: WorkflowStatement) -> str:
        """Wire linear nodes: step1 → step2 → ... → last (returns None)."""
        steps = [
            s for s in wf.body
            if isinstance(s, (GenerateIntoStatement, CallStatement))
        ]
        node_vars: list[tuple[str, str]] = []  # (var_name, class_name)
        for idx, stmt in enumerate(steps):
            if isinstance(stmt, GenerateIntoStatement):
                fn = stmt.generate_clause.function_name
            else:
                fn = stmt.procedure_name
            class_name = f"Step{idx + 1}_{fn.capitalize()}Node"
            var_name = f"step{idx + 1}"
            node_vars.append((var_name, class_name))

        lines = [
            "# ── Flow wiring  (mirrors WORKFLOW control flow) "
            "─────────────────────────────",
            "# SPL: sequential GENERATE/CALL chain — linear pipeline",
            "",
            "def build_flow() -> Flow:",
        ]
        for var_name, class_name in node_vars:
            lines.append(f"    {var_name} = {class_name}()")

        lines.append("")
        for i, (var_name, _) in enumerate(node_vars[:-1]):
            next_var = node_vars[i + 1][0]
            lines.append(f'    {var_name} - "step{i + 2}" >> {next_var}')

        lines.append(f"    return Flow(start={node_vars[0][0]})")
        return "\n".join(lines)

    # ── ReAct pattern generators ──────────────────────────────────────────────

    def _gen_nodes_react(self, wf: WorkflowStatement) -> str:
        segs = self._segment_body(wf)
        parts = [
            "# ── Nodes  (each mirrors one GENERATE / CALL / EVALUATE block) "
            "────────────────"
        ]
        parts.append(self._gen_node_decide(segs, wf))
        parts.append(self._gen_node_search(segs, wf))
        parts.append(self._gen_node_answer(segs, wf))
        return "\n\n".join(parts)

    def _gen_node_decide(self, segs: dict, wf: WorkflowStatement) -> str:
        """DecideNode — GENERATE INTO @decision + EVALUATE routing."""
        gen = next(
            (s for s in segs["pre_eval"] if isinstance(s, GenerateIntoStatement)),
            None,
        )
        target = self._key(gen.target_variable) if gen else "decision"

        # Extract EVALUATE condition match strings
        eval_stmt = self._find_evaluate(wf)
        contains_strs: list[str] = []
        if eval_stmt and eval_stmt.when_clauses:
            contains_strs = self._extract_contains_strs(
                eval_stmt.when_clauses[0].condition
            )

        inp_keys = [self._key(p.name) for p in wf.inputs]

        fn_name = gen.generate_clause.function_name if gen else "Decide"
        lines = [
            "class DecideNode(Node):",
            f"    # SPL: GENERATE {fn_name}(...) INTO @{target}",
            f"    # post() routes: {' OR '.join(repr(s) for s in contains_strs)} → answer; else → search",
            "",
            "    def prep(self, shared):",
            "        # Extract — inputs + accumulated context",
        ]
        for k in inp_keys:
            lines.append(f'        {k} = shared["{k}"]')
        lines.append('        context = shared.get("context", "")')
        ret_vars = inp_keys + ["context"]
        lines.append(f"        return {', '.join(ret_vars)}")

        lines += [
            "",
            "    def exec(self, prep_res):",
            "        # Transform — LLM decides: search or answer",
        ]
        if gen:
            gc = gen.generate_clause
            unpack = ", ".join(inp_keys + ["context"])
            lines.append(f"        {unpack} = prep_res")
            lines.append(f'        print("Deciding next action ...")')
            # Derive arg locals from GENERATE arguments (preserves correct param mapping)
            arg_locals = [
                self._key(a.name) if isinstance(a, ParamRef) else self._expr_local(a)
                for a in gc.arguments
            ]
            lines.append(
                f"        return _call_llm({self._model_expr_local(gc.model)}, "
                f"{self._prompt_fmt(gc.function_name, gc.arguments, arg_locals)})"
            )
        else:
            lines.append('        return ""')

        # Expand pipe-separated contains values (SPL encodes OR conditions as pipe)
        expanded: list[str] = []
        for s in contains_strs:
            expanded.extend(part.strip() for part in s.split("|"))
        contains_strs = expanded

        lines += [
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — store decision; EVALUATE routing",
            f'        shared["{target}"] = exec_res',
            '        i = shared.get("iteration", 0)',
        ]

        if contains_strs:
            check = " or ".join(f"{repr(s)} in exec_res" for s in contains_strs)
            lines.append(f"        if {check}:")
            lines.append('            return "answer"')

        # WHILE guard: max_iterations fallback
        while_stmt = self._find_while(wf)
        if while_stmt and hasattr(while_stmt.condition, "right"):
            right = while_stmt.condition.right
            if isinstance(right, ParamRef):
                max_iter_key = self._key(right.name)
                default = self._default_for(max_iter_key, wf)
                lines.append(f'        if i >= shared.get("{max_iter_key}", {default}):')
                lines.append('            return "answer"')
            elif isinstance(right, Literal):
                lines.append(f'        if i >= {right.value}:')
                lines.append('            return "answer"')

        lines.append('        return "search"')
        return "\n".join(lines)

    def _gen_node_search(self, segs: dict, wf: WorkflowStatement) -> str:
        """SearchNode — CALL tool + context/iteration update from ELSE branch."""
        call = next(
            (s for s in segs["else_stmts"]
             if isinstance(s, CallStatement) and s.procedure_name not in ("write_file",)),
            None,
        )
        call_target = (
            self._key(call.target_variable) if (call and call.target_variable) else "search_results"
        )
        tool_name = call.procedure_name if call else "web_search"

        assignments = [s for s in segs["else_stmts"] if isinstance(s, AssignmentStatement)]

        lines = [
            "class SearchNode(Node):",
            f"    # SPL: CALL {tool_name}(@decision) INTO @{call_target} + context update",
            "",
            "    def prep(self, shared):",
            "        # Extract — decision YAML and current context",
            '        return shared.get("decision", ""), shared.get("context", "")',
            "",
            "    def exec(self, prep_res):",
            "        # Transform — web search (extracts search_query from YAML automatically)",
            "        decision, _ = prep_res",
            '        print("Searching the web ...")',
            "        return _web_search(decision)",
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — store results; update context and iteration counter",
            "        _, context = prep_res",
            f'        shared["{call_target}"] = exec_res',
        ]

        # Render AssignmentStatements from ELSE branch
        rendered_keys: set[str] = set()
        for s in assignments:
            key = self._key(s.variable)
            val = self._expr_shared(s.expression)
            lines.append(f'        shared["{key}"] = {val}')
            rendered_keys.add(key)

        # Ensure iteration is always incremented
        if "iteration" not in rendered_keys:
            lines.append('        shared["iteration"] = shared.get("iteration", 0) + 1')

        lines.append('        return "decide"')
        return "\n".join(lines)

    def _gen_node_answer(self, segs: dict, wf: WorkflowStatement) -> str:
        """AnswerNode — GENERATE AnswerQuestion + RETURN (handles both exit paths)."""
        # Prefer WHEN branch (clean exit); fall back to post stmts (max_iterations path)
        gen = next(
            (s for s in segs["when_stmts"] if isinstance(s, GenerateIntoStatement)),
            None,
        )
        if gen is None:
            gen = next(
                (s for s in segs["post"] if isinstance(s, GenerateIntoStatement)),
                None,
            )
        target = self._key(gen.target_variable) if gen else "answer"
        inp_keys = [self._key(p.name) for p in wf.inputs]

        fn_name = gen.generate_clause.function_name if gen else "Answer"
        lines = [
            "class AnswerNode(Node):",
            f"    # SPL: GENERATE {fn_name}(...) INTO @{target} + RETURN",
            "",
            "    def prep(self, shared):",
            "        # Extract — original question and full research context",
        ]
        for k in inp_keys:
            lines.append(f'        {k} = shared["{k}"]')
        lines.append('        context = shared.get("context", "")')
        ret_vars = inp_keys + ["context"]
        lines.append(f"        return {', '.join(ret_vars)}")

        lines += [
            "",
            "    def exec(self, prep_res):",
            "        # Transform — synthesize final answer from all gathered research",
        ]
        if gen:
            gc = gen.generate_clause
            unpack = ", ".join(inp_keys + ["context"])
            lines.append(f"        {unpack} = prep_res")
            lines.append(f'        print("Generating final answer ...")')
            arg_locals = [
                self._key(a.name) if isinstance(a, ParamRef) else self._expr_local(a)
                for a in gc.arguments
            ]
            lines.append(
                f"        return _call_llm({self._model_expr_local(gc.model)}, "
                f"{self._prompt_fmt(gc.function_name, gc.arguments, arg_locals)})"
            )
        else:
            lines.append('        return ""')

        lines += [
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — write answer and print status",
            f'        shared["{target}"] = exec_res',
            '        i = shared.get("iteration", 0)',
            '        max_i = shared.get("max_iterations", 3)',
            '        status = "complete" if i < max_i else "max_iterations"',
            '        print(f"\\nStatus:     {status}")',
            '        print(f"Iterations: {i}")',
            '        print(f"\\n{exec_res}")',
            '        shared["status"] = status',
            '        return None',
        ]
        return "\n".join(lines)

    def _gen_build_flow_react(self, wf: WorkflowStatement) -> str:
        return '''\
# ── Flow wiring  (mirrors WORKFLOW control flow) ─────────────────────────────
# SPL:  WHILE loop → GENERATE DecideAction → EVALUATE → answer or search
#
# PocketFlow conditional edges via post() return value (action string):
#   decide.post() → "answer"  (EVALUATE contains match OR max_iterations guard)
#   decide.post() → "search"  (else branch — external tool call needed)
#   search.post() → "decide"  (WHILE back-edge — loop continues)

def build_flow() -> Flow:
    decide = DecideNode()
    search = SearchNode()
    answer = AnswerNode()

    # SPL: EVALUATE exit condition → answer
    decide - "answer" >> answer

    # SPL: ELSE branch → search tool call
    decide - "search" >> search

    # SPL: WHILE back-edge — search → decide
    search - "decide" >> decide

    return Flow(start=decide)'''

    # ── self_refine node generators (Phase 1 — unchanged) ────────────────────

    def _gen_node_draft(self, init_stmts, wf) -> str:
        gen = next((s for s in init_stmts if isinstance(s, GenerateIntoStatement)), None)
        iter_init = next(
            (s for s in init_stmts
             if isinstance(s, AssignmentStatement) and self._key(s.variable) == "iteration"),
            None,
        )
        target = self._key(gen.target_variable) if gen else "current"

        lines = [
            "class DraftNode(Node):",
            f"    # SPL: initial GENERATE {gen.generate_clause.function_name}(...)"
            f" INTO @{target}" if gen else "    # SPL: initial draft",
            "",
            "    def prep(self, shared):",
            "        # Extract — pull INPUT vars from shared store",
        ]
        for p in wf.inputs:
            k = self._key(p.name)
            lines.append(f'        {k} = shared["{k}"]')
        inp_keys = [self._key(p.name) for p in wf.inputs]
        lines.append(f'        return {", ".join(inp_keys) if len(inp_keys) > 1 else (inp_keys[0] if inp_keys else "None")}')

        lines += [
            "",
            "    def exec(self, prep_res):",
            "        # Transform — LLM call",
        ]
        if gen:
            gc = gen.generate_clause
            if len(wf.inputs) > 1:
                lines.append(f"        {', '.join(inp_keys)} = prep_res")
            else:
                lines.append(f"        {inp_keys[0] if inp_keys else 'task'} = prep_res")
            lines.append(f'        print("Generating initial draft ...")')
            lines.append(
                f"        return _call_llm({self._model_expr_local(gc.model)}, "
                f"{self._prompt_fmt(gc.function_name, gc.arguments, inp_keys)})"
            )
        else:
            lines.append('        return ""')

        lines += [
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — write results back to shared store",
            f'        shared["{target}"] = exec_res',
        ]
        if iter_init:
            lines.append(f'        shared["iteration"] = {self._expr_shared(iter_init.expression)}')

        for s in init_stmts:
            if isinstance(s, CallStatement) and s.procedure_name == "write_file":
                args = self._write_args_shared(s.arguments)
                lines.append(f"        _write({', '.join(args)})")
            elif isinstance(s, LoggingStatement):
                lines.append(f"        {self._log_shared(s)}")

        lines.append('        return "critique"')
        return "\n".join(lines)

    def _gen_node_critique(self, pre_eval_stmts, wf) -> str:
        call = next(
            (s for s in pre_eval_stmts
             if isinstance(s, CallStatement) and s.procedure_name in self.sub_workflows),
            None,
        )
        gen = next(
            (s for s in pre_eval_stmts if isinstance(s, GenerateIntoStatement)),
            None,
        )
        target = "feedback"
        if call and call.target_variable:
            target = self._key(call.target_variable)
        elif gen:
            target = self._key(gen.target_variable)

        eval_stmt = self._find_evaluate(wf)
        match_str = None
        if eval_stmt:
            for wc in eval_stmt.when_clauses:
                if isinstance(wc.condition, SemanticCondition):
                    sem = wc.condition.semantic_value
                    if sem.startswith("contains:"):
                        match_str = sem[len("contains:"):]

        while_stmt = self._find_while(wf)
        max_iter_key = None
        iter_key = "iteration"
        if while_stmt and hasattr(while_stmt.condition, "right"):
            max_iter_key = self._key(
                while_stmt.condition.right.name
                if isinstance(while_stmt.condition.right, ParamRef)
                else str(while_stmt.condition.right)
            )

        critique_gen = gen
        if critique_gen is None and call:
            sub_wf = self.sub_workflows.get(call.procedure_name)
            if sub_wf:
                critique_gen = next(
                    (s for s in sub_wf.body if isinstance(s, GenerateIntoStatement)), None
                )
        model_field = critique_gen.generate_clause.model if critique_gen else None
        model_is_var = model_field is not None and (
            (isinstance(model_field, str) and model_field.startswith("@"))
            or isinstance(model_field, ParamRef)
        )
        model_key = self._key(model_field.name if isinstance(model_field, ParamRef) else model_field) if model_is_var else None

        prep_return = (
            f'return shared["current"], shared.get("iteration", 0), shared.get("{model_key}", "llama3.2")'
            if model_is_var
            else 'return shared["current"], shared.get("iteration", 0)'
        )
        exec_unpack = "current, _, model = prep_res" if model_is_var else "current, _ = prep_res"
        post_unpack = "_, i, _ = prep_res" if model_is_var else "_, i = prep_res"

        lines = [
            "class CritiqueNode(Node):",
            f'    # SPL: GENERATE critique(@current) INTO @{target}',
            f'    # post() mirrors EVALUATE @{target} WHEN contains("{match_str}") + WHILE guard',
            "",
            "    def prep(self, shared):",
            '        # Extract — pull current draft, iteration counter, and model',
            f'        {prep_return}',
            "",
            "    def exec(self, prep_res):",
            "        # Transform — LLM critique call",
            f"        {exec_unpack}",
        ]

        if call:
            sub_wf = self.sub_workflows.get(call.procedure_name)
            if sub_wf:
                for sub_s in sub_wf.body:
                    if isinstance(sub_s, GenerateIntoStatement):
                        gc = sub_s.generate_clause
                        model_arg = "model" if model_is_var else self._model_expr_local(gc.model)
                        lines.append(f'        print("Critiquing current draft ...")')
                        lines.append(
                            f"        return _call_llm({model_arg}, "
                            f'CRITIQUE_PROMPT.format(current=current))'
                        )
                        break
        elif gen:
            gc = gen.generate_clause
            model_arg = "model" if model_is_var else self._model_expr_local(gc.model)
            lines.append(f'        print("Critiquing current draft ...")')
            lines.append(
                f"        return _call_llm({model_arg}, "
                f"{self._prompt_fmt(gc.function_name, gc.arguments, ['current'])})"
            )
        else:
            lines.append('        return ""')

        lines += [
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — save feedback; route based on EVALUATE + WHILE guard",
            f'        shared["{target}"] = exec_res',
            f"        {post_unpack}",
        ]

        for s in pre_eval_stmts:
            if isinstance(s, CallStatement) and s.procedure_name == "write_file":
                lines.append(
                    f"        _write({', '.join(self._write_args_shared(s.arguments))})"
                    .replace('shared["feedback"]', 'exec_res')
                    .replace("shared['feedback']", 'exec_res')
                    .replace('shared["iteration"]', 'i')
                    .replace("shared['iteration']", 'i')
                )
            elif isinstance(s, LoggingStatement):
                lines.append(f"        {self._log_shared(s)}")

        if match_str:
            lines.append(f'        if {repr(match_str)} in exec_res:')
            lines.append(f'            print(f"Approved at iteration {{i}}")')
            lines.append('            return "commit"')

        if max_iter_key:
            lines.append(
                f'        if i >= shared.get("{max_iter_key}", {self._default_for(max_iter_key, wf)}):'
            )
            lines.append(f'            print(f"Max iterations reached | iterations={{i}}")')
            lines.append('            return "commit"')

        lines.append('        return "refine"')
        return "\n".join(lines)

    def _gen_node_refine(self, else_stmts, wf) -> str:
        gen = next((s for s in else_stmts if isinstance(s, GenerateIntoStatement)), None)
        iter_assign = next(
            (s for s in else_stmts
             if isinstance(s, AssignmentStatement) and self._key(s.variable) == "iteration"),
            None,
        )
        target = self._key(gen.target_variable) if gen else "current"

        model_field = gen.generate_clause.model if gen else None
        model_is_var = model_field is not None and (
            (isinstance(model_field, str) and model_field.startswith("@"))
            or isinstance(model_field, ParamRef)
        )
        model_key = self._key(model_field.name if isinstance(model_field, ParamRef) else model_field) if model_is_var else None

        prep_return = (
            f'return shared["current"], shared["feedback"], shared.get("iteration", 0), shared.get("{model_key}", "llama3.2")'
            if model_is_var
            else 'return shared["current"], shared["feedback"], shared.get("iteration", 0)'
        )
        exec_unpack = "current, feedback, _, model = prep_res" if model_is_var else "current, feedback, _ = prep_res"

        lines = [
            "class RefineNode(Node):",
            f"    # SPL: GENERATE refine(@current, @feedback) INTO @{target}",
            "",
            "    def prep(self, shared):",
            "        # Extract — pull current draft, feedback, iteration counter, and model",
            f'        {prep_return}',
            "",
            "    def exec(self, prep_res):",
            "        # Transform — LLM refinement call",
            f"        {exec_unpack}",
        ]

        if gen:
            gc = gen.generate_clause
            model_arg = "model" if model_is_var else self._model_expr_local(gc.model)
            lines.append(f'        print("Refining draft ...")')
            lines.append(
                f"        return _call_llm({model_arg}, "
                f"{self._prompt_fmt(gc.function_name, gc.arguments, ['current', 'feedback'])})"
            )
        else:
            lines.append('        return current')

        lines += [
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — update draft and increment iteration counter",
            f'        shared["{target}"] = exec_res',
        ]

        if iter_assign:
            lines.append(f'        shared["iteration"] = prep_res[2] + 1')

        for s in else_stmts:
            if isinstance(s, CallStatement) and s.procedure_name == "write_file":
                lines.append(
                    f"        _write({', '.join(self._write_args_shared(s.arguments))})"
                )
            elif isinstance(s, LoggingStatement):
                lines.append(f"        {self._log_shared(s)}")

        lines.append('        return "critique"')
        return "\n".join(lines)

    def _gen_node_commit(self, when_stmts, post_stmts, wf) -> str:
        lines = [
            "class CommitNode(Node):",
            "    # SPL: RETURN @current WITH status, iterations",
            "",
            "    def prep(self, shared):",
            '        return shared.get("current", ""), shared.get("iteration", 0), shared.get("feedback", "")',
            "",
            "    def exec(self, prep_res):",
            "        return prep_res",
            "",
            "    def post(self, shared, prep_res, exec_res):",
            "        # Load — write final output and log status",
            "        current, i, feedback = exec_res",
        ]

        all_stmts = list(when_stmts) + list(post_stmts)
        written = False
        for s in all_stmts:
            if isinstance(s, CallStatement) and s.procedure_name == "write_file" and not written:
                lines.append(
                    f"        _write({', '.join(self._write_args_shared(s.arguments))})"
                )
                written = True

        lines += [
            '        approved = shared.get("feedback", "") and "[APPROVED]" in shared.get("feedback", "")',
            '        status = "complete" if approved else "max_iterations"',
            '        print(f"\\nStatus:     {status}")',
            '        print(f"Iterations: {i}")',
            '        print(f"\\n{current}")',
            '        shared["status"] = status',
            '        return None',
        ]
        return "\n".join(lines)

    # ── Entry point generator ─────────────────────────────────────────────────

    def _gen_main(self, wf: WorkflowStatement) -> str:
        segs = self._segment_body(wf)
        lines = [
            "# ── Entry point  (SPL: built into CLI — `spl3 run ...`) "
            "────────────────────────\n",
            "@click.command()",
        ]

        for p in wf.inputs:
            pname = self._key(p.name)
            flag = pname.replace("_", "-")
            ptype = self._py_type(p.param_type)
            default = self._py_default(p)
            if ptype == "int":
                lines.append(
                    f'@click.option("--{flag}", default={default},'
                    f" show_default=True, type=int)"
                )
            elif p.default_value is None:
                lines.append(f'@click.option("--{flag}", required=True)')
            else:
                lines.append(
                    f'@click.option("--{flag}", default={default}, show_default=True)'
                )

        sig = ", ".join(
            f"{self._key(p.name)}: {self._py_type(p.param_type)}" for p in wf.inputs
        )
        lines.append(f"def main({sig}):")
        lines.append("    # SPL: INPUT @vars → shared store (ETL staging area)")
        lines.append("    shared = {")
        for p in wf.inputs:
            k = self._key(p.name)
            lines.append(f'        "{k}": {k},')

        if self.pattern == "react":
            # Render init assignments from AST (e.g. @context := "..." + @question)
            init_keys: set[str] = set()
            for s in segs["init"]:
                if isinstance(s, AssignmentStatement):
                    key = self._key(s.variable)
                    val = self._expr_local(s.expression)
                    lines.append(f'        "{key}": {val},')
                    init_keys.add(key)
            # Ensure working vars are always present
            covered = {self._key(p.name) for p in wf.inputs} | init_keys
            for k in ("decision", "search_results", "answer"):
                if k not in covered:
                    lines.append(f'        "{k}": "",')
        elif self.pattern == "self_refine":
            lines.append('        "iteration": 0,')
            lines.append('        "current": "",')
            lines.append('        "feedback": "",')
        # linear: no extra shared vars needed beyond inputs

        lines.append("    }")
        lines.append("    build_flow().run(shared)")

        lines += [
            "",
            "",
            'if __name__ == "__main__":',
            "    main()",
        ]
        return "\n".join(lines)

    # ── Body segmentation ─────────────────────────────────────────────────────

    def _segment_body(self, wf: WorkflowStatement) -> dict:
        """Split workflow body into: init / pre_eval / when_stmts / else_stmts / post."""
        stmts = wf.body
        init: list = []
        pre_eval: list = []
        when_stmts: list = []
        else_stmts: list = []
        post: list = []

        while_stmt = None
        found_while = False
        for s in stmts:
            if isinstance(s, WhileStatement):
                while_stmt = s
                found_while = True
            elif not found_while:
                init.append(s)
            else:
                post.append(s)

        if while_stmt is not None:
            eval_stmt = None
            for s in while_stmt.body:
                if isinstance(s, EvaluateStatement):
                    eval_stmt = s
                    break
                pre_eval.append(s)

            if eval_stmt is not None:
                for wc in eval_stmt.when_clauses:
                    when_stmts.extend(wc.statements)
                if eval_stmt.else_statements:
                    else_stmts.extend(eval_stmt.else_statements)

        return {
            "init":       init,
            "pre_eval":   pre_eval,
            "when_stmts": when_stmts,
            "else_stmts": else_stmts,
            "post":       post,
        }

    # ── AST navigation helpers ────────────────────────────────────────────────

    def _find_while(self, wf: WorkflowStatement):
        return next((s for s in wf.body if isinstance(s, WhileStatement)), None)

    def _find_evaluate(self, wf: WorkflowStatement):
        ws = self._find_while(wf)
        if ws:
            return next((s for s in ws.body if isinstance(s, EvaluateStatement)), None)
        return None

    def _default_for(self, key: str, wf: WorkflowStatement) -> str:
        """Find the default value for an INPUT parameter by key name."""
        for p in wf.inputs:
            if self._key(p.name) == key and p.default_value is not None:
                return self._expr_shared(p.default_value)
        return "3"

    # ── Expression rendering ──────────────────────────────────────────────────

    def _key(self, var_name: str) -> str:
        return var_name.lstrip("@")

    def _expr_shared(self, expr) -> str:
        """Convert SPL expression to Python — uses shared["x"] for @vars."""
        if isinstance(expr, ParamRef):
            return f'shared["{self._key(expr.name)}"]'
        if isinstance(expr, str):
            if expr.startswith("@"):
                return f'shared["{self._key(expr)}"]'
            return repr(expr)
        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                return repr(expr.value)
            return str(expr.value)
        if isinstance(expr, NoneLiteral):
            return "None"
        if isinstance(expr, FStringLiteral):
            return self._fstr_shared(expr.template)
        if hasattr(expr, "op"):
            left = self._expr_shared(expr.left)
            right = self._expr_shared(expr.right)
            return f"{left} {expr.op} {right}"
        if hasattr(expr, "operator") and hasattr(expr, "left") and hasattr(expr, "right"):
            left = self._expr_shared(expr.left)
            right = self._expr_shared(expr.right)
            return f"{left} {expr.operator} {right}"
        if isinstance(expr, UnaryOp):
            return f"not ({self._expr_shared(expr.operand)})"
        if isinstance(expr, CompoundCondition):
            left = self._expr_shared(expr.left)
            right = self._expr_shared(expr.right)
            op = "and" if expr.operator == "AND" else "or"
            return f"({left} {op} {right})"
        return f"# TODO: {type(expr).__name__}"

    def _expr_local(self, expr) -> str:
        """Convert SPL expression to Python — uses local var names (for main() init)."""
        if isinstance(expr, ParamRef):
            return self._key(expr.name)
        if isinstance(expr, str):
            if expr.startswith("@"):
                return self._key(expr)
            return repr(expr)
        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                return repr(expr.value)
            return str(expr.value)
        if isinstance(expr, NoneLiteral):
            return "None"
        if isinstance(expr, FStringLiteral):
            return self._fstr_local(expr.template)
        if hasattr(expr, "op"):
            left = self._expr_local(expr.left)
            right = self._expr_local(expr.right)
            return f"{left} {expr.op} {right}"
        if hasattr(expr, "operator") and hasattr(expr, "left") and hasattr(expr, "right"):
            left = self._expr_local(expr.left)
            right = self._expr_local(expr.right)
            return f"({left} {expr.operator} {right})"
        return self._expr_shared(expr)  # fallback

    def _fstr_shared(self, template: str) -> str:
        """'{@log_dir}/draft_{@iteration}.md' → f\"{shared['log_dir']}/draft_{shared['iteration']}.md\""""
        result = re.sub(r"\{@(\w+)\}", r"""{shared['\1']}""", template)
        result = result.replace('"', '\\"')
        result = result.replace('\n', '\\n')
        return f'f"{result}"'

    def _fstr_local(self, template: str) -> str:
        """'{@question} ...' → f\"{question} ...\""""
        result = re.sub(r"\{@(\w+)\}", r"{\1}", template)
        result = result.replace('"', '\\"')
        return f'f"{result}"'

    def _model_expr(self, model_field) -> str:
        """Model expression for post()/shared context."""
        if model_field is None:
            return '"llama3.2"'
        if isinstance(model_field, str):
            if model_field.startswith("@"):
                return f'shared["{self._key(model_field)}"]'
            return repr(model_field)
        return self._expr_shared(model_field)

    def _model_expr_local(self, model_field) -> str:
        """Model expression for exec() context — uses local variable, not shared dict."""
        if model_field is None:
            return '"llama3.2"'
        if isinstance(model_field, str):
            if model_field.startswith("@"):
                return self._key(model_field)
            return repr(model_field)
        if isinstance(model_field, ParamRef):
            return self._key(model_field.name)
        return self._model_expr(model_field)

    def _prompt_fmt(self, fn_name: str, arguments: list, local_vars: list[str]) -> str:
        """FN_PROMPT.format(param=local_var) — uses local variables from prep_res."""
        const = fn_name.upper() + "_PROMPT"
        params = self.fn_params.get(fn_name, [])
        if not params:
            return f"{const}.format({', '.join(local_vars[:len(arguments)])})"
        kv = []
        for idx, param in enumerate(params):
            val = local_vars[idx] if idx < len(local_vars) else '""'
            kv.append(f"{param.name}={val}")
        return f"{const}.format({', '.join(kv)})"

    def _write_args_shared(self, arguments: list) -> list[str]:
        return [
            self._fstr_shared(a.template) if isinstance(a, FStringLiteral)
            else self._expr_shared(a)
            for a in arguments
        ]

    def _log_shared(self, stmt: LoggingStatement) -> str:
        expr = stmt.expression
        if isinstance(expr, FStringLiteral):
            return f"print({self._fstr_shared(expr.template)})"
        if isinstance(expr, Literal):
            return f"print({repr(str(expr.value))})"
        return f"print({self._expr_shared(expr)})"

    # ── Type / default helpers ────────────────────────────────────────────────

    def _py_type(self, param_type: str) -> str:
        if param_type is None:
            return "str"
        t = param_type.upper()
        if t in ("INTEGER", "INT"):
            return "int"
        if t in ("FLOAT", "REAL"):
            return "float"
        if t in ("BOOL", "BOOLEAN"):
            return "bool"
        return "str"

    def _py_default(self, param) -> str:
        if param.default_value is None:
            return "None"
        return self._expr_shared(param.default_value)
