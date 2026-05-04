# S2 Rag Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S1-rag-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S2-rag-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    START([Start]) --> B
    subgraph OFFLINE["Offline Indexing Workflow"]
    B["Chunk Raw<br/>Texts"]
    C["Generate Vector<br/>Embeddings"]
    D["Construct FAISS<br/>Index"]
    E["Log & Persist<br/>Index"]
    B --> C
    C --> D
    D --> E
    end
    subgraph SHARED["@shared Variable Store"]
    S1["@texts"]
    S2["@embeddings"]
    S3["@index"]
    S4["@query"]
    S5["@query_embedding"]
    S6["@retrieved_doc"]
    S7["@answer"]
    end
    subgraph ONLINE["Online Query Workflow"]
    F["Accept User<br/>Query"]
    G["Embed<br/>Query"]
    H["Nearest-Neighbor<br/>Search"]
    I["Retrieve Top<br/>Document"]
    J["Format Prompt<br/>(GenerateAnswer)"]
    K["Execute GENERATE<br/>LLM Call"]
    L["Write Markdown<br/>File"]
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    end
    E -->|"@index stored"| S3
    E --> F
    F --- S4
    G --- S5
    H --- S3
    I --- S6
    K --- S7
    L --> END([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S2-rag-openrouter-qwen.mmd -o S2-rag-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-rag-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
