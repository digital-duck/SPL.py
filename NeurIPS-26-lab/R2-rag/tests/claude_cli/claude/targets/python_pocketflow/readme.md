## S3-rag-claude_cli-sonnet — RAGPipeline (PocketFlow)

### Setup

```bash
conda activate spl123
pip install pocketflow numpy
# claude CLI must be on $PATH and authenticated
claude --version
```

### Run

```bash
# interactive — question only
python S3-rag-claude_cli-sonnet_python_pocketflow.py "What is SPL?"

# with file output
python S3-rag-claude_cli-sonnet_python_pocketflow.py "What is PocketFlow?" answer.txt

python /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/sonnet/targets/python_pocketflow/S3-rag-claude_cli-sonnet_python_pocketflow.py \
"What is PocketFlow?" answer.txt

# programmatic (filename contains hyphens, so use importlib)
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    'rag', pathlib.Path('S3-rag-claude_cli-sonnet_python_pocketflow.py')
)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
answer = m.run_rag_pipeline(documents=[...], query='...', output_path='out.txt')
"
```

### Expected output pattern

```
=== Generated Answer ===
PocketFlow is a minimalist 100-line LLM framework for Python. It provides...
```

If `output_path` contains a `.`, the answer is also written to that file and a confirmation path is stored in `shared["write_result"]`; otherwise `write_result` is `"skipped"`.

### SPL → PocketFlow mapping

| SPL construct | PocketFlow equivalent |
|---|---|
| `WORKFLOW RAGPipeline` | `build_rag_pipeline() → Flow` + `run_rag_pipeline()` entry function |
| `INPUT @documents LIST, @query TEXT, @output_path TEXT := ""` | `run_rag_pipeline(documents, query, output_path="")` signature |
| `OUTPUT @generated_answer TEXT` | `return shared["generated_answer"]` |
| `CALL chunk_documents(@documents) INTO @texts` | `ChunkDocumentsNode` → `shared["texts"]` |
| `CALL embed_documents(@texts) INTO @embeddings` | `EmbedDocumentsNode` → `shared["embeddings"]` |
| `CALL create_faiss_index(@embeddings) INTO @index` | `CreateFaissIndexNode` → `shared["index"]` |
| `CALL embed_query(@query) INTO @query_embedding` | `EmbedQueryNode` → `shared["query_embedding"]` |
| `CALL retrieve_document(@index,@query_embedding,@texts) INTO @retrieved_document` | `RetrieveDocumentNode` → `shared["retrieved_document"]` |
| `GENERATE generate_answer(@query, @retrieved_document) INTO @generated_answer` | `GenerateAnswerNode` → `_claude_cli(prompt)` → `shared["generated_answer"]` |
| `EVALUATE @output_path WHEN contains(".") THEN … ELSE … END` | `WriteOutputNode.exec` — `if "." in output_path` branch |
| `CALL write_file(@output_path, @generated_answer) INTO @write_result` | `open(output_path, "w").write(...)` → `shared["write_result"]` |
| `@write_result := "skipped"` | `return "skipped"` in the `else` branch |
| `RETURN @generated_answer WITH status = "complete"` | `shared["status"] = "complete"` + `return shared["generated_answer"]` |
| `CREATE FUNCTION generate_answer(…)` | Module-level `generate_answer(query, retrieved_document)` calling `_claude_cli` |
| Node chaining (`>>`) | `chunk >> embed >> index >> embed_q >> retrieve >> generate >> write` |