INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 62 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case', 'model'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 34 tokens, 1448ms
INFO:spl.executor:GENERATE chain done -> @v1 (198 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 41 tokens, 1138ms
INFO:spl.executor:GENERATE chain done -> @v2 (257 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 71 tokens, 1575ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (351 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 77 tokens, 1666ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (396 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 198 chars | status=complete

Status:  complete
Output:  Summarize this technical document, focusing on the core algorithm, its key components, and its intended purpose, assuming the reader has a foundational understanding of quantum computing principles.
LLM calls: 4  Latency: 5831ms
Log:     /home/gong2/.spl/logs/prompt_self_tuning-ollama-20260424-005054.md
