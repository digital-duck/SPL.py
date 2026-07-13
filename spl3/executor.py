"""SPL 3.0 Executor — extends SPL 2.0 executor with new type system support.

New capabilities over SPL 2.0:
  - NoneLiteral (NONE / NULL)  →  evaluates to '' (empty string, consistent
                                  with undefined variables in the string store)
  - SetLiteral                 →  serializes as sorted, deduplicated JSON array
  - INT / INTEGER param type   →  INPUT params coerced via int(float(x))
  - FLOAT param type           →  INPUT params coerced via float(x)
  - IMAGE / AUDIO / VIDEO      →  when a GENERATE function has an IMAGE-typed
                                  param, the executor encodes the file/URL via
                                  spl3.codecs.encode_image() and calls
                                  adapter.generate_multimodal() instead of
                                  adapter.generate().  Workflow INPUT params of
                                  these types are still passed through as-is.
  - CallParallelStatement      →  dispatches branches via WorkflowComposer
  - ToolAPINode                →  CREATE TOOL_API ... AS PYTHON $$ ... $$
                                  exec()d into KernelSession (or fallback dict) at
                                  load time, registered in executor's tool table
  - SolveStatement             →  SOLVE @var [TYPE] := python_expr
                                  sends expression to IPython kernel, assigns str
                                  representation of result to @var
  - AssertStatement            →  ASSERT python_expr [OTHERWISE <body>]
                                  sends bool(expr) to kernel; executes otherwise_body
                                  (or raises ToolFailed) when result is falsy

SPL 2.0 backward compatibility is fully preserved.
"""

from __future__ import annotations

import json
import logging
import re

_log = logging.getLogger("spl.executor")

from spl.executor import Executor as SPL2Executor

from spl.ast_nodes import Condition, NamedArg
from spl3.ast_nodes import (
    NoneLiteral, SetLiteral, CallParallelStatement, UnaryOp, CompoundCondition,
    ToolAPINode, SolveStatement, AssertStatement, ImportMCPStatement,
)
from spl3.types import coerce_to_int, coerce_to_float


# Types that receive numeric coercion in workflow INPUT init
_INT_TYPES   = {"INT", "INTEGER"}
_FLOAT_TYPES = {"FLOAT"}


def _builtin_clean_code(text: str) -> str:
    """Remove common LLM output artifacts from generated code.

    Currently handles:
      - Markdown fences  (```python ... ``` or ``` ... ```)
      - Prose preamble before the first fence (e.g. "Here is the code:\n```python\n...")
      - Leading / trailing blank lines

    Future candidates: shebang lines, stray prose commentary,
    indentation normalisation, BOM stripping.
    """
    text = text.strip()
    # If there is a fenced code block anywhere, extract just its content.
    # This handles prose preamble that precedes the fence.
    m = re.search(r'```[^\n]*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: no fences found — strip any stray fence markers and return.
    text = re.sub(r'```[^\n]*\n?', '', text)
    text = re.sub(r'\n?```', '', text)
    return text.strip()


class SPL3Executor(SPL2Executor):
    """SPL 3.0 executor, extending SPL 2.0 with the extended type system."""

    def __init__(self, *args, kernel: bool = False, kernel_scope: str = "session",
                 kernel_timeout: float = 60.0, kernel_name: str = "python3",
                 persistence=None, workflow_id: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.functions._builtins["clean_code"] = lambda text: _builtin_clean_code(str(text))

        # IPython kernel — lazy start on first run_python call
        self._kernel_enabled = kernel
        self._kernel: "IPythonKernel | None" = None
        if kernel:
            from spl3.kernel import IPythonKernel
            self._kernel = IPythonKernel(scope=kernel_scope, timeout=kernel_timeout,
                                         kernel_name=kernel_name)
            self._register_run_python()

        # MCP server pool — lazily created on first AS MCP or IMPORT MCP
        self._mcp_pool: "MCPServerPool | None" = None

        # Persistence backend for durable execution (sqlite, postgres, dbos)
        self._persistence = persistence
        self._workflow_id = workflow_id
        self._step_counter: int = 0      # global across parent + all sub-workflows
        self._persistence_started: bool = False   # guards top-level-only lifecycle
        if persistence is not None:
            self._register_hitl_tools()

    def _register_run_python(self) -> None:
        """Register run_python(@code) as a synchronous @spl_tool."""
        kernel = self._kernel

        def run_python(code: str) -> str:
            from spl.executor import ToolFailed
            from spl3.kernel import KernelExecutionError
            try:
                return kernel.execute(str(code))
            except KernelExecutionError as e:
                raise ToolFailed(f"run_python kernel error: {e}") from e
            except TimeoutError as e:
                raise ToolFailed(f"run_python timeout: {e}") from e

        self.functions.register_tool("run_python", run_python)
        _log.info("IPython kernel registered: CALL run_python(@code) INTO @result")

    def _register_hitl_tools(self) -> None:
        """Register wait_for_approval / send_approval as built-in CALL targets."""
        persistence = self._persistence

        async def wait_for_approval(workflow_id: str, event_key: str,
                                    timeout_seconds: str = "") -> str:
            t = float(timeout_seconds) if timeout_seconds else None
            return await persistence.wait_for_event(workflow_id, event_key, t)

        async def send_approval(workflow_id: str, event_key: str, value: str) -> str:
            await persistence.send_event(workflow_id, event_key, value)
            return "sent"

        self.functions.register_tool("wait_for_approval", wait_for_approval)
        self.functions.register_tool("send_approval", send_approval)
        _log.info("HITL tools registered: wait_for_approval / send_approval")

    def close(self) -> None:
        """Shut down the IPython kernel (if running) then delegate to SPL 2.0 close."""
        if self._kernel is not None and self._kernel.is_running:
            self._kernel.shutdown()
        super().close()

    # ------------------------------------------------------------------ #
    # Statement dispatch — routes SPL 3.0 statement types to handlers     #
    # ------------------------------------------------------------------ #

    async def _execute_statement(self, stmt, state) -> None:
        """Override base dispatch to handle SPL 3.0 statement types.

        Handles:
          SolveStatement        → _exec_solve
          AssertStatement       → _exec_assert
          CallParallelStatement → _execute_call_parallel
          Everything else       → SPL 2.0 base dispatch
        """
        if isinstance(stmt, SolveStatement):
            await self._exec_solve(stmt, state)
        elif isinstance(stmt, AssertStatement):
            await self._exec_assert(stmt, state)
        elif isinstance(stmt, CallParallelStatement):
            await self._execute_call_parallel(stmt, state)
        else:
            await super()._execute_statement(stmt, state)

    # ------------------------------------------------------------------ #
    # SOLVE / ASSERT — kernel-routed deterministic constructs             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _resolve_python_template(template: str, state) -> str:
        """Substitute @@varname@@ markers with values from workflow state.

        Parser writes @var as @@varname@@ in the template; this method
        replaces each marker with state.get_var(varname).
        """
        import re
        return re.sub(r'@@(\w+)@@', lambda m: state.get_var(m.group(1)), template)

    async def _exec_solve(self, stmt: SolveStatement, state) -> None:
        """Execute SOLVE @var [TYPE] := python_template via the IPython kernel.

        Substitutes @@varname@@ markers, wraps the expression in a
        _spl_solve_result = ...; print(str(_spl_solve_result)) pattern,
        sends to the kernel, and assigns the printed output to @var.
        """
        if self._kernel is None:
            from spl.executor import ToolFailed
            raise ToolFailed(
                "SOLVE requires --kernel flag; run with 'spl3 run --kernel ...'"
            )
        code = self._resolve_python_template(stmt.python_template, state)
        kernel_code = (
            f"_spl_solve_result = {code}\n"
            f"print(str(_spl_solve_result))"
        )
        from spl.executor import ToolFailed
        from spl3.kernel import KernelExecutionError
        try:
            result = self._kernel.execute(kernel_code)
        except KernelExecutionError as e:
            raise ToolFailed(f"SOLVE kernel error: {e}") from e
        except TimeoutError as e:
            raise ToolFailed(f"SOLVE timeout: {e}") from e

        state.set_var(stmt.target_variable, result.strip())
        _log.info("SOLVE @%s := %s -> %r", stmt.target_variable, code, result.strip())

    async def _exec_assert(self, stmt: AssertStatement, state) -> None:
        """Execute ASSERT python_template [OTHERWISE ...].

        Two execution paths:
        - Kernel present: send to IPython kernel (symbolic / SOLVE context).
        - No kernel: eval in a namespace of registered tools + builtins.
          Safe for TOOL_API predicates (e.g. ASSERT is_optimal(@solution)).

        If the result is falsy, executes otherwise_body; if otherwise_body is
        empty, raises ToolFailed (assertion failure).
        """
        from spl.executor import ToolFailed

        code = self._resolve_python_template(stmt.python_template, state)

        if self._kernel is None:
            # Kernel-free path: eval with tools namespace.
            # Covers TOOL_API predicates without requiring --kernel.
            # Use repr()-quoted substitution so state values become proper
            # Python string literals (not bare JSON/dict literals).
            import re as _re
            code = _re.sub(
                r'@@(\w+)@@',
                lambda m: repr(state.get_var(m.group(1))),
                stmt.python_template,
            )
            ns: dict = {}
            ns.update(self.functions._builtins)
            ns.update(self.functions._tools)
            try:
                passed = bool(eval(code, ns))  # noqa: S307
            except Exception as e:
                raise ToolFailed(f"ASSERT eval error: {e}") from e
            _log.info("ASSERT (tools-eval) %s -> %s", code, passed)
        else:
            # Kernel path: symbolic / math expressions in IPython context.
            kernel_code = (
                f"_spl_assert_result = bool({code})\n"
                f"print(_spl_assert_result)"
            )
            from spl3.kernel import KernelExecutionError
            try:
                result = self._kernel.execute(kernel_code)
            except KernelExecutionError as e:
                raise ToolFailed(f"ASSERT kernel error: {e}") from e
            except TimeoutError as e:
                raise ToolFailed(f"ASSERT timeout: {e}") from e
            passed = result.strip() == "True"
            _log.info("ASSERT %s -> %s", code, passed)

        if not passed:
            if stmt.otherwise_body:
                await self._execute_body(stmt.otherwise_body, state)
            else:
                raise ToolFailed(
                    f"ASSERT failed: {code!r} returned False"
                )

    # ------------------------------------------------------------------ #
    # Expression evaluation                                                #
    # ------------------------------------------------------------------ #

    def _eval_expression(self, expr, state) -> str:
        """Evaluate an expression to a string value.

        Handles SPL 3.0 additions before delegating to SPL 2.0:
          NoneLiteral  →  '' (empty string; same as undefined variable)
          SetLiteral   →  sorted, deduplicated JSON array string
        """
        # NOT <expr> — boolean negation
        if isinstance(expr, UnaryOp) and expr.operator == 'NOT':
            val = self._eval_expression(expr.operand, state)
            # Falsy values: '', '0', 'false', 'FALSE', 'False', 'none', 'null'
            falsy = val.strip().lower() in ('', '0', 'false', 'none', 'null')
            return 'true' if falsy else 'false'

        # NONE / NULL literal → empty string
        if isinstance(expr, NoneLiteral):
            return ""

        # SET literal → sorted, deduplicated JSON array
        if isinstance(expr, SetLiteral):
            elements = [self._eval_expression(e, state) for e in expr.elements]
            unique_sorted = sorted(set(elements))
            return json.dumps(unique_sorted)

        return super()._eval_expression(expr, state)

    # ------------------------------------------------------------------ #
    # WHILE condition evaluation                                            #
    # ------------------------------------------------------------------ #

    def _eval_while_cond(self, cond, state) -> bool:
        """Recursively evaluate a WHILE condition to bool.

        Handles SPL 3.0 additions:
          UnaryOp(NOT)      — boolean negation
          CompoundCondition — AND / OR of two sub-conditions
          Condition         — numeric comparison (delegated)
        Falls through to truthy string check for plain expressions.
        """
        if isinstance(cond, CompoundCondition):
            left_val  = self._eval_while_cond(cond.left,  state)
            right_val = self._eval_while_cond(cond.right, state)
            if cond.operator == 'AND':
                return left_val and right_val
            else:  # OR
                return left_val or right_val

        if isinstance(cond, UnaryOp) and cond.operator == 'NOT':
            return not self._eval_while_cond(cond.operand, state)

        if isinstance(cond, Condition):
            ls = self._eval_expression(cond.left,  state)
            rs = self._eval_expression(cond.right, state)
            try:
                return self._compare(float(ls), cond.operator, float(rs))
            except (ValueError, TypeError):
                if cond.operator == "=":
                    return ls == rs
                if cond.operator in ("!=", "<>"):
                    return ls != rs
                return False

        # Plain expression — truthy string check
        val = self._eval_expression(cond, state)
        return bool(val and val != '0' and val.lower() not in ('false', 'none', 'null'))

    async def _exec_while(self, stmt, state):
        """Override to use _eval_while_cond for SPL 3.0 compound conditions."""
        from spl.ast_nodes import SemanticCondition
        # Only intercept CompoundCondition and UnaryOp; delegate the rest to SPL 2.0
        if isinstance(stmt.condition, (CompoundCondition, UnaryOp)):
            iteration = 0
            max_iter  = stmt.max_iterations or self.DEFAULT_MAX_ITERATIONS
            while iteration < max_iter:
                if state.committed:
                    return
                if not self._eval_while_cond(stmt.condition, state):
                    break
                await self._execute_body(stmt.body, state)
                iteration += 1
            if iteration >= max_iter:
                from spl.exceptions import MaxIterationsReached
                raise MaxIterationsReached(
                    f"WHILE loop exceeded {max_iter} iterations"
                )
            return
        # SPL 2.0 handles Condition and SemanticCondition
        await super()._exec_while(stmt, state)


    # ------------------------------------------------------------------ #
    # GENERATE — multimodal dispatch for IMAGE/AUDIO/VIDEO-typed params   #
    # ------------------------------------------------------------------ #

    _MULTIMODAL_TYPES = {"IMAGE", "AUDIO", "VIDEO"}

    async def _exec_generate_into(self, stmt, state):
        """Persistence wrapper + multimodal dispatch for GENERATE statements.

        Persistence (opt-in):
          - Increments global step counter and checks cache for exactly-once.
          - Checkpoints after successful execution.

        Multimodal dispatch:
          - Delegates to generate_multimodal() when any param is IMAGE/AUDIO/VIDEO.
          - Falls through to SPL 2.0 for text-only workflows (zero overhead).
        """
        _pers = self._persistence
        _wfid = self._workflow_id
        step_idx: int | None = None
        step_name: str | None = None

        if _pers is not None and _wfid is not None:
            step_idx = self._step_counter
            self._step_counter += 1
            first_gc = stmt.generate_clause
            fn_name = getattr(first_gc, "function_name", step_idx) if first_gc else step_idx
            step_name = f"GENERATE:{fn_name}"
            cached = await _pers.get_step_result(_wfid, step_idx)
            if cached is not None:
                _log.info("Skipping step %d (%s) — cached", step_idx, step_name)
                if stmt.target_variable and stmt.target_variable not in ("NONE", "_"):
                    state.set_var(stmt.target_variable, cached)
                return

        await self._exec_generate_into_impl(stmt, state)

        if _pers is not None and _wfid is not None and step_idx is not None:
            tgt = stmt.target_variable
            result = state.get_var(tgt) if tgt and tgt not in ("NONE", "_") else ""
            await _pers.checkpoint(_wfid, step_idx, step_name or "", result,
                                   dict(state.variables))

    async def _exec_generate_into_impl(self, stmt, state):
        """Multimodal dispatch implementation (separated for persistence wrapping)."""
        first_gen = stmt.generate_clause
        if first_gen is None:
            return await super()._exec_generate_into(stmt, state)

        func_def = self.functions.get(first_gen.function_name)
        if not func_def:
            return await super()._exec_generate_into(stmt, state)

        mm_param_names = {
            p.name for p in func_def.parameters
            if (getattr(p, "param_type", None) or "").upper() in self._MULTIMODAL_TYPES
        }
        if not mm_param_names:
            return await super()._exec_generate_into(stmt, state)

        # ── Multimodal path ───────────────────────────────────────────────
        from spl3.codecs.image_codec import encode_image
        from spl3.codecs.audio_codec import encode_audio

        current_gen = first_gen
        last_content: str = ""
        segment_count = 0

        while current_gen is not None:
            segment_count += 1

            args_text = []
            for arg in current_gen.arguments:
                args_text.append(self._eval_expression(arg, state))

            if segment_count > 1 and not args_text:
                args_text = [last_content]

            # Resolve function def for this segment (may differ from first)
            seg_func_def = self.functions.get(current_gen.function_name)
            if seg_func_def:
                seg_mm_params = {
                    p.name: (getattr(p, "param_type", None) or "").upper()
                    for p in seg_func_def.parameters
                    if (getattr(p, "param_type", None) or "").upper() in self._MULTIMODAL_TYPES
                }
                prompt = seg_func_def.body
                media_parts = []
                for param, arg_val in zip(seg_func_def.parameters, args_text):
                    ptype = seg_mm_params.get(param.name)
                    if ptype == "IMAGE":
                        try:
                            media_parts.append(encode_image(arg_val))
                        except Exception as exc:
                            _log.warning("IMAGE encode failed for %s=%r: %s",
                                         param.name, arg_val, exc)
                    elif ptype == "AUDIO":
                        try:
                            media_parts.append(encode_audio(arg_val))
                        except Exception as exc:
                            _log.warning("AUDIO encode failed for %s=%r: %s",
                                         param.name, arg_val, exc)
                    else:
                        prompt = prompt.replace("{" + param.name + "}", arg_val)
            else:
                prompt = f"Task: {current_gen.function_name}\n\n"
                for i, arg_val in enumerate(args_text):
                    prompt += f"Input {i+1}:\n{arg_val}\n\n"
                media_parts = []

            if self.default_model:
                model = self.default_model
            elif "model" in state.current_overrides:
                model = state.current_overrides["model"]
            else:
                model = current_gen.model or ""
                if model.startswith("@"):
                    model = state.get_var(model[1:])

            budget = current_gen.output_budget
            if isinstance(budget, str) and budget.startswith("@"):
                budget = int(state.get_var(budget[1:]))
            max_tokens = int(budget) if budget else self.default_max_tokens

            temp = current_gen.temperature or 0.7
            if "temperature" in state.current_overrides:
                try:
                    temp = float(state.current_overrides["temperature"])
                except ValueError:
                    pass

            self._log_prompt(current_gen.function_name, model, prompt, max_tokens, temp)
            self._check_budget(state)

            if media_parts and hasattr(self.adapter, "generate_multimodal"):
                content = [{"type": "text", "text": prompt}] + media_parts
                gen_result = await self.adapter.generate_multimodal(
                    content,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temp,
                )
            else:
                gen_result = await self.adapter.generate(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temp,
                )

            state.record_llm_call(gen_result)
            last_content = gen_result.content

            _log.info("GENERATE segment %d (%s) -> %d tokens, %.0fms",
                      segment_count, current_gen.function_name,
                      gen_result.output_tokens, gen_result.latency_ms)

            current_gen = current_gen.next_segment

        if stmt.target_variable and stmt.target_variable not in ("NONE", "_"):
            if last_content:
                state.set_var(stmt.target_variable, last_content)
                _log.info("GENERATE chain done -> @%s (%d chars total)",
                          stmt.target_variable, len(last_content))
            else:
                _log.warning("GENERATE chain returned empty content for @%s — variable unchanged",
                             stmt.target_variable)
        else:
            _log.info("GENERATE chain done -> [DISCARDED] (%d chars)", len(last_content))

    # ------------------------------------------------------------------ #
    # CREATE TOOL_API — load and register before execution                 #
    # ------------------------------------------------------------------ #

    def _load_tool_apis(self, program) -> None:
        """Exec each CREATE TOOL_API body and register in the executor's tool table.

        When a KernelSession is active, bodies are exec()d into the kernel's
        shared namespace so tool definitions can import packages at definition
        time and reuse them across calls within the same run.

        When no kernel is active, bodies exec into an isolated dict (original
        behaviour) — the resulting callable is still registered correctly.

        Called once at the start of execute_program() before any WORKFLOW or
        PROMPT statement executes, so CALL dispatch can resolve tool names
        defined inline in the .spl file.
        """
        kernel = self._kernel
        for stmt in program.statements:
            if not isinstance(stmt, ToolAPINode):
                continue

            if stmt.runtime == "MCP":
                # MCP tools are loaded async in execute_program via _load_mcp_tool_apis
                continue

            if stmt.runtime != "PYTHON":
                _log.warning(
                    "CREATE TOOL_API '%s': runtime '%s' is not supported yet — skipped",
                    stmt.name, stmt.runtime,
                )
                continue

            # Only KernelSession (in-process) exposes define_tool; the
            # out-of-process IPythonKernel does not — TOOL_API bodies are
            # host-side callables, so they exec in-process either way.
            if kernel is not None and hasattr(kernel, "define_tool"):
                fn = kernel.define_tool(stmt.name, stmt.python_body)
            else:
                namespace: dict = {}
                try:
                    exec(compile(stmt.python_body, f"<tool_api:{stmt.name}>", "exec"), namespace)
                except Exception as exc:
                    raise RuntimeError(
                        f"CREATE TOOL_API '{stmt.name}': failed to compile/exec body — {exc}"
                    ) from exc

                fn = namespace.get(stmt.name)
                if fn is None:
                    raise RuntimeError(
                        f"CREATE TOOL_API '{stmt.name}': body must define a Python function "
                        f"named '{stmt.name}' at the top level."
                    )
                if not callable(fn):
                    raise RuntimeError(
                        f"CREATE TOOL_API '{stmt.name}': '{stmt.name}' in the body is not "
                        f"callable (got {type(fn).__name__})."
                    )

            self.register_tool(stmt.name, fn)
            _log.debug(
                "Registered TOOL_API '%s' -> %r (via %s)",
                stmt.name, fn, "kernel" if kernel else "exec",
            )

    def _ensure_mcp_pool(self):
        if self._mcp_pool is None:
            from spl3.mcp_bridge import MCPServerPool
            self._mcp_pool = MCPServerPool()
        return self._mcp_pool

    async def _load_mcp_tool(self, stmt: ToolAPINode) -> None:
        """Load a single CREATE TOOL_API ... AS MCP tool."""
        from spl3.mcp_bridge import parse_mcp_config, make_mcp_tool_callable

        config = parse_mcp_config(stmt.python_body)
        server_name = config.get("server", "")
        command = config.get("command", "")
        tool_name = config.get("tool", stmt.name)

        if not server_name or not command:
            raise RuntimeError(
                f"CREATE TOOL_API '{stmt.name}' AS MCP: "
                f"body must specify server and command"
            )

        pool = self._ensure_mcp_pool()
        handle = await pool.get_or_start(server_name, command)

        if tool_name not in handle.tool_names:
            raise RuntimeError(
                f"CREATE TOOL_API '{stmt.name}' AS MCP: "
                f"tool '{tool_name}' not found on server '{server_name}'. "
                f"Available: {', '.join(handle.tool_names)}"
            )

        fn = make_mcp_tool_callable(pool, server_name, tool_name)
        self.register_tool(stmt.name, fn)
        _log.debug("Registered MCP TOOL_API '%s' -> %s/%s", stmt.name, server_name, tool_name)

    async def _load_mcp_tool_apis(self, program) -> None:
        """Load all CREATE TOOL_API ... AS MCP blocks from the program."""
        for stmt in program.statements:
            if not isinstance(stmt, ToolAPINode):
                continue
            if stmt.runtime == "MCP":
                await self._load_mcp_tool(stmt)

    async def _load_mcp_imports(self, program) -> None:
        """Load all IMPORT MCP statements from the program."""
        from spl3.mcp_bridge import make_mcp_tool_callable

        for stmt in program.statements:
            if not isinstance(stmt, ImportMCPStatement):
                continue

            pool = self._ensure_mcp_pool()
            handle = await pool.get_or_start(stmt.server_name, stmt.command)

            for tool_name in handle.tool_names:
                if stmt.only and tool_name not in stmt.only:
                    continue
                if stmt.except_ and tool_name in stmt.except_:
                    continue

                reg_name = f"{stmt.prefix}_{tool_name}" if stmt.prefix else tool_name
                fn = make_mcp_tool_callable(pool, stmt.server_name, tool_name)
                self.register_tool(reg_name, fn)
                _log.debug(
                    "Registered MCP import '%s' -> %s/%s",
                    reg_name, stmt.server_name, tool_name,
                )

    async def execute_program(self, analysis, params=None):
        """Execute program, loading TOOL_API definitions before any workflow runs.

        Load order (later entries win on name collision):
          1. Library tools from ~/.spl/tool_apis/ (promoted shared libraries)
          2. MCP imports (IMPORT MCP statements)
          3. Inline TOOL_API blocks from the current .spl file (AS PYTHON or AS MCP)
        """
        # 1. Load promoted TOOL_API libraries from registry (~/.spl/tool_apis/)
        try:
            from spl3.tool_api_registry import load_all_into_executor
            n = load_all_into_executor(self)
            if n:
                _log.debug("Loaded %d TOOL_API library file(s) from registry", n)
        except Exception as exc:
            _log.warning("TOOL_API registry load failed (non-fatal): %s", exc)

        # 2. MCP imports (IMPORT MCP statements)
        await self._load_mcp_imports(analysis.ast)

        # 3. Inline TOOL_API blocks: AS PYTHON (sync) + AS MCP (async)
        self._load_tool_apis(analysis.ast)
        await self._load_mcp_tool_apis(analysis.ast)

        try:
            return await super().execute_program(analysis, params=params)
        finally:
            if self._mcp_pool is not None:
                await self._mcp_pool.shutdown()

    # ------------------------------------------------------------------ #
    # Workflow execution — typed INPUT param coercion                     #
    # ------------------------------------------------------------------ #

    async def execute_workflow(self, stmt, params=None):
        """Execute a WORKFLOW statement with SPL 3.0 type coercion and optional
        persistence lifecycle.

        Type coercion (always active):
          INT / INTEGER  →  int(float(value))   (handles '42', '42.0', etc.)
          FLOAT          →  float(value)
          IMAGE/AUDIO/VIDEO → pass through unchanged (file path / data URI)

        Persistence lifecycle (opt-in via --persistence flag, top-level only):
          - Calls start_workflow on first run, or resumes from saved checkpoint.
          - Sub-workflow CALL invocations reuse the same executor and bypass
            this block via the _persistence_started guard.
        """
        # --- Type coercion ---
        if params and stmt.inputs:
            params = dict(params)  # don't mutate caller's dict
            for inp in stmt.inputs:
                ptype = (inp.param_type or "").upper()
                if inp.name not in params:
                    continue
                if ptype in _INT_TYPES:
                    try:
                        params[inp.name] = str(coerce_to_int(str(params[inp.name])))
                    except ValueError as e:
                        _log.warning("INT coercion failed for %s: %s", inp.name, e)
                elif ptype in _FLOAT_TYPES:
                    try:
                        params[inp.name] = str(coerce_to_float(str(params[inp.name])))
                    except ValueError as e:
                        _log.warning("FLOAT coercion failed for %s: %s", inp.name, e)

        # --- Persistence lifecycle (top-level only) ---
        if self._persistence is None or self._workflow_id is None or self._persistence_started:
            return await super().execute_workflow(stmt, params=params)

        self._persistence_started = True
        wf_id = self._workflow_id
        wf_name = getattr(stmt, "name", "workflow")
        saved_vars = await self._persistence.start_workflow(wf_id, wf_name, params or {})

        if saved_vars:
            _log.info("Resuming %s from checkpoint (%d vars)", wf_id, len(saved_vars))
            merged = dict(params or {})
            merged.update(saved_vars)
            params = merged

        try:
            result = await super().execute_workflow(stmt, params=params)
            status = getattr(result, "status", "complete") if result else "complete"
            value = getattr(result, "content", str(result)) if result else ""
            await self._persistence.finish_workflow(wf_id, value, status)
            return result
        except Exception as exc:
            await self._persistence.finish_workflow(wf_id, str(exc), "error")
            raise

    # ------------------------------------------------------------------ #
    # Sub-workflow CALL argument resolution                                 #
    # ------------------------------------------------------------------ #

    def _resolve_sub_workflow_args(self, arguments, param_names, state) -> dict[str, str]:
        """Bind CALL arguments to a sub-workflow's INPUT parameter names.

        Named args (key=value) bind directly by name; positional args fill
        the remaining parameter slots in declaration order. Mirrors the
        SPL 2.0 procedure-binding rule in spl.executor (named_args /
        positional_args) — without this, `f(a, k1=v1, k2=v2)` would bind
        v1/v2 to whatever parameters happen to sit at indices 1/2,
        regardless of the keyword names actually used.
        """
        named_args = {a.name: a.value for a in arguments if isinstance(a, NamedArg)}
        positional_args = [a for a in arguments if not isinstance(a, NamedArg)]

        args: dict[str, str] = {}
        pos_idx = 0
        for param_name in param_names:
            if param_name in named_args:
                args[param_name] = self._eval_expression(named_args[param_name], state)
            elif pos_idx < len(positional_args):
                args[param_name] = self._eval_expression(positional_args[pos_idx], state)
                pos_idx += 1

        # Fall back to arg0, arg1, ... for any leftover positional args beyond
        # the known parameter list (keeps prior behaviour for unregistered targets).
        extra_start = len(param_names)
        for j in range(pos_idx, len(positional_args)):
            args[f"arg{extra_start + (j - pos_idx)}"] = self._eval_expression(positional_args[j], state)

        return args

    # ------------------------------------------------------------------ #
    # CALL PARALLEL execution                                              #
    # ------------------------------------------------------------------ #

    async def _execute_call_parallel(self, stmt: CallParallelStatement, state) -> None:
        """Execute a CALL PARALLEL statement using WorkflowComposer.

        Requires a WorkflowComposer to be attached as self.composer before
        execution.  Attach it after constructing the executor:

            executor = SPL3Executor(adapter=adapter)
            executor.composer = WorkflowComposer(registry, executor)

        If no composer is set, logs a warning and skips the parallel branches.
        """
        composer = getattr(self, "composer", None)

        if composer is None:
            _log.warning(
                "CALL PARALLEL: no WorkflowComposer attached; "
                "set executor.composer = WorkflowComposer(registry, executor). "
                "Skipping %d branch(es).",
                len(stmt.branches),
            )
            return

        # Build (name, args_dict, into_var) tuples for all branches.
        # Arguments are positional; we resolve names from the target workflow's
        # INPUT param list if available, otherwise use arg0, arg1, ...
        calls = []
        for branch in stmt.branches:
            try:
                defn = composer.registry.get(branch.workflow_name)
                param_names = [inp.name for inp in defn.ast_node.inputs]
            except Exception:
                param_names = []

            args = self._resolve_sub_workflow_args(branch.arguments, param_names, state)

            calls.append((branch.workflow_name, args, branch.target_var))

        results = await composer.call_parallel(calls)

        for sub_result in results:
            state.set_var(sub_result.output_var, sub_result.output_value)
            state.total_llm_calls += sub_result.total_llm_calls
            state.total_latency_ms += sub_result.latency_ms
            state.response_workers |= sub_result.response_workers

    # ------------------------------------------------------------------ #
    # CALL statement — registry-aware override with self-healing           #
    # ------------------------------------------------------------------ #

    async def _exec_call(self, stmt, state) -> None:
        """Execute CALL with persistence checkpointing and optional self-healing.

        Persistence (opt-in):
          - Exactly-once: returns cached result if step already completed.
          - Checkpoints result after successful execution.

        Self-healing (opt-in via --kernel --self-healing):
          - Catches ModuleNotFoundError, pip-installs the missing package, retries once.
          - If direct install fails, LLM resolves the correct package name first.
        """
        _pers = self._persistence
        _wfid = self._workflow_id
        step_idx: int | None = None
        step_name: str | None = None

        # Persistence: exactly-once check
        if _pers is not None and _wfid is not None:
            step_idx = self._step_counter
            self._step_counter += 1
            step_name = f"CALL:{stmt.procedure_name}"
            cached = await _pers.get_step_result(_wfid, step_idx)
            if cached is not None:
                _log.info("Skipping step %d (%s) — cached", step_idx, step_name)
                tgt = getattr(stmt, "target_variable", None)
                if tgt and tgt not in ("NONE", "_"):
                    state.set_var(tgt, cached)
                return

        # Self-healing execution
        kernel = self._kernel
        if not (kernel and getattr(kernel, "self_healing", False)):
            await self._exec_call_inner(stmt, state)
        else:
            from spl.executor import ToolFailed
            for attempt in range(2):
                try:
                    await self._exec_call_inner(stmt, state)
                    break
                except ToolFailed as exc:
                    cause = exc.__cause__
                    if attempt == 0 and isinstance(cause, ModuleNotFoundError):
                        await self._self_heal_module(cause)
                    else:
                        raise

        # Persistence: checkpoint after success
        if _pers is not None and _wfid is not None and step_idx is not None:
            tgt = getattr(stmt, "target_variable", None)
            result = state.get_var(tgt) if tgt and tgt not in ("NONE", "_") else ""
            await _pers.checkpoint(_wfid, step_idx, step_name or "", result,
                                   dict(state.variables))

    async def _exec_call_inner(self, stmt, state) -> None:
        """Registry-aware CALL dispatch (extracted for self-healing retry support).

        1. If a WorkflowComposer is attached and the name is found in the
           registry, delegate to the composer (sub-workflow CALL).
        2. Otherwise fall through to SPL 2.0 tool / builtin / LLM handling.
        """
        composer = getattr(self, "composer", None)
        if composer is not None:
            from spl3.registry import RegistryError
            try:
                defn = composer.registry.get(stmt.procedure_name)
            except RegistryError:
                defn = None

            if defn is not None:
                try:
                    param_names = [inp.name for inp in defn.ast_node.inputs]
                except (AttributeError, TypeError):
                    param_names = []

                args = self._resolve_sub_workflow_args(stmt.arguments, param_names, state)

                into_var = stmt.target_variable or ""
                sub_result = await composer.call(stmt.procedure_name, args, into_var)

                if into_var:
                    state.set_var(into_var, sub_result.output_value)
                state.total_llm_calls += sub_result.total_llm_calls
                state.total_latency_ms += sub_result.latency_ms
                state.response_workers |= sub_result.response_workers
                return

        await super()._exec_call(stmt, state)

    async def _self_heal_module(self, exc: ModuleNotFoundError) -> None:
        """pip-install the missing module; escalate to LLM if direct install fails."""
        module = getattr(exc, "name", None) or (
            str(exc).split("'")[1] if "'" in str(exc) else str(exc)
        )
        kernel = self._kernel
        assert kernel is not None  # only called when kernel.self_healing is True
        _log.info("Self-healing: module '%s' not found, attempting pip install", module)
        if kernel.pip_install(module):
            return
        _log.info(
            "Self-healing: direct install of '%s' failed, asking LLM for package name",
            module,
        )
        package = await self._resolve_package_via_llm(module)
        if package and package != module:
            kernel.pip_install(package)

    async def _resolve_package_via_llm(self, module_name: str) -> str:
        """Ask the adapter which pip package provides a missing Python module."""
        prompt = (
            f"The Python module '{module_name}' is not installed. "
            f"What is the exact pip package name to install it? "
            f"Reply with only the package name, nothing else."
        )
        try:
            result = await self.adapter.generate(
                prompt=prompt,
                system="You are a Python package resolver. Reply with only the pip package name.",
                model=self.default_model or "",
                max_tokens=20,
            )
            return (result.content or "").strip().split()[0]
        except Exception as e:
            _log.warning("LLM package resolution failed: %s", e)
            return ""


Executor = SPL3Executor  # convenience alias for cli.py imports
