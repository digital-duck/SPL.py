INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/23_structured_output/structured_output.spl
Registry: []
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ac8d3484-0d8c-43c0-b908-1e9d32b566a1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/ac8d3484-0d8c-43c0-b908-1e9d32b566a1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ac8d3484-0d8c-43c0-b908-1e9d32b566a1 completed by agent ducklover1 in 13776ms (111 tokens)

Status:     complete
Output:     {
  "entities": [
    {
      "type": "PERSON",
      "value": "John Smith"
    },
    {
      "type": "ORGANIZATION",
      "value": "Acme Corp"
    }
  ],
  "dates": [
    {
      "type": "DATE",
      "value": "March 2021"
    }
  ],
  "financials": [
    {
      "type": "MONETARY_VALUE",
      "value": "$95,000/year"
    }
  ]
}
LLM calls:  1
Latency:    16414ms
Tokens:     99 in / 111 out
Log:     /home/papagame/.spl/logs/structured_output-momagrid-20260419-204754.md
