<!-- merged: spl30 + spl20 -->

# SPL 3.0 Cookbook

SPL 3.0 extends SPL 3.0 with multimodal types (`IMAGE`, `AUDIO`, `VIDEO`),
sub-workflow `CALL` composition, and `CALL PARALLEL` concurrency.
Recipe 05 is the entry point; recipes 50–64 cover the full SPL 3.0 capability set.

Each recipe has its own `README.md` with full details, parameters, and examples.

---

## Validation Experiments

Six runs across 3 runtimes × 2 deployment targets validate both **DODA** (cross-runtime semantic consistency) and **Momagrid** scaling.

| # | Runtime | Deployment | Catalog | Momagrid support |
|---|---------|------------|---------|-----------------|
| 1 | `spl3` (Python) | Single GPU | `cookbook_catalog.json` | — |
| 2 | `spl3` (Python) | LAN grid (4 GPUs) | `cookbook_catalog.json` | ✅ native |
| 3 | `spl-go` | Single GPU | `cookbook_catalog-go.json` | — |
| 4 | `spl-go` | LAN grid (4 GPUs) | `cookbook_catalog-go.json` | ✅ native |
| 5 | `spl-ts` | Single GPU | `cookbook_catalog-ts.json` | — |
| 6 | `spl-ts` | LAN grid (4 GPUs) | `cookbook_catalog-ts.json` | ✅ native |

**LAN cluster** (duck/cat/dog/goose): 3× GTX 1080 Ti (11 GB VRAM, GOLD tier) + 1× RTX 4060 (8 GB VRAM, SILVER tier). Hub: `http://192.168.0.235:9000`.

### Run commands

```bash
# Exp 1 — spl3, single GPU
mkdir -p cookbook/logs

python cookbook/run_all.py --adapter ollama --model gemma3 \
  2>&1 | tee cookbook/logs/exp1_spl3_single_ollama_$(date +%Y%m%d_%H%M%S).md

python cookbook/run_all.py --adapter ollama --model gemma3 \
  --ids "01-66" \
  2>&1 | tee cookbook/logs/exp1_spl3_single_ollama_gemma3_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --adapter claude_cli \
  2>&1 | tee cookbook/logs/exp1_spl3_single_claude_cli_$(date +%Y%m%d_%H%M%S).md



# Exp 2 — spl3, Momagrid
export MOMAGRID_HUB_URL=http://192.168.0.235:9000
python cookbook/run_all.py --adapter momagrid --model llama3.2 --workers 4 \
  2>&1 | tee cookbook/logs/exp2_spl3_momagrid_$(date +%Y%m%d_%H%M%S).md

# Exp 3 — spl-go, single GPU
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json \
  --adapter ollama --model gemma3 \
  2>&1 | tee cookbook/logs/exp3_splgo_single_$(date +%Y%m%d_%H%M%S).md

# Exp 4 — spl-go, Momagrid
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json \
  --adapter momagrid --model llama3.2 --workers 4 \
  2>&1 | tee cookbook/logs/exp4_splgo_momagrid_$(date +%Y%m%d_%H%M%S).md

# Exp 5 — spl-ts, single GPU
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-ts.json \
  --adapter ollama --model gemma3 \
  2>&1 | tee cookbook/logs/exp5_splts_single_$(date +%Y%m%d_%H%M%S).md

# Exp 6 — spl-ts, Momagrid
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-ts.json \
  --adapter momagrid --model llama3.2 --workers 4 \
  2>&1 | tee cookbook/logs/exp6_splts_momagrid_$(date +%Y%m%d_%H%M%S).md
```

### What results populate

| Section | Source experiments |
|---|---|
| §6.4 Recipe pass rates | Exp 1, 3, 5 (single GPU) |
| §7.1 Cross-runtime latency | Exp 1, 3, 5 |
| §7.4 Multi-runtime conformance | Exp 1, 3, 5 |
| Appendix B Momagrid validation | Exp 2, 4 |

---

## Recipe Index

| # | Recipe | Flow | Group | Tier | Model(s) |
|---|--------|------|-------|------|----------|
| [05](05_self_refine/) | self_refine | TEXT → TEXT | entry | 1 | gemma3 + llama3.2 (Ollama) |
| [50](50_code_pipeline/) | code_pipeline | TEXT → TEXT | text / code | 1 | gemma4 (Ollama) |
| [51](51_image_caption/) | image_caption | IMAGE → TEXT | → text | 1 | gemma4:e4b (Ollama) |
| [52](52_audio_summary/) | audio_summary | AUDIO → TEXT | → text | 1 | gemma4:e4b (Ollama) |
| [53](53_video_summary/) | video_summary | VIDEO → TEXT | → text | 1 | gemma4 (Ollama) |
| [54](54_text_to_image/) | text_to_image | TEXT → IMAGE | text → | 2 | DALL-E 3 (OpenAI) |
| [55](55_text_to_speech/) | text_to_speech | TEXT → AUDIO | text → | 2 | OpenAI TTS or system |
| [56](56_text_to_video/) | text_to_video | TEXT → VIDEO | text → | 2 | Veo 2 / RunwayML |
| [57](57_image_convert/) | image_convert | IMAGE → IMAGE | image | 1 | codec only |
| [58](58_image_restyle/) | image_restyle | IMAGE → IMAGE | image | 2 | gemma4:e4b + DALL-E 3 |
| [59](59_audio_convert/) | audio_convert | AUDIO → AUDIO | audio | 1 | codec only |
| [60](60_voice_dialogue/) | voice_dialogue | AUDIO → AUDIO | audio | 4 | LFM-2.5 + gemma4 + OpenAI TTS |
| [61](61_video_to_audio/) | video_to_audio | VIDEO → AUDIO | video | 1 | codec only |
| [62](62_video_to_image/) | video_to_image | VIDEO → IMAGE | video | 1 | gemma4 optional |
| [63](63_parallel_code_review/) | parallel_code_review | TEXT → TEXT | advanced | 1 | gemma4 (Ollama) |
| [64](64_parallel_news_digest/) | parallel_news_digest | TEXT → TEXT | advanced | 1 | gemma4 (Ollama) |

**Tier key:** 1 = Ollama only (no API key) · 2 = OpenAI key · 3 = OpenRouter key · 4 = OpenAI + OpenRouter + Ollama

---

## Setup

```bash
conda activate spl3
pip install spl-llm>=2.0.0
pip install -e ~/projects/digital-duck/SPL30

# Tier 1 models (Ollama)
ollama serve
ollama pull gemma4:e4b
ollama pull gemma3
ollama pull llama3.2

# Codec tools (recipes 57–62)
pip install Pillow pydub
sudo apt install ffmpeg        # Ubuntu/Debian

# API keys (tier 2+)
export OPENAI_API_KEY=sk-...
export OPENROUTER_API_KEY=sk-or-...
```

---

## Running recipes

```bash
# SPL workflows (recipes 05, 50, 63, 64)
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama

# Multimodal — native spl3 run (recipes 51–53)
spl3 run cookbook/51_image_caption/image_caption.spl \
    --adapter ollama \
    --param photo="cookbook/51_image_caption/sample/photo.jpg" \
    --param model="gemma4:e4b"

spl3 run cookbook/52_audio_summary/audio_summary.spl \
    --adapter ollama \
    --param clip="cookbook/52_audio_summary/sample/clip.wav" \
    --param model="gemma4:e4b"

# Physical runners (run.py) for recipes with extra options
python cookbook/51_image_caption/run.py --image path/to/photo.jpg
python cookbook/52_audio_summary/run.py --audio path/to/clip.wav

# Batch run (reads cookbook_catalog.json)
python cookbook/run_all.py              # tier-1 active recipes
python cookbook/run_all.py --tier 1     # Ollama only
python cookbook/run_all.py --ids 51,52  # specific recipes
python cookbook/run_all.py --all        # everything
```

---

## Groups

### Entry
**05 self_refine** — The first SPL 3.0 recipe. Demonstrates `CALL` sub-workflow
dispatch: `critique_workflow` is called from the orchestrator, with a retry
loop that stops on `[APPROVED]`. Start here.

### Text / Code (50)
**50 code_pipeline** — NDD closure: `generate → review → improve → test →
document → extract_spec → spec_judge`. Seven sub-workflows composed via `CALL`.
The reference implementation of the closure principle.

### Multimodal → Text (51–53)
Recipes that take a media file and produce a text description, transcript, or summary.
- **51 image_caption** — describe / OCR an image (IMAGE → TEXT)
- **52 audio_summary** — transcribe / summarise audio (AUDIO → TEXT)
- **53 video_summary** — summarise / transcribe a video (VIDEO → TEXT)

### Text → Multimodal (54–56)
Recipes that take a text prompt and produce a media file.
- **54 text_to_image** — DALL-E 3 image generation (TEXT → IMAGE)
- **55 text_to_speech** — TTS audio file (TEXT → AUDIO)
- **56 text_to_video** — Veo 2 / RunwayML video clip (TEXT → VIDEO)

### Image (57–58)
- **57 image_convert** — format conversion: PNG ↔ JPEG ↔ WebP ↔ BMP (codec only)
- **58 image_restyle** — vision analysis + DALL-E 3 restyle (IMAGE → IMAGE)

### Audio (59–60)
- **59 audio_convert** — format conversion: WAV ↔ MP3 ↔ OGG ↔ FLAC (codec only)
- **60 voice_dialogue** — full voice assistant: transcribe → respond → speak

### Video → (61–62)
- **61 video_to_audio** — extract audio track: .mp4 → .mp3 / .wav / .flac (codec only)
- **62 video_to_image** — extract frame(s); optional gemma4 caption

### Advanced Parallel (63–64)
- **63 parallel_code_review** — style + security + test reviews via `CALL PARALLEL`
- **64 parallel_news_digest** — three topics summarised concurrently, merged into a briefing

---

# SPL 3.0 Cookbook

Ready-to-run recipes demonstrating SPL 3.0 capabilities. Each recipe is self-contained.

## Prerequisites

```bash
conda create -n spl2 python=3.11
conda activate spl2

pip install -e ".[dev]"          # install spl
# pip install httpx                # for ollama/openrouter/momagrid adapters

ollama pull gemma3               # at least one model
ollama serve                     # start ollama (if not running)
```

## Batch Runner — `run_all.py`

`run_all.py` uses a Click CLI with three subcommands: `list`, `catalog`.

### Run recipes

```bash
cd ~/projects/digital-duck/SPL20

# Run all active recipes (sequential, ollama adapter)
python cookbook/run_all.py \
  --adapter ollama --model gemma3 \
  2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md

# Override adapter and model
python cookbook/run_all.py  --adapter ollama --model gemma3

# Run specific recipes or ranges
python cookbook/run_all.py  --ids "04,10,23-35"
python cookbook/run_all.py  --ids "04,10,25,26,29,30,32,33"

# Run recipes in a category
python cookbook/run_all.py  --category agentic
```

### Run on momagrid (parallel mode)

When `--adapter momagrid` is set, all recipes are submitted **concurrently** so the hub
dispatcher sees multiple tasks in the queue at once and distributes work across GPU nodes:

```bash
export MOMAGRID_HUB_URL=http://192.168.1.10:9000

# All active recipes in parallel
python cookbook/run_all.py  --adapter momagrid --model llama3.2

# Limit concurrency (default: one worker per recipe)
python cookbook/run_all.py  --adapter momagrid --model llama3.2 --workers 4

# Subset in parallel
python cookbook/run_all.py  --adapter momagrid --ids "01-10,13"
```

In parallel mode, each recipe logs to its own file under `<recipe_dir>/`. Completion
messages print as recipes finish; a summary table appears at the end.

### Running from a client machine (laptop, no GPU required)

The machine submitting recipes does **not** need to be a grid agent — it is a pure client.
It submits SPL tasks to the hub over HTTP; the hub dispatches them to GPU nodes.

**Step 1 — Verify hub is reachable**

```bash
curl http://192.168.0.235:9000/agents
```

You should see a JSON list of online agents. If this fails, check that you are on the same
LAN as the hub machine (duck, 192.168.0.235).

**Step 2 — Install dependencies (first time only)**

```bash
cd ~/projects/digital-duck/SPL20
pip install -e .       # install spl package
pip install httpx      # momagrid adapter HTTP client
```

If the repo is not cloned yet:

```bash
git clone https://github.com/digital-duck/SPL20 ~/projects/digital-duck/SPL20
cd ~/projects/digital-duck/SPL20
pip install -e .
pip install httpx
```

**Step 3 — Run all recipes**

```bash
bash cookbook/run_cookbook_on_momagrid.sh
```

The script exports `MOMAGRID_HUB_URL=http://192.168.0.235:9000` and runs all 37 active
recipes with `--workers 10`. Output is saved to `cookbook/out/run_all_<timestamp>-momagrid.md`.

Or run directly:

```bash
export MOMAGRID_HUB_URL=http://192.168.0.235:9000
python cookbook/run_all.py  --adapter momagrid --workers 10 2>&1 \
  | tee cookbook/out/run_laptop_$(date +%Y%m%d_%H%M%S).md
```

`--workers 10` controls how many recipes the client submits concurrently to the hub.
The hub's own dispatch across GPU nodes is independent of this value.

---

### Hub URL resolution (no env var needed)

The momagrid adapter resolves the hub URL in this order:

1. `hub_url=` constructor argument
2. `MOMAGRID_HUB_URL` environment variable
3. `~/.igrid/config.yaml` → `hub.urls[0]`  ← auto-populated by `mg join`
4. `http://localhost:9000` (last resort)

After running `mg join <hub-url>` on any machine, subsequent `spl3 run --adapter momagrid`
calls will find the hub automatically without needing to export `MOMAGRID_HUB_URL`.

### LAN cluster — tuning agent participation

The hub dispatches tasks by **tier first** (GOLD > SILVER > BRONZE), then by least active
tasks. With `--max-concurrent 3` (the default) and three GOLD nodes, the grid has 9 GOLD
slots — a SILVER node only receives work when all 9 GOLD slots are busy.

**To give lower-tier nodes more work, choose one:**

**Option A — Promote the node's tier** (use when the hardware is comparable):
```bash
# PostgreSQL hub
psql momagrid -c "UPDATE agents SET tier='GOLD' WHERE name='goose';"

# SQLite hub
sqlite3 .igrid/hub.sqlite3 "UPDATE agents SET tier='GOLD' WHERE name='goose';"
```
The change takes effect immediately; no hub restart required.

**Option B — Increase max-concurrent slots per agent** (use when you want all nodes busier):
```bash
# Restart the hub with more slots per agent
mg hub up --max-concurrent 5   # 4 nodes × 5 = 20 total slots
```
With 20 slots and 10 workers the SILVER node starts filling in much sooner.

**Reference — LAN 4-node cluster (duck/cat/dog/goose)**

| Node  | GPU           | VRAM  | Tier   |
|-------|---------------|-------|--------|
| duck  | GTX 1080 Ti   | 11 GB | GOLD   |
| cat   | GTX 1080 Ti   | 11 GB | GOLD   |
| dog   | GTX 1080 Ti   | 11 GB | GOLD   |
| goose | RTX 4060      |  8 GB | SILVER |

Hub: `http://192.168.0.235:9000` (duck machine, PostgreSQL backend)

---

### Hub-to-Hub Peering over the Internet (Pinggy)

By default a Momagrid hub is only reachable inside its LAN.
[Pinggy](https://pinggy.io) creates a temporary public HTTPS tunnel to a local port — no account required, no binary to install — so two users on different LANs can test hub-to-hub peering without opening firewall ports.

**Scenario:** Bob and Alice each run their own LAN Momagrid hub and want to peer the two grids.

#### Step 1 — Start the local hub

Both Bob and Alice must have their hub running before opening the tunnel:

```bash
mg hub up
```

#### Step 2 — Each user opens a Pinggy tunnel

Bob (hub on port 9000):
```bash
ssh -p 443 -R0:localhost:9000 a.pinggy.io
```

Alice (same command):
```bash
ssh -p 443 -R0:localhost:9000 a.pinggy.io
```

Each session prints a public URL in the terminal, e.g.:
```
https://qgzqm-99-111-153-200.run.pinggy-free.link
```

Bob and Alice exchange their URLs (chat, Slack, etc.).

#### Step 3 — Point the SPL client at the Pinggy URL

To submit recipes through the tunnel rather than the LAN IP, set `MOMAGRID_HUB_URL` to your own Pinggy URL:

```bash
# Bob
export MOMAGRID_HUB_URL=https://qgzqm-99-111-153-200.run.pinggy-free.link

# Alice
export MOMAGRID_HUB_URL=https://abcde-11-22-33-44.run.pinggy-free.link
```

Quick smoke test — does the hub respond over the tunnel?

```bash
curl $MOMAGRID_HUB_URL/health
```

#### Step 4 — Register the peer hub

Bob registers Alice's public URL:
```bash
mg peer add https://abcde-11-22-33-44.run.pinggy-free.link
```

Alice registers Bob's:
```bash
mg peer add https://qgzqm-99-111-153-200.run.pinggy-free.link
```

Verify both sides see each other:
```bash
mg peer list
```

Expected output (Bob's side):
```
This hub: <bob-hub-id>
  <alice-hub-id>  https://abcde-11-22-33-44.run.pinggy-free.link  [online]
```

#### Step 5 — Run a recipe across the peered grids

Bob submits recipes to his hub; the hub forwards overflow to Alice's:
```bash
python cookbook/run_all.py --adapter momagrid --ids "01-05" --workers 4
```

Or target a single recipe:
```bash
spl3 run cookbook/47_arxiv_morning_brief/arxiv_morning_brief.spl \
    --adapter momagrid \
    --param urls='["https://arxiv.org/pdf/2501.12948"]'
```

Alice does the same against her own `MOMAGRID_HUB_URL`.

#### Notes

| Topic | Detail |
|---|---|
| Tunnel lifetime | Free Pinggy tunnels stay open as long as the `ssh` session is alive; close the terminal to tear it down |
| Port | Change `-R0:localhost:9000` if your hub uses a different port |
| Keepalive | Add `-o "ServerAliveInterval 30"` to prevent idle disconnects |
| Persistent URL | A paid Pinggy account gives a fixed subdomain — useful if you want a stable peer URL across sessions |

---

### Browse recipes

```bash
# Brief list
python cookbook/run_all.py list
python cookbook/run_all.py list --category agentic
python cookbook/run_all.py list --status new

# Full catalog table
python cookbook/run_all.py catalog
python cookbook/run_all.py catalog --category reasoning
python cookbook/run_all.py catalog --status approved
```

## Analyzing Results — `analyze_logs.py`

After any `run_all.py` run, use `analyze_logs.py` to generate paper-ready reports.
Batch logs are written to `cookbook/logs/`; the analyzer finds the latest one automatically.

### Single-runtime stats

```bash
# Aggregate metrics for the latest spl3 run (default)
python cookbook/analyze_logs.py --paper-stats

# Specific log file
python cookbook/analyze_logs.py \
  --run cookbook/logs/exp1_spl3_single_20260419_121027.md \
  --paper-stats

# Per-recipe markdown table
python cookbook/analyze_logs.py --summary

# HTML report saved to cookbook/out/
python cookbook/analyze_logs.py --html

# Everything at once
python cookbook/analyze_logs.py --all
```

Use `--runtime` to label the report (propagates into HTML title and stdout headers):

```bash
python cookbook/analyze_logs.py \
  --run cookbook/logs/exp3_splgo_single_20260419_140000.md \
  --runtime spl-go \
  --paper-stats
```

### Cross-runtime comparison (§6.4 conformance matrix)

Once all three single-GPU runs are complete, generate the cross-runtime table used in §6.4:

```bash
python cookbook/analyze_logs.py \
  --compare spl3=cookbook/logs/exp1_spl3_single_YYYYMMDD_HHMMSS.md \
  --compare spl-go=cookbook/logs/exp3_splgo_single_YYYYMMDD_HHMMSS.md \
  --compare spl-ts=cookbook/logs/exp5_splts_single_YYYYMMDD_HHMMSS.md
```

Output includes:
- Per-recipe ✅/❌ matrix across all runtimes
- Pass-rate and wall-time summary table (paste directly into the paper)
- Count of recipes approved across **all** runtimes

Add Momagrid runs to extend to the full 6-experiment matrix:

```bash
python cookbook/analyze_logs.py \
  --compare "spl3 (single)"=cookbook/logs/exp1_spl3_single_....md \
  --compare "spl3 (grid)"=cookbook/logs/exp2_spl3_momagrid_....md \
  --compare "spl-go (single)"=cookbook/logs/exp3_splgo_single_....md \
  --compare "spl-go (grid)"=cookbook/logs/exp4_splgo_momagrid_....md \
  --compare "spl-ts (single)"=cookbook/logs/exp5_splts_single_....md \
  --compare "spl-ts (grid)"=cookbook/logs/exp6_splts_momagrid_....md
```

### Non-default catalog files

```bash
# spl-go catalog
python cookbook/analyze_logs.py \
  --run cookbook/logs/exp3_splgo_single_....md \
  --runtime spl-go \
  --catalog-file cookbook/cookbook_catalog-go.json \
  --paper-stats
```

## Code-RAG

Run
```bash
spl3 code-rag seed cookbook/ --catalog cookbook/cookbook_catalog.json
```
once the run finishes to capture all (prompt, SPL) pairs into the Code-RAG index.



## Recipes

Status: `✓` done · `-` parser/runtime pending · `todo` not yet written

### Tier 1 — Core SPL (Language Fundamentals)

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 01 | Hello World | `hello.spl` | Minimal SPL program — verify spl + Ollama work | ✓ |
| 02 | Ollama Proxy | `proxy.spl` | General-purpose LLM query — proxy any Ollama model | ✓ |
| 03 | Multilingual | `multilingual.spl` | Greet in any language — parametric `lang` demo | ✓ |
| 04 | Model Showdown | `showdown.spl` | Same prompt to multiple models via CTEs, compare output | ✓ |
| 05 | Self-Refine | `self_refine.spl` | Iterative improvement: draft → critique → refine loop | ✓ |
| 06 | ReAct Agent | `react_agent.spl` | Reasoning + Acting loop with tool-call pattern | ✓ |
| 07 | Safe Generation | `safe_generation.spl` | Exception handling for production LLM safety | ✓ |
| 08 | RAG Query | `rag_query.spl` | Retrieval-augmented generation over indexed documents | - |
| 09 | Chain of Thought | `chain.spl` | Multi-step reasoning: Research → Analyze → Summarize | ✓ |
| 10 | Batch Test | `batch_test.sh` | Automated testing of multiple .spl scripts across models | ✓ |

### Tier 2 — Agentic Patterns

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 11 | Debate Arena | `debate.spl` | Adversarial debate between two LLM personas with a judge | ✓ |
| 12 | Plan and Execute | `plan_execute.spl` | Planner decomposes task into steps, executor runs each one | ✓ |
| 13 | Map-Reduce | `map_reduce.spl` | Split large docs into chunks, summarize each, combine results | ✓ |
| 14 | Multi-Agent | `multi_agent.spl` | Researcher → Analyst → Writer collaboration via PROCEDURE | ✓ |
| 15 | Code Review | `code_review.spl` | Multi-pass review: security, performance, style, bugs | ✓ |
| 16 | Reflection | `reflection.spl` | Meta-cognitive loop: solve → reflect → correct until confident | ✓ |
| 17 | Tree of Thought | `tree_of_thought.spl` | Explore multiple reasoning paths, score and pick the best | ✓ |
| 18 | Guardrails | `guardrails.spl` | Input/output safety pipeline with PII detection and filtering | ✓ |
| 19 | Memory Chat | `memory_chat.spl` | Persistent memory across conversations via memory.get/set | - |
| 20 | Ensemble Voting | `ensemble.spl` | Generate multiple answers, score and vote for consensus | ✓ |
| 21 | Multi-Model Pipeline | `multi_model.spl` | Per-step model selection with GENERATE...USING MODEL and quality loop | ✓ |
| 22 | Text2SPL Demo | `text2spl_demo.sh` | Natural language to SPL 3.0 compiler — prompt, workflow, and auto modes | - |

### Tier 3 — SPL Language Features (Completeness)

| # | Recipe | Script | Key Feature | Status |
|---|--------|--------|-------------|--------|
| 23 | Structured Output | `structured_output.spl` | `CREATE FUNCTION` with JSON schema — extract typed data from free text | ✓ |
| 24 | Few-Shot Prompting | `few_shot.spl` | Gold-standard examples embedded in `SELECT` context | ✓ |
| 25 | Nested Procedures | `nested_procs.spl` | `PROCEDURE` calling `PROCEDURE` — deep composability | ✓ |
| 26 | Prompt A/B Test | `ab_test.spl` | CTEs + `EVALUATE` scoring — compare two prompt variants, pick winner | ✓ |

### Tier 4 — Real-World Pipelines

| # | Recipe | Script | Domain | Status |
|---|--------|--------|--------|--------|
| 27 | Data Extraction | `data_extraction.spl` | Pull structured fields from messy text (names, dates, amounts) | ✓ |
| 28 | Customer Support Triage | `support_triage.spl` | Classify → route → draft response in one workflow | ✓ |
| 29 | Meeting Notes → Actions | `meeting_actions.spl` | Transcript in, structured TODO list + owners out | ✓ |
| 30 | Code Generator + Tests | `code_gen.spl` | Generate function, then generate its unit tests | ✓ |
| 31 | Sentiment Pipeline | `sentiment.spl` | Batch sentiment over a list, aggregate trends | ✓ |

### Tier 5 — Advanced Agentic Patterns

| # | Recipe | Script | Pattern | Status |
|---|--------|--------|---------|--------|
| 32 | Socratic Tutor | `socratic_tutor.spl` | Ask guiding questions rather than giving answers directly | ✓ |
| 33 | Interview Simulator | `interview_sim.spl` | Two-persona structured Q&A with evaluation | ✓ |
| 34 | Progressive Summarizer | `progressive_summary.spl` | Layered summary: sentence → paragraph → page | ✓ |
| 35 | Hypothesis Tester | `hypothesis.spl` | Generate hypothesis → design test → evaluate evidence | ✓ |

### Tier 6 — Tool Connectors (Multimodal)

Tool connectors mirror the LLM adapter pattern. `backend` is to connectors what `model` is to adapters.
Local and online backends are interchangeable — declared in `config.yaml` or overridden via `--connector`.

```yaml
# .spl/config.yaml
connectors:
  pdf:
    backend: pymupdf          # local default
    # backend: adobe-api      # online alternative
  transcribe:
    backend: whisper          # local
    model: base
    # backend: assemblyai     # online alternative
  tts:
    backend: piper            # local
    # backend: elevenlabs     # online alternative
```

```bash
# CLI override — same pattern as --adapter
spl3 run script.spl --connector pdf=pymupdf
spl3 run script.spl --connector transcribe=assemblyai
```

| # | Recipe | Script | Connector | Status |
|---|--------|--------|-----------|--------|
| 36 | PDF Analyst | `pdf_analyst.spl` | `tool.pdf_to_md` — ingest PDF, extract insights | todo |
| 37 | Audio → Action Items | `audio_actions.spl` | `tool.transcribe` — meeting recording → structured tasks | todo |


## Quick Smoke Test

```bash
# Parse all recipes (no LLM needed)
for f in cookbook/*/*.spl; do spl validate "$f"; done

# Run hello world with echo adapter (no Ollama needed)
spl3 run cookbook/01_hello_world/hello.spl

# Run with Ollama
spl3 run cookbook/01_hello_world/hello.spl --adapter ollama


```


### Test — Hello World

```bash
spl3 run cookbook/01_hello_world/hello.spl --adapter ollama
```

```
============================================================
Model: gemma3
Tokens: 38 in / 45 out
Latency: 1200ms
------------------------------------------------------------
Hello! I'm your friendly SPL 3.0 assistant. SPL (Structured Prompt Language)
is a declarative language for orchestrating LLM workflows — think SQL for AI.
============================================================
```


### Test — Ollama Proxy (any model, any prompt)

```bash
spl3 run cookbook/02_ollama_proxy/proxy.spl --adapter ollama --model gemma3 prompt="Explain quantum computing"
```

```
============================================================
Model: gemma3
Tokens: 44 in / 824 out
Latency: 12965ms
------------------------------------------------------------
Okay, let's break down quantum computing...
============================================================
```


### Test — Multilingual Greeting

```bash
spl3 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Chinese"
```

```
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 440ms
------------------------------------------------------------
你好，文！ (Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
```


### Test — Model Showdown (compare models)

```bash
bash cookbook/04_model_showdown/showdown.sh "What is the meaning of life?"
```


### Test — Self-Refining Agent

```bash
spl3 run cookbook/05_self_refine/self_refine.spl --adapter ollama --model gemma3 task="Write a haiku about coding"
```


### Test — Multi-Model Pipeline (per-step model selection)

```bash
spl3 run cookbook/21_multi_model_pipeline/multi_model.spl --adapter ollama topic="climate change"
```

This recipe showcases `GENERATE ... USING MODEL` — each step can target a different model within the same workflow.


### Test — Text2SPL Demo (NL → SPL compiler)

```bash
bash cookbook/22_text2spl_demo/text2spl_demo.sh
```

Demonstrates the `spl text2spl` / `spl text2spl` command: natural language descriptions compiled into valid SPL 3.0 code with automatic validation.


### Test — Batch Test (all models x all recipes)

```bash
bash cookbook/10_batch_test/batch_test.sh
```

### Fixes

┌────────┬─────────────────────────────────────────────────────┬──────────────────────────────────────────────────┐
  │ Recipe │                        Issue                        │                       Fix                        │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 04     │ Old cli.py signature (before tools/allowed_tools)   │ Fixed by our earlier cli.py update               │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 06/13  │ --tools/--claude-allowed-tools unknown options      │ Added to spl3/cli.py run command                 │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 17     │ qwen2.5 model not pulled → 404                      │ Changed DEFAULT list to                          │
  │        │                                                     │ ['gemma3','phi4','gemma3']                       │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 22     │ spl3 text2spl command missing                       │ Added text2spl + validate commands to            │
  │        │                                                     │ spl3/cli.py                                      │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 50/63  │ Double --param --param in apply_overrides           │ Fixed: consume flag+value together               │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 57     │ --model injected into python runner; wrong filename │ Fixed injection (spl3-only) +                    │
  │        │                                                     │ photo.png→photo.jpg                              │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 59     │ --model injected + no audio sample files            │ Fixed injection; marked inactive (wip)           │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 51     │ spl.codecs + spl.adapters.liquid not yet            │ Marked inactive (wip)                            │
  │        │ implemented                                         │                                                  │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 61     │ Missing run.py + no sample directory                │ Marked inactive (wip)                            │
  ├────────┼─────────────────────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ 63     │ gemma4 hardcoded as default model                   │ Added review_model=gemma3 to catalog             │
  └────────┴─────────────────────────────────────────────────────┴──────────────────────────────────────────────────┘

```bash
python cookbook/run_all.py --adapter ollama --model gemma3 \
  --ids "04,06,13,17,22,50,51,57,63" \
  2>&1 | tee cookbook/logs/exp1_spl3_single_$(date +%Y%m%d_%H%M%S).md
```
