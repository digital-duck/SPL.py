# What If LLM Workflow Orchestration Could Be Done Like Writing SQL?

*Repo: [github.com/digital-duck/SPL.py](https://github.com/digital-duck/SPL.py) (Apache 2.0)*

## The SQL lesson

SQL changed data engineering by separating **what** you want from **how** to get it. Before SQL, every data pipeline was imperative code tied to a specific storage engine. After SQL, you declared the logic once and the engine handled the rest. You don't rewrite your query when you move from MySQL to Postgres.

LLM workflows today are where data engineering was before SQL: imperative Python scripts, hard-wired to one LLM provider's API, unreproducible the moment you swap a model or move to a different machine.

SPL ([Structured Prompt Language](https://arxiv.org/abs/2602.21257)) was initially introduced to manage prompt and context, and is now extended to orchestrate LLM workflows. Here is what that looks like side by side:

```sql
-- SQL: declare what data you want
SELECT   product, SUM(revenue)
FROM     sales
WHERE    region = 'APAC'
GROUP BY product;
-- Runs on Postgres, MySQL, SQLite — zero changes.
```

```sql
-- SPL: declare what the workflow does
WORKFLOW solve_math_problem
  INPUT  @problem TEXT
  OUTPUT @result  TEXT
DO
  GENERATE decompose(@problem)         INTO @plan
  SOLVE    execute_step(@plan)         INTO @answer
  ASSERT   @answer is valid
  GENERATE explain(@problem, @answer)  INTO @result
END
```

```bash
# Runs on local GPU, distributed grid, or cloud API — zero changes.
spl3 run solve_math_problem.spl --adapter ollama     --model gemma3
spl3 run solve_math_problem.spl --adapter claude_cli --model claude-sonnet-4-6
spl3 run solve_math_problem.spl --adapter momagrid   --model gemma4:e2b
spl3 run solve_math_problem.spl --adapter openrouter --model qwen/qwen3.6-plus
```

The `.spl` file is the logical specification. The adapter and model are runtime flags. Same file, same logic, different execution — just like SQL.

If you have built LLM workflows and hit provider lock-in, unverifiable outputs, or API costs that scale faster than your workload, read on. We try to prescribe **One SPL pill** that **kills three pains.**

### Pain-point #1: Framework lock-in

Your LangChain script calls `openai.chat.completions.create()`. You want to try Claude? Rewrite the glue code. Run locally with Ollama? Rewrite again. Switch to a distributed grid? Start over.

This is the same problem SQL solved for data. The query says *what*; the engine handles *how*. SPL does the same: the `.spl` file declares the workflow logic, and the `--adapter` flag at runtime picks the engine. Fourteen adapters ship today — Ollama, Claude, OpenRouter, Momagrid, and others — and adding one means implementing two methods (`generate` and `generate_multimodal`), not rewriting every workflow.

One workflow file. One `--adapter` flag. Many providers.

### Pain-point #2: Output seems right, but unverified

LLMs produce fluent, confident answers. Some are correct. Some are wrong. From outside the system, they look identical. We call this failure mode *silent unverified success* — and it is the default in every agent framework today. The LLM says the answer is right, and there is no structural mechanism to disagree. Keep in mind that no matter how confidently an LLM behaves, it is rooted in statistical learning pre-trained on available data.

SPL makes verification a language construct, not a convention someone might forget:

- **`GENERATE`** — the LLM. Probabilistic. Drafts plans, translates intent, narrates results.
- **`SOLVE`** — the kernel. Deterministic, bit-perfect. Executes exact computation (SymPy, SageMath, Lean 4).
- **`ASSERT`** — the gate. Deterministic. Passes or fails; the LLM cannot override it.

Two execution modes, syntactically distinct, in one file. You can *grep* which parts of a pipeline are LLM output and which are kernel-verified. The LLM plans and explains; the kernel solves and checks. Provenance is structural — baked into the language — not a convention that erodes the moment someone forgets a wrapper function.

Here is what both modes look like in the same workflow:

```sql
GENERATE decompose_problem(@problem) INTO @steps_text

WHILE @i < @n_steps DO
  CALL solve_chain_step(@step, @running_expression, @backend) INTO @step_summary
  EVALUATE @running_expression
    WHEN = "solver_error" THEN
      RETURN "[SOLVER FAILURE] Step could not be computed"
        WITH status = "solver_error"
  END
END

GENERATE explain_chain(@problem, @trace) INTO @result
```

The `GENERATE` steps are probabilistic — the LLM decomposes and explains. The `CALL solve_chain_step` dispatches to a deterministic kernel (`SOLVE` under the hood) that executes each math step exactly. If any step fails verification, the workflow exits with an explicit error status. The LLM never gets to summarize whether verification happened.

### Pain-point #3: Token tax and data privacy

Every `GENERATE` call to an external API has a per-token cost. One call is cheap. A batch of overnight experiment runs, document processing jobs, or code review queues? That is a line item that hits the business bottom line.

And every token sent externally is data that left the building. Proprietary source code, regulated content, student data — these are not theoretical concerns.

**Momagrid** is a lightweight distributed inference grid built for exactly this. Consumer GPUs — gaming PCs, MacBooks with Apple Silicon, developer workstations — each running Ollama plus a thin agent process. The hub sits on the LAN. The models run on-device. No new hardware budget. No API calls. No data egress.

Two commands to stand up the grid:

```bash
mg hub up                    # launch the hub on one machine
mg join http://192.168.0.1   # any machine with a GPU joins the grid
```

From the SPL workflow's perspective, nothing changes. Swap `--adapter ollama` to `--adapter momagrid` and `GENERATE` steps distribute across the grid automatically. `SOLVE` and `ASSERT` stay local — deterministic operations never cross the network. This is DODA in action: **Design Once, Deploy Anywhere.** The same `.spl` file runs on a single laptop, a LAN grid of consumer GPUs, or a cloud API — zero code changes.

The hardware is already there. An office with developer MacBooks sitting idle overnight already owns a distributed inference cluster — it just is not wired up yet. A school or university with a laptop fleet has the same opportunity: free, private inference for educational AI workflows, with zero dependency on commercial API availability or per-student budget allocation.

## Case study: NeuroSymbolic Math Verification (one SPL pill, three pains killed)

To demonstrate how it all works together, we use a specific [math workflow](https://github.com/digital-duck/SPL.py/blob/main/cookbook/77_neurosymbolic/symbolic_math.spl) that touches all three points: the same `.spl` file runs on Ollama, Claude, or Momagrid (pain 1 gone); a SymPy/SageMath kernel verifies every math step the LLM produces (pain 2 gone); the grid runs on idle consumer GPUs with zero data egress (pain 3 gone).

### The Math problem

We ask ten different LLMs to "differentiate 3x³ − x, then solve for x." Without verification, most will give you a fluent, confident answer. Some of those answers will be wrong. You cannot tell which ones without checking — and if you are checking by hand, what was the LLM for?

### Experimental design

We ran a controlled A/B across **10 models**, **20 math problems** (algebra, calculus, ODEs, systems), and **2 modes**:

- **Solver ON**: the LLM decomposes the problem into steps; a SymPy/Sage kernel executes each step exactly; the LLM narrates the verified trace.
- **Solver OFF**: the same problem, the same LLM, no kernel. The LLM solves it end-to-end, unaided.

Total: **4,700+ experimental cells** across multiple runs, dispatched via Ollama and Momagrid adapters with consumer GPU workers.

The A/B question: *does the deterministic kernel do real work, or would the LLM have gotten there anyway?*

### The SPL recipe

The workflow is [`symbolic_math.spl`](symbolic_math.spl) — 310 lines, including comments. The core loop is what you saw above: `GENERATE` a plan, `SOLVE` each step through the kernel, fail-fast on any solver error, `GENERATE` a narration of the verified trace. The solver backend (SymPy, SageMath, or Lean 4) is a `--param backend=` flag, not a code change. The LLM provider is an `--adapter` flag. The same file runs every cell in the benchmark:

```bash
export PROBLEM="differentiate 3*x**3 - x, solve for x"

# Local, single GPU
spl3 run symbolic_math.spl --adapter ollama --model gemma3 --param problem=$PROBLEM

# Distributed across consumer GPU grid
spl3 run symbolic_math.spl --adapter momagrid --model gemma4:e2b --param problem=$PROBLEM

# Cloud API
spl3 run symbolic_math.spl --adapter claude_cli --param problem=$PROBLEM
```

### Benchmark results

The headline finding — the **auditability gap**:

| Model | Solver ON (verified) | Solver OFF (unverified) |
|---|---|---|
| gemma4:e2b | **91.5%** | 97.5% |
| sonnet-4-6 | **90.6%** | 100% |
| rnj-1 | **84.7%** | 100% |
| qwen2.5 | **72.6%** | 100% |
| gemma3 | **70.7%** | 100% |
| phi4 | **69.7%** | 100% |
| llama3.2 | **66.9%** | 100% |
| deepseek-v2:16b | **54.3%** | 100% |
| lfm2.5 | **41.1%** | 75.6% |
| phi3 | **27.4%** | 100% |

Read the right column first. Nine out of ten models report **100% pass rate** with the solver off. Every answer looks correct. None are verified.

Now read the left column. With the kernel checking each step, pass rates drop to 27%–92%. The kernel is catching real errors that the LLM confidently hid. That gap between the two columns — that is the *silent unverified success* problem, measured at scale.

The best model (gemma4:e2b) still gets 91.5% verified — meaning even a strong model produces wrong math on roughly 1 in 11 problems that it would have otherwise reported as correct. The weakest (phi3) drops from a claimed 100% to an actual 27.4%. Without the kernel, you would never know.

**Distributed speedup**: the same benchmark that took 60 minutes on a single GPU completed in 20 minutes on 3 consumer GPUs via Momagrid — exactly linear scaling. The workflow code was identical.


## Try it

Both [SPL](https://github.com/digital-duck/SPL.py) and [Momagrid](https://github.com/digital-duck/momagrid) projects are **Apache 2.0** open-sourced.

**SPL** — the workflow language and runtime:

```bash
# Python runtime + CLI from PyPI
pip install spl-llm

# your first SPL workflow
spl3 run cookbook/05_self_refine/self_refine.spl --llm ollama:gemma3 \
    --param task="explain linear algebra"
```

**Momagrid** — the distributed inference grid:

```bash
git clone https://github.com/digital-duck/momagrid
cd momagrid && go build           # build from source (Go)
mg hub up                         # start the hub
mg join http://<HUB-IP>:9000      # workers join from any machine on the same network
```

**Reproduce the case-study benchmark:**

```bash
# Run Recipe 77 locally (needs Ollama + a model pulled)
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --llm ollama:gemma3 \
    --param problem="differentiate 3*x**3 - x, then solve for x"

# Or run the full experiment grid on Momagrid
python cookbook/77_neurosymbolic/run_experiment_momagrid.py --workers 6
```

No API key required to start. Ollama runs free, local models. SPL ships 14 adapters — when you want to compare against cloud models, add `--adapter openrouter` or `--adapter claude_cli` and the workflow stays the same. *Note:* `--llm ollama:gemma3` is shorthand for `--adapter ollama --model gemma3`


## The honest limits

**The correspondence gap.** The deterministic kernel verifies the *computation*, not the natural-language claim. "Differentiate 3x³ − x" goes in; SymPy returns 9x² − 1 exactly. But the link between the prose problem statement and the symbolic expression is the one thing nothing machine-checks. Mitigations that ship: the verified statement and the prose claim are stored side by side for human audit, and an LLM faithfulness judge gates badge assignment — but the judge can only *withhold* a badge, never grant one. Badges are granted by the kernel.

**The eval surface.** The kernels evaluate LLM-emitted expression strings (`sympify`, `sage_eval`). This is a local research tool running the operator's own model on the operator's machine. Do not point it at untrusted input.

**Momagrid today and next step.** The benchmark runs on a home LAN: one hub, three consumer GPU nodes. The architecture scales linearly with agent count — the receipts are at 3-GPU scale. The next milestone is a WAN hub with a public domain, where anyone with a GPU and Ollama can register and contribute capacity.

**Scope.** Computational math: algebra, calculus, ODEs, linear algebra, systems. The Lean 4 integration handles formal proof checking for known results in mathlib. This is not novel theorem proving and not whole-textbook formalization — it is making "an LLM said so" auditable for the claims that matter.

---

*[SPL.py](https://github.com/digital-duck/SPL.py) · [Momagrid](https://github.com/digital-duck/momagrid) · Apache 2.0 · Recipes, benchmarks, and raw data in the repo.*
