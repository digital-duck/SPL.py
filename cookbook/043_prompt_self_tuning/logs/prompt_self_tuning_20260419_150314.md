INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 62 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 18 tokens, 479ms
INFO:spl.executor:GENERATE chain done -> @v1 (100 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 14 tokens, 283ms
INFO:spl.executor:GENERATE chain done -> @v2 (85 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 498 tokens, 5556ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (2521 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 471 tokens, 5287ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (2195 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 100 chars | status=complete

Status:  complete
Output:  Summarize the core mathematical concepts and high-level architecture of a complex quantum algorithm.
LLM calls: 4  Latency: 11607ms
Log:     /home/papagame/.spl/logs/prompt_self_tuning-ollama-20260419-152658.md
