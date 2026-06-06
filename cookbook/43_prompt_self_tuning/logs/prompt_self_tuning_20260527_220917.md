INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 65 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case', 'model'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 47 tokens, 1067ms
INFO:spl.executor:GENERATE chain done -> @v1 (264 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 43 tokens, 882ms
INFO:spl.executor:GENERATE chain done -> @v2 (249 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 86 tokens, 1454ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (455 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 83 tokens, 1401ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (416 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 264 chars | status=complete

Status:  complete
Output:  Summarize this technical document, focusing on the core algorithm's functionality, key steps, and any significant mathematical concepts, assuming the reader has a foundational understanding of quantum mechanics but may not be an expert in this specific algorithm.

LLM calls: 4  Latency: 4806ms
Log:     /home/papagame/.spl/logs/prompt_self_tuning-ollama-20260527-224405.md
