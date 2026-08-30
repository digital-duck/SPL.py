# SPL.ts Native Cookbook

The SPL.ts cookbook lives at `/home/papagame/projects/digital-duck/SPL.ts/cookbook/`. It contains **36 pure-TypeScript recipes** — no Python tools, no external bridges, no TOOL_API dependencies. Every recipe runs against the echo adapter (deterministic, zero-cost) and against any real adapter (Ollama, OpenAI, Anthropic, Google).

## Prerequisites

- Build the TypeScript runtime:

```bash
cd ~/projects/digital-duck/SPL.ts
npm run build        # tsc → dist/
```

- Ollama running locally for live model runs: `ollama serve`

## Run a recipe

```bash
cd ~/projects/digital-duck/SPL.ts

# Quick smoke-test (echo adapter — deterministic, zero cost)
node dist/cli.js run ./cookbook/01_hello/hello.spl --adapter echo

# Live model run (Ollama)
node dist/cli.js run ./cookbook/01_hello/hello.spl --adapter ollama

# Pass params
node dist/cli.js run ./cookbook/29_adversarial_refine/adversarial_refine.spl \
    --adapter ollama \
    --param claim="AI will replace most white-collar jobs within 10 years" \
    --param max_rounds=3

# Validate syntax without running
node dist/cli.js validate ./cookbook/30_adaptive_failover/adaptive_failover.spl
```

## Run all recipes (smoke-test suite)

```bash
cd ~/projects/digital-duck/SPL.ts

for f in cookbook/*/; do
  name=$(basename "$f")
  spl=$(ls "$f"*.spl 2>/dev/null | head -1)
  [ -z "$spl" ] && continue
  result=$(node dist/cli.js run "$spl" --adapter echo 2>&1)
  if echo "$result" | grep -q "Error\|ParseError\|TypeError"; then
    echo "FAIL  $name"
  else
    echo "OK    $name"
  fi
done
```

## Why a separate cookbook?

SPL.ts does not implement `CREATE TOOL_API` — the Python-backed tool mechanism used in SPL.py. Recipes that call Python tools crash at parse time in SPL.ts. The native cookbook replaces every TOOL_API call with stdlib equivalents (`word_count`, `contains`, `iif`, `json_set`, etc.) and equivalent SPL logic.

The SPL.py catalog at `cookbook_catalog-ts.json` (same directory as this README) is the cross-runtime index; it now points exclusively to SPL.ts native recipe files.

## Catalog

```bash
# View the SPL.ts catalog
cat ~/projects/digital-duck/SPL.ts/cookbook/catalog.json | python3 -m json.tool | grep '"name"'
```

## Recipe overview

| ID | Name | Category | Key features |
|----|------|----------|--------------|
| 01 | Hello World | basics | Basic GENERATE |
| 02 | Chain of Thought | basics | Sequential GENERATE INTO |
| 03 | Self-Refine | agentic | WHILE + EVALUATE + COMMIT |
| 04 | Nested Procedures | basics | PROCEDURE + CALL chain |
| 05 | Parallel Perspectives | multi-agent | CALL PARALLEL ... END |
| 06 | Sentiment Router | application | Multi-branch EVALUATE |
| 07 | Batch Processing | application | WHILE + list_get (1-based) + list_length |
| 08 | Multi-Agent Collaboration | multi-agent | PROCEDURE delegation + LOGGING |
| 09 | Code Gen + Tests | application | Sequential generation pipeline |
| 10 | Data Pipeline | application | json_get + iif with comparison args |
| 11 | Debate Arena | multi-agent | CALL PARALLEL opening + WHILE rebuttals |
| 12 | Reflection Agent | agentic | WHILE + EVALUATE > 0.85 + iterative correction |
| 13 | Ensemble Voting | multi-agent | CALL PARALLEL 5-way + score/consensus/select |
| 14 | Parallel News | multi-agent | CALL PARALLEL sub-WORKFLOWs + fan-out merge |
| 15 | Progressive Summary | application | 3-layer summary + EVALUATE >= 3 |
| 16 | Hypothesis Tester | agentic | Multi-branch EVALUATE with variable threshold |
| 17 | Parallel Code Review | multi-agent | CALL PARALLEL 3 reviewer sub-WORKFLOWs |
| 18 | Multi-Pass Code Review | application | read_file + severity-gated EVALUATE |
| 19 | Safe Generation | agentic | EVALUATE exact string + EXCEPTION + RETRY |
| 20 | Multi-Model Pipeline | multi-agent | GENERATE USING MODEL per step + quality loop |
| 21 | Headline News Aggregator | application | EVALUATE > coverage score + gap fill |
| 22 | Memory-Augmented Chat | agentic | trim_turns + stateless caller-managed memory |
| 23 | Credit Risk Assessment | application | iif+contains stdlib extraction + int fast path |
| 24 | Vision to Action | application | classify once + contains() decision tree |
| 25 | A/B Test | agentic | CALL PARALLEL 2 variants + iif winner |
| 26 | Structured Extraction | agentic | GENERATE JSON + validate loop + enrich on failure |
| 27 | Plan and Execute | agentic | line_count + WHILE + split_part step extraction |
| 28 | Text Analytics Pipeline | application | CALL PARALLEL 4-way + json_set accumulation |
| 29 | Adversarial Refinement | agentic | WHILE AND compound + score-gated termination |
| 30 | Adaptive Failover | agentic | USING MODEL per GENERATE + stdlib quality gate |
| 31 | Prompt Self-Tuning | agentic | CALL PARALLEL variants + nested EVALUATE winner |
| 32 | Product Description Refiner | agentic | WHILE AND compound + critique-rewrite-score loop |
| 33 | Tree of Thought | multi-agent | CALL PARALLEL 3 paths (lens+model); score/select/refine; EVALUATE = 'sound' verify |
| 34 | Regulatory News Audit | application | WHILE line_count+split_part; json_get risk routing; EVALUATE = 'high' alert |
| 35 | Socratic Tutor | application | Persona func in GENERATE; EVALUATE > understanding score; adaptive Q3 |
| 36 | Autonomous Code Pipeline | agentic | WHILE AND test-gated loop; 8 PROCEDURE sub-steps; optional closure check |

## SPL.ts parser notes

- Comparison ops (`>`, `<`, `>=`, `<=`, `=`, `!=`) work in assignment RHS and function call args
- `CALL PARALLEL ... END` requires explicit `END` terminator
- `CALL PARALLEL` calls WORKFLOWs or PROCEDUREs — not CREATE FUNCTIONs
- Reserved keywords (cannot be workflow/procedure/function names): `explain`, `parallel`, `solve`
- `CALL read_file(path) INTO @var` returns `''` on missing file (executor catches ENOENT)
- Variables are all `Map<string, string>` — use `to_int()` / `to_float()` before numeric comparisons
- `EVALUATE @var WHEN >= @other_var` works — right side is a full expression

## Stdlib quick reference

| Function | Signature | Returns |
|----------|-----------|---------|
| `word_count` | `(text)` | integer string |
| `line_count` | `(text)` | integer string |
| `contains` | `(text, substring)` | 'true'/'false' |
| `iif` | `(cond, then, else)` | string |
| `isnull` | `(val)` | 'true'/'false' |
| `to_int` | `(val)` | integer string |
| `to_float` | `(val)` | float string |
| `split_part` | `(text, delim, n)` | nth part |
| `list_get` | `(list, n)` | nth item (1-based) |
| `list_length` | `(list)` | count |
| `trim_turns` | `(history, n)` | last n turns |
| `json_get` | `(json, key)` | value |
| `json_set` | `(json, key, value)` | updated JSON |
