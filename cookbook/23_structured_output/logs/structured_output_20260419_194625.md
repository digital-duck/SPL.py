INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 7fd240e3-1616-495d-84e4-33ded1fb6fb3 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/7fd240e3-1616-495d-84e4-33ded1fb6fb3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/7fd240e3-1616-495d-84e4-33ded1fb6fb3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/7fd240e3-1616-495d-84e4-33ded1fb6fb3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/7fd240e3-1616-495d-84e4-33ded1fb6fb3 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 7fd240e3-1616-495d-84e4-33ded1fb6fb3 completed by agent wengong in 3925ms (64 tokens)

Status:     complete
Output:     {"entities": {"person": {"name": "John Smith", "age": 42}, "organization": {"name": "Acme Corp"}, "date": {"year": 2021, "month": "March"}, "salary": {"amount": 95000, "unit": "year"}}}
LLM calls:  1
Latency:    6147ms
Tokens:     99 in / 64 out
Log:     /home/papagame/.spl/logs/structured_output-momagrid-20260419-194734.md
