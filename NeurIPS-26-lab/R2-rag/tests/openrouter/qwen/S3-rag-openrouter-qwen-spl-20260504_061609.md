INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S3-rag-openrouter-qwen.spl
Registry: ['RAGPipeline']
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
  File "/home/wengong/projects/digital-duck/SPL.py/spl3/cli.py", line 201, in _run_workflow
    loaded = load_tools_module(tools_module)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/spl/tools.py", line 71, in load_tools_module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 936, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1073, in get_code
  File "<frozen importlib._bootstrap_external>", line 1130, in get_data
FileNotFoundError: [Errno 2] No such file or directory: '/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py'
