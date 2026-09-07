[INFO] [parallel_code_review] starting 3-way parallel review | lang=python review_model=gemma4
[DEBUG] [style_review] lang=python
[DEBUG] [security_audit] lang=python
[DEBUG] [test_generator] lang=python
Error: execution error: CALL PARALLEL branch "security_audit": ModelUnavailable: GENERATE security_audit_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

CALL PARALLEL branch "test_generator": ModelUnavailable: GENERATE test_generator_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

CALL PARALLEL branch "style_review": ModelUnavailable: GENERATE style_review_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

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

execution error: CALL PARALLEL branch "security_audit": ModelUnavailable: GENERATE security_audit_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

CALL PARALLEL branch "test_generator": ModelUnavailable: GENERATE test_generator_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

CALL PARALLEL branch "style_review": ModelUnavailable: GENERATE style_review_prompt: ollama: HTTP 404: {"error":{"message":"model 'gemma4' not found","type":"not_found_error","param":null,"code":null}}

