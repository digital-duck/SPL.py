# SPL — Structured Prompt Language

**SPL** is a declarative language for agentic AI workflows — SQL for LLMs.

Where SQL abstracts over databases, SPL abstracts over language models: the same `.spl` file runs on Ollama, Claude, OpenAI, Gemini, or a Momagrid compute grid without changing a single line of workflow code.

```sql
WORKFLOW self_refine
    INPUT:  @topic TEXT
    OUTPUT: @essay TEXT
DO
    GENERATE writer(@topic) INTO @essay
    CALL critique_workflow(@essay) INTO @feedback
    GENERATE refiner(@essay, @feedback) INTO @essay
    COMMIT @essay
END
```

```bash
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama --param topic="the Tao of coding"
```

## Why SPL

Most agentic frameworks require hundreds of lines of imperative Python to wire up prompts, manage context, handle errors, and switch LLM providers. SPL takes a different path: **declare what you want, not how to get it.**

| Concern | Framework approach | SPL approach |
|---|---|---|
| Provider switch | Rewrite adapter glue code | `--adapter ollama` → `--adapter momagrid` |
| Retry logic | Try/except boilerplate | `RETRY` / `EXCEPTION WHEN` |
| Sub-agent calls | Async queue + callback hell | `CALL workflow_name() INTO @result` |
| Parallel agents | `asyncio.gather` + coordination | `CALL PARALLEL ... END` |
| Token budgets | Manual prompt trimming | `OPTIMIZE ... WITHIN 2000 TOKENS` |

## Language Layers

SPL synthesizes three programming paradigms:

| Layer | Inspiration | SPL construct |
|---|---|---|
| Data | SQL | `SELECT`, `WITH`, `GENERATE` |
| Logic | Python | `CALL`, `@spl_tool`, typed variables |
| Orchestration | Linux shell | `WORKFLOW` composition, `IMPORT` |

## Version History

| Version | Highlights |
|---|---|
| **1.0** | `SELECT … GENERATE` paradigm; single-query `PROMPT` statements; lexer, parser, executor foundation |
| **2.0** | Multi-step `WORKFLOW`; `PROCEDURE`; `EVALUATE` (semantic branching); `WHILE`; 14 LLM adapters; text2SPL compiler; Momagrid adapter |
| **3.0** | Workflow-to-workflow `CALL`; `CALL PARALLEL`; `IMPORT`; Hub registry; Hub-to-Hub peering; multimodal codecs (image / audio / video); `splc` transpiler (Go, TypeScript, LangGraph) |

## Quick Start

```bash
conda create -n spl123 python=3.11
conda activate spl123        # Python 3.11+

pip install -e ".[dev]"      # install from this repo

# Verify install
spl3 --help

# Run hello world (Ollama)
spl3 run cookbook/01_hello_world/hello.spl --adapter ollama

# Run self-refine with a local model
spl3 run cookbook/05_self_refine/self_refine.spl \
    --adapter ollama \
    --param writer_model=gemma3 \
    --param critic_model=gemma3

# Run all active recipes
python cookbook/run_all.py

# Run a specific subset
python cookbook/run_all.py --ids 01,05,13

# Run multimodal / SPL 3.0 recipes (tier 1 = Ollama only)
python cookbook/run_all.py --tier 1 --category multimodal
```

## CLI Reference

```bash
spl3 run   <file.spl> [--adapter NAME] [--model MODEL] [--param KEY=VALUE ...]
spl3 validate  <file.spl>
spl3 explain   <file.spl>
spl3 text2spl  "natural language description" [--mode prompt|workflow|auto]
spl3 code-rag  seed <dir> --catalog <catalog.json>
spl3 code-rag  query "judge-retry loop"
spl3 --hub http://localhost:8080 run <file.spl>       # Hub-backed registry
spl3 --hub http://localhost:8080 register <dir/>       # register workflows on Hub
```

## Adapters

Four adapters form the **mandatory baseline** that every SPL runtime must support — they cover the full development lifecycle from local prototyping to production grid deployment:

| Adapter | Provider | Stage | Notes |
|---|---|---|---|
| `ollama` | Local models | Local prototyping | Zero cost, zero credentials, works offline — lowest barrier to entry |
| `claude_cli` | Claude Code CLI | Best-model validation | Top-tier Anthropic models; subscription billing, no per-call cost |
| `openrouter` | 200+ models | Broad model coverage | Single key unlocks frontier + open-source models for cross-model testing |
| `momagrid` | Decentralized GPU grid | Production grid | SPL workflows as system calls dispatched across owned GPU hardware |

Additional adapters available in the Python (`spl3`) runtime:

| Adapter | Provider | Notes |
|---|---|---|
| `anthropic` | Claude (Anthropic API) | `ANTHROPIC_API_KEY` |
| `openai` | GPT / o-series | `OPENAI_API_KEY` |
| `google` | Gemini | `GOOGLE_API_KEY` |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` |
| `qwen` | Qwen (Alibaba) | `DASHSCOPE_API_KEY` |
| `bedrock` | AWS Bedrock | boto3 + AWS credentials |
| `vertex` | GCP Vertex AI | `GOOGLE_CLOUD_PROJECT` + ADC |
| `azure_openai` | Azure OpenAI | `AZURE_OPENAI_ENDPOINT` + key |
| `dd_llm_bridge` | Any dd-llm provider | Generic bridge |

> **Porting checklist**: Any new SPL runtime port must implement the four mandatory adapters before being considered feature-complete. `echo` is testing scaffolding only.

## Architecture

```
spl/              SPL 2.0 runtime (lexer, parser, executor, 14 adapters)
  lexer.py          tokenization
  parser.py         recursive-descent parser → AST
  ast_nodes.py      30+ dataclass node types
  executor.py       runtime engine
  analyzer.py       semantic validation
  optimizer.py      token budget allocation
  explain.py        ASCII plan rendering
  ir.py             JSON AST serialization
  text2spl.py       natural language → SPL compiler
  adapters/         LLM backend plugins
  storage/          SQLite memory + vector store (RAG)

spl3/             SPL 3.0 extension layer (inherits from spl/)
  executor.py       SPL3Executor(SPL2Executor) — CALL dispatch, type coercion
  parser.py         SPL3Parser(SPL2Parser) — IMPORT, SET, NONE, CALL PARALLEL
  composer.py       workflow-to-workflow CALL execution
  registry.py       LocalRegistry + FederatedRegistry
  hub_registry.py   REST-backed Hub registry
  event.py          WorkflowInvocationEvent (UUID, lifecycle, Hub serialization)
  status.py         COMMIT status → exception type mapping
  codecs/           image / audio / video codec layer
  splc/             transpilers: Go, TypeScript, LangGraph
  text2spl/         SPL 3.0 text2spl (extends spl/text2spl.py)
  adapters/         SPL 3.0 adapters: multimodal, Liquid, Snap

cookbook/         65 recipes (SPL 2.0: 00–49, SPL 3.0: 50–64)
tests/            unified test suite (300+ tests)
```

## Cookbook

65 recipes spanning beginner to advanced:

| Range | Theme |
|---|---|
| `00–09` | Basics: hello world, proxy, multilingual, model showdown, self-refine, ReAct |
| `10–19` | Patterns: batch test, debate, plan-execute, map-reduce, multi-agent, reflection, tree-of-thought |
| `20–29` | Applied: text2SPL, structured output, few-shot, nested procs, A/B test, data extraction |
| `30–39` | Applications: code gen, sentiment, Socratic tutor, interview sim, hypothesis tester, tool use |
| `40–49` | Advanced: human steering, knowledge synthesis, prompt tuning, adaptive failover, vision, finance |
| `50–64` | SPL 3.0: code pipeline, multimodal (image/audio/video), parallel code review, voice dialogue |

```bash
python cookbook/run_all.py --list           # all 65 recipes
python cookbook/run_all.py --catalog        # full table with tier + category
python cookbook/run_all.py --check          # verify env vars + Ollama models
```

## Momagrid — Decentralized Compute Grid

The `momagrid` adapter routes SPL inference tasks to a [Momagrid Hub](https://github.com/digital-duck/momagrid), which dispatches them across a LAN grid of GPU nodes.

```bash
export MOMAGRID_HUB_URL=http://192.168.1.10:9000

# Single recipe on the grid
spl3 run cookbook/05_self_refine/self_refine.spl --adapter momagrid -m llama3.2

# Full cookbook in parallel (fills the task queue so all nodes get work)
python cookbook/run_all.py --adapter momagrid --workers 5
```

SPL 3.0 extends Momagrid as a **Compute OS**: each `CALL workflow_name()` becomes a Hub-dispatched system call; `CALL PARALLEL` concurrently routes sub-workflows to different nodes.

## Tests

```bash
pytest                              # full suite
pytest tests/test_registry.py       # single file
pytest -k test_status_mapping       # single test
```

## Development Workflow

SPL.py is the **stable public repo**. New features are prototyped in [SPL30](https://github.com/digital-duck/SPL30) and graduate here when they have test coverage and a cookbook recipe.

Future major versions (`spl4/`, `spl5/`, ...) will be prototyped in SPL30 and added as new subpackages alongside `spl/` and `spl3/`. The `spl3` CLI command is permanent — it always points to the highest available runtime layer.

## License

Apache-2.0
