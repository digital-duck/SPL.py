2026-05-04 07:34:05,039 [INFO] Starting workflow. Topic: PocketFlow LLM orchestration framework
2026-05-04 07:34:05,040 [INFO] [ITERATION] Step 1 / 1
Traceback (most recent call last):
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/targets/python_pocketflow/S4-research-openrouter-qwen.py", line 73, in _search_web
    from ddgs import DDGS
ModuleNotFoundError: No module named 'ddgs'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/targets/python_pocketflow/S4-research-openrouter-qwen.py", line 173, in <module>
    final_report = workflow.run(topic=args.topic)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/targets/python_pocketflow/S4-research-openrouter-qwen.py", line 141, in run
    self.state["web_results"] = _search_web(self.state["current_queries"])
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/targets/python_pocketflow/S4-research-openrouter-qwen.py", line 75, in _search_web
    from duckduckgo_search import DDGS
ModuleNotFoundError: No module named 'duckduckgo_search'
