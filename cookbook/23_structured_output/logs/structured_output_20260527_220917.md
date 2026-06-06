INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"

Status:     complete
Output:     ```json
{
  "employee_name": "John Smith",
  "employee_age": 42,
  "company_name": "Acme Corp",
  "joining_date_month": "March",
  "joining_date_year": 2021,
  "salary": 95000,
  "salary_frequency": "year"
}
```
LLM calls:  1
Latency:    1714ms
Tokens:     128 in / 92 out
Log:     /home/papagame/.spl/logs/structured_output-ollama-20260527-222314.md
