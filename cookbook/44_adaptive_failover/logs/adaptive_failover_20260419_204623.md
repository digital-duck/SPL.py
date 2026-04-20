INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/44_adaptive_failover/adaptive_failover.spl
Registry: ['adaptive_failover']
Loaded 62 tool(s) from ./cookbook/44_adaptive_failover/tools.py
Running workflow: adaptive_failover(['query', 'primary_model', 'fallback_model'])
[INFO] Attempting generation with primary model: phi4
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2f31eb2f-7187-4421-ba00-c4232a206a2c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/2f31eb2f-7187-4421-ba00-c4232a206a2c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/2f31eb2f-7187-4421-ba00-c4232a206a2c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/2f31eb2f-7187-4421-ba00-c4232a206a2c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/2f31eb2f-7187-4421-ba00-c4232a206a2c "HTTP/1.1 200 OK"
