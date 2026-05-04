INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S3-rag-openrouter-gemini.spl
Registry: ['RagIndexingAndQuery']
INFO:faiss.loader:Loading faiss with AVX2 support.
INFO:faiss.loader:Successfully loaded faiss with AVX2 support.
Loaded 71 tool(s) from /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/tools.py
Running workflow: RagIndexingAndQuery(['raw_input', 'user_query', 'model'])
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (GenerateAnswer) -> 50 tokens, 1367ms
INFO:spl.executor:GENERATE chain done -> @final_response (240 chars total)
INFO:spl.executor:RETURN: 240 chars | status=complete

Status:  complete
Output:  Based on the context provided, PocketFlow is a minimalist LLM framework for building agentic pipelines.

The provided context does not contain information on how to install it, so I don't know the answer to the second part of your question.
LLM calls: 1  Latency: 2810ms
Log:     /home/papagame/.spl/logs/S3_rag_openrouter_gemini-openrouter-20260504-151243.md
