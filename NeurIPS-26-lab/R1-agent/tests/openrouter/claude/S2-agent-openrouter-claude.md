# S2 Agent Openrouter Claude Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/claude/S1-agent-openrouter-claude-1-spec.md --adapter openrouter --model anthropic/claude-sonnet-4.6 -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/claude/S2-agent-openrouter-claude.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A([Start]) --> B[Initialize shared state\n@question from CLI input\n@context = No previous search]
    B --> C[DecideAction\nGENERATE YAML decision\nfrom @question and @context]
    C --> D[Parse YAML response\nextract action field]
    D --> E{{YAML Parse\nSuccessful?}}
    E -->|No - YAMLError| F[Attempt block-scalar\nregex repair]
    F --> G{{Repair\nSuccessful?}}
    G -->|Yes| H[Re-parse repaired YAML]
    H --> I{{action field\nvalue?}}
    G -->|No| J[Raise ValueError\nEXCEPTION ParseError]
    J --> K([Workflow Error Exit])
    E -->|Yes| I
    I -->|action == search| L[Write @search_query\nto shared state]
    L --> M[SearchWeb\nCALL search_web_duckduckgo\nwith @search_query]
    M --> N[Retrieve up to 5\nDuckDuckGo results\nTitle / URL / Snippet blocks]
    N --> O[Append to @context\nSEARCH: query\nRESULTS: results]
    O --> P[Return decide\nroute back to DecideAction]
    P --> C
    I -->|action == answer| Q[AnswerQuestion\nGENERATE final answer\nfrom @question and @context]
    Q --> R[Store plain prose\nresponse in @answer]
    R --> S{{Output file\npath specified?}}
    S -->|Yes - --out flag| T[CALL write_file\nwrite @answer to file path]
    T --> U[Return done\nstatus = done]
    S -->|No| U
    U --> V[RETURN @answer\nWITH status=done]
    V --> W([End])
    style A fill:#4CAF50,color:#fff
    style W fill:#4CAF50,color:#fff
    style K fill:#f44336,color:#fff
    style C fill:#2196F3,color:#fff
    style M fill:#FF9800,color:#fff
    style Q fill:#9C27B0,color:#fff
    style J fill:#f44336,color:#fff
    style P fill:#607D8B,color:#fff
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/claude/S2-agent-openrouter-claude.mmd -o S2-agent-openrouter-claude.spl`
4. Validate: `spl3 validate S2-agent-openrouter-claude.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
