INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/43_prompt_self_tuning/prompt_self_tuning.spl
Registry: ['prompt_self_tuning']
Loaded 62 tool(s) from ./cookbook/43_prompt_self_tuning/tools.py
Running workflow: prompt_self_tuning(['baseline_prompt', 'failed_case'])
[INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 653dcc8c-2d8b-44d0-a2b8-f77c7b4d7d6e completed by agent wengong in 12059ms (20 tokens)
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 20 tokens, 14397ms
INFO:spl.executor:GENERATE chain done -> @v1 (100 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 292cee13-bca5-4f75-a613-6fb1dc52841a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/292cee13-bca5-4f75-a613-6fb1dc52841a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 292cee13-bca5-4f75-a613-6fb1dc52841a completed by agent wengong in 38402ms (24 tokens)
INFO:spl.executor:GENERATE segment 1 (variation_prompt) -> 24 tokens, 40654ms
INFO:spl.executor:GENERATE chain done -> @v2 (130 chars total)
[INFO] Running mini A/B test on variants ...
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 78ec6716-9810-4fef-9924-eb1081cac806 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/78ec6716-9810-4fef-9924-eb1081cac806 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/78ec6716-9810-4fef-9924-eb1081cac806 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/78ec6716-9810-4fef-9924-eb1081cac806 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/78ec6716-9810-4fef-9924-eb1081cac806 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/78ec6716-9810-4fef-9924-eb1081cac806 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 78ec6716-9810-4fef-9924-eb1081cac806 completed by agent wengong in 6074ms (289 tokens)
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 289 tokens, 8149ms
INFO:spl.executor:GENERATE chain done -> @result_v1 (1460 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 55b56190-4972-4dbb-a9c7-874e85ad67e8 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/55b56190-4972-4dbb-a9c7-874e85ad67e8 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 55b56190-4972-4dbb-a9c7-874e85ad67e8 completed by agent wengong in 7988ms (594 tokens)
INFO:spl.executor:GENERATE segment 1 (test_prompt) -> 594 tokens, 10182ms
INFO:spl.executor:GENERATE chain done -> @result_v2 (3432 chars total)
[INFO] Winner: variant 1
INFO:spl.executor:RETURN: 100 chars | status=complete

Status:  complete
Output:  Summarize a simplified version of the technical document or provide an overview of its key concepts.
LLM calls: 4  Latency: 73382ms
Log:     /home/papagame/.spl/logs/prompt_self_tuning-momagrid-20260419-210513.md
