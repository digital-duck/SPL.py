INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"

Status:     complete
Output:     ```json
{
  "entities": [
    {
      "type": "Person",
      "name": "John Smith",
      "age": 42,
      "organization": "Acme Corp",
      "position": null,
      "salary": {
        "unit": "year",
        "value": 95000
      },
      "employment_date": "March 2021"
    }
  ]
}
```
LLM calls:  1
Latency:    1239ms
Tokens:     99 in / 88 out
Log:     /home/papagame/.spl/logs/structured_output-ollama-20260419-121918.md
