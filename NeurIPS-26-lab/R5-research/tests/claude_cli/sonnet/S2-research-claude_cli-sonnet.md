# S2 Research Claude Cli Sonnet Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/claude_cli/sonnet/S1-research-claude_cli-sonnet-1-spec.md --adapter claude_cli --model claude-sonnet-4-6 -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/claude_cli/sonnet/S2-research-claude_cli-sonnet.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["planner(topic, feedback='')"]
    B --> C["@queries: 3 search queries"]
    C --> D{loop_count >= 2?}
    D -->|Yes - force finalize| E["synthesizer forced:<br/>write_concise_report(topic, notes)"]
    D -->|No| F["researcher batch:<br/>CALL search_web(query)"]
    F --> G["GENERATE extract facts<br/>per query in parallel"]
    G --> H["ACCUMULATE @note_set<br/>INTO @notes"]
    H --> I["GENERATE synthesizer<br/>(topic, notes, loop_count)"]
    I --> J{"EVALUATE @decision<br/>action?"}
    J -->|action == research| K["loop_count += 1<br/>@feedback = decision.feedback"]
    K --> L["GENERATE planner<br/>(topic, feedback)"]
    L --> M["@queries updated"]
    M --> D
    J -->|action == finalize| N["@report = decision.content"]
    E --> N
    N --> O["CALL write_file<br/>(report, path=out)"]
    O --> P(["RETURN @report<br/>status='complete'"])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/claude_cli/sonnet/S2-research-claude_cli-sonnet.mmd -o S2-research-claude_cli-sonnet.spl`
4. Validate: `spl3 validate S2-research-claude_cli-sonnet.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
