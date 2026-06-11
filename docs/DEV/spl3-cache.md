# Design: `spl3 cache` — Content-Level Caching

> **Status**: Phase 1 implemented — content cache, CLI, stdlib tools, and unit tests complete. Phase 2 (adapter-level prefix caching) and Phase 3 (SPL language `CACHE BY` / `UNLESS STALE`) pending.
> **2026-06-11 (B-4):** the single provenance ordinal described below was replaced by a trust-badge *set* on two orthogonal axes (claim: `machine_verified` → `machine_proved`; exposition: `ai_reviewed` → `human_verified`) — see `sage_lean_integration_plan.md` §B.1 and `spl3-lean.md` §4. Sections 6–9 are updated to the badge model; pre-B-4 DBs and exports migrate automatically.

---

## 1. Motivation

The micro-textbook workflow is LLM-intensive by design: generating and verifying
every concept section in a knowledge graph costs dozens of LLM calls per run.
Good caching is not a performance optimisation — it is what makes iterative
development of a large project economically feasible, and what makes on-demand
generation safe to serve to learners without re-running the full verification
loop each time.

The deeper principle: **a verified section is correct forever, until its inputs
change**. A section that passed `ASSERT reducible`, `verify_math`, and
`shape_check` does not become wrong because time passes. TTL-based expiry is the
wrong invalidation strategy for this content. Content-addressable storage (CAS)
— where the cache key is a hash of the inputs, not a timestamp — is the right
model. Same principle git uses for blobs and commits.

---

## 2. What Already Exists

### 2.1 `dd-cache` — the existing caching library in the dd-* ecosystem

`dd-cache` (`digital-duck/dd-cache`, MIT) is the shared caching layer built
specifically for the dd-* ecosystem. Its DESIGN.md explicitly lists `spl` as one
of the three packages it was built to serve. It is already a dependency of `spl/`.

**Architecture — backend-swappable via `BaseCacheAdapter`:**

```
BaseCacheAdapter (ABC)
├── InMemoryCache   — dict + lazy TTL eviction, stdlib only, process lifetime
├── DiskCache       — SQLite BLOB store (pickle), stdlib only, persistent
└── RedisCache      — Redis via redis-py, optional dep, distributed
```

**Uniform interface** (all adapters):
```python
cache.get(key)                        # → Any | None
cache.set(key, value, *, ttl=None)    # ttl in seconds; see TTL semantics below
cache.delete(key)                     # → bool
cache.exists(key)                     # → bool
cache.clear()
cache.stats()                         # → CacheStats(backend, total_keys, ttl_enabled, extra)
cache.get_or_set(key, fn, *, ttl)     # cache-miss pattern — calls fn() on miss, stores result
```

**TTL semantics** (all adapters, enforced at `BaseCacheAdapter`):

| Value | Meaning |
|-------|---------|
| `ttl=None` | Never expire — entry lives until explicitly deleted or `clear()`ed. Used by Layer 2 (content cache). |
| `ttl=0` | Expire immediately — entry is stale as soon as it is written; every subsequent `get()` returns `None`. Useful for bypassing the cache in tests or during troubleshooting without changing call sites. |
| `ttl=N` (N > 0) | Expire after N seconds. Used by Layer 1 (prompt cache, default 3600 s). |
| `ttl<0` | Immediate expiry — `dd_cache` silently treats negative values as expired (same observable effect as `ttl=0`; no exception raised). Treat as equivalent to `ttl=0` in application code. |

`ContentCache` (Layer 2) does not expose `ttl` to callers — it always passes `ttl=None` internally, enforcing the write-once immutable invariant at the API boundary.

**Key utilities** (`dd_cache.utils`):
```python
make_key(*parts: str) -> str          # joins parts with ":" — namespace-aware key construction
serialize(value) / deserialize(data)  # pickle round-trip for arbitrary Python objects
```

`DiskCache` stores `(key TEXT, value BLOB, expires_at REAL)` in SQLite.
Expiry is lazy — evicted on `get()` / `exists()`, no background sweep.
`InMemoryCache` uses a `dict` + `_expiry` dict; no deps, ideal for process-scoped L1.
`RedisCache` delegates TTL to native Redis `SET … EX`.

The adapter pattern means swapping backends — local dev → team Redis →
future `MomagridCacheAdapter` — requires no changes to code that calls `ContentCache`.

### 2.2 Prompt cache (`spl/storage/memory.py` + `spl/executor.py`)

Layer 1 (prompt cache) already exists and uses `dd-cache.DiskCache` directly:

- **Backend**: `dd_cache.DiskCache(path=".spl/prompt_cache.db")`.
- **Key**: `sha256(f"{model}:{assembled_prompt}")` — exact string match.
- **TTL**: configurable (`cache_ttl`, default 3600 s).
- **CLI**: `spl cache list` / `spl cache clear`.
- **Enabled via**: `spl run --cache` or `cache: true` in config.

This is the right tool for **development iteration** — avoid paying for the same
LLM call twice in the same session. It is the **wrong tool** for verified
generative content:

| Gap | Why it matters |
|-----|---------------|
| Exact-prompt key | Adding one sentence of prior-section context changes the hash → miss. Concept-level caching needs a key stable across prompt reformulations. |
| TTL invalidation | Verified content should be immutable until its *inputs* change, not until a timer fires. |
| No provenance | The cache stores raw blobs but not which workflow, rubric version, or dependency state produced them — so re-use across rubric upgrades or graph revisions is unsafe. |
| No dependency tracking | If `span` is regenerated, the cache has no way to know that all sections depending on `span` are now stale. |

### 2.3 `spl3/` — no cache layer yet

`spl3/` has no cache infrastructure. The `kv_store` in `MemoryStore` is workflow
runtime state, not a reuse cache.

---

## 3. Two Cache Layers — the Right Split

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2 — Content Cache  (new)                                 │
│  Key: hash(concept + params + rubric_version + dep_hashes)      │
│  TTL: none — write-once immutable                               │
│  Scope: cross-session, portable / shareable                     │
│  Invalidation: input-driven (CAS), explicit, cascading          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ miss → generate + verify → store
┌───────────────────────────▼─────────────────────────────────────┐
│  Layer 1 — Prompt Cache  (exists in spl/)                       │
│  Key: sha256(model + assembled_prompt)                          │
│  TTL: 1–24 h (configurable)                                     │
│  Scope: per-session / per-workspace                             │
│  Invalidation: TTL, explicit clear                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ miss → LLM call → store
                            ▼
                      LLM adapter
                  (server-side prompt caching
                   transparent via Anthropic / OpenAI)
```

Layer 1 (prompt cache) already exists and stays unchanged.
Layer 2 (content cache) is what this design builds.

The executor checks Layer 2 first. A Layer 2 hit skips both the LLM call **and**
the verification loop — the entry is already known-good. A Layer 2 miss falls
through to Layer 1 (which may save the raw LLM call cost) and then to the live
adapter. After a successful generate+verify cycle, the result is promoted into
Layer 2.

Server-side caching (Anthropic `cache_control`, OpenAI automatic prefix caching)
is a third, orthogonal layer that reduces input token cost on Layer 1 misses.
It requires no changes to the content cache design and is handled at the adapter
level.

---

## 4. Open-Source Survey

### 4.1 LLM-Specific Caches

**GPTCache** (Zilliz, Apache 2.0) — the most feature-rich OSS semantic cache for
LLMs. Architecture: query → embedding → vector store lookup (cosine similarity
threshold) → cache hit or miss. Pluggable: embedding models (OpenAI, Hugging
Face, ONNX), vector stores (Milvus, Faiss, Redis, Qdrant), storage backends
(SQLite, MySQL). Production sweet spot: 0.90–0.95 cosine similarity threshold;
at 0.90, false-positive rate is ~3%.

**The 3% false-positive problem**: a semantically similar prompt is not the same
prompt. For correctness-critical content (math sections, verified proofs), a 3%
rate of serving the wrong cached answer is unacceptable. GPTCache's exact-match
path and SQLite backend are worth reusing directly; its semantic-similarity path
must not be used for Layer 2. Exact match by content key is the only safe lookup
strategy when correctness is non-negotiable.

**LangChain cache** (MIT) — `InMemoryCache`, `SQLiteCache`, `RedisCache` (all
exact match), `RedisSemanticCache` (vector-based). Simple to use but all operate
at raw `(prompt, llm_string)` granularity — no concept-level key or dependency
tracking.

**Anthropic prompt caching** — server-side, 5-minute TTL default (up to 1 hour
extended). Cache writes cost 1.25× input tokens; hits cost 0.10×. Up to 4
breakpoints per request. Workspace-isolated. Enable by adding
`cache_control: {"type": "ephemeral"}` on system/context blocks. Cost reduction
of ~90% on prefix hits.

**OpenAI prompt caching** — automatic on ≥ 1024 tokens, 128-token increment
granularity. TTL 5–10 minutes (max 1 hour; extended option to 24 hours). 50–90%
cost reduction, 80% latency reduction. No configuration; free within standard
pricing.

Both server-side caches are Layer 0 — they reduce the cost of LLM calls that
Layer 1 and Layer 2 missed. Enable them at the adapter level; they require no
changes to the content cache.

**LMCache** (research, Apache 2.0) — KV-cache sharing across nodes using a
three-tier architecture: GPU HBM (hot) → CPU DRAM (warm) → local disk/remote
(cold). Achieves 2.5 GB/s from local disk, ~1.5 GB/s from peer nodes. Relevant
for Momagrid distributed inference — a future integration point, not Phase 1.

### 4.2 Caching Patterns

**Content-addressable storage (CAS / git-objects model)** — the canonical
solution for immutable, dependency-aware caching. Key = hash of inputs, not hash
of outputs. If any input changes, the key changes → automatic invalidation, no
bookkeeping. This is the model for Layer 2's key computation.

**Write-once immutable cache** — once a verified entry is stored, it is never
mutated in place. A re-generation creates a new entry with a new key (because the
inputs changed). Old entries remain accessible by their old key until explicitly
purged. Natural audit trail; safe rollback to any prior verified state.

**Fragment-level caching** — cache static prompt prefixes (pedagogical
guidelines, domain description, rubric) separately from dynamic per-concept
suffixes. Reduces token cost on Layer 1 misses by enabling Anthropic/OpenAI
prefix caching to hit more aggressively. For the micro-textbook: the workflow
preamble (domain, graph structure, primitives) is the cacheable prefix; the
per-concept generation call is the dynamic suffix.

**Dependency-graph invalidation** — the build-system pattern (Make, Bazel, Nix,
Nix derivations). When upstream node X changes, all downstream nodes that depend
on X are invalidated. For the micro-textbook: if `linear_combination` is
regenerated (new content hash), all concepts whose `composed_of` references
`linear_combination` get new dependency hashes → their Layer 2 keys change →
automatic miss → re-generate on next request.

**Stale-while-revalidate** — serve the cached entry immediately; refresh
asynchronously in the background. Appropriate for `machine_generated` content
where latency matters more than strict freshness. Not appropriate for entries at
`machine_verified` or above — correctness guarantee must be re-established before
serving.

---

## 5. Cache Key Design

### 5.1 Content key (Layer 2) — CAS model

```python
def content_key(
    concept: str,
    params: dict,                    # domain, payoff_weight, primitive_budget, …
    rubric_version: str,             # version of rubric used for verification
    dep_hashes: dict[str, str],      # {upstream_concept: sha256(its_content)}
) -> str:
    payload = json.dumps({
        "concept":  concept,
        "params":   params,
        "rubric":   rubric_version,
        "deps":     dep_hashes,      # changes when any upstream concept changes
    }, sort_keys=True)
    return sha256(payload.encode()).hexdigest()
```

`dep_hashes` is computed by traversing `ancestors(graph, concept)` and hashing
the stored content of each ancestor. If any ancestor is regenerated, its
`content_hash` changes → `dep_hashes` changes → this concept's key changes →
automatic miss. No bookkeeping required; the CAS chain enforces consistency.

### 5.2 Content hash (used as dep_hash by dependents)

```python
def content_hash(content: str) -> str:
    return sha256(content.encode()).hexdigest()[:16]  # 16 hex chars — short enough for dep_hashes JSON
```

### 5.3 Prompt key (Layer 1, unchanged)

```python
prompt_hash = sha256(f"{model}:{assembled_prompt}".encode()).hexdigest()
```

No change to the existing implementation.

---

## 6. Core Types

```python
# spl3/cache/types.py

# Trust badges (B-4) — a set on two orthogonal axes, not one ladder:
CLAIM_BADGES      = ["machine_verified", "machine_proved"]   # attest the math
EXPOSITION_BADGES = ["ai_reviewed", "human_verified"]        # attest the prose
# [] = machine_generated baseline; 'canonical' is derived (is_canonical():
# top badge on both axes), shown as ★ in the CLI, never stored.

@dataclass
class CacheEntry:
    key: str                         # content_key — hash of inputs
    concept: str                     # concept name (e.g. "eigenpair")
    content: str                     # the generated+verified section text
    content_hash: str                # sha256(content) — used as dep_hash by dependents
    rubric_version: str
    dep_hashes: dict[str, str]       # inputs used to produce this entry
    params: dict
    adapter: str
    model: str
    token_cost: int                  # tokens spent generating
    created_at: str
    hit_count: int                   # how many times served from cache
    badges: list[str] = []           # trust badge set (see above)
    stale: bool = False              # explicitly invalidated but not yet purged
    verdict: dict | None = None      # latest promotion's audit record
    verifier: str = ""               # engine-of-record: "sympy" | "sage" | "lean" | ""
    statement: str = ""              # kernel-checked Lean prop backing machine_proved

@dataclass
class CacheStats:
    total_entries: int
    by_badge: dict[str, int]         # {"machine_verified": 12, "machine_proved": 1, …}
    unbadged: int                    # machine_generated baseline count
    canonical: int                   # derived ★ count
    total_hits: int
    total_token_cost: int            # tokens spent generating all entries
    estimated_tokens_saved: int      # sum(hit_count * token_cost) across all entries
    concepts: list[str]
    stale_count: int
```

---

## 7. Architecture

### 7.1 Two-component design

`ContentCache` is built from two components with different responsibilities:

```
ContentCache
│
├── _store: dd_cache.BaseCacheAdapter          blob storage (swappable)
│   ├── DiskCache(".spl/content_cache.db")     local dev — SQLite, no extra deps
│   ├── InMemoryCache()                        in-process L1 hot tier (future)
│   └── RedisCache(host=…)                     team shared (future)
│       └── MomagridCacheAdapter(…)            distributed node peers (future)
│
└── _meta: sqlite3.Connection                  metadata index (always local)
    ├── content_meta table                     badges, stale, token_cost, hit_count
    └── dep_graph table                        cascading invalidation via recursive CTE
```

**Why split?**

`dd-cache` excels at `key → blob` with TTL and backend swap. Everything it does
not model — trust badges, stale flags, hit counts, token cost, dependency
graph — lives in the metadata index. The metadata index is always local SQLite
because it needs relational queries (recursive CTE for cascading invalidation,
badge aggregation for stats). Blob storage can be remote; metadata cannot.

**Key composition** uses `dd_cache.utils.make_key`:

```python
from dd_cache.utils import make_key

# Layer 1 prompt cache (existing):
layer1_key = make_key("spl", "prompt", sha256(f"{model}:{prompt}").hexdigest())

# Layer 2 content cache (new):
layer2_key = make_key("spl3", "content", content_key(concept, params, rubric_ver, dep_hashes))
```

The `"spl3:content:"` prefix namespaces content keys away from Layer 1 prompt
keys — both can safely share the same `DiskCache` file, or use separate files.

**`get_or_set` maps to `CACHE BY`:**

```python
# what the executor does for GENERATE … CACHE BY:
section = store.get_or_set(
    layer2_key,
    fn=lambda: generate_and_verify(concept),
    ttl=None,    # no expiry — content is immutable once verified
)
```

### 7.2 Module layout

```
spl3/cache/
├── __init__.py      # exports ContentCache, get_content_cache
├── types.py         # CacheEntry, CacheStats (extend dd_cache.CacheStats)
├── keys.py          # content_key(), content_hash(); imports make_key from dd_cache.utils
├── meta.py          # MetaStore — SQLite metadata index (badges, dep_graph, stale)
├── content.py       # ContentCache — wraps BaseCacheAdapter + MetaStore; full API
└── cli.py           # spl3 cache subcommands
```

No `store.py` — blob storage is delegated entirely to `dd-cache`.

### 7.3 ContentCache API

```python
class ContentCache:
    def __init__(
        self,
        store: BaseCacheAdapter,               # e.g. DiskCache(".spl/content_cache.db")
        meta_path: str = ".spl/content_meta.db",
    ): ...

    def get(
        self, concept: str, params: dict,
        rubric_version: str, dep_hashes: dict,
        min_badge: Optional[str] = None,
    ) -> Optional[CacheEntry]: ...
    # Returns None on miss or if the badge set does not satisfy min_badge.
    # The filter is axis-local: min_badge="machine_verified" is satisfied
    # by machine_verified or machine_proved, never by exposition badges.

    def put(
        self, concept: str, content: str, badges: list[str] | str = None,
        params: dict = None, rubric_version: str = "v1", dep_hashes: dict = None,
        adapter: str = "", model: str = "", token_cost: int = 0,
        verifier: str = "", statement: str = "",
        provenance: str = None,        # legacy single-tier input, converted
    ) -> CacheEntry: ...

    def promote(
        self, key: str, badge: str,
        verdict: Optional[dict] = None,
    ) -> list[str]:
        """Add a trust badge to the entry's set (no ladder, no downgrade,
        duplicate add is an error). verdict stored for auditability."""

    def invalidate(self, concept: str, cascade: bool = True) -> list[str]:
        """Mark stale; cascade=True propagates via dep_graph recursive CTE."""

    def dependents(self, concept: str) -> list[str]:
        """All concepts whose dep_hashes reference this concept (from dep_graph table)."""

    def stats(self) -> CacheStats: ...
    def export(self, path: Path) -> None: ...
    def import_(self, path: Path, merge: bool = True) -> int: ...
```

### 7.4 Metadata index schema (SQLite — always local)

```sql
-- content_meta: queryable metadata for every entry in the dd-cache blob store
CREATE TABLE content_meta (
    key          TEXT PRIMARY KEY,     -- same key as in dd-cache store
    concept      TEXT NOT NULL,
    content_hash TEXT NOT NULL,        -- sha256(content)[:16] — dep_hash used by dependents
    badges       TEXT NOT NULL DEFAULT '[]',  -- JSON trust-badge set (B-4)
    rubric_ver   TEXT NOT NULL,
    dep_hashes   TEXT NOT NULL,        -- JSON {concept: content_hash}
    params       TEXT NOT NULL,        -- JSON
    adapter      TEXT,
    model        TEXT,
    token_cost   INTEGER DEFAULT 0,
    hit_count    INTEGER DEFAULT 0,
    stale        INTEGER DEFAULT 0,
    verdict      TEXT,                 -- JSON JudgeResult from latest promotion
    verifier     TEXT NOT NULL DEFAULT '',  -- engine-of-record (A-3)
    statement    TEXT NOT NULL DEFAULT '',  -- Lean prop backing machine_proved (B-4)
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE INDEX idx_concept ON content_meta(concept);
CREATE INDEX idx_stale   ON content_meta(stale);

-- Pre-B-4 DBs carried a single `provenance` ordinal instead of `badges`;
-- MetaStore migrates them on open (each legacy tier becomes the badge set
-- attesting only what it attested; 'machine_generated' → '[]').

-- dep_graph: maintained on every put(); drives cascading invalidation
CREATE TABLE dep_graph (
    dependent   TEXT NOT NULL,   -- concept name that depends on…
    dependency  TEXT NOT NULL,   -- …this upstream concept name
    PRIMARY KEY (dependent, dependency)
);
```

The `dep_graph` table is what makes `invalidate(cascade=True)` a single SQL
recursive CTE query — no in-Python graph traversal over JSON columns needed.
The blob store (`dd-cache`) never needs to be scanned for invalidation.

**On `promote()`:** updates `badges` and `verdict` in `content_meta` only;
the blob in `dd-cache` is unchanged (content is immutable, trust is metadata).
This is efficient — no blob re-serialization on promotion.

---

## 8. Provenance Integration

The content cache is the physical implementation of the micro-textbook
trust-badge pipeline. Badges accumulate on two independent axes:

```
GENERATE write_section(@concept, @graph)
    → cache.put(badges=[])                                  # baseline

CALL verify_math(@section) → 'pass (sympy)'                 # claim axis
    → cache.promote(key, "machine_verified")                #   (or put with
                                                            #    verifier="sympy")
recipe 76: Lean kernel-checks the formalized claim          # claim axis, top
    → cache_put(badges='machine_proved', verifier='lean',
                statement=@lean_stmt)

spl3 judge @section --criteria correctness → PASS           # exposition axis
    → cache.promote(key, "ai_reviewed", verdict=judge_result)

human editor accepts                                        # exposition axis, top
    → cache.promote(key, "human_verified")
```

An entry holding the top badge on *both* axes is `canonical` (derived, ★ in
the CLI). The delivery layer filters per axis:
`cache.get(concept, …, min_badge="machine_verified")` — learners never
receive mathematically unverified content, and an `ai_reviewed`-only entry
does not slip through (the pre-B-4 ordinal allowed exactly that). Entries
below the threshold are a cache miss, even if the key is present.

---

## 9. CLI Design

```bash
# Inspect
spl3 cache list [--concept NAME] [--badge BADGE] [--format table|json]
spl3 cache show <key>                            # full entry; renders prose + Lean statement together
spl3 cache stats                                 # hit rate, tokens saved, badge breakdown

# Invalidation
spl3 cache invalidate --concept NAME             # mark stale, output: list of affected keys
spl3 cache invalidate --concept NAME --cascade   # propagate to all dependents
spl3 cache clear --stale                         # remove all stale-flagged entries
spl3 cache clear --all                           # full wipe (prompt cache unaffected)
spl3 cache clear --badge unbadged                # remove baseline (machine_generated) entries only

# Portability — team sharing without a live remote store
spl3 cache export -o cache.tar.gz
spl3 cache import cache.tar.gz [--merge]         # --merge: skip conflicts; default: error on conflict

# Manual promotion
spl3 cache promote <key> --to human_verified
```

---

## 10. SPL Language Integration

### 10.1 `CACHE BY` clause on `GENERATE`

```spl
GENERATE write_section(@concept, @graph) INTO @section
    CACHE BY concept=@concept, rubric=@rubric_version, deps=@dep_hashes
```

The executor computes `dep_hashes` automatically by traversing
`ancestors(@graph, @concept)` and reading each ancestor's `content_hash` from the
cache. It checks Layer 2 before calling the LLM. On a hit, `@section` is bound
immediately with zero LLM cost; on a miss, the LLM is called and the result is
stored at the unbadged `machine_generated` baseline.

### 10.2 `UNLESS STALE` modifier

```spl
GENERATE write_section(@concept, @graph) INTO @section
    CACHE BY concept=@concept, rubric=@rubric_version, deps=@dep_hashes
    UNLESS STALE
```

`UNLESS STALE` treats invalidated (stale-flagged) entries as misses. Without it,
stale entries are served with a warning — useful during rubric transitions where
you want to serve old content while re-generation runs in the background.

### 10.3 `cache_get` / `cache_put` (no new syntax — already in micro-textbook design)

The `answer_on_demand` workflow already uses:

```spl
CALL cache_get(@concept) INTO @section
EVALUATE @section:
    WHEN miss:
        CALL build_micro_textbook(@concept) INTO @section
        CALL cache_put(@concept, @section)
APPEND @section TO @lesson
```

This maps directly to `ContentCache.get()` and `ContentCache.put()`. Register
`cache_get` / `cache_put` as stdlib tool-api calls — no new syntax required.

---

## 11. Integration Points

### 11.1 `build_micro_textbook` — warm vs cold run

The `FOR @concept IN @order DO` loop checks Layer 2 before each generation:

```
cold run (first time):   every concept generates + verifies → populates cache
warm run (second time):  every concept is a Layer 2 hit → near-zero LLM cost
partial run (rubric bump): invalidated concepts regenerate; unaffected hits serve
```

A fully warm cache makes subsequent runs of `build_micro_textbook` essentially
free. This is critical for the iterative development workflow: tweak a rubric,
invalidate affected concepts, re-run — only the changed subtree is regenerated.

### 11.2 `answer_on_demand` — lazy textbook warming

The on-demand cache is Layer 2. A learner asking about `eigenpair` gets the
cached verified section instantly after the first generation. The cache warms
organically as learners explore different concepts. A published textbook ships
with a pre-warmed cache export (`spl3 cache export`); importing it gives every
learner instant responses for all verified concepts.

### 11.3 `spl3 judge` integration

When `spl3 judge` passes an entry, it adds the `ai_reviewed` exposition badge
via `cache.promote(key, "ai_reviewed", verdict=judge_result)`. The
`JudgeResult` is stored alongside the entry for auditability. This closes the
loop between the judge design (spl3-judge.md) and the cache design — the verdict
that authorised the promotion is permanently recorded.

### 11.4 Anthropic / OpenAI server-side prefix caching (Layer 0)

Enable transparently at the adapter level:
- Anthropic: add `cache_control: {"type": "ephemeral"}` to system prompt and
  large context blocks (graph, domain description). 0.10× cost on subsequent
  calls within the 5-minute window; up to 90% cost reduction.
- OpenAI: automatic on ≥ 1024-token prompts; no configuration needed.

Both apply to Layer 1 misses (the raw LLM call). They compound with Layer 2:
a Layer 2 hit saves 100% of the call cost; a Layer 1 hit saves the LLM token
cost; a server-side hit reduces the token cost on a Layer 1 miss. Three layers
of defence against unnecessary spend.

### 11.5 Future: Momagrid distributed cache (Layer 3)

LMCache's peer-to-peer KV-cache sharing model maps naturally onto Momagrid's
distributed node topology. A Momagrid node that has generated a verified concept
section can serve it to other nodes as a cache export. This is a post-Phase-1
concern but the architecture (export/import portability) is designed to accommodate
it without changes.

---

## 12. What Not to Build

**A new blob storage backend.** `dd-cache` already exists and is already a
dependency. `DiskCache` is SQLite-backed, zero extra deps, and handles
serialization. Do not write a new `SQLiteContentStore` from scratch — wrap
`BaseCacheAdapter` instead.

**Semantic similarity matching.** At 0.90 cosine threshold, the false-positive
rate is ~3% — roughly 1 in 33 cache lookups returns the wrong answer. For
correctness-critical content this is not a trade-off, it is a bug. Exact-match by
content key is the only acceptable strategy for Layer 2. If semantic caching is
ever added, confine it to Layer 1 (ephemeral, TTL-controlled) and never to
verified content.

**Remote cache (L3) in Phase 1.** `export`/`import` covers team sharing without
a live infrastructure dependency. Add a remote backend (S3, Redis) only when
profiling shows SQLite is a bottleneck.

**In-process L1 dict in Phase 1.** SQLite reads are fast enough for Phase 1;
add an in-process LRU only when profiling shows the overhead matters.

**Cache-aware LLM routing.** Routing to cheaper models when a partial hit exists
is a valid future optimisation but out of scope here.

---

## 13. Implementation Plan

### Phase 1 — Content cache, CLI, executor integration
- [x] `spl3/cache/types.py` — `CacheEntry`, `CacheStats`, `PROVENANCE_TIERS`, `provenance_rank()`
- [x] `spl3/cache/keys.py` — `content_key()`, `content_hash()`; imports `make_key` from `dd_cache.utils`
- [x] `spl3/cache/meta.py` — `MetaStore`: SQLite metadata index with `content_meta` + `dep_graph` tables; recursive CTE for cascading invalidation
- [x] `spl3/cache/content.py` — `ContentCache(store: BaseCacheAdapter, meta_path)`: get/put/get_or_put/promote/invalidate/dependents/stats/export/import_/clear*; `ttl=None` always passed internally
- [x] `spl3/cache/__init__.py` — exports `ContentCache`, `get_content_cache`, types, key helpers
- [x] `spl3/cache/cli.py` — `spl3 cache` subgroup: list, show, stats, clear, invalidate, export, import, promote; wired into `spl3/cli.py`
- [x] Default instantiation: `get_content_cache()` → `ContentCache(DiskCache(".spl/content_cache.db"), ".spl/content_meta.db")`
- [ ] Executor: check Layer 2 (`ContentCache.get`) before Layer 1 on `GENERATE`; compute `dep_hashes` from graph ancestors
- [x] stdlib: `cache_get` / `cache_put` registered as `@spl_tool` in `spl/stdlib.py`
- [x] `min_provenance` filter on `cache.get()` — serve only entries at or above a specified tier
- [x] Unit tests (38/38): CAS key computation, dep_graph cascading, provenance promotion, export/import round-trip, backend-swap (DiskCache ↔ InMemoryCache), TTL semantics (`ttl=None`/`ttl=0`/`ttl<0`)

### Phase 2 — Anthropic / OpenAI adapter-level prefix caching
- [ ] Anthropic adapter: `cache_control` on system + large context blocks
- [ ] OpenAI adapter: verify automatic prefix caching fires on long prompts
- [ ] Token-cost accounting: distinguish `cache_read_tokens` from `input_tokens` in SPL cost reporting
- [ ] Integration test: verify 90%+ cost reduction on warm Layer 1 runs

### Phase 3 — SPL language integration
- [ ] `CACHE BY` clause in lexer / parser / AST
- [ ] `UNLESS STALE` modifier
- [ ] Executor: auto-compute `@dep_hashes` from graph ancestors when `CACHE BY` is present
- [ ] Integration tests via `.spl` fixtures using the micro-textbook `build_micro_textbook` workflow
- [ ] Verify cold→warm run cost delta matches expected Layer 2 hit rate

### Phase 4 — Stack integration
- [ ] Wire `spl3 judge --promote` to `cache.promote()` (closes loop with spl3-judge.md)
- [ ] `spl3 cache stats` integrated into NDD leaderboard: "tokens saved via Layer 2" column
- [ ] Pre-warmed cache export bundled with micro-textbook deliverable
- [ ] Design doc for Layer 3 (Momagrid peer cache sharing)

---

## 14. Key Design Decisions (summary)

| Decision | Rationale |
|----------|-----------|
| `dd-cache.BaseCacheAdapter` as blob backend | dd-cache was built for the dd-* ecosystem including spl; reuse it rather than reinventing blob storage. Backend swap (DiskCache → RedisCache → MomagridCacheAdapter) is free. |
| Separate metadata index (SQLite) from blob store | Provenance, dep_graph, stale, hit_count need relational queries; dd-cache is a KV store, not a relational DB. Metadata is always local; blobs can be remote. |
| `make_key("spl3", "content", …)` for key namespacing | Prevents collision with Layer 1 prompt keys; both layers can safely share one DiskCache file if desired |
| `get_or_set(key, fn, ttl=None)` for cache-miss pattern | dd-cache provides this helper; maps directly to `CACHE BY` executor behavior without new abstractions |
| `promote()` updates metadata only, not blob | Trust badges are metadata; content is immutable. No blob re-serialization on promotion — fast and safe. |
| Layer 2 key = hash of inputs (CAS), not hash of content | Content can legitimately change; inputs changing is the correct invalidation signal |
| No TTL on Layer 2 | Verified content does not expire; time is not an invalidation criterion |
| `ttl=None` / `ttl=0` / `ttl<0` semantics | `None`=never expire; `0`=expire immediately (cache bypass, useful in tests/troubleshooting); negative=`ValueError`. `ContentCache` hides `ttl` entirely — callers cannot set it. |
| `dep_graph` table for cascading invalidation | SQL recursive CTE is fast; avoids parsing JSON dep_hashes for every invalidation query |
| Exact-match only for Layer 2 | 3% false-positive rate on semantic similarity is unacceptable for correctness-critical content |
| Provenance field on every entry | Cache and trust tier are the same concern — entries carry their verification status |
| `min_provenance` filter on `cache.get()` | Delivery layer controls which tier reaches learners; unverified entries are misses at the delivery boundary |
| Export/import over live remote store | Lower infrastructure dependency; sufficient for team sharing in Phase 1 |
| Server-side prefix caching at adapter layer | Orthogonal to content cache; reduces Layer 1 LLM call cost without touching cache design |
