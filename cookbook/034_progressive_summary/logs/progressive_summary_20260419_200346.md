[INFO] Progressive summary | audience=executive layers=3
Error: execution error: ModelUnavailable: GENERATE summarize: momagrid: task 26e174ef-fa3e-4818-8d38-9eb96576e49b timed out after 5m0s
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

execution error: ModelUnavailable: GENERATE summarize: momagrid: task 26e174ef-fa3e-4818-8d38-9eb96576e49b timed out after 5m0s
