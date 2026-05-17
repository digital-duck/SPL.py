# Few Shot Workflow

Generated from `few_shot.spl` via `spl3 spl2mmd` (AST-direct, no LLM).

## Mermaid Diagram

```mermaid
flowchart TD
    subgraph SG_few_shot_classifier["PROMPT: few_shot_classifier"]
    direction TB
    START1(["Start"])
    SEL2["SELECT  SystemRoleCall,  examples,  text,  domain"]
    START1 --> SEL2
    GEN3[/"GENERATE classify(text, examples)"/]
    SEL2 --> GEN3
    END4(["End"])
    GEN3 --> END4
    end
    class START1 term
    class SEL2 assign
    class GEN3 llm
    class END4 term
    classDef llm fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    classDef term fill:#fce7f3,stroke:#ec4899,color:#831843
    classDef fn fill:#f0fdf4,stroke:#86efac,color:#166534
    classDef assign fill:#f8fafc,stroke:#64748b,color:#1e293b
```
