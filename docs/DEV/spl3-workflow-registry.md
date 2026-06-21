# SPL Workflow Registry — Composable Radicals

> **Status:** Vision / design phase. Not yet implemented.

## The idea

Chinese has ~400 elemental characters ("radicals") that compose into
50,000+ compound characters. Each radical is irreducible — it carries a
stable meaning and combines predictably. The ZiNets research on elemental
characters demonstrates this: once you have the radicals, the language
becomes rich in expressiveness without inventing from scratch.

SPL workflows can follow the same pattern. The 65+ cookbook recipes already
contain recurring workflow patterns — self-refinement, multi-agent debate,
verified chain, plan-then-execute, iterative deepening, fan-out/fan-in.
Many of these are irreducible: they solve one structural problem and
compose cleanly into larger workflows.

## The design

### Radical = a curated, irreducible workflow pattern

A radical is a `.spl` workflow that:

1. Solves exactly one structural problem (refinement, verification,
   debate, routing, aggregation)
2. Has typed `INPUT`/`OUTPUT` so it composes via `CALL`
3. Is provider-agnostic — works with any `--adapter`
4. Is tested across multiple concrete use cases

### Registry = the radical library

```
~/.spl/workflows/
    refine.spl          -- WHILE quality < threshold: GENERATE improve
    verify_chain.spl    -- plan → SOLVE each step → narrate
    debate.spl          -- N agents argue → judge selects
    fan_out.spl         -- CALL PARALLEL over a list → merge
    route.spl           -- EVALUATE input → dispatch to specialist
    rag_retrieve.spl    -- embed → search → rerank → inject
```

### Composition = complex workflows from radicals

```spl
IMPORT "refine"
IMPORT "verify_chain"
IMPORT "debate"

WORKFLOW research_and_verify
  INPUT @question TEXT
  OUTPUT @answer TEXT
DO
  CALL debate(@question, agents=3) INTO @candidate
  CALL verify_chain(@candidate, backend="sympy") INTO @verified
  CALL refine(@verified, criterion="clarity") INTO @answer
END
```

Three radicals, one workflow. Each radical is tested independently. The
composition is declarative. The same compound workflow runs on any adapter.

### Discovery and sharing

- `spl3 workflow list` — show registered radicals with signatures
- `spl3 workflow promote recipe.spl --name refine` — curate a radical
- `spl3 workflow search "verification"` — find by capability

The workflow registry complements the tool registry (`~/.spl/tool_apis/`):

| Registry | Contains | Invoked by | Runtime |
|---|---|---|---|
| Tool API | Deterministic Python functions | `CALL` | Python exec |
| Workflow | Composable `.spl` patterns | `CALL` | SPL executor |
| MCP | External tool servers | `CALL` | JSON-RPC |

All three register into `FunctionRegistry` and are callable via `CALL` —
the dispatch is uniform regardless of where the implementation lives.

### Connection to MCP (§ spl3-mcp-integration.md)

When SPL exposes workflows as an MCP server (`spl3 serve --mcp`), every
registered radical becomes a callable MCP tool. External systems (Claude
Desktop, other agents, IDE extensions) can discover and invoke SPL
workflow radicals without knowing SPL exists. The radical registry is the
catalog; MCP is the transport.

### Open questions

- **Parameterization**: how much should a radical be configurable vs
  opinionated? (e.g., `refine` takes a `criterion` param, but should
  the number of iterations be a param or fixed?)
- **Versioning**: radicals evolve — how to handle breaking changes in
  INPUT/OUTPUT signatures?
- **Curation**: who decides what is "irreducible"? Start with the cookbook
  patterns that recur in 3+ recipes.
- **Naming**: radical names should be verbs (`refine`, `verify`, `debate`,
  `route`) — the workflow is an action, not a thing.
