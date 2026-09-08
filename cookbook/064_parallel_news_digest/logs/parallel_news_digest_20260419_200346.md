[DEBUG] [summarise_single] topic=""
Error: execution error: ModelUnavailable: GENERATE summarise_topic: momagrid: task 999e12ed-d6c9-406c-95ce-d0e8f3ad5a1c timed out after 5m0s
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

execution error: ModelUnavailable: GENERATE summarise_topic: momagrid: task 999e12ed-d6c9-406c-95ce-d0e8f3ad5a1c timed out after 5m0s
