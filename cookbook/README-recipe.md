# Cookbook Recipe Analysis & Plan (2026-07-17)

Two-part output from a review session, to be implemented in a follow-up chat:
1. Findings from reviewing the ~79 existing recipes for refactor/cleanup opportunities.
2. Proposed new recipes showcasing SPL's **dual-mode** pattern (LLM-only vs LLM+deterministic-verify), to broaden the "verifier ladder" beyond the existing math-heavy set.

---

## Part 1 — Existing Recipe Review Findings (prioritized)

### 1. `77_neurosymbolic` missing from `cookbook_catalog.json` — high priority

`cookbook_catalog.json` has 79 entries (ids 01–80, no 77) — the `77_neurosymbolic/` directory exists on disk and is currently the most actively-developed recipe (paper drafts, `run_experiment.py`, the full experiment DB, `latex_tables_for_paper.tex`), but it was never added to the catalog. Very likely an oversight given how central it now is (TMLR paper, the full 1,200-cell Python/Go experiment runs). **Action**: add a catalog entry (`id: "77"`, dir `77_neurosymbolic`, category `reasoning`/neurosymbolic, description referencing the verifier-ladder/round-trip design).

### 2. Three orphan directories — all abandoned, safe to delete

| Orphan dir | Catalog counterpart | Verdict | Evidence |
|---|---|---|---|
| `05_v3_self_refine` | `05_self_refine` (id 05) | Abandoned fork | Only 4 commits, last 2026-04-19; the catalog's `05_self_refine` kept receiving commits through 2026-07-10. Self-contained cross-framework benchmark (autogen/langgraph/crewai, `self_refine.go`, `targets/{go,ts}`) never folded back in. |
| `71_linalg_micro_textbook` | `71_linalg_concept_book` | Gutted, superseded | Commit `4b86472` ("refine") deleted all real source (`build_micro_textbook.spl`, `linalg_graph.py`, `style_profiles.py`, `readme.md`); only `archive/`/`logs/`/cache `.db` files remain. |
| `74_domain_textbook` | `74_concept_book` | Gutted, superseded | Same commit `4b86472` deleted all yaml graphs/scripts; work was consolidated into `74_concept_book`'s generic `graph_lib.py`. Only `__pycache__` remains. |

**Action**: delete all three directories — nothing left worth merging back.

### 3. Real code duplication in media recipes

The same `convert_audio()` ffmpeg logic is implemented **three times**: `cookbook/tools/audio_tools.py`, `cookbook/tools/stdlib_media.spl` (inline Python), and `cookbook/59_audio_convert/run.py` (reimplements it standalone instead of calling the shared tool). Only 5 of ~79 `.spl` files actually import from `cookbook/tools/` at all.

**Near-free fix**: `cookbook/61_video_to_audio/` is marked `wip` only because it has no `run.py`/`sample/` dir — but `cookbook/tools/video_tools.py::extract_audio()` already implements exactly what it needs. Likely completable in minutes by wrapping the existing shared tool.

**Action**: consolidate the 3x-duplicated `convert_audio()` into the shared `tools/audio_tools.py` version everywhere; build out `61_video_to_audio/run.py` around the existing `extract_audio()` helper.

### 4. `52_audio_summary` / `60_voice_dialogue` "disabled" status — looks genuinely still valid, not stale

Both cite LFM-2.5 rejecting audio input on OpenRouter/Ollama, dated 2026-06-07 — an external/upstream blocker. `60_voice_dialogue/sample/` confirmed to contain only `.gitkeep` (no audio), matching the stated blocker. `59`/`61` "wip" status is accurate for the same reason (missing sample/run.py).

**Action**: no change needed — re-check the LFM-2.5 audio-input blocker periodically, but don't treat as stale right now.

### 5. Minor — stale cross-recipe numbering references

`59_audio_convert/readme.md` header says "Recipe 58" (actual id 59); both `59` and `61` readmes reference "recipe 51 (audio_summary)" / "recipe 53 (text_to_speech)" — actual ids are 52 and 55. Leftover from a past renumbering pass.

**Action**: grep/fix the stale recipe-number references in these readmes.

### 6. Dead-file clutter

18 recipes (e.g. `12_plan_and_execute`, `33_interview_sim`, `48_credit_risk`, `65_llm_splc`) carry a 1-line stub `tools.py` reading `"# Migrated to CREATE TOOL_API in ...spl"`. Harmless but pure clutter since the real logic already lives in the `.spl` file.

**Action**: delete these 18 stub files repo-wide.

### No other supersession chains found

Beyond the known 70→71→73→74 (linalg → concept-book → geometry → generic domain-textbook) and 50→79 (code_pipeline → pytest-verified upgrade) arcs — those are already-good generalizations, not duplicative.

---

## Part 2 — Proposed New Recipes (dual-mode showcase)

Existing dual-mode recipes (67/68/75/76/77/78/79/80) all follow the verifier-ladder shape: `enable_solver=false` → free-form LLM answer only; `enable_solver=true` → LLM handles NL parsing/narration while a deterministic tool computes, and a round-trip check confirms the result. They currently cover algebra/calculus/ODEs (67), Sage (75), Lean (76), linear programming (78), and computer vision (80). The proposals below extend the pattern into domains those don't touch.

Only `networkx` is already installed among the libraries these would need; the others require a `pip install` note, same as Sage/Lean already do.

| # | Recipe | Domain | Deterministic verifier | New dep? | Why it's a good next one |
|---|---|---|---|---|---|
| 1 | **81_graph_reasoning** | Discrete math (shortest path, bipartite check, cycle detection) | `networkx` | No — already installed | Fastest to build; extends the ladder into discrete/combinatorial reasoning, distinct from 67/75/78's continuous math |
| 2 | **82_logic_puzzle_solver** | Constraint satisfaction (Zebra-style puzzles, Sudoku-lite) | `python-constraint` or `z3-solver` | Yes | A genuinely different verifier *class* — SAT/CSP, not numeric — complements 78's LP with combinatorial logic |
| 3 | **83_unit_dimensional_check** | Physics/engineering word problems (kinematics, unit conversions) | `pint` | Yes | New tool family; physics word-problems are close to the η_AI energy-efficiency framing — natural next data point for the scaling-trend argument |
| 4 | **84_sql_verifier** | Text-to-SQL from a natural-language question | Real SQLite execution, row-level diff vs ground truth | No (stdlib `sqlite3`) | High practical relevance; "run it and check the rows" is a crisp, legible round-trip story for reviewers |
| 5 | **85_property_based_code_verify** | Code generation | `hypothesis` property-based testing (vs 79's example-based pytest) | Yes | Directly extends 79's own upgrade arc (50→79) one rung further — auto-generated edge cases instead of fixed examples |
| 6 | **86_financial_calc_verifier** | Compound interest / loan amortization word problems | Closed-form formula recompute | No (stdlib `decimal`) | Business-facing domain, ties to existing credit-risk/regulatory-audit recipes (48/49) without needing a new library |
| 7 | **87_route_optimization** | Vehicle-routing / TSP-style logistics | `ortools` | Yes | A second, harder optimization class beyond 78's LP — NP-hard combinatorial, still exactly checkable |

**Recommended starting order**: #1 and #2 first (cheapest, no risky new deps; #2 fills the clearest gap since there's no combinatorial/logical-reasoning verifier-ladder recipe yet). #3 is the most paper-relevant given the η_AI energy-efficiency research direction.

---

## Next Steps (for the follow-up implementation session)

1. Decide which cleanup items from Part 1 to apply (catalog fix for 77, delete 3 orphan dirs, consolidate audio-convert duplication, fix stale readme numbering, delete 18 dead `tools.py` stubs).
2. Decide which new recipes from Part 2 to build, and in what order (81/82 recommended first).
3. For each new recipe: follow the existing verifier-ladder recipe shape (see `77_neurosymbolic/symbolic_math.spl` + `sympolic_tools.spl` as the reference pattern — `enable_solver` param, `CREATE TOOL_API` for the deterministic tool, round-trip check via a `classify_from_value`-style function, `RETURN ... WITH roundtrip = ...`).
4. Add each new recipe to `cookbook_catalog.json` (and `cookbook_catalog-go.json` if it should be included in the Go recipe-test pass) as it's built.
