INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/47_arxiv_morning_brief/arxiv_morning_brief.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/47_arxiv_morning_brief/functions.spl
INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/47_arxiv_morning_brief/summarize_paper.spl
Registry: ['arxiv_morning_brief', 'summarize_paper']
Loaded 68 tool(s) from ./cookbook/47_arxiv_morning_brief/tools.py
Running workflow: arxiv_morning_brief(['urls'])
[INFO] arXiv Morning Brief — starting
INFO:arxiv_morning_brief.tools:parse_urls: loaded 2 URLs from /home/papagame/projects/digital-duck/SPL.py/cookbook/47_arxiv_morning_brief/arxiv-papers.txt
[INFO] Papers to process: 2
[INFO] Paper 0/2: https://arxiv.org/abs/2602.15860
WARNING:pypdf._reader:invalid pdf header: b'<!DOC'
WARNING:pypdf._reader:EOF marker not found
INFO:spl.executor:Exception ToolError caught by handler 'ToolError'
[WARN] Skipping https://arxiv.org/abs/2602.15860: tool/download error
[INFO] Paper 1/2: https://arxiv.org/abs/2601.09732
WARNING:pypdf._reader:invalid pdf header: b'<!DOC'
WARNING:pypdf._reader:EOF marker not found
INFO:spl.executor:Exception ToolError caught by handler 'ToolError'
[WARN] Skipping https://arxiv.org/abs/2601.09732: tool/download error
[INFO] All 2 papers processed — writing brief ...
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1d31ccf8-f076-4740-8f42-bf061e50b086 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/1d31ccf8-f076-4740-8f42-bf061e50b086 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/1d31ccf8-f076-4740-8f42-bf061e50b086 "HTTP/1.1 200 OK"
