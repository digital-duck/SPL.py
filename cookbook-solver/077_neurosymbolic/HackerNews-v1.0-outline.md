# SPL: Declarative LLM Workflow with Deterministic Mode and Distributed Inference

## proposed outline by WEN

Key features:
- prefer declarative than imperative
  - SQL and PL/SQL inspired
- deterministic mode blends with probabilistic mode
  - GENERATE, EVALUATE
  - SOLVE, ASSERT
- distributed local inference complements API-centric inference
  - adapters : momagrid vs openrouter 

Case-study: Math workflow to demonstrate our SPL language

- Experimental Design
- SPL Recipe #77
- Benchmark Results
- The honest limits
- Try IT

## Claude's refined outline (v2 — incorporates Wen's edits)

### Title

**SPL: What If LLM Workflows Were More Like SQL?**

---

### Section structure

#### 1. The SQL analogy (lede — hook the reader) ~40 lines
- SQL separated *what* data you want from *how* to get it. That separation
  changed data engineering. LLM workflows today are where data engineering
  was before SQL: imperative scripts, provider-specific, unreproducible.
- SPL applies the same idea to LLM workflows: declare the logic once,
  run it anywhere.
- **Side-by-side snippet**: SQL query vs SPL workflow (5-8 lines each).
  Show `SELECT`/`FROM`/`WHERE` next to `GENERATE`/`SOLVE`/`ASSERT`.
  The reader should *see* the kinship instantly.

#### 2. Three pain points — one language ~100 lines
- Transition line: "One SPL file, three problems solved." Not three
  features bolted on — the same declarative design that eliminates
  vendor lock-in is what makes verification structural and distributed
  inference a flag-swap.

**Pain point 1: Vendor lock-in — you rewrite code every time you switch providers**
- Today: your LangChain script calls `openai.chat.completions.create()`.
  You want to try Claude, or run locally with Ollama? Rewrite the glue code.
  Switch to a distributed grid? Rewrite again.
- SQL solved this decades ago: you don't rewrite your query when you move
  from Postgres to MySQL. The query says *what*, the engine handles *how*.
- SPL applies the same separation. A `.spl` file is the logical spec — it
  never changes regardless of provider or deployment. Swap a CLI flag,
  not the workflow.
- Brief `.spl` snippet showing `--adapter ollama` vs `--adapter momagrid`
  on the same file — zero code changes.

**Pain point 2: You can't tell which outputs are actually verified**
- LLMs produce fluent, confident answers. Some are right. Some are wrong.
  From outside the system, they look identical. This is the "silent
  unverified success" problem — and it's the default in every agent
  framework today.
- SPL makes verification a first-class language construct, not a
  convention someone might forget. `GENERATE` = the LLM (probabilistic).
  `SOLVE`/`ASSERT` = the kernel (deterministic, bit-perfect). Two modes,
  syntactically distinct, in one file. You can *grep* which parts are verified.
- The LLM plans and explains; the kernel solves and checks. The LLM
  cannot override the kernel. Provenance is structural, not convention.
- Brief `.spl` snippet: a workflow that GENERATEs a math plan, SOLVEs it
  with SymPy, ASSERTs the result — ~8 lines showing both modes.

**Pain point 3: Token tax and data leaving the building**
- Every `GENERATE` call to an external API has a per-token cost. At batch
  scale — overnight experiment runs, document processing, code review
  queues — it becomes a real item that hits the business bottom-line.
- Every token sent externally is data that left the building. Proprietary
  code, regulated content, student data — these are not theoretical concerns.
- **Momagrid**: a lightweight distributed inference grid. Consumer GPUs
  (gaming PCs, MacBooks with Metal) running Ollama + a thin agent process.
  Hub on the LAN, models on-device. No new hardware budget, no API calls,
  no data egress. Idle GPU-equipped machines and developers' Mac laptops
  form the grid to meet batch inference workloads overnight, with 2
  simple commands:
    - `mg hub up` to launch the Hub
    - `mg join <HUB-URL>` for any worker agent to contribute
- Same `.spl` file: swap `--adapter ollama` to `--adapter momagrid` and
  GENERATE steps distribute across the grid. SOLVE/ASSERT stay local
  (DODA: Design Once, Deploy Anywhere).
- Schools and universities: laptop fleet = free, private inference cluster
  for educational AI workflows.

#### 3. Case study: Recipe 77 — one SPL file, three pains killed ~100 lines
- One concrete workflow that demonstrates all three: same `.spl` runs on
  Ollama, Claude, or Momagrid (pain 1 gone); the kernel verifies every
  math step the LLM produces (pain 2 gone); the grid runs on idle
  consumer GPUs with zero data egress (pain 3 gone).

**Experimental design**
- 10 models × 22 problems × 2 modes (solver on / solver off) = 4700+ cells
  (actual: 4727 cells across multiple runs)
- The A/B question: does the deterministic kernel do real work, or would
  the LLM have gotten there anyway?

**The SPL recipe**
- Show the actual `symbolic_math.spl` snippet (~10 key lines)
- Point out: same file runs locally, on Momagrid grid, or on top-tier
  AI-provider cloud

**Benchmark results** (from experiment_results_by_model.csv)
- Headline finding — the **auditability gap**:
  - Solver OFF: 9 out of 10 models report 100% pass rate. Every answer
    looks correct. But none are verified.
  - Solver ON: pass rates drop to 27%–92%. The kernel exposes real errors
    that the LLM confidently hid.
  - This IS the "silent unverified success" problem, measured at scale.
- Top 3 verified (solver=on): gemma4 91.5%, sonnet-4-6 90.6%, rnj-1 84.7%
- Bottom 3 verified: phi3 27.4%, lfm2.5 41.1%, deepseek-v2 54.3%
- Momagrid speedup: 3 consumer GPUs → 3× (linear scaling), 60 min → 20 min

#### 4. The honest limits ~30 lines
- The deterministic kernel verifies the solver's math, not the LLM's
  natural-language claim. The link between prose and formula is the one
  thing nothing machine-checks (mitigations: side-by-side audit, LLM
  faithfulness judge that can only withhold badges, citation-first path).
- Eval surface: local research tool running the operator's own model.
  Do not point this at untrusted input.
- Momagrid currently demonstrated on LAN; WAN hub (public domain, open
  registration for anyone with GPU + Ollama) is the next milestone.
- Scope: computational math (algebra, calculus, systems). Not novel
  theorem proving, not whole-textbook formalization.

#### 5. Try it (Apache 2.0, open source) ~30 lines
- `pip install spl-llm` — SPL runtime + CLI (PyPI)
- Momagrid — clone the repo and build with Go:
  - `git clone https://github.com/digital-duck/momagrid && cd momagrid && go build`
- Both projects Apache 2.0 licensed
- GitHub links: digital-duck/SPL.py, digital-duck/momagrid
- 3-4 copy-paste commands that reproduce the case study
- Works with free local models (Ollama) — no API key required to start

---

### Tone and length targets
- **~300 lines** (half of v0.3)
- First-person, direct, no hedging on claims but honest about limits
- Show code early and often — this is Show HN, not a position paper
- Every claim backed by a runnable command or a pinned receipt
- No internal project history (no "the bug that started this" narrative)
- No individual model anecdotes (no rnj-1 story) — save for a follow-up
