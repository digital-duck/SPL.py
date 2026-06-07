INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/42_knowledge_synthesis/knowledge_synthesis.spl
Registry: ['knowledge_synthesis']
Loaded 67 tool(s) from ./cookbook/42_knowledge_synthesis/tools.py
Running workflow: knowledge_synthesis(['raw_text', 'model'])
[INFO] Extracting insights from new information ...
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (synthesize) -> 59 tokens, 1763ms
INFO:spl.executor:GENERATE chain done -> @insights (348 chars total)
[WARN] Knowledge base update returned: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gongai/projects/digital-duck/SPL.py/spl/code_rag.py)
INFO:spl.executor:RETURN: 125 chars | status=error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gongai/projects/digital-duck/SPL.py/spl/code_rag.py)

Status:  complete
Output:  Operation: error:cannot import name 'CodeRAG' from 'spl.code_rag' (/home/gongai/projects/digital-duck/SPL.py/spl/code_rag.py)
LLM calls: 1  Latency: 1765ms
Log:     /home/gongai/.spl/logs/knowledge_synthesis-ollama-20260607-161448.md
