INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/68_problem_generator/problem_generator.spl
Registry: ['problem_generator']
Running workflow: problem_generator(['model'])
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (write_lesson_intro) -> 69 tokens, 2144ms
INFO:spl.executor:GENERATE chain done -> @intro (421 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (write_word_problem) -> 35 tokens, 1338ms
INFO:spl.executor:GENERATE chain done -> @problem_text (133 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (write_worked_solution) -> 160 tokens, 3345ms
INFO:spl.executor:GENERATE chain done -> @solution (484 chars total)
ERROR:spl.executor:Unhandled SPL exception [ToolFailed]: Tool 'write_file' raised: write_file() takes 2 positional arguments but 3 were given — no EXCEPTION WHEN handler matched; propagating to caller. Add 'WHEN OTHERS THEN' to catch all exceptions.
Traceback (most recent call last):
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1260, in _exec_call
    result_str = tool(*args_text, **kwargs_text)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: write_file() takes 2 positional arguments but 3 were given

The above exception was the direct cause of the following exception:

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
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 688, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 164, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 754, in _execute_statement
    await self._exec_while(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 337, in _exec_while
    await super()._exec_while(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1089, in _exec_while
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
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 1264, in _exec_call
    raise ToolFailed(f"Tool '{stmt.procedure_name}' raised: {e}") from e
spl.executor.ToolFailed: Tool 'write_file' raised: write_file() takes 2 positional arguments but 3 were given
