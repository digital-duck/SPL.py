INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/34_progressive_summary/progressive_summary.spl
Registry: ['progressive_summarizer']
Running workflow: progressive_summarizer(['text', 'audience'])
[INFO] Progressive summary | audience=executive layers=3
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 6f7525a2-40be-4cfd-9f10-0ab58fa21e81 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/6f7525a2-40be-4cfd-9f10-0ab58fa21e81 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/6f7525a2-40be-4cfd-9f10-0ab58fa21e81 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/6f7525a2-40be-4cfd-9f10-0ab58fa21e81 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/6f7525a2-40be-4cfd-9f10-0ab58fa21e81 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/6f7525a2-40be-4cfd-9f10-0ab58fa21e81 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6f7525a2-40be-4cfd-9f10-0ab58fa21e81 completed by agent papa-game in 6861ms (166 tokens)
INFO:spl.executor:GENERATE segment 1 (summarize) -> 166 tokens, 8502ms
INFO:spl.executor:GENERATE chain done -> @sentence_summary (814 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task fd76aa92-a1c5-4842-b2a6-b56f954d8256 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/fd76aa92-a1c5-4842-b2a6-b56f954d8256 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/fd76aa92-a1c5-4842-b2a6-b56f954d8256 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/fd76aa92-a1c5-4842-b2a6-b56f954d8256 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/fd76aa92-a1c5-4842-b2a6-b56f954d8256 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/fd76aa92-a1c5-4842-b2a6-b56f954d8256 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task fd76aa92-a1c5-4842-b2a6-b56f954d8256 completed by agent gong2 in 5718ms (433 tokens)
INFO:spl.executor:GENERATE segment 1 (expand_summary) -> 433 tokens, 8544ms
INFO:spl.executor:GENERATE chain done -> @paragraph_summary (2499 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 681a5e23-fa42-4b3e-9093-c26f1cfae6d4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/681a5e23-fa42-4b3e-9093-c26f1cfae6d4 "HTTP/1.1 200 OK"
