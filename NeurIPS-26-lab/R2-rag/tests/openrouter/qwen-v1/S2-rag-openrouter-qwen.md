# S2 Rag Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S1-rag-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S2-rag-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start Workflow] --> B[Initialize @texts]
    B --> C[WHILE: Chunk Documents via CALL]
    C --> D[Embed Chunks via CALL]
    D --> E[CALL: Construct FAISS @index]
    E --> F[CALL: Embed User Query]
    F --> G[CALL: Vector Similarity Search]
    G --> H{{Distance Exceeds Threshold?}}
    H -->|Yes| I[Trigger Fallback Response]
    H -->|No| J[GENERATE via AnswerSynthesis]
    J --> K[RETURN Answer & Metadata]
    I --> K
    C -->|Error| L[EXCEPTION Handler: Log & Degrade]
    D -->|Error| L
    F -->|Error| L
    G -->|Error| L
    J -->|Error| L
    L --> K
    K --> M[End Workflow]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/qwen/S2-rag-openrouter-qwen.mmd -o S2-rag-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-rag-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
