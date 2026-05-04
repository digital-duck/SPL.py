# S2 Rag Openrouter Gemini Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S1-rag-openrouter-gemini-1-spec.md --adapter openrouter --model google/gemini-3-flash-preview -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S2-rag-openrouter-gemini.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    Start([Start]) --> ChunkDocs["Chunk Documents<br/>(fixed_size_chunk)"]
    subgraph Offline_Indexing["Offline Indexing Phase"]
    ChunkDocs --> EmbedDocs["Embed Documents<br/>(CALL Embedding Service)"]
    EmbedDocs --> CreateIndex["Create FAISS Index<br/>(Store Vectors)"]
    end
    CreateIndex --> EmbedQuery["Embed User Query<br/>(CALL Embedding Service)"]
    subgraph Online_Query["Online RAG Phase"]
    EmbedQuery --> Retrieve["Retrieve Document<br/>(Vector Search)"]
    Retrieve --> GenerateAnswer["GenerateAnswer Function<br/>(Context + Question)"]
    GenerateAnswer --> LLMCall["GENERATE Response<br/>(LLM Synthesis)"]
    end
    LLMCall --> End([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S2-rag-openrouter-gemini.mmd -o S2-rag-openrouter-gemini.spl`
4. Validate: `spl3 validate S2-rag-openrouter-gemini.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
