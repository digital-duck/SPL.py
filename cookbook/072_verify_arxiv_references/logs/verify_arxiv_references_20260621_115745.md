INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/72_verify_arxiv_references/verify_arxiv_references.spl
Registry: ['verify_arxiv_references']
Running workflow: verify_arxiv_references(['in_refs', 'out_dir', 'model'])
INFO:spl.executor:Exception ToolFailed caught by handler 'OTHERS'
Traceback (most recent call last):
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 688, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 164, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 768, in _execute_statement
    await self._exec_call(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 854, in _exec_call
    await self._exec_call_inner(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 908, in _exec_call_inner
    await super()._exec_call(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1291, in _exec_call
    raise ToolFailed(
spl.executor.ToolFailed: Procedure 'init_spl_log' not found — no tool, no builtin, no procedure registered. Check spelling or ensure the TOOL_API library is promoted (spl3 tool-api promote).

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 4917, in <module>
    main()
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1912, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 63, in wrapper
    return fn(*args, adapter=adapter, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 716, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 857, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 712, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 691, in execute_workflow
    handled = await self._handle_exception(e, stmt.exception_handlers, state)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1359, in _handle_exception
    await self._execute_body(handler.statements, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 164, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 768, in _execute_statement
    await self._exec_call(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 854, in _exec_call
    await self._exec_call_inner(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 908, in _exec_call_inner
    await super()._exec_call(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1291, in _exec_call
    raise ToolFailed(
spl.executor.ToolFailed: Procedure 'spl_log' not found — no tool, no builtin, no procedure registered. Check spelling or ensure the TOOL_API library is promoted (spl3 tool-api promote).
