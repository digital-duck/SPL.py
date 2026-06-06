# S2 Agent Claude Cli Claude Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S1-agent-claude_cli-claude-1-spec.md --adapter claude_cli --model claude-sonnet-4-6 -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S2-agent-claude_cli-claude.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["Initialize<br/>@question from CLI<br/>@context = 'No previous search'"]
    B --> C["GENERATE decide_action<br/>LLM produces fenced YAML block"]
    C --> D{"YAML parse<br/>success?"}
    D -->|No| E["Force block scalars<br/>on known keys, retry"]
    E --> F{"Retry parse<br/>success?"}
    F -->|No| Z([ValueError / Exception])
    F -->|Yes| G{"EVALUATE<br/>@decision.action?"}
    D -->|Yes| G
    G -->|action == search| H["Set @search_query<br/>from @decision"]
    H --> I["CALL search_web<br/>DuckDuckGo(@search_query)"]
    I --> J["Append SEARCH + RESULTS<br/>block to @context"]
    J -->|loop back| C
    G -->|action == answer| K["GENERATE answer_question<br/>LLM synthesizes prose answer"]
    K --> L["Store result<br/>as @answer"]
    L --> M(["RETURN @answer<br/>status = done"])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S2-agent-claude_cli-claude.mmd -o S2-agent-claude_cli-claude.spl`
4. Validate: `spl3 validate S2-agent-claude_cli-claude.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
