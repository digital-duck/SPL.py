# Show HN: Orchestrate LLM Workflows Declaratively Like SQL

*Repo: [github.com/digital-duck/SPL.py](https://github.com/digital-duck/SPL.py) (Apache 2.0)*

SQL separated **what** from **how** for data — your query runs on Postgres, MySQL, or SQLite unchanged. LLM workflows today are where data processing was before SQL: imperative Python tied to one provider's API.

SPL ([Structured Prompt Language](https://arxiv.org/abs/2602.21257)) applies the same separation:

```sql
WORKFLOW solve_math
  INPUT @problem TEXT  OUTPUT @result TEXT
DO
  GENERATE decompose(@problem)         INTO @plan
  SOLVE    execute_step(@plan)         INTO @answer
  GENERATE explain(@problem, @answer)  INTO @result
END
```

```bash
spl3 run solve_math.spl --adapter ollama     --model gemma3
spl3 run solve_math.spl --adapter claude_cli --model claude-sonnet-4-6
spl3 run solve_math.spl --adapter momagrid   --model gemma4:e2b
```

Same `.spl` file, 14 adapters, zero code changes. One SPL pill to kill three pains:

**1. Provider lock-in.** The `.spl` file is the logic; `--adapter` picks the engine at runtime. Swap providers without touching the workflow.

**2. Unverified output.** `GENERATE` = LLM (probabilistic). `SOLVE` = deterministic kernel (SymPy/SageMath/Lean 4). `ASSERT` = pass/fail gate the LLM cannot override. Two execution modes, syntactically distinct, in one file.

**3. Cost & privacy.** [Momagrid](https://github.com/digital-duck/momagrid) distributes inference across consumer GPUs on a LAN — no API costs, no data egress. Two commands: 
```bash
mg hub up                    # launch the hub on one machine
mg join http://192.168.0.1   # any machine with a GPU joins the grid
```

**Benchmark — 10 models × 20 math problems, solver ON vs OFF:**

To demonstrate how it all works together, we use a specific [math workflow](https://github.com/digital-duck/SPL.py/blob/main/cookbook/77_neurosymbolic/symbolic_math.spl) that touches all three pain-points, below is a short summary of benchmark results

| Model | Verified | Unverified |
|---|---|---|
| gemma4:e2b | 91.5% | 97.5% |
| sonnet-4-6 | 90.6% | 100% |
| qwen2.5 | 72.6% | 100% |
| gemma3 | 70.7% | 100% |
| phi3 | 27.4% | 100% |

9 of 10 models claim 100% with solver off. With the kernel checking each step, verified rates drop to 27–92%. That gap is *silent unverified success* — measured across 4,700+ experimental cells on consumer GPUs via Momagrid.


**Try it** — no API key needed, Ollama runs free local models:

```bash
pip install spl-llm
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl \
    --llm ollama:gemma3 \
    --param problem="differentiate 3*x**3 - x, then solve for x"
```

**Honest limits:** The kernel verifies computation, not the NL-to-symbolic translation. Momagrid receipts are at 3-GPU home LAN scale (Next step is to host the Hub on WAN). The eval surface runs LLM-emitted expressions locally — don't point at untrusted input.
