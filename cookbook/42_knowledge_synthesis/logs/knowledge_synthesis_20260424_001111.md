INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/42_knowledge_synthesis/knowledge_synthesis.spl
Registry: ['knowledge_synthesis']
Loaded 62 tool(s) from ./cookbook/42_knowledge_synthesis/tools.py
Running workflow: knowledge_synthesis(['raw_text', 'model'])
[INFO] Extracting insights from new information ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (synthesize) -> 64 tokens, 6852ms
INFO:spl.executor:GENERATE chain done -> @insights (364 chars total)
[WARN] Knowledge base update returned: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gong2/projects/digital-duck/SPL.py/spl/code_rag.py)
INFO:spl.executor:RETURN: 124 chars | status=error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gong2/projects/digital-duck/SPL.py/spl/code_rag.py)

Status:  complete
Output:  Operation: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gong2/projects/digital-duck/SPL.py/spl/code_rag.py)
LLM calls: 1  Latency: 6861ms
Log:     /home/gong2/.spl/logs/knowledge_synthesis-ollama-20260424-005046.md
