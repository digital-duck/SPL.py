# S2 Agent Claude Cli Claude Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S1-agent-claude_cli-claude-1-spec.md --adapter claude_cli --model claude-sonnet-4-6 -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/claude_cli/claude/S2-agent-claude_cli-claude.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start: Set @question from CLI\n@context = 'No previous search'] --> B[GENERATE decide_action\n@question + @context → YAML decision]
    B --> C{{Parse YAML safely}}
    C -->|Parse OK| D{{EVALUATE @decision action}}
    C -->|YAMLError| E[Force block-scalar on known keys\nRewrite lines with pipe notation]
    E --> F{{Retry yaml.safe_load}}
    F -->|Parse OK| D
    F -->|Still fails| G[Raise ValueError\nEXCEPTION: YAMLParseError]
    D -->|action == search| H[Set @search_query from decision]
    H --> I[CALL search_web_duckduckgo\n@search_query → up to 5 results]
    I --> J[Append to @context\nSEARCH: query\nRESULTS: results]
    J -->|return decide — loop back| B
    D -->|action == answer| K[GENERATE answer_question\n@question + @context → prose answer]
    K --> L[Store result in @answer]
    L --> M[RETURN @answer\nstatus = done]
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
