Registry: workflows=[] prompts=[extract_entities]
Running prompt: extract_entities(text)
[SPL][WARN] Unknown function: extract_entity_schema

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
Latency:    1405ms
Tokens:     61 in / 38 out
Est. Cost:  $0.0000
Log:        /home/papagame/.spl/logs/structured_output-ollama-20260419-142124-ts.md
