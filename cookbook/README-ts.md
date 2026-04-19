# Testing spl-ts with the Cookbook

`cookbook_catalog_ts.json` mirrors the standard catalog but runs every recipe through the `spl-ts` binary (TypeScript runtime). Use it to catch regressions and find missing functionality before they reach production.

## Prerequisites

- `spl-ts` binary on your PATH (`~/.local/bin/spl-ts` is a symlink into `~/projects/digital-duck/SPL.ts/`)
- Ollama running locally (`ollama serve`)

```bash
# Verify spl-ts is reachable
spl-ts --version

# Rebuild if needed  (~/.local/bin/spl-ts is a symlink — just rebuild in place)
cd ~/projects/digital-duck/SPL.ts && npm run build
```

## Run all active recipes against spl-ts

```bash
cd ~/projects/digital-duck/SPL20

# Sequential (recommended for first pass — shows live output)
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json 2>&1 | tee cookbook/out/run_all_ts_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json \
    --ids "04,06,12,13,14,18,20,25,26,28-33,36,37,41-44,47-49" \
    2>&1 | tee cookbook/out/run_all_ts_$(date +%Y%m%d_%H%M%S).md

python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json \
    --ids "12,18,20,25,26,28,29,30,31,32,33,49" \
    2>&1 | tee cookbook/out/run_all_ts_$(date +%Y%m%d_%H%M%S).md

# Override model
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --model llama3.2

# Run specific recipes by ID
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --ids 01,02,05,07
```

## Browse the ts catalog

```bash
# Full table
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog

# Filter by category
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog --category agentic

# What's disabled and why
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog --status disabled
```

## Disabled recipes and why

| Recipes | Reason | Unblocked by |
|---|---|---|
| 08 | `rag.query()` not yet implemented | Implement RAG built-in in spl-ts |
| 19 | `memory.get/set` not yet implemented | Implement memory built-ins in spl-ts |
| 22 | Shell script calls `spl2` internally | Rewrite `text2spl_demo.sh` for spl-ts |
| 38, 39, 40 | Bedrock / Vertex / Azure adapters not in spl-ts | Port cloud-provider adapters to TypeScript |
| 41 | `wait_for_human_feedback` reads from stdin — incompatible with JSON-RPC bridge | Redesign for non-interactive use |
| 47 | `tools.py` requires `dd_cache` + `dd_extract` packages not installed | Install deps or rewrite tools.py |

## Logs

Each recipe writes a `-ts.md` suffixed log to `~/.spl/logs/` (e.g. `hello-ollama-20260418-103000-ts.md`), making it easy to distinguish from Python and Go runtime logs in the same directory.

## Comparing runtimes side by side

```bash
# Run the same recipe on all three runtimes, then compare logs
spl     run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-go  run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-ts  run ./cookbook/01_hello_world/hello.spl --adapter ollama

ls -lt ~/.spl/logs/hello-* | head -6
```



## latest test results

=== Summary: 8/24 Success  (total 160.2s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
04    Model Showdown                OK            1.0s
06    ReAct Agent                   FAILED        0.0s
12    Plan and Execute              FAILED       52.1s
13    Map-Reduce Summarizer         OK           14.0s
14    Multi-Agent Collaboration     FAILED        0.0s
18    Guardrails Pipeline           FAILED        0.0s
20    Ensemble Voting               FAILED        0.0s
25    Nested Procedures             FAILED        0.0s
26    Prompt A/B Test               FAILED        0.0s
28    Customer Support Triage       FAILED        0.0s
29    Meeting Notes to Actions      FAILED        0.0s
30    Code Generator + Tests        FAILED        0.0s
31    Sentiment Pipeline            FAILED        0.0s
32    Socratic Tutor                FAILED        0.0s
33    Interview Simulator           FAILED        0.0s
36    Tool-Use / Function-Call      OK           11.3s
37    Headline News Aggregator      OK           27.4s
41    Human Steering                FAILED        2.6s
42    Knowledge Synthesis           OK            1.2s
43    Prompt Self-Tuning            OK            6.2s
44    Adaptive Failover             OK           28.8s
47    arXiv Morning Brief           FAILED        0.1s
48    Credit Risk Assessment        OK           11.3s
49    Regulatory News Audit         FAILED        3.9s

