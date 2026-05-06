# S2 Thinking Claude Cli Sonnet Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/S1-thinking-claude_cli-sonnet-1-spec.md --adapter claude_cli --model claude-sonnet-4-6 -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/S2-thinking-claude_cli-sonnet.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["Initialize shared state:<br/>@problem, @thoughts=[], @thought_number=0, @solution=None"]
    B --> C
    subgraph LOOP["ChainOfThought Loop (continue action)"]
    C["prep():<br/>Format @thoughts to @thoughts_text<br/>Extract last plan to @last_plan_text<br/>Increment @current_thought_number"]
    D["exec():<br/>GENERATE ChainOfThoughtStep<br/>(@problem, @thoughts_text,<br/>@last_plan_text, @thought_number)<br/>INTO @thought_data"]
    E{Assert required<br/>YAML fields?}
    F["Retry<br/>max_retries=3, wait=10s"]
    G["post():<br/>Append @thought_data to @thoughts"]
    H{next_thought_needed?}
    J["Print current_thinking<br/>and updated plan"]
    C --> D
    D --> E
    E -->|Fail - YAMLError| F
    F --> D
    E -->|Pass| G
    G --> H
    H -->|true - continue| J
    J --> C
    end
    H -->|false - end| I["Set @solution = current_thinking<br/>RETURN status=complete<br/>iterations=thought_number"]
    I --> K([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/S2-thinking-claude_cli-sonnet.mmd -o S2-thinking-claude_cli-sonnet.spl`
4. Validate: `spl3 validate S2-thinking-claude_cli-sonnet.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
