INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 8476bd8f-f0ab-4b1f-a863-3be13f7c9e29 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/8476bd8f-f0ab-4b1f-a863-3be13f7c9e29 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/8476bd8f-f0ab-4b1f-a863-3be13f7c9e29 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/8476bd8f-f0ab-4b1f-a863-3be13f7c9e29 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 8476bd8f-f0ab-4b1f-a863-3be13f7c9e29 completed by agent ducklover1 in 3035ms (42 tokens)

Status:     complete
Output:     {"entities": {"name": "John Smith", "age": 42, "company": "Acme Corp", "employment_date": "March 2021", "salary": 95000}}
LLM calls:  1
Latency:    4119ms
Tokens:     99 in / 42 out
Log:     /home/papagame/.spl/logs/structured_output-momagrid-20260419-210149.md
