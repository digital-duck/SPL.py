# Self Refine Workflow

Generated from `self_refine.spl` via `spl3 spl2mmd` (AST-direct, no LLM).

## Mermaid Diagram

```mermaid
flowchart TD
    FN1["FUNCTION draft()"]
    FN2["FUNCTION critique()"]
    FN3["FUNCTION refine()"]
    subgraph SG_self_refine["WORKFLOW: self_refine"]
    direction TB
    START4(["Start"])
    A5["@iteration := 0"]
    LOG6>"LOG(INFO) f'Self-refine starte...'"]
    A5 --> LOG6
    GEN7[/"GENERATE draft(@task) -> @current"/]
    LOG6 --> GEN7
    LOG8>"LOG(INFO) 'Initial draft ready'"]
    GEN7 --> LOG8
    SUB9[["CALL write_file(f'(@log_d..., @current)"]]
    LOG8 --> SUB9
    WHILE10{"WHILE: @iteration < @max_iterations"}
    LOG11>"LOG(DEBUG) f'Iteration (@iterat...'"]
    GEN12[/"GENERATE critique(@current) -> @feedback"/]
    LOG11 --> GEN12
    SUB13[["CALL write_file(f'(@log_d..., @feedback)"]]
    GEN12 --> SUB13
    EVAL14{"EVALUATE: @feedback"}
    LOG16>"LOG(INFO) f'Approved at iterat...'"]
    SUB17[["CALL write_file(f'(@log_d..., @current)"]]
    LOG16 --> SUB17
    RET18(["RETURN @current (status='comp..., iterations=@iter...)"])
    SUB17 --> RET18
    EVAL14 -->|WHEN contains:(APPROVED)| LOG16
    A19["@iteration := @iteration + 1"]
    GEN20[/"GENERATE refine(@current, @feedback) -> @current"/]
    A19 --> GEN20
    LOG21>"LOG(DEBUG) f'Refined | iteratio...'"]
    GEN20 --> LOG21
    SUB22[["CALL write_file(f'(@log_d..., @current)"]]
    LOG21 --> SUB22
    EVAL14 -->|ELSE| A19
    SUB22 --> MERGE15
    MERGE15[" "]
    SUB13 --> EVAL14
    WHILE10 -->|True| LOG11
    MERGE15 -.-> WHILE10
    SUB9 --> WHILE10
    LOG23>"LOG(WARN) f'Max iterations rea...'"]
    WHILE10 --> LOG23
    SUB24[["CALL write_file(f'(@log_d..., @current)"]]
    LOG23 --> SUB24
    RET25(["RETURN @current (status='max_..., iterations=@iter...)"])
    SUB24 --> RET25
    START4 --> A5
    END26(["End"])
    EXC27{"EXCEPTION MaxIterationsReached"}
    SUB28[["CALL write_file(f'(@log_d..., @current)"]]
    RET29(["RETURN @current (status='part...)"])
    SUB28 --> RET29
    EXC27 --> SUB28
    EXC30{"EXCEPTION BudgetExceeded"}
    RET31(["RETURN @current (status='budg...)"])
    EXC30 --> RET31
    end
    class FN1 fn
    class FN2 fn
    class FN3 fn
    class START4 term
    class A5 assign
    class LOG6 log
    class GEN7 llm
    class LOG8 log
    class SUB9 proc
    class WHILE10 ctrl
    class LOG11 log
    class GEN12 llm
    class SUB13 proc
    class EVAL14 ctrl
    class LOG16 log
    class SUB17 proc
    class RET18 term
    class A19 assign
    class GEN20 llm
    class LOG21 log
    class SUB22 proc
    class LOG23 log
    class SUB24 proc
    class RET25 term
    class END26 term
    class EXC27 ctrl
    class SUB28 proc
    class RET29 term
    class EXC30 ctrl
    class RET31 term
    classDef llm fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    classDef proc fill:#fef3c7,stroke:#f59e0b,color:#78350f
    classDef ctrl fill:#ede9fe,stroke:#8b5cf6,color:#3b0764
    classDef term fill:#fce7f3,stroke:#ec4899,color:#831843
    classDef log fill:#f8fafc,stroke:#94a3b8,color:#64748b
    classDef fn fill:#f0fdf4,stroke:#86efac,color:#166534
    classDef assign fill:#f8fafc,stroke:#64748b,color:#1e293b
```
