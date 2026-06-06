INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S3-rag-openrouter-qwen.spl
Registry: ['RAGPipeline']
INFO:faiss.loader:Loading faiss with AVX2 support.
INFO:faiss.loader:Successfully loaded faiss with AVX2 support.
Loaded 71 tool(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/tools.py
Running workflow: RAGPipeline(['raw_input', 'user_query', 'model'])
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (FormatPrompt) -> 1070 tokens, 20461ms
INFO:spl.executor:GENERATE chain done -> @result (412 chars total)
INFO:spl.executor:RETURN: 412 chars | status=complete

Status:  complete
Output:  **PocketFlow** is a minimalist, lightweight framework designed for building LLM-powered agentic pipelines. It focuses on simplicity and composability, allowing developers to chain AI agents, tools, and workflows with minimal boilerplate code.

**Installation:**
```bash
pip install pocketflow
```
For the exact package name, dependencies, and usage examples, refer to its official GitHub repository or PyPI page.
LLM calls: 1  Latency: 20857ms
Log:     /home/wengong/.spl/logs/S3_rag_openrouter_qwen-openrouter-20260504-063152.md
