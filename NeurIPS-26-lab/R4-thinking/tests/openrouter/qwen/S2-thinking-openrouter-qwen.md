# S2 Thinking Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S1-thinking-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S2-thinking-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["Init State:<br/>Problem & Plan"]
    B --> C
    subgraph LOOP["ChainOfThought Loop"]
    C{"WHILE: next_thought_needed?"}
    D["CREATE FUNCTION:<br/>Assemble Prompt"]
    E["GENERATE:<br/>Call LLM & Parse"]
    F{"YAML/Schema<br/>Valid?"}
    G["EXCEPTION:<br/>Catch & Recover"]
    H{"Continue Loop?"}
    I["Update State &<br/>Stream Progress"]
    C -->|True| D
    D --> E
    E --> F
    F -->|No| G
    G --> C
    F -->|Yes| H
    H -->|True| I
    I --> C
    end
    H -->|False| J["Extract Final<br/>Solution"]
    J --> K["Side-Effects:<br/>Print & Save File"]
    K --> L["RETURN:<br/>Output & Metadata"]
    L --> M([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S2-thinking-openrouter-qwen.mmd -o S2-thinking-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-thinking-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
