INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S3-rag-openrouter-qwen.spl
Registry: ['RAGPipeline']
INFO:faiss.loader:Loading faiss with AVX2 support.
INFO:faiss.loader:Successfully loaded faiss with AVX2 support.
Loaded 71 tool(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py
Running workflow: RAGPipeline(['raw_input', 'user_query', 'model'])
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 400 Bad Request"
ERROR:spl.executor:Unhandled SPL exception [ToolFailed]: Tool 'GenerateVectorEmbeddings' raised: do embedding request: Post "http://127.0.0.1:46081/embedding": EOF (status code: 400) — no EXCEPTION WHEN handler matched; propagating to caller. Add 'WHEN OTHERS THEN' to catch all exceptions.
Traceback (most recent call last):
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 1232, in _exec_call
    result_str = tool(*args_text)
                 ^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py", line 50, in GenerateVectorEmbeddings
    embeddings = [_get_embedding(t) for t in texts]
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py", line 50, in <listcomp>
    embeddings = [_get_embedding(t) for t in texts]
                  ^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py", line 32, in _get_embedding
    resp = ollama.embed(model=_EMBED_MODEL, input=text)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/ollama/_client.py", line 415, in embed
    return self._request(
           ^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/ollama/_client.py", line 199, in _request
    return cls(**self._request_raw(*args, **kwargs).json())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/anaconda3/envs/spl123/lib/python3.11/site-packages/ollama/_client.py", line 143, in _request_raw
    raise ResponseError(e.response.text, e.response.status_code) from None
ollama._types.ResponseError: do embedding request: Post "http://127.0.0.1:46081/embedding": EOF (status code: 400)

The above exception was the direct cause of the following exception:

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
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 340, in execute_workflow
    return await super().execute_workflow(stmt, params=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 683, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 718, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 762, in _execute_statement
    await self._exec_call(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/executor.py", line 436, in _exec_call
    await super()._exec_call(stmt, state)
  File "/home/wengong/projects/digital-duck/SPL.py/spl/executor.py", line 1236, in _exec_call
    raise ToolFailed(f"Tool '{stmt.procedure_name}' raised: {e}") from e
spl.executor.ToolFailed: Tool 'GenerateVectorEmbeddings' raised: do embedding request: Post "http://127.0.0.1:46081/embedding": EOF (status code: 400)
