=== SPL Cookbook Batch Run — 2026-04-24 00:04:21 ===
    Adapter : ollama  |  Model : gemma3

[01] Hello World
     cmd : spl3 run --model gemma3 ./cookbook/01_hello_world/hello.spl --adapter ollama
     log : /home/gong2/projects/digital-duck/SPL.py/cookbook/01_hello_world/logs/hello_20260424_000421.md
     | INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/01_hello_world/hello.spl
     | Registry: []
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | 
     | Status:     complete
     | Output:     好的，没问题！ 让我来解释一下 SPL。
     | 
     | SPL 通常指的是 **Service Provider License (服务提供商许可证)**， 也就是**服务提供商许可协议**。 
     | 
     | 简单来说，它是由云服务提供商（例如阿里云、腾讯云、亚马逊云锋等）颁发给客户的许可，允许客户在他们的云平台上运行和部署应用程序。 
     | 
     | **更详细一点，SPL 通常包含以下内容：**
     | 
     | *   **使用条款：**  规定了客户如何使用云服务，例如使用限制、数据安全要求等。
     | *   **服务级别协议 (SLA)：**  承诺了云服务提供商对服务可用性、性能等方面的保证。
     | *   **责任限制：**  说明了在一定情况下，云服务提供商对客户造成的损失的责任限制。
     | *   **数据管辖权：**  规定了客户的数据存储位置和管理方式。
     | 
     | **所以，当你使用云服务时，通常需要与云服务提供商签署一份 SPL 协议。**
     | 
     | 希望这个解释对你有帮助!  如果你还有其他问题，随时可以问我。 😊 
     | 
     | (Hǎo de, méi wèntí! Ràng wǒ lái jiěshì yīxià zhī de SPL.  SPL zūnshù zhì Service Provider License (服务提供商许可证),  ruò yě Service Provider Kehéyuētiaokuì.  Jiǎndān yīxià, tā shì yóu fúyǒulei bǎnyíng (例如阿里云、腾讯云、亚马逊云锋等) péngfā gěi kèhù de xǔkě, yǔnxǔ yú tāmen de yún píngdàng shàng yùnxíng hé bǔzhōng yìngyòng chéngxù.  Gèng xiángxì yītiān, SPL zūnshù zhóngfàn yǐxià de nàtiányì: ... )
     | 
     | LLM calls:  1
     | Latency:    13810ms
     | Tokens:     46 in / 417 out
     | Log:     /home/gong2/.spl/logs/hello-ollama-20260424-000422.md
     result: SUCCESS  (15.1s)

[02] Ollama Proxy
     cmd : spl3 run --model gemma3 ./cookbook/02_ollama_proxy/proxy.spl --adapter ollama --param prompt=Explain quantum computing in one sentence
     log : /home/gong2/projects/digital-duck/SPL.py/cookbook/02_ollama_proxy/logs/proxy_20260424_000421.md
     | INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/02_ollama_proxy/proxy.spl
     | Registry: []
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | 
     | Status:     complete
     | Output:     Quantum computing utilizes the principles of quantum mechanics, like superposition and entanglement, to perform complex calculations far beyond the capabilities of classical computers.
     | LLM calls:  1
     | Latency:    1407ms
     | Tokens:     42 in / 27 out
     | Log:     /home/gong2/.spl/logs/proxy-ollama-20260424-000437.md
     result: SUCCESS  (2.7s)


=== Summary: 2/2 Success  (total 17.8s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  OK          15.1s
02     Ollama Proxy                 OK           2.7s

