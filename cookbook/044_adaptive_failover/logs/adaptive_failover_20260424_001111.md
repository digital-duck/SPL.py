INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/44_adaptive_failover/adaptive_failover.spl
Registry: ['adaptive_failover']
Loaded 62 tool(s) from ./cookbook/44_adaptive_failover/tools.py
Running workflow: adaptive_failover(['query', 'primary_model', 'fallback_model', 'model'])
[INFO] Attempting generation with primary model: phi4
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/cli.py", line 691, in <module>
    main()
    ~~~~^^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/core.py", line 1161, in __call__
    return self.main(*args, **kwargs)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/core.py", line 1082, in main
    rv = self.invoke(ctx)
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/core.py", line 1443, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/click/decorators.py", line 33, in new_func
    return f(get_current_context(), *args, **kwargs)
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/cli.py", line 149, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                              tools_module, allowed_tools))
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/cli.py", line 236, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/executor.py", line 336, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/projects/digital-duck/SPL.py/spl/executor.py", line 683, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/gong2/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/gong2/projects/digital-duck/SPL.py/spl/executor.py", line 744, in _execute_statement
    await self._exec_generate_into(stmt, state)
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/executor.py", line 192, in _exec_generate_into
    return await super()._exec_generate_into(stmt, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/projects/digital-duck/SPL.py/spl/executor.py", line 953, in _exec_generate_into
    gen_result = await self.adapter.generate(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/gong2/projects/digital-duck/SPL.py/spl3/cli.py", line 40, in generate
    return await self._inner.generate(prompt, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/projects/digital-duck/SPL.py/spl/adapters/dd_llm_bridge.py", line 65, in generate
    result = await asyncio.to_thread(
             ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<6 lines>...
    )
    ^
  File "/home/gong2/anaconda3/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/dd_llm/adapters/openai_sdk.py", line 71, in call
    resp = client.chat.completions.create(
        model=effective_model,
    ...<3 lines>...
        **kwargs,
    )
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/openai/_utils/_utils.py", line 287, in wrapper
    return func(*args, **kwargs)
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/openai/resources/chat/completions/completions.py", line 1211, in create
    return self._post(
           ~~~~~~~~~~^
        "/chat/completions",
        ^^^^^^^^^^^^^^^^^^^^
    ...<47 lines>...
        stream_cls=Stream[ChatCompletionChunk],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/openai/_base_client.py", line 1314, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gong2/anaconda3/lib/python3.13/site-packages/openai/_base_client.py", line 1087, in request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'message': "model 'phi4' not found", 'type': 'not_found_error', 'param': None, 'code': None}}
