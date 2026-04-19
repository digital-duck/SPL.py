# Testing spl-go with the Cookbook

`cookbook_catalog-go.json` mirrors the standard catalog but runs every recipe through the `spl-go` binary (zero-dependency Go runtime). Use it to catch regressions and find missing functionality before they reach production.

## Prerequisites

- `spl-go` binary on your PATH (built from `~/projects/digital-duck/SPL.go/`)
- Ollama running locally (`ollama serve`)

```bash
# Verify spl-go is reachable
spl-go version

# Rebuild if needed  (~/.local/bin/spl-go is a symlink — just rebuild in place)
cd ~/projects/digital-duck/SPL.go && go build -o spl-go .
```

## Run all active recipes against spl-go

```bash
cd ~/projects/digital-duck/SPL20

# Sequential (recommended for first pass — shows live output)
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json 2>&1 | tee cookbook/logs/run_all_go_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json \
    --ids "4, 14, 17, 25, 06, 37, 13, 36, 41–44, 47–49" \
    2>&1 | tee cookbook/logs/run_all_go_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json \
    --ids "4, 6,13,14,17,25,36,37" \
    2>&1 | tee cookbook/logs/run_all_go_$(date +%Y%m%d_%H%M%S).md


# Override model
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json --model llama3.2

# Run specific recipes by ID
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json --ids 01,02,05,07
```

## Browse the go catalog

```bash
# Full table
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json --catalog

# Filter by category
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json --catalog --category agentic

# What's disabled and why
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json --catalog --status disabled
```

## Disabled recipes and why

| Recipes | Reason | Status |
|---|---|---|
| 06, 37 | `claude_cli` adapter | **Unblocked ✓ 2026-04-18** — `claude_cli` adapter exists; use `--adapter claude_cli --allowed-tools WebSearch` |
| 13, 36, 41–44, 47–49 | `--tools` Python plugin | **Unblocked ✓ 2026-04-18** — `--tools path/to/tools.py` loads `@spl_tool` functions via subprocess |
| 22 | Shell script calls `spl2` internally | **Unblocked ✓ 2026-04-18** — `--spl-bin spl-go` flag; catalog enabled; `--no-validate` bug fixed |
| 04 | `qwen2.5` model not installed | **Fixed ✓ 2026-04-18** — catalog overrides `model_3=llama3.2` |
| 06 | `--claude-allowed-tools` wrong flag name | **Fixed ✓ 2026-04-18** — corrected to `--allowed-tools`; recipe enabled |
| 17 | `COUNT()` not in Go stdlib + `qwen2.5` missing | **Fixed ✓ 2026-04-18** — `count` alias added; catalog overrides `models=["gemma3","phi4","llama3.2"]` |
| 38, 39, 40 | Bedrock / Vertex / Azure adapters not in spl-go | Still blocked — port cloud-provider adapters |

### Using `--tools`

```bash
# Recipe 36 — Tool-Use (deterministic math via Python, narrative via LLM)
spl-go run cookbook/36_tool_use/tool_use.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/36_tool_use/tools.py \
    sales="1200,1450,1380,1600,1750,1900"

# Recipe 13 — Map-Reduce
spl-go run cookbook/13_map_reduce/map_reduce.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/13_map_reduce/tools.py

# Recipe 41 — Human Steering
spl-go run cookbook/41_human_steering/human_steering.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/41_human_steering/tools.py
```

The `--tools` flag loads any Python file with `@spl_tool`-decorated functions.
Each function becomes a CALL-able tool in the SPL workflow — dispatched before
procedures and LLM fallback. Python itself is invoked as a subprocess; no Python
interpreter is embedded in the Go binary.

### Using `claude_cli` adapter

```bash
# Recipe 37 — Headline News (claude_cli, no WebSearch needed)
spl-go run cookbook/37_headline_news/headline_news.spl \
    --adapter claude_cli --model claude-opus-4-6 \
    topic="artificial intelligence"

# Recipe 06 — ReAct Agent (claude_cli + WebSearch tool)
spl-go run cookbook/06_react_agent/react_agent.spl \
    --adapter claude_cli --model claude-sonnet-4-6 \
    --allowed-tools WebSearch \
    --tools cookbook/06_react_agent/tools.py \
    country="France"
```

## Logs

Each recipe writes a `-go.md` suffixed log to `~/.spl/logs/` (e.g. `hello-ollama-20260413-103000-go.md`), making it easy to distinguish from Python runtime logs in the same directory.

## Comparing runtimes side by side

```bash
# Run the same recipe on both runtimes, then diff the logs
spl     run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-go  run ./cookbook/01_hello_world/hello.spl --adapter ollama

ls -lt ~/.spl/logs/hello-* | head -4
```


## latest test results

=== Summary: 3/8 Success  (total 167.3s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
04    Model Showdown                FAILED       15.4s
06    ReAct Agent                   FAILED        0.0s
13    Map-Reduce Summarizer         OK           16.1s
14    Multi-Agent Collaboration     FAILED        0.0s
17    Tree of Thought               FAILED       93.4s
25    Nested Procedures             FAILED        0.0s
36    Tool-Use / Function-Call      OK           11.2s
37    Headline News Aggregator      OK           31.2s

=== Summary: 5/8 Success  (total 572.7s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
04    Model Showdown                FAILED       38.2s
06    ReAct Agent                   FAILED        0.0s
13    Map-Reduce Summarizer         OK           24.6s
14    Multi-Agent Collaboration     OK          202.9s
17    Tree of Thought               FAILED      159.6s
25    Nested Procedures             OK           98.1s
36    Tool-Use / Function-Call      OK           11.4s
37    Headline News Aggregator      OK           38.0s

---

● FEATURES.md is already updated — I did that at the end of the last step, marking recipes 05, 50, 63, 64 as [DONE] ¹ for 
  spl-go with the footnote explaining echo-adapter verification.
                                                                                                                          
Yes, that's exactly the right plan:
                                                                                                                        
1. You run the four recipes with --adapter ollama (live LLM)                                                            
2. If they pass — upgrade [DONE] ¹ to [DONE] (drop the footnote qualifier) in FEATURES.md
3. If a new error surfaces — it'll be an executor-level issue (variable binding, OUTPUT handling, etc.), not a parser   
issue, so we fix it there                                                                                               
                                                                                                                        
The commands to run:                                                                                                    
```bash
cd ~/projects/digital-duck/SPL30

spl-go run cookbook/05_self_refine/self_refine.spl \
    --adapter ollama \
    --param writer_model="gemma3" \
    --param critic_model="gemma3" \
    --param max_iterations=1

spl-go run cookbook/50_code_pipeline/code_pipeline.spl \
    --adapter ollama \
    --param model="gemma3" \
    --param log_dir="cookbook/50_code_pipeline/logs-spl-go" \
    --param spec="write a Python function that reverses a string" 

export SPEC="write a Python function reverse_string(s: str) -> str that returns the input string with characters in reverse order, handles empty string by returning empty string"
export MODEL="gemma4:e4b"            #   "gemma3"
spl-go run cookbook/50_code_pipeline/code_pipeline.spl \
    --adapter ollama \
    --param model="$MODEL" \
    --param log_dir="cookbook/50_code_pipeline/logs-spl-go" \
    --param spec="$SPEC" 


spl-go run cookbook/63_parallel_code_review/parallel_code_review.spl \
    --adapter ollama \
    --param model="gemma4:e4b" \
    --param code="def add(a, b): return a - b"

spl-go run cookbook/64_parallel_news_digest/parallel_news_digest.spl \
    --adapter ollama \
    --param model="gemma4:e4b" \
    --param topic="AI"
```                                                                                                                  
Run them from the SPL30/ directory so relative IMPORT paths resolve correctly.       