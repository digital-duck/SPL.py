# cookbook-pocketflow — Migration Progress & Notes

## Guiding Principle

- Curate agentic workflow patterns from open-source frameworks (PocketFlow, LangGraph, …)
- Enhance SPL's expressiveness as a language
- Build a SPL workflow registry

---

## Progress Tracker

| # | Recipe | Phase | Status | Difficulty | tools.spl | Notes |
|---|--------|-------|--------|-----------|-----------|-------|
| 001 | chat | 1 | ✅ done | 3/10 | inline (S3) | First run truncated+preamble; re-run S3 fixed it |
| 002 | structured_output | 1 | ✅ done | 2/10 | inline (S3) | Clean first pass |
| 003 | workflow | 1 | ✅ done | 2/10 | inline (S3) | Clean first pass |
| 004 | agent | 0 | ✅ done | 5/10 | hand-written | S3 generates CALL targets not in stdlib; tools.spl required |
| 005 | rag | 0 | ✅ done | 6/10 | hand-written | FAISS pipeline non-trivial; base64 matrix passing between stateless calls |
| 006 | map_reduce | 1 | ✅ done | 3/10 | inline (S3) | CALL PARALLEL maps cleanly |
| 008 | chat_guardrail | 1 | ✅ done | 3/10 | inline (S3) | EVALUATE guardrail gate |
| 014 | thinking | 0 | ✅ done | 5/10 | hand-written | Inner YAML validation loop; many helpers |
| 017 | judge | 0 | ✅ done | 3/10 | none | Pure GENERATE loop; no tools |
| 032 | deep_research | 0 | ✅ done | 5/10 | none | CALL PARALLEL + nested WHILE; stdlib search_web sufficient |
| 042 | nodejs_upgrade_agent | 4 | ✅ done | 7/10 | hand-written | Original SPL recipe (not PocketFlow migration); 3 sub-workflows + 9 tools; discovered WHEN = vs equals() syntax |
| 010 | multi_agent | 2 | ✅ done | 4/10 | inline (S3) | Clean pass |
| 011 | supervisor | 2 | ✅ done | 4/10 | inline (S3) | Clean pass |
| 012 | batch_node | 2 | ✅ done | 4/10 | inline (S3) | S3 failed first run (session limit); clean on retry |
| 013 | batch_flow | 2 | ✅ done | 4/10 | inline (S3) | Session limit on first run; clean on retry |
| 015 | chat_memory | 2 | ✅ done | 5/10 | inline (S3) | S3 took 216s — largest phase-2 recipe |
| 016 | mcp | 2 | ✅ done | 5/10 | inline (S3) | MCP tool dispatch pattern |
| 018 | debate | 2 | ✅ done | 4/10 | inline (S3) | Adversarial 2-agent + judge |
| 019 | agentic_rag | 2 | ✅ done | 5/10 | inline (S3) | Agent-decides-which-docs pattern |
| 020 | heartbeat | 2 | ✅ done | 5/10 | inline (S3) | Periodic monitoring + nested WORKFLOW |
| 021 | self_healing | 2 | ✅ done | 5/10 | inline (S3) | Self-repair WHILE + EVALUATE |
| 030 | lead_generation | 3 | ✅ done | 5/10 | inline (S3) | 4 TOOL_APIs + 4 CREATE FUNCTIONs; CSV parsing + scoring loop |
| 031 | invoice | 3 | ✅ done | 4/10 | inline (S3) | PDF→JSON extraction + math validation |
| 033 | text2sql | 3 | ✅ done | 4/10 | inline (S3) | SQLite tools + WHILE debug-retry loop; hit session limit on 1st run |
| 034 | communication | 3 | ✅ done | 3/10 | inline (S3) | int_add/safe_divide tools; uses stdlib list_get/trim/word_count/lower |
| 040 | coding_agent | 4 | ✅ done | 6/10 | inline (S3) | 5 TOOL_APIs; S3 used SQL-style `''` quoting in Python — fixed 5 bodies manually |
| 041 | agent_skills | 4 | ✅ done | 4/10 | inline (S3) | 2 TOOL_APIs; skill routing via keyword extraction + EVALUATE |
| 050 | a2a | 5 | ✅ done | 4/10 | inline (S3) | 4 TOOL_APIs, 3 workflows; agent-to-agent handoff pattern |
| 051 | async_basic | 5 | ✅ done | 3/10 | inline (S3) | 1 TOOL_API, 5 workflows; async fan-out basics |
| 052 | batch | 5 | ✅ done | 4/10 | inline (S3) | 2 TOOL_APIs; fixed SQL-style `''regex''` in 2 bodies |
| 053 | cli_hitl | 5 | ✅ done | 3/10 | inline (S3) | 2 TOOL_APIs; human-in-the-loop approval gate |
| 054 | code_generator | 5 | ✅ done | 5/10 | inline (S3) | 1 TOOL_API, 6 workflows; largest Tier-5 recipe (201L) |
| 055 | flow | 5 | ✅ done | 3/10 | inline (S3) | 1 TOOL_API; fixed `''\\s+''` regex quoting |
| 056 | majority_vote | 5 | ✅ done | 3/10 | inline (S3) | 1 TOOL_API; multi-candidate voting pattern |
| 057 | tao | 5 | ✅ done | 4/10 | inline (S3) | 1 TOOL_API, 4 workflows; Tree of Abstraction pattern |
| 058 | tool_crawler | 5 | ✅ done | 5/10 | inline (S3) | 12 TOOL_APIs; most tools of any recipe; 3 quoting fixes needed |
| 059 | tool_database | 5 | ✅ done | 3/10 | inline (S3) | 3 TOOL_APIs; SQLite CRUD helpers |
| 060 | tool_embeddings | 5 | ✅ done | 3/10 | inline (S3) | 2 TOOL_APIs; embedding similarity pattern |
| 061 | tool_pdf_vision | 5 | ✅ done | 4/10 | inline (S3) | 2 TOOL_APIs; SPL OK — `pdf2image` not in spl123 env (install separately) |
| 062 | tool_search | 5 | ✅ done | 3/10 | inline (S3) | 1 TOOL_API; web search wrapper |
| 063 | tracing | 5 | ✅ done | 5/10 | inline (S3) | 8 TOOL_APIs; execution tracing + logging pattern |
| 064 | visualization | 5 | ✅ done | 4/10 | inline (S3) | 7 TOOL_APIs; fixed SQL-style `''regex''` quoting in validate_payment |

---

## Difficulty Analysis (Claude sonnet-4-6 self-assessment)

### S1→S3 pipeline only (auto-migration)

| Tier | Recipes | Rating | Main driver |
|------|---------|--------|-------------|
| Tier 1 basics (no tools) | 001–003, 006, 008, 017 | **2–3 / 10** | Linear / single-loop workflows; SPL constructs map 1:1 |
| Tier 1 with tools | 004 | **5 / 10** | ReAct loop + CALL targets not in stdlib |
| Tier 2 with embedding | 005 | **6 / 10** | FAISS pipeline; stateless tool interface requires encoding trick |
| Tier 2 thought tracking | 014 | **5 / 10** | Inner WHILE, many YAML helpers |
| Tier 2 CALL PARALLEL | 032 | **5 / 10** | Nested loops; more nodes → more mmd2spl hallucination risk |

### S4 tools.spl (hand-written — not yet automated)

| Recipe | Rating | Why |
|--------|--------|-----|
| 004_agent | **4 / 10** | YAML helpers straightforward; search_web already in stdlib |
| 005_rag | **7 / 10** | Full FAISS pipeline; base64 encoding to pass numpy arrays across stateless tool calls |
| 014_thinking | **5 / 10** | JSON/YAML list manipulation; conceptually clear, moderately tedious |

**Key insight:** S4 (tools.spl) is the primary bottleneck, not S1→S3. The pipeline
is reliable for simple workflows but degrades when generated CALL targets don't align
with stdlib — tool boundary identification currently requires human judgment.

---

## Known Pipeline Pitfalls

| Step | Issue | Fix |
|------|-------|-----|
| S3 | LLM preamble prose + `___SPL_BEGIN___` marker before actual SPL | Re-run S3; usually clears on retry |
| S3 | Truncated output (file ends mid-workflow) | Re-run S3 |
| S3 | Semicolons after `INPUT`/`OUTPUT` declarations | Remove manually |
| S3 | Nested `DO…END;` wrappers | Remove extra `END;` |
| S3 | CALL targets invented by LLM (not in stdlib or tools.spl) | Add to tools.spl or remap to stdlib equivalent |
| S3 | Python bodies use SQL-style `''x''` instead of `'x'` for string literals | Replace `''x''` → `'x'` in all `$$...$$` PYTHON blocks |
| S2 | `\n` in node labels, Unicode `→`, wrong `{{}}` shape | Fixed in spl3 |

---

## Agentic Workflow Pattern Coverage

42 recipes (41 PocketFlow + 1 original) collectively exercise 15 distinct agentic
workflow patterns. This is the primary value-add to the SPL cookbook: every pattern
below now has a validated, runnable reference implementation in SPL.

### Pattern taxonomy

| Pattern | Recipes | Key SPL constructs |
|---------|---------|-------------------|
| **Basic LLM I/O** | 001 chat, 002 structured_output, 003 workflow | `GENERATE`, `INPUT`/`OUTPUT` |
| **ReAct / tool-calling agent** | 004 agent, 040 coding_agent | `WHILE` + `EVALUATE` action dispatch + `CREATE TOOL_API` |
| **RAG** | 005 rag, 019 agentic_rag, 060 tool_embeddings | `CREATE TOOL_API` (FAISS/embed) + `CALL` chain |
| **Map-reduce / batch** | 006 map_reduce, 012 batch_node, 013 batch_flow, 052 batch | `CALL PARALLEL`, sub-workflow `CALL`, `WHILE` index loop |
| **Guardrails / safety** | 008 chat_guardrail | `EVALUATE` gate before final response |
| **Extended thinking** | 014 thinking | Inner `WHILE` + YAML validation helpers |
| **Evaluation / judging** | 017 judge, 056 majority_vote | `WHILE` multi-sample + `GENERATE` judge prompt |
| **Multi-agent orchestration** | 010 multi_agent, 011 supervisor, 050 a2a | `EVALUATE` router + `CALL` sub-agent dispatch |
| **Memory / conversation state** | 015 chat_memory, 034 communication | `append_turn` / `int_add` accumulators |
| **Protocol / tool integration** | 016 mcp, 062 tool_search, 059 tool_database | `CREATE TOOL_API` wrapping external APIs |
| **Adversarial / debate** | 018 debate | Two-agent `CALL` loop + `GENERATE` judge |
| **Self-healing / repair** | 021 self_healing, 042 nodejs_upgrade_agent | `WHILE` retry + `EXCEPTION WHEN BudgetExceeded` |
| **Deep / tree-of-thought research** | 032 deep_research, 057 tao | `CALL PARALLEL` fan-out + nested `WHILE` |
| **Document / data extraction** | 030 lead_generation, 031 invoice, 061 tool_pdf_vision | `CREATE TOOL_API` (PDF/CSV parse) + `EVALUATE` validator |
| **Code / SQL generation** | 033 text2sql, 040 coding_agent, 054 code_generator | `WHILE` debug-retry + `GENERATE` + `CREATE TOOL_API` exec |
| **Monitoring / tracing** | 020 heartbeat, 063 tracing | Periodic `WHILE` + `CREATE TOOL_API` logger |
| **Agent skills routing** | 041 agent_skills | `EVALUATE` keyword-match dispatch + `CALL` skill |
| **Web crawling** | 058 tool_crawler | 12-tool BFS crawler; `WHILE` queue loop |
| **HITL / human-in-the-loop** | 053 cli_hitl | `CREATE TOOL_API` approval gate (sync) |
| **Async fan-out** | 051 async_basic | Sub-workflow decomposition via multiple `CALL`s |
| **Visualization / reporting** | 064 visualization, 042 nodejs_upgrade_agent | `GENERATE` report + `write_file` |

### SPL construct coverage

| Construct | # recipes exercising it | Notes |
|-----------|------------------------|-------|
| `GENERATE ... INTO @var` | 42 / 42 | Universal |
| `CREATE TOOL_API ... AS PYTHON $$` | 36 / 42 | 6 recipes use stdlib only |
| `WHILE condition DO ... END` | 22 / 42 | Retry, iteration, queue loops |
| `EVALUATE @var WHEN ... ELSE ... END` | 28 / 42 | Dispatch, guard, status check |
| `CALL PARALLEL ... END` | 4 / 42 | 006, 010, 032, 051 |
| `CALL sub_workflow(...) INTO @var` | 12 / 42 | Sub-workflow composition |
| `EXCEPTION WHEN BudgetExceeded` | 2 / 42 | 021, 042 |
| `IMPORT 'tools'` | 5 / 42 | Phase-0 seeded recipes |
| `CREATE FUNCTION` (prompt template) | 30 / 42 | Named prompt reuse |

### Gaps and future coverage

| Pattern | Status | Path |
|---------|--------|------|
| Durable interrupt / resume | not covered | DBOS adapter (see cookbook-langgraph plan) |
| Streaming intermediate outputs | not covered | adapter concern; out of scope for .spl |
| Time travel / rollback | not covered | needs SPL checkpointing design |
| Multi-modal (image/audio input) | partial (061 pdf_vision) | `generate_multimodal()` dispatcher already in executor |
| Cross-node distributed state | not covered | Momagrid Hub-to-Hub registry expands this |

---

## Tool Registry

See [`tool_api_registry.md`](tool_api_registry.md) — quick-lookup of all
`CREATE TOOL_API` functions across cookbook-pocketflow, with stdlib promotion candidates.

---

## Next Steps

- [x] Phase 2: Tier 2 recipes (010–021) — all 10/10 validated ✅ (no tools.spl needed; S3 generated inline)
- [x] Phase 3: Tier 3 recipes (030–034) — all 4/4 validated ✅ (S3 generated inline; 033/034 re-run after session limit)
- [x] Phase 4: Tier 4 recipes (040–041) — all 2/2 validated ✅ (040 had SQL-style `''` quoting bug in 5 Python bodies; fixed manually)
- [x] Phase 5 wave 1: Tier 5 recipes (050–058) — all 9/9 validated ✅ (052/055/058 needed quoting fixes)
- [x] Phase 5 wave 2: Tier 5 recipes (059–064) — all 6/6 validated ✅ (064 needed quoting fix; 061 needs `pip install pdf2image`)
- [ ] Promote `parse_yaml`, `extract_yaml_field`, `append_turn` to stdlib (see registry)
- [ ] Automate S4: add LLM-assisted `utils.py → tools.spl` conversion step to pipeline
- [ ] Start `cookbook-langgraph/` following same structure
