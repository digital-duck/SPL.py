# S3-RAG-OpenRouter-Qwen Pipeline

This implementation translates the `S3-rag-openrouter-qwen.spl` logical workflow into a runnable Python script using a minimalist ETL-style orchestration pattern (PocketFlow paradigm).

## 🔧 Setup Instructions
1. Ensure Python 3.8+ is installed.
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Set your OpenRouter API key in your environment:
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```
4. Save the implementation as `S3_rag_openrouter_qwen.py`.

## 🚀 Run Command
```bash
python S3_rag_openrouter_qwen.py
```

## 📤 Expected Output Pattern
```text
[LOG] Index constructed: 3 vectors. Persisting to disk...
[LOG] Output written to output.md

Execution Status: {'status': 'complete'}
Final Output:
PocketFlow is a minimalist ETL-style LLM orchestration framework designed to simplify workflow management and pipeline execution.
```
*(Note: If `OPENROUTER_API_KEY` is not set, a mock response will be generated and logged.)*

## 🗺️ SPL to Python Mapping Table

| SPL Construct | Python / PocketFlow Equivalent |
|---------------|--------------------------------|
| `CREATE FUNCTION ... RETURNS TEXT AS $$...$$` | `def FormatPrompt(doc, query) -> str:` |
| `WORKFLOW RAGPipeline` | `class S3RagOpenrouterQwenPipeline:` |
| `INPUT @raw_input STRING, @user_query STRING := "default query"` | `__init__(self, raw_input: str, user_query: str = "default query")` |
| `OUTPUT @result STRING` | `self.result: str` attribute & `run()` return type |
| `@var := @val;` | Local Python assignment: `var = val` |
| `CALL ChunkRawTexts(@texts) INTO @texts;` | `texts = self._call_chunk_raw_texts(texts)` |
| `CALL GenerateVectorEmbeddings(...) INTO ...` | `embeddings = self._call_generate_vector_embeddings(...)` |
| `CALL ConstructFAISSIndex(...) INTO ...` | `index = self._call_construct_faiss_index(...)` |
| `CALL LogAndPersistIndex(...) INTO ...` | `persist_status = self._call_log_and_persist_index(...)` |
| `GENERATE FormatPrompt(...) INTO @result;` | `self.result = self._generate_with_openrouter(prompt)` |
| `CALL write_file(...) INTO ...` | `self._call_write_file(...)` |
| `RETURN @result WITH status = "complete";` | `return self.result, {"status": "complete"}` |