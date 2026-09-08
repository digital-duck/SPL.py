INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/40_azure_openai_quickstart/azure_openai_quickstart.spl
Registry: ['azure_openai_quickstart']
Running workflow: azure_openai_quickstart(['prompt', 'model'])
INFO:spl.executor:CTE GENERATE answer (model=gpt-4o)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/cli.py", line 4585, in <module>
    main()
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1406, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1873, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 824, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/cli.py", line 555, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/cli.py", line 681, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/executor.py", line 568, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl/executor.py", line 683, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/gongai/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/executor.py", line 134, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/home/gongai/projects/digital-duck/SPL.py/spl/executor.py", line 766, in _execute_statement
    await self._exec_select_into(stmt, state)
  File "/home/gongai/projects/digital-duck/SPL.py/spl/executor.py", line 790, in _exec_select_into
    result = await self._exec_generate_into_prompt(cte.nested_prompt, state)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl/executor.py", line 874, in _exec_generate_into_prompt
    gen_result = await self.adapter.generate(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl3/cli.py", line 47, in generate
    return await self._inner.generate(prompt, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/projects/digital-duck/SPL.py/spl/adapters/dd_llm_bridge.py", line 65, in generate
    result = await asyncio.to_thread(
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/dd_llm/adapters/openai_sdk.py", line 71, in call
    resp = client.chat.completions.create(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_utils/_utils.py", line 287, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/resources/chat/completions/completions.py", line 1211, in create
    return self._post(
           ^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_base_client.py", line 1314, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gongai/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_base_client.py", line 1087, in request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'message': "model 'gpt-4o' not found", 'type': 'not_found_error', 'param': None, 'code': None}}
