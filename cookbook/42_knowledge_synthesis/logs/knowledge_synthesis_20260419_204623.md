INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/42_knowledge_synthesis/knowledge_synthesis.spl
Registry: ['knowledge_synthesis']
Loaded 62 tool(s) from ./cookbook/42_knowledge_synthesis/tools.py
Running workflow: knowledge_synthesis(['raw_text'])
[INFO] Extracting insights from new information ...
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 07feb5a9-1b7c-45fe-a4c4-af38ff2fbba3 completed by agent papa-game in 4789ms (52 tokens)
INFO:spl.executor:GENERATE segment 1 (synthesize) -> 52 tokens, 8255ms
INFO:spl.executor:GENERATE chain done -> @insights (316 chars total)
[WARN] Knowledge base update returned: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)
INFO:spl.executor:RETURN: 127 chars | status=error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)

Status:  complete
Output:  Operation: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)
LLM calls: 1  Latency: 8263ms
Log:     /home/papagame/.spl/logs/knowledge_synthesis-momagrid-20260419-205052.md
