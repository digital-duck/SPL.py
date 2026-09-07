INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/44_adaptive_failover/adaptive_failover.spl
Registry: ['adaptive_failover']
Loaded 65 tool(s) from ./cookbook/44_adaptive_failover/tools.py
Running workflow: adaptive_failover(['query', 'primary_model', 'fallback_model', 'model'])
[INFO] Attempting generation with primary model: phi4-mini
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 4399, in <module>
    main()
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1514, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1435, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1902, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1298, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 853, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 547, in run
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
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 652, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 427, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 683, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 744, in _execute_statement
    await self._exec_generate_into(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 199, in _exec_generate_into
    return await super()._exec_generate_into(stmt, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 953, in _exec_generate_into
    gen_result = await self.adapter.generate(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 47, in generate
    return await self._inner.generate(prompt, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/adapters/dd_llm_bridge.py", line 65, in generate
    result = await asyncio.to_thread(
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/dd-llm/dd_llm/adapters/openai_sdk.py", line 76, in call
    resp = client.chat.completions.create(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_utils/_utils.py", line 287, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/resources/chat/completions/completions.py", line 1211, in create
    return self._post(
           ^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_base_client.py", line 1314, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/openai/_base_client.py", line 1087, in request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'message': "model 'phi4-mini' not found", 'type': 'not_found_error', 'param': None, 'code': None}}
