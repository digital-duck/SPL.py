INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 62 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 26 tokens, 575ms
INFO:spl.executor:GENERATE chain done -> @v1 (145 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 24 tokens, 389ms
INFO:spl.executor:GENERATE chain done -> @v2 (157 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 141 tokens, 1653ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (720 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 447 tokens, 5018ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (2695 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 145 chars | status=complete

Status:  complete
Output:  Summarize a simplified version of a technical document that conveys the core principles and mathematical concepts applied in a quantum algorithm.
LLM calls: 4  Latency: 7638ms
Log:     /home/papagame/.spl/logs/prompt_self_tuning-ollama-20260419-122746.md
