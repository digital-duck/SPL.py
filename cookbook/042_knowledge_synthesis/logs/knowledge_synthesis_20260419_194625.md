INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/42_knowledge_synthesis/knowledge_synthesis.spl
Registry: ['knowledge_synthesis']
Loaded 62 tool(s) from ./cookbook/42_knowledge_synthesis/tools.py
Running workflow: knowledge_synthesis(['raw_text'])
[INFO] Extracting insights from new information ...
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 63507157-8bd7-4dde-bc0f-ff216df9f98b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/63507157-8bd7-4dde-bc0f-ff216df9f98b "HTTP/1.1 200 OK"
