# S2 Rag Claude Cli Sonnet Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/sonnet/S1-rag-claude_cli-sonnet-1-spec.md --adapter claude_cli --model claude-sonnet-4-6 -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/sonnet/S2-rag-claude_cli-sonnet.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    START([Start]) --> A
    subgraph OFFLINE["Offline Indexing Workflow"]
    A["ChunkDocuments<br/>(BatchNode)<br/>split texts -> 2000-char chunks"]
    B["EmbedDocuments<br/>(BatchNode)<br/>text-embedding-ada-002 per chunk"]
    C["CreateIndex<br/>(Node)<br/>faiss.IndexFlatL2 + index.add"]
    A -->|"@texts (chunks)"| B
    B -->|"@embeddings (float32 matrix)"| C
    end
    subgraph SHARED["@shared Variable Store"]
    S1["@texts"]
    S2["@embeddings"]
    S3["@index"]
    S4["@query"]
    S5["@query_embedding"]
    S6["@retrieved_document"]
    S7["@generated_answer"]
    end
    subgraph ONLINE["Online Query Workflow"]
    D["EmbedQuery<br/>(Node)<br/>embed user query -> (1, dim)"]
    E["RetrieveDocument<br/>(Node)<br/>index.search k=1 nearest neighbor"]
    F["GenerateAnswer<br/>(Node)<br/>GENERATE via LLM prompt template"]
    G{Output path<br/>supplied?}
    H["write_file<br/>(side-effect)<br/>persist Q/A pair to disk"]
    D -->|"@query_embedding"| E
    E -->|"@retrieved_document<br/>{text, index, distance}"| F
    F -->|"@generated_answer"| G
    G -->|Yes| H
    G -->|No| END
    H --> END
    end
    START --> A
    C -->|"@index stored"| S3
    C -->|done| D
    D --- S4
    D --- S5
    E --- S3
    E --- S1
    F --- S4
    F --- S6
    F --- S7
    END([Return @generated_answer])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/sonnet/S2-rag-claude_cli-sonnet.mmd -o S2-rag-claude_cli-sonnet.spl`
4. Validate: `spl3 validate S2-rag-claude_cli-sonnet.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
