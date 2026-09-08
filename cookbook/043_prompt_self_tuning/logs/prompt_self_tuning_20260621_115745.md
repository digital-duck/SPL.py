INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 68 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case', 'model'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 63 tokens, 2118ms
INFO:spl.executor:GENERATE chain done -> @v1 (338 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 50 tokens, 1515ms
INFO:spl.executor:GENERATE chain done -> @v2 (286 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 355 tokens, 6476ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (1755 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 78 tokens, 1977ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (383 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 338 chars | status=complete

Status:  complete
Output:  Summarize this technical document, focusing on the core concepts and algorithmic steps while explaining any key mathematical or physical principles involved in layman's terms.  If the document is highly specialized, provide a summary suitable for an engineer with a strong foundation in [relevant field - e.g., physics, computer science].
LLM calls: 4  Latency: 12088ms
Log:     /home/papagame/.spl/logs/prompt_self_tuning-ollama-gemma3-20260621-123907.md
