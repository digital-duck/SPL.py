INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S3-agent-openrouter-gemini.spl
Registry: ['ResearchAssistant']
Running workflow: ResearchAssistant(['user_query', 'model'])
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (DecideAction) -> 1 tokens, 1206ms
INFO:spl.executor:GENERATE chain done -> @action (6 chars total)
/home/papagame/projects/digital-duck/SPL.py/spl/stdlib.py:608: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  results = DDGS().text(q, max_results=5)
INFO:primp:response: https://www.bing.com/search?q=What+is+PocketFlow+and+how+do+I+install+it%3F 200
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (DecideAction) -> 1 tokens, 770ms
INFO:spl.executor:GENERATE chain done -> @action (6 chars total)
/home/papagame/projects/digital-duck/SPL.py/spl/stdlib.py:608: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  results = DDGS().text(q, max_results=5)
INFO:primp:response: https://www.bing.com/search?q=What+is+PocketFlow+and+how+do+I+install+it%3F 200
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (DecideAction) -> 1 tokens, 836ms
INFO:spl.executor:GENERATE chain done -> @action (6 chars total)
/home/papagame/projects/digital-duck/SPL.py/spl/stdlib.py:608: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  results = DDGS().text(q, max_results=5)
INFO:primp:response: https://www.bing.com/search?q=What+is+PocketFlow+and+how+do+I+install+it%3F 200
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (DecideAction) -> 1 tokens, 898ms
INFO:spl.executor:GENERATE chain done -> @action (6 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (AnswerQuestion) -> 523 tokens, 3702ms
INFO:spl.executor:GENERATE chain done -> @final_response (2336 chars total)
INFO:spl.executor:RETURN: 2336 chars | status=complete

Status:  complete
Output:  Based on the gathered information, **PocketFlow** primarily refers to a minimalist, lightweight Large Language Model (LLM) framework. There is also a secondary personal finance application of the same name.

### What is PocketFlow?
PocketFlow is a minimalist LLM framework designed to be highly efficient, consisting of roughly **100 lines of code**. Its core philosophy is to simplify the abstraction of LLM frameworks into a **Graph** structure. 

Key features include:
*   **Minimalist Design:** Built with zero external dependencies to keep the codebase clean and easy to debug.
*   **Versatility:** Despite its small size, it supports popular AI design patterns such as Multi-Agent systems, Workflows, and Retrieval-Augmented Generation (RAG).
*   **Self-Programming:** It is designed to enable "Agents to build Agents," allowing LLMs to program and maintain their own workflows.
*   **Orchestration:** It functions as a lightweight orchestrator that encapsulates LLM calls, API requests, and data transformations into reusable sub-tasks.

*(Note: There is also a personal finance app called PocketFlow located at getpocketflow.com which focuses on net worth tracking and spending forecasts.)*

---

### How to Install PocketFlow
Based on the documentation from the official repository and DeepWiki, you can install the framework using the following methods:

#### 1. Via Python Package Manager (pip)
The most common way to install the framework is through pip:
```bash
pip install pocketflow
```

#### 2. From Source (GitHub)
Since the framework is designed to be a "100-line framework," many developers choose to clone it directly to inspect or modify the source code:
1.  Clone the repository:
    ```bash
    git clone https://github.com/the-pocket/PocketFlow.git
    ```
2.  Navigate to the directory:
    ```bash
    cd PocketFlow
    ```
3.  Install dependencies (if any are listed in the specific implementation you are using):
    ```bash
    pip install -r requirements.txt
    ```

#### 3. Development Setup
To use PocketFlow for building applications, you will typically need to set up your environment variables for the LLM providers you plan to use (such as an `OPENAI_API_KEY`). Because it is a minimalist framework, it is often integrated directly into your project as a single module rather than a complex library.
LLM calls: 5  Latency: 9155ms
Log:     /home/papagame/.spl/logs/S3_agent_openrouter_gemini-openrouter-20260504-150709.md
