# S2 Agent Ollama Gemma3 Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/ollama/gemma3/S1-agent-ollama-gemma3-1-spec.md --adapter ollama --model gemma3 -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/ollama/gemma3/S2-agent-ollama-gemma3.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[User Query] --> B{{Decision Node}}
    B -- Search --> C[Search Node]
    C --> D[DuckDuckGo]
    B -- Answer --> E[Answer Node]
    E --> F[LLM - Answer Generation]
    F --> E
    E --> G[Agent Output]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/ollama/gemma3/S2-agent-ollama-gemma3.mmd -o S2-agent-ollama-gemma3.spl`
4. Validate: `spl3 validate S2-agent-ollama-gemma3.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
