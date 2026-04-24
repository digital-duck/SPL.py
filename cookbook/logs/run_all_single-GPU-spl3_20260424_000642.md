=== SPL Cookbook Batch Run — 2026-04-24 00:06:43 ===
    Adapter : ollama  |  Model : gemma3

[01] Hello World
     cmd : spl3 run --model gemma3 ./cookbook/01_hello_world/hello.spl --adapter ollama
     log : /home/gong2/projects/digital-duck/SPL.py/cookbook/01_hello_world/logs/hello_20260424_000643.md
     | INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/01_hello_world/hello.spl
     | Registry: []
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | 
     | Status:     complete
     | Output:     Okay, let's talk about SPL! 
     | 
     | SPL stands for **Structured Prompt Language**. Think of it as a way to tell a language model *exactly* what you want it to do, step-by-step, in a really clear and organized way. 
     | 
     | Basically, it’s a special language designed to orchestrate workflows with “agentic” models – models that can actually *do* things and interact with other tools. 
     | 
     | Here's the key thing: SPL is designed to be easy to read and write, so you don't need to be a coding expert to use it. It’s meant to be accessible for everyone! 
     | 
     | **In short, it's a way to build complex interactions with language models, like guiding them through a series of tasks.**
     | 
     | Would you like me to:
     | 
     | *   Give you a simple example of how SPL might be used?
     | *   Explain some of the core concepts in more detail?
     | LLM calls:  1
     | Latency:    4145ms
     | Tokens:     96 in / 199 out
     | Log:     /home/gong2/.spl/logs/hello-ollama-20260424-000644.md
     result: SUCCESS  (5.5s)


=== Summary: 1/1 Success  (total 5.5s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  OK           5.5s

