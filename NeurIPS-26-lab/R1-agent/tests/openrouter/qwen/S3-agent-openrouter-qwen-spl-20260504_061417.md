INFO:spl.registry:Registry: loaded 1 workflow(s) from /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S3-agent-openrouter-qwen.spl
Registry: ['DecisionAgent']
Running workflow: DecisionAgent(['user_query', 'model'])
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (decide_action) -> 851 tokens, 16684ms
INFO:spl.executor:GENERATE chain done -> @raw_yaml (65 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (validate_yaml) -> 890 tokens, 17027ms
INFO:spl.executor:GENERATE chain done -> @yaml_status (5 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (extract_action) -> 288 tokens, 5943ms
INFO:spl.executor:GENERATE chain done -> @action_token (6 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (decide_action) -> 1823 tokens, 33595ms
INFO:spl.executor:GENERATE chain done -> @raw_yaml (77 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (validate_yaml) -> 697 tokens, 15024ms
INFO:spl.executor:GENERATE chain done -> @yaml_status (5 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (extract_action) -> 291 tokens, 6071ms
INFO:spl.executor:GENERATE chain done -> @action_token (6 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (decide_action) -> 1182 tokens, 22110ms
INFO:spl.executor:GENERATE chain done -> @raw_yaml (77 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (validate_yaml) -> 354 tokens, 7477ms
INFO:spl.executor:GENERATE chain done -> @yaml_status (5 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (extract_action) -> 246 tokens, 5271ms
INFO:spl.executor:GENERATE chain done -> @action_token (6 chars total)
INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (generate_final) -> 3281 tokens, 60603ms
INFO:spl.executor:GENERATE chain done -> @final_response (3792 chars total)
INFO:spl.executor:RETURN: 3792 chars | status=complete

Status:  complete
Output:  Based on current open-source ecosystem knowledge, here is a comprehensive overview of **PocketFlow** and how to install it:

### 🔍 What is PocketFlow?
**PocketFlow** is a lightweight, minimalist framework for building LLM (Large Language Model) applications and AI agent workflows. It was designed as a deliberate alternative to heavier, abstraction-heavy libraries like LangChain or LlamaIndex. Its core philosophy centers on **transparency, simplicity, and composability**.

Key characteristics:
- **Ultra-lightweight**: Core functionality is implemented in ~100–200 lines of code, making it easy to read, audit, and modify.
- **Node/Graph-based execution**: Workflows are built by connecting discrete steps (nodes) that process state, call LLMs, run tools, or evaluate outputs.
- **Zero magic**: No hidden state management, automatic retries, or opaque abstractions. You control the exact execution flow.
- **Provider-agnostic**: Does not bundle LLM clients. Works seamlessly with OpenAI, Anthropic, local models (via Ollama/LiteLLM), or any OpenAI-compatible API.
- **Ideal for**: Rapid prototyping, educational purposes, production agent pipelines where you need full control over prompt routing, tool calling, and error handling.

> ⚠️ **Note on naming**: There is an older, archived Tencent project also named "PocketFlow" (focused on deep learning model compression, ~2018). The active, widely-used project today is the **LLM workflow framework**.

---

### 📦 How to Install PocketFlow

PocketFlow is published on PyPI and requires **Python 3.9+**.

#### 1. Basic Installation
```bash
pip install pocketflow
```

#### 2. Install LLM Providers (Optional but Recommended)
PocketFlow intentionally ships without LLM dependencies to stay minimal. Install your preferred client separately:
```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For unified multi-provider routing (recommended)
pip install litellm
```

#### 3. Verify Installation
```bash
python -c "import pocketflow; print(pocketflow.__version__)"
```

---

### 🛠️ Quick Start Example
Here's a minimal workflow demonstrating how PocketFlow structures LLM calls:

```python
from pocketflow import Node, Graph

# 1. Define a node that calls an LLM
def summarize(text, **kwargs):
    # Insert your LLM client logic here (OpenAI, LiteLLM, etc.)
    # Example: response = client.chat.completions.create(...)
    return f"[Summary] {text[:50]}..."

# 2. Build a simple graph
workflow = Graph()
workflow.add_node("summarize", summarize)
workflow.set_start("summarize")

# 3. Execute
result = workflow.run(input_text="A long technical article about quantum computing...")
print(result)
```

As you scale, you can add conditional branches, tool-calling nodes, memory/state tracking, and retry logic by simply chaining more nodes and defining edges.

---

### 📌 Important Notes
- **Documentation**: The official GitHub repository (`github.com/the-pocket/PocketFlow` or similar) contains the latest API reference, examples, and migration guides. The framework is actively evolving.
- **No built-in vector stores or retrievers**: PocketFlow focuses on control flow. For RAG, combine it with `langchain`, `llama-index`, or custom retrieval logic.
- **Debugging**: Because execution is explicit and synchronous by default, standard Python debuggers (`pdb`, `breakpoint()`) work out-of-the-box.
- **Community & Support**: Check the repo's Discussions/Issues for version-specific changes, as the API may shift slightly as the project matures.

If you're building LLM agents or need fine-grained control over workflow execution without framework overhead, PocketFlow is a highly efficient choice. Let me know if you need a specific implementation example (e.g., tool calling, streaming, or multi-agent routing).
LLM calls: 10  Latency: 189816ms
Log:     /home/wengong/.spl/logs/S3_agent_openrouter_qwen-openrouter-20260504-061418.md
