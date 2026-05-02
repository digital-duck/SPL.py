# SPL Round-Trip Experiments — OpenRouter Adapter

**Goal:** Repeat the 5-recipe round-trip pipeline using the **OpenRouter** adapter as the
controlled experimental environment for cross-model comparison.  OpenRouter provides a single
adapter, single auth, and single HTTP path — only `--model` changes between runs.  This mirrors
the DODA principle applied to the *experiment itself*: same SPL source, same pipeline, same
evaluation criteria, only the model slot varies.

**Experimental design:**
```
5 recipes  ×  N models  =  5N data points
              (all via openrouter adapter — no adapter-implementation confounds)
```

**Models under comparison:**

| Model | OpenRouter slug | Provider | Note |
|-------|----------------|----------|--------|
| Claude Opus 4.6 | `anthropic/claude-opus-4-6` | Anthropic | as LLM judge for spl3 compare |

| [x] Claude Sonnet 4.6 | `anthropic/claude-sonnet-4-6` | Anthropic | Use claude_cli adapter, 1M context, $3/M input tokens, $15/M output tokens |

| [x] Gemini 3 Flash | `google/gemini-3-flash-preview` | Google | 1.05M context, $0.50/M input tokens, $3/M output tokens |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | Google | (smoke test) 1.05M context, $0.30/M input tokens, $2.50/M output tokens |

| [x] DeepSeek v4 Pro | `deepseek/deepseek-v4-pro` | DeepSeek | 1.05M context, $0.435/M input tokens, $0.87/M output tokens |
| DeepSeek v4 Flash | `deepseek/deepseek-v4-flash` | DeepSeek | 1.05M context, $0.14/M input tokens, $0.28/M output tokens |

| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` | Meta (open) | |

[x] to be used for NeurIPS experiments

> **Why OpenRouter over per-vendor CLI adapters:**  `claude_cli` vs `gemini_cli` vs `ollama`
> differ in adapter implementation, auth mechanism, subprocess overhead, and retry logic —
> all potential confounds.  OpenRouter eliminates them: every model sees the same HTTP call,
> the same prompt, and the same response path.  The only independent variable is the model.

---

## Why OpenRouter instead of gemini_cli

| Issue | gemini_cli | openrouter |
|-------|-----------|------------|
| CLI loop detection | Aborts when invoked from another session (`_recoverFromLoop`) | Not applicable — pure HTTP |
| Auth | Gemini CLI session / Google account | `OPENROUTER_API_KEY` env var |
| Model access | Gemini models only | 100+ models: Gemini, Claude, GPT-4, Llama, DeepSeek |
| Cost | Free (subscription) | Pay-per-token (Gemini Flash ~$0.075/1M input) |
| Reliability | CLI session-dependent | API SLA |
| Experimental control | Adapter varies per model | **Single adapter for all models** ✓ |

---

## Prerequisites

### 1 — Install httpx

```bash
pip install httpx
```

Verify:
```bash
python -c "import httpx; print(httpx.__version__)"
# 0.28.1
```

### 2 — Set API key

Get a key from [openrouter.ai/keys](https://openrouter.ai/keys), then:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

To persist across sessions, add to `~/.bashrc`:
```bash
echo 'export OPENROUTER_API_KEY=sk-or-v1-...' >> ~/.bashrc
```

Verify the adapter is reachable:
```bash
cd ~/projects/digital-duck/SPL.py
python -c "
from spl.adapters import get_adapter
a = get_adapter('openrouter', model='google/gemini-2.5-pro-preview')
print('OpenRouter adapter OK:', a.default_model)
"
```

### 3 — Working directory

All commands below assume:
```bash
cd ~/projects/digital-duck/SPL.py
conda activate base
```

### 4 — Create output directories

```bash
mkdir -p ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent
mkdir -p ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag
mkdir -p ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge
mkdir -p ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking
mkdir -p ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research
```

---

## Available Models (OpenRouter slugs)

| Model | Slug | Use case |
|-------|------|----------|
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | Primary — mirrors gemini_cli target |
| Gemini 2.5 Pro | `google/gemini-2.5-pro-preview` | Higher quality, slower |
| Gemini 2.0 Flash | `google/gemini-2.0-flash-001` | Fallback if preview unavailable |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4-5` | Cross-model comparison |
| Claude Sonnet 4.5 | `anthropic/claude-opus-4.6` | Cross-model comparison |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` | Open-source baseline |

---

## The Round-Trip Pipeline

```
Original PocketFlow recipe  (oracle)
  │
  ├─ Step 1: spl3 splc describe   → <recipe>-splc-python_pocketflow-spec.md
  │
  ├─ Step 2: spl3 text2spl        → <recipe>.spl
  │
  ├─ Step 2A: spl3 text2mmd       → <recipe>.mmd / .png
  │
  ├─ Step 2B: spl3 mmd2spl        → <recipe>.spl  (visual roundtrip check)
  │
  ├─ Step 3: spl3 validate        → OK / errors
  │
  ├─ Step 3B: spl3 compare        → fidelity note (v0 vs canonical)
  │
  ├─ Step 4: spl3 run             → (smoke test) (LLM execution)
  │
  ├─ Step 5: spl3 splc compile    → <recipe>_python_pocketflow.py
  │             --llm --adapter openrouter --model google/gemini-2.5-flash
  │
  └─ Step 6: python <recipe>.py   → functional test (compare with oracle output)
```

---

## Recipe 1 — `pocketflow-agent` (SPL ID 73) ✓ COMPLETE [2026-04-30]

**Pattern:** ReAct loop (decide → search → decide → ... → answer)
**Oracle:** `~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/`

**Step 1 — splc describe:**
```bash
# Set MODEL once, reuse across all steps — easy to switch for cross-model comparison
export MODEL="google/gemini-2.5-flash"
# export MODEL="anthropic/claude-sonnet-4-5"
# export MODEL="anthropic/claude-opus-4"
# export MODEL="meta-llama/llama-3.3-70b-instruct"
export MODEL="deepseek/deepseek-v4-flash"
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model $MODEL
```

**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter openrouter --model $MODEL \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent-v0.spl
```

**Step 2A — text2mmd:**
```bash
spl3 text2mmd \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/flow-splc-python_pocketflow-spec.md \
  --adapter openrouter --model google/gemini-2.5-flash \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/ \
  -o pocketflow-agent.mmd
```

**Step 2B — mmd2spl:**
```bash
spl3 mmd2spl \
  ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.mmd \
  --adapter openrouter --model google/gemini-2.5-flash \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.spl
```

**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.spl
```

**Step 3B — compare:**
```bash
spl3 compare \
  ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent-v0.spl \
  ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.spl \
  --adapter openrouter --model google/gemini-2.5-flash
```

**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.spl \
  --adapter openrouter --model $MODEL \
  --param question="What is machine learning?"
```

**Step 5 — splc compile (LLM):**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/pocketflow-agent.spl \
  --lang python/pocketflow \
  --llm \
  --adapter openrouter --model $MODEL \
  --overwrite
```

**Step 6 — python run:**
```bash
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py \
  --adapter openrouter --model $MODEL \
  --question "What is machine learning?"
```

| Step | Status | Notes |
|------|--------|-------|
| splc describe | ✓ | `flow-splc-python_pocketflow-spec.md` |
| text2spl | ✓ | `pocketflow-agent-v0.spl` — auto mkdir worked |
| validate | ✓ | OK |
| spl3 run | ✓ | `--param initial_query="What is machine learning?"` |
| splc compile `--llm` | ✓ | `targets/python_pocketflow/pocketflow-agent_python_pocketflow.py` |
| python run | ✓ | `--adapter openrouter --model $MODEL --question "..."` |

**Manual fixes required:** 0 (auto-mkdir, mock-client guard, click CLI all pre-fixed)
**Round-trip verdict:** ✓ Full pipeline works end-to-end via `MODEL` env var
**Key insight:** `export MODEL=...` + reuse across all steps = trivial model switching, zero command edits

---

## Recipe 2 — `pocketflow-rag` (SPL ID 66) — TODO

**Pattern:** Linear pipeline (chunk → embed → index → retrieve → generate)
**Oracle:** `~/projects/wgong/PocketFlow/cookbook/pocketflow-rag/`

**Step 1 — splc describe:**
```bash
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-rag/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model google/gemini-2.5-flash
```

**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-rag/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter openrouter --model google/gemini-2.5-flash \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag/pocketflow-rag.spl
```

**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag/pocketflow-rag.spl
```

**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag/pocketflow-rag.spl \
  --adapter openrouter --model google/gemini-2.5-flash \
  --workflow rag_e2e \
  --param texts="Machine learning is a subset of artificial intelligence. It enables systems to learn from data without being explicitly programmed. Deep learning uses neural networks with many layers." \
  --param query="What is machine learning?"
```

**Step 5 — splc compile (LLM):**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag/pocketflow-rag.spl \
  --lang python/pocketflow \
  --llm \
  --adapter openrouter --model google/gemini-2.5-flash \
  --overwrite
```

**Step 6 — python run:**
```bash
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-rag/targets/python_pocketflow/pocketflow-rag_python_pocketflow.py \
  --query "What is machine learning?" \
  --texts "Machine learning is a subset of artificial intelligence. It enables systems to learn from data without being explicitly programmed. Deep learning uses neural networks with many layers."
```

| Step | Status | Notes |
|------|--------|-------|
| splc describe | [ ] | |
| text2spl | [ ] | |
| validate | [ ] | |
| spl3 run | [ ] | |
| splc compile | [ ] | |
| python run | [ ] | |

---

## Recipe 3 — `pocketflow-judge` (SPL ID 69) — TODO

**Pattern:** Linear pipeline + iterative refinement (generate → judge → refine loop)
**Oracle:** `~/projects/wgong/PocketFlow/cookbook/pocketflow-judge/`

**Step 1 — splc describe:**
```bash
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-judge/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model google/gemini-2.5-flash
```

**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-judge/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter openrouter --model google/gemini-2.5-flash \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge/pocketflow-judge.spl
```

**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge/pocketflow-judge.spl
```

**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge/pocketflow-judge.spl \
  --adapter openrouter --model google/gemini-2.5-flash \
  --param product_task="A noise-cancelling wireless headphone with 30-hour battery life" \
  --param max_attempts=3
```

**Step 5 — splc compile (LLM):**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge/pocketflow-judge.spl \
  --lang python/pocketflow \
  --llm \
  --adapter openrouter --model google/gemini-2.5-flash \
  --overwrite
```

**Step 6 — python run:**
```bash
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-judge/targets/python_pocketflow/pocketflow-judge_python_pocketflow.py \
  --product-task "A noise-cancelling wireless headphone with 30-hour battery life" \
  --max-attempts 3
```

| Step | Status | Notes |
|------|--------|-------|
| splc describe | [ ] | |
| text2spl | [ ] | |
| validate | [ ] | |
| spl3 run | [ ] | |
| splc compile | [ ] | |
| python run | [ ] | |

---

## Recipe 4 — `pocketflow-thinking` (SPL ID 67) — TODO

**Pattern:** Chain-of-thought reasoning (iterative thinking + planning state management)
**Oracle:** `~/projects/wgong/PocketFlow/cookbook/pocketflow-thinking/`

**Step 1 — splc describe:**
```bash
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-thinking/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model google/gemini-2.5-flash
```

**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-thinking/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter openrouter --model google/gemini-2.5-flash \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking/pocketflow-thinking.spl
```

**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking/pocketflow-thinking.spl
```

**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking/pocketflow-thinking.spl \
  --adapter openrouter --model google/gemini-2.5-flash \
  --param max_iterations=2 \
  --param problem="Why is the speed of light constant in all reference frames?"
```

**Step 5 — splc compile (LLM):**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking/pocketflow-thinking.spl \
  --lang python/pocketflow \
  --llm \
  --adapter openrouter --model google/gemini-2.5-flash \
  --overwrite
```

**Step 6 — python run:**
```bash
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-thinking/targets/python_pocketflow/pocketflow-thinking_python_pocketflow.py \
  --problem "Why is the speed of light constant in all reference frames?"
```

| Step | Status | Notes |
|------|--------|-------|
| splc describe | [ ] | |
| text2spl | [ ] | |
| validate | [ ] | |
| spl3 run | [ ] | |
| splc compile | [ ] | |
| python run | [ ] | |

---

## Recipe 5 — `pocketflow-deep-research` (SPL ID 77) — TODO

**Pattern:** Multi-step research loop (iterative research + synthesis + quality gates)
**Oracle:** `~/projects/wgong/PocketFlow/cookbook/pocketflow-deep-research/`

**Step 1 — splc describe:**
```bash
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-deep-research/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model google/gemini-2.5-flash
```

**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-deep-research/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter openrouter --model google/gemini-2.5-flash \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research/pocketflow-deep-research.spl
```

**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research/pocketflow-deep-research.spl
```

**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research/pocketflow-deep-research.spl \
  --adapter openrouter --model google/gemini-2.5-flash \
  --param research_question="What are the key breakthroughs in transformer architecture since 2017?" \
  --param depth=3
```

**Step 5 — splc compile (LLM):**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research/pocketflow-deep-research.spl \
  --lang python/pocketflow \
  --llm \
  --adapter openrouter --model google/gemini-2.5-flash \
  --overwrite
```

**Step 6 — python run:**
```bash
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-openrouter/pocketflow-deep-research/targets/python_pocketflow/pocketflow-deep-research_python_pocketflow.py \
  --research-question "What are the key breakthroughs in transformer architecture since 2017?" \
  --depth 3
```

| Step | Status | Notes |
|------|--------|-------|
| splc describe | [ ] | |
| text2spl | [ ] | |
| validate | [ ] | |
| spl3 run | [ ] | |
| splc compile | [ ] | |
| python run | [ ] | |

---

## Results Table (fill in as experiments complete)

| Recipe | Pattern | Manual fixes | SPL valid | splc compile | python run | Score |
|--------|---------|-------------|-----------|--------------|------------|-------|
| pocketflow-agent | react | 0 | ✓ | ✓ | ✓ | TBD |
| pocketflow-rag | linear | | | | | |
| pocketflow-judge | linear+refine | | | | | |
| pocketflow-thinking | chain-of-thought | | | | | |
| pocketflow-deep-research | multi-agent | | | | | |

**Score definition:**
- 1.0 = fully automated, zero manual fixes, output equivalent to oracle
- 0.8 = 1–2 minor manual fixes (syntax/env), output equivalent
- 0.5 = structural match, output differs
- 0.0 = failed to produce runnable code

---

## Cross-Model Comparison Matrix (all via OpenRouter)

The controlled experiment: same SPL source, same pipeline, same `openrouter` adapter,
only `--model` changes.

| Recipe | gemini-2.5-flash | claude-sonnet-4-5 | llama-3.3-70b | deepseek-v3 |
|--------|-----------------|-------------------|---------------|-------------|
| pocketflow-agent score | | | | |
| pocketflow-rag score | | | | |
| pocketflow-judge score | | | | |
| pocketflow-thinking score | | | | |
| pocketflow-deep-research score | | | | |
| **avg manual fixes** | | | | |
| **avg latency (s)** | | | | |

### Reference baseline (claude_cli adapter, separate runs)

| Recipe | claude_cli (sonnet-4-6) | notes |
|--------|------------------------|-------|
| pocketflow-agent | TBD | |
| pocketflow-rag | 0.5 | CALL stubs limit behavioral fidelity |
| pocketflow-judge | 1.0 | perfect round-trip |
| pocketflow-thinking | TBD | |
| pocketflow-deep-research | TBD | |

*Baseline uses a different adapter — not directly comparable on latency/cost, but useful
for sanity-checking SPL fidelity scores.*

---

## Observations Log

### [2026-04-30] Recipe 1 — pocketflow-agent ✓

- **MODEL env var pattern works perfectly**: `export MODEL=google/gemini-2.5-flash` then reuse
  `--adapter openrouter --model $MODEL` across all 6 steps — no command edits needed to switch models.
  This is the recommended protocol for all subsequent recipes and cross-model runs.
- **Zero manual fixes**: All infrastructure issues (auto-mkdir, mock-client guard, click CLI)
  were pre-fixed before running — clean automated pipeline on first attempt.
- **OpenRouter as controlled env confirmed**: Single adapter, single auth, model slot is the
  only variable. SPL stack demonstrated full DODA portability in practice.

---

## Known Issues / Watch-outs

1. **splc compile — always use `--llm`**: Deterministic pattern detection misidentifies complex
   SPL patterns (e.g., reAct detected as self_refine when two WHEN branches are present).
   Always add `--llm --adapter openrouter --model ...` to Step 5.

2. **CALL stubs in compiled code**: `CALL sub_workflow()` nodes are compiled as LLM simulation
   stubs by the transpiler — not real retrieval. This is a known structural fidelity limitation
   for RAG-style recipes. Score 0.5 max for recipes that rely on CALL.

3. **Multi-workflow `.spl` files**: Use `--workflow NAME` with `spl3 run` for files that define
   more than one WORKFLOW block (e.g., pocketflow-rag has `rag_index`, `rag_query`, `rag_e2e`).

4. **OpenRouter model slugs**: Must match exactly as listed at openrouter.ai/models.
   `gemini-2.5-flash-preview` ≠ `gemini-3-flash-preview` (different generations).

5. **Rate limits**: Gemini 2.5 Flash via OpenRouter has per-minute token limits. If Step 4
   (`spl3 run`) fails with a 429, wait 60s and retry.

---

## References

- SPL.py repo: `~/projects/digital-duck/SPL.py`
- PocketFlow cookbook: `~/projects/wgong/PocketFlow/cookbook/`
- OpenRouter adapter: `~/projects/digital-duck/SPL.py/spl/adapters/openrouter.py`
- claude_cli results: `readme-claude.md` (same directory)
- gemini_cli results: `readme-gemini.md` (same directory)
- Experiment overview: `readme.md` (same directory)
- Paper draft: `~/projects/digital-duck/zinets/docs/conference/NeurIPS/2026/Beyond-Vibe-Coding/`
