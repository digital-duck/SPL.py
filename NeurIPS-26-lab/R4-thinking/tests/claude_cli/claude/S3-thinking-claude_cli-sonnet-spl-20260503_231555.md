INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/S3-thinking-claude_cli-sonnet.spl
Registry: ['ChainOfThought']
Loaded 71 tool(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/tools.py
Running workflow: ChainOfThought(['problem', 'model'])
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 405 tokens, 11061ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1623 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 327 tokens, 8419ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1309 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 360 tokens, 9199ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1442 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 252 tokens, 6897ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1011 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 360 tokens, 9273ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1441 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 275 tokens, 7528ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1101 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 407 tokens, 9289ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1631 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 344 tokens, 8661ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1377 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 300 tokens, 9054ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1200 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 500 tokens, 11937ms
INFO:spl.executor:GENERATE chain done -> @thought_data (2003 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 393 tokens, 8788ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1575 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 423 tokens, 10111ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1694 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 404 tokens, 9912ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1616 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 273 tokens, 8077ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1094 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 339 tokens, 8920ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1358 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 353 tokens, 10398ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1415 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 366 tokens, 10995ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1465 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 363 tokens, 8490ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1454 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 324 tokens, 8620ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1296 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 370 tokens, 10243ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1483 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 287 tokens, 7720ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1151 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 404 tokens, 10130ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1616 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 191 tokens, 6230ms
INFO:spl.executor:GENERATE chain done -> @thought_data (767 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 454 tokens, 10020ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1818 chars total)
INFO:spl.executor:GENERATE segment 1 (ChainOfThoughtStep) -> 283 tokens, 9688ms
INFO:spl.executor:GENERATE chain done -> @thought_data (1133 chars total)
ERROR:spl.executor:Unhandled SPL exception [BudgetExceeded]: LLM call limit reached (25/25). Increase max_llm_calls in config if intentional. — no EXCEPTION WHEN handler matched; propagating to caller. Add 'WHEN OTHERS THEN' to catch all exceptions.
Traceback (most recent call last):
  File "/home/wengong/anaconda3/envs/spl123/bin/spl3", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1406, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1873, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 824, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/cli.py", line 150, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/cli.py", line 237, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 336, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 683, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 748, in _execute_statement
    await self._exec_while(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 158, in _exec_while
    await super()._exec_while(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 1122, in _exec_while
    await self._execute_body(stmt.body, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 748, in _execute_statement
    await self._exec_while(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 158, in _exec_while
    await super()._exec_while(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 1122, in _exec_while
    await self._execute_body(stmt.body, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 744, in _execute_statement
    await self._exec_generate_into(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 192, in _exec_generate_into
    return await super()._exec_generate_into(stmt, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 952, in _exec_generate_into
    self._check_budget(state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 354, in _check_budget
    raise BudgetExceeded(
spl.executor.BudgetExceeded: LLM call limit reached (25/25). Increase max_llm_calls in config if intentional.
