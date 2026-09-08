INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/42_knowledge_synthesis/knowledge_synthesis.spl
Registry: ['knowledge_synthesis']
Loaded 62 tool(s) from ./cookbook/42_knowledge_synthesis/tools.py
Running workflow: knowledge_synthesis(['raw_text'])
[INFO] Extracting insights from new information ...
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c0256151-62ce-4126-ae93-129a78add68c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c0256151-62ce-4126-ae93-129a78add68c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c0256151-62ce-4126-ae93-129a78add68c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c0256151-62ce-4126-ae93-129a78add68c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c0256151-62ce-4126-ae93-129a78add68c completed by agent gong2 in 1138ms (59 tokens)
INFO:spl.executor:GENERATE segment 1 (synthesize) -> 59 tokens, 4079ms
INFO:spl.executor:GENERATE chain done -> @insights (374 chars total)
[WARN] Knowledge base update returned: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)
INFO:spl.executor:RETURN: 127 chars | status=error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)

Status:  complete
Output:  Operation: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/papagame/projects/digital-duck/SPL.py/spl/code_rag.py)
LLM calls: 1  Latency: 4080ms
Log:     /home/papagame/.spl/logs/knowledge_synthesis-momagrid-20260419-210509.md
