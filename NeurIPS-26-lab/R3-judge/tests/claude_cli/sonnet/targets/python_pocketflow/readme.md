## S3-judge-claude_cli-sonnet — PocketFlow Judge Workflow

### Setup

```bash
conda activate spl123
pip install pocketflow          # minimalist ETL-style LLM orchestration
# claude CLI must be on PATH and authenticated
claude --version
```

### Run

```bash
# Default task
python S3-judge-claude_cli-sonnet.py

# Custom task
python S3-judge-claude_cli-sonnet.py "explain quantum entanglement for a high-school student"

python /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/claude_cli/sonnet/targets/python_pocketflow/S3-judge-claude_cli-sonnet_python_pocketflow.py \
"explain quantum entanglement for a high-school student"

```



### Expected Output Pattern

```
Task      : explain quantum entanglement for a high-school student

Status    : pass          # or "max_attempts" if all retries exhausted
Attempts  : 1             # 0–2 retries consumed (0 = passed on first try)

--- Final Description ---
<refined multi-paragraph response>

--- Final Score ---
VERDICT: PASS, Score: 8, Feedback: Clear and well-structured...
```

### SPL → PocketFlow Construct Map

| SPL construct | PocketFlow equivalent |
|---|---|
| `CREATE FUNCTION f(...) RETURNS TEXT AS $$ ... $$` | Module-level `_f()` helper calling `_call_llm()` |
| `WORKFLOW judge_workflow` | `run_judge_workflow()` entry point + `build_flow()` |
| `INPUT @task TEXT` | `shared["task"]` key seeded before `flow.run(shared)` |
| `OUTPUT @final_description TEXT` | `shared["final_description"]` read after `flow.run()` |
| `@var := value` | `shared["var"] = value` in `post()` |
| `GENERATE f(...) INTO @var` | `Node.exec()` calls the LLM helper; `Node.post()` writes `shared["var"]` |
| `EVALUATE @judgment WHEN contains(...) THEN ... ELSE ... END` | `CheckVerdictNode.exec()` / `.post()` with conditional `return "pass"` / `return "retry"` / `return "max_attempts"` |
| `WHILE @attempts < 3 DO ... END` | `check - "retry" >> generate` back-edge; `MAX_ATTEMPTS = 3` guard in `CheckVerdictNode.post()` |
| `RETURN @var WITH status = "pass"` | `shared["status"] = "pass"; return "pass"` — terminal action (no outgoing edge) |
| `RETURN @var WITH status = "max_attempts"` | `shared["status"] = "max_attempts"; return "max_attempts"` — terminal action |

### Flow Graph

```
GenerateDraftNode ──► EvaluateDraftNode ──► CheckVerdictNode
        ▲                                          │
        │                 "retry" (attempts < 3) ◄─┤
        └──────────────────────────────────────────┘
                                                   │
                          "pass" or "max_attempts" ──► (terminal / Flow ends)
```