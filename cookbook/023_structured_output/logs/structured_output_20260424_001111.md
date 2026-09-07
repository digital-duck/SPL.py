INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"

Status:     complete
Output:     ```json
{
  "name": "John Smith",
  "age": 42,
  "company": "Acme Corp",
  "join_date": "March 2021",
  "salary": 95000,
  "salary_period": "year"
}
```
LLM calls:  1
Latency:    2069ms
Tokens:     128 in / 74 out
Log:     /home/gong2/.spl/logs/structured_output-ollama-20260424-002539.md
