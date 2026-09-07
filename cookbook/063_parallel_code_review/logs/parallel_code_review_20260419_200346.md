[INFO] [parallel_code_review] starting 3-way parallel review | lang=python review_model=gemma3
[DEBUG] [style_review] lang=python
[DEBUG] [test_generator] lang=python
[DEBUG] [security_audit] lang=python
Error: execution error: CALL PARALLEL branch "security_audit": ModelUnavailable: GENERATE security_audit_prompt: momagrid: task 76cc61b3-4382-4029-909b-888a5e7e2d5b timed out after 5m0s
CALL PARALLEL branch "test_generator": ModelUnavailable: GENERATE test_generator_prompt: context canceled
CALL PARALLEL branch "style_review": ModelUnavailable: GENERATE style_review_prompt: context canceled
Usage:
  spl-go run <file.spl> [KEY=VALUE...] [flags]

Flags:
      --allowed-tools stringArray   Tools to allow for claude_cli adapter (e.g. --allowed-tools WebSearch Bash)
  -h, --help                        help for run
  -p, --param stringArray           Parameter as KEY=VALUE (repeatable)
      --plan                        Show pre-execution plan and resource estimates
      --tools string                Path to Python tools file (.py) — registers @spl_tool functions as CALL-able tools
      --workers int                 Number of parallel workers for independent workflow steps (0 = sequential)

Global Flags:
  -a, --adapter string   LLM adapter (echo, ollama, momagrid)
      --model string     LLM model name
  -v, --verbose          Enable verbose output

execution error: CALL PARALLEL branch "security_audit": ModelUnavailable: GENERATE security_audit_prompt: momagrid: task 76cc61b3-4382-4029-909b-888a5e7e2d5b timed out after 5m0s
CALL PARALLEL branch "test_generator": ModelUnavailable: GENERATE test_generator_prompt: context canceled
CALL PARALLEL branch "style_review": ModelUnavailable: GENERATE style_review_prompt: context canceled
