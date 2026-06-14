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
| 010 | multi_agent | 2 | — | | | |
| 011 | supervisor | 2 | — | | | |
| 012 | batch_node | 2 | — | | | |
| 013 | batch_flow | 2 | — | | | |
| 015 | chat_memory | 2 | — | | | |
| 016 | mcp | 2 | — | | | |
| 018 | debate | 2 | — | | | |
| 019 | agentic_rag | 2 | — | | | |
| 020 | heartbeat | 2 | — | | | |
| 021 | self_healing | 2 | — | | | |
| 030 | lead_generation | 3 | — | | | |
| 031 | invoice | 3 | — | | | |
| 033 | text2sql | 3 | — | | | |
| 034 | communication | 3 | — | | | |
| 040 | coding_agent | 4 | — | | | |
| 041 | agent_skills | 4 | — | | | |

*Tier 5 (050–064) deferred until Tiers 1–4 are complete.*

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
| S2 | `\n` in node labels, Unicode `→`, wrong `{{}}` shape | Fixed in spl3 |

---

## Tool Registry

See [`tool_api_registry.md`](tool_api_registry.md) — quick-lookup of all
`CREATE TOOL_API` functions across cookbook-pocketflow, with stdlib promotion candidates.

---

## Next Steps

- [ ] Phase 2: Tier 2 recipes (010–021) — expect tools.spl needed for 019_agentic_rag
- [ ] Promote `parse_yaml`, `extract_yaml_field`, `append_turn` to stdlib (see registry)
- [ ] Automate S4: add LLM-assisted `utils.py → tools.spl` conversion step to pipeline
- [ ] Start `cookbook-langgraph/` following same structure
