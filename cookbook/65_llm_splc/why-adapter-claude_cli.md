# Why `claude_cli` is the Recommended Adapter for Batch Vibe-Coding

> **Status: internal notes — not published yet.**
> Core pattern validated in production by upgrade-agent.
> Expanding validation to more SPL recipe use-cases before publishing.

## 1. Zero marginal cost at batch scale

`claude_cli` uses Claude Code subscription billing (flat rate).
Running 10 recipe compilations costs the same as 1.
That cost structure is what makes batch vibe-coding viable:
compile → review → fix for every target, without watching a token meter.

Direct API adapters (anthropic, openai) charge per token — the review and fix
steps double or triple the token spend per run. For a single recipe that's
acceptable; for a full cookbook or an enterprise knowledge-capture pipeline it
compounds fast.

## 2. The self-review loop only works with a frontier model

The `llm_splc` workflow has three steps: compile → review → fix.
The review step is only as good as the reviewer.

Observed contrast (2026-04-20, recipe 63 → crewai/autogen):

| Adapter | Review tokens | Result |
|---|---|---|
| `ollama/gemma3` | 5 tokens, 1.2s | `[APPROVED]` — rubber-stamp, hallucinated APIs in output |
| `claude_cli` | 275–306 tokens, 39–112s | Caught model mismatch, missing `asyncio.to_thread`, deprecated imports |

A weak reviewer defeats the purpose of the self-review loop entirely.

## 3. `llm_splc` is a general pattern

The compile → review → fix loop is not specific to SPL compilation.
It applies to any code generation task where:
- the spec is declarative and human-readable
- the output needs to be validated against the spec
- gaps need to be corrected before the artifact is written

The `.spl` file codifies the loop itself. `claude_cli` is what makes the
reviewer trustworthy enough to catch real gaps.

## 4. Batch parallelism is free

Two `spl3 run` commands targeting `autogen` and `crewai` simultaneously,
both using `claude_cli` — zero additional cost. That is the enterprise
scaling story: the same flat subscription funds the full compilation matrix.

## 5. Validation status

**Production-validated:** upgrade-agent uses this pattern for batch
code generation — flat billing + frontier reviewer confirmed at enterprise scale.

**SPL cookbook validation in progress:**

- [x] recipe 63 → autogen (2026-04-20): fix step caught model mismatch + async bug
- [x] recipe 63 → crewai (2026-04-20): correct Agent/Task/Crew/Process structure
- [x] recipe 11 → crewai (2026-04-20): approved on first pass
- [ ] recipe 63 → langgraph: cross-validate against deterministic `splc` output
- [ ] recipe 11 → autogen
- [ ] recipe 05 (self_refine) → langgraph: diff vs splc for gap analysis
- [ ] Measure wall-time for full cookbook compilation batch
- [ ] Test `claude-opus-4-7` vs `claude-sonnet-4-6` on fix step quality



## 6. Appendix - Test Runs

- /home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/targets/llm_splc-claude-cli-crewai-20260420-1.md
- /home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/targets/llm_splc-claude-cli-autogen-20260420-1.md