INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 67 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case', 'model'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 41 tokens, 1299ms
INFO:spl.executor:GENERATE chain done -> @v1 (229 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 49 tokens, 1326ms
INFO:spl.executor:GENERATE chain done -> @v2 (296 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 76 tokens, 1840ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (365 chars total)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 183 tokens, 3219ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (868 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 229 chars | status=complete

Status:  complete
Output:  Summarize this technical document, focusing on explaining the core algorithm and its key components in a way that is accessible to someone with a basic understanding of computer science but no prior knowledge of quantum physics.

LLM calls: 4  Latency: 7686ms
Log:     /home/gongai/.spl/logs/prompt_self_tuning-ollama-20260607-161450.md
