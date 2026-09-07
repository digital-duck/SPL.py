# Recipe-77 Momagrid experiment run 20260620-183652

DB source: `exp-momagrid-20260620-183652`
Momagrid Hub: http://192.168.0.170:9000/
Workers: 6


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p003` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="differentiate 3*x**3-x, then factor if needed, finally solve for x" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000//tasks "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/opt/anaconda3/envs/spl123/bin/spl3", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1912, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/cli.py", line 684, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
  File "/opt/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/spl123/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/cli.py", line 825, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 627, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 688, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 161, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 752, in _execute_statement
    await self._exec_evaluate(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 1063, in _exec_evaluate
    await self._execute_body(stmt.else_statements, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 161, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 752, in _execute_statement
    await self._exec_evaluate(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 1063, in _exec_evaluate
    await self._execute_body(stmt.else_statements, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 161, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 770, in _execute_statement
    await self._exec_do_block(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 1333, in _exec_do_block
    await self._execute_body(stmt.statements, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 161, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 750, in _execute_statement
    await self._exec_generate_into(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 372, in _exec_generate_into
    await self._exec_generate_into_impl(stmt, state)
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/executor.py", line 395, in _exec_generate_into_impl
    return await super()._exec_generate_into(stmt, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/executor.py", line 959, in _exec_generate_into
    gen_result = await self.adapter.generate(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl3/cli.py", line 53, in generate
    return await self._inner.generate(prompt, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/mac-wen/projects/digital-duck/SPL.py/spl/adapters/momagrid.py", line 159, in generate
    raise RuntimeError(
RuntimeError: Momagrid task submission failed (HTTP 404): 404 page not found

```

