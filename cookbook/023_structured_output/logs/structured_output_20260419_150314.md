INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"

Status:     complete
Output:     ```json
{
  "entities": {
    "name": [
      {
        "value": "John Smith",
        "type": "string"
      }
    ],
    "age": [
      {
        "value": "42",
        "type": "integer"
      }
    ],
    "company": [
      {
        "value": "Acme Corp",
        "type": "string"
      },
      {
        "value": "organization",
        "type": "string"
      }
    ],
    "employment_date": [
      {
        "value": "March 2021",
        "type": "date"
      }
    ],
    "income": [
      {
        "value": "$95,000/year",
        "type": "amount"
      },
      {
        "value": "integer",
        "type": "unit"
      }
    ]
  }
}
```
LLM calls:  1
Latency:    2209ms
Tokens:     99 in / 185 out
Log:     /home/papagame/.spl/logs/structured_output-ollama-20260419-151226.md
