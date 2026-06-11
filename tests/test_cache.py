"""Unit tests for spl3/cache.

Covers:
- CAS key computation (content_key / content_hash)
- Badge-set trust model (B-4): two orthogonal axes, no cross-axis ordering
- MetaStore: put, get, promote (badge add), invalidate (cascade), dependents
- Pre-B-4 DB migration: legacy single-ordinal `provenance` → badge set
- ContentCache: get/put round-trip, min_badge filter, statement round-trip,
  ttl=0 bypass, legacy provenance= compatibility
- Export/import round-trip (incl. pre-B-4 archives)
- Backend-swap: DiskCache → InMemoryCache same behaviour
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from dd_cache import DiskCache, InMemoryCache

from spl3.cache.keys import content_key, content_hash
from spl3.cache.meta import MetaStore
from spl3.cache.content import ContentCache
from spl3.cache.types import (
    ALL_BADGES,
    CLAIM_BADGES,
    EXPOSITION_BADGES,
    CacheEntry,
    badge_axis,
    badge_rank,
    badges_from_provenance,
    is_canonical,
    normalize_badges,
    satisfies,
)


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def mem_cache():
    return InMemoryCache()


@pytest.fixture
def meta_store(tmp_dir):
    return MetaStore(meta_path=str(tmp_dir / "meta.db"))


@pytest.fixture
def disk_content_cache(tmp_dir):
    return ContentCache(
        store=DiskCache(path=str(tmp_dir / "content.db")),
        meta_path=str(tmp_dir / "meta.db"),
    )


@pytest.fixture
def mem_content_cache(tmp_dir):
    return ContentCache(
        store=InMemoryCache(),
        meta_path=str(tmp_dir / "meta_mem.db"),
    )


# ------------------------------------------------------------------ #
# CAS key computation                                                  #
# ------------------------------------------------------------------ #

class TestContentKey:
    def test_same_inputs_same_key(self):
        k1 = content_key("span", {"domain": "linalg"}, "v1", {"vector": "abc"})
        k2 = content_key("span", {"domain": "linalg"}, "v1", {"vector": "abc"})
        assert k1 == k2

    def test_different_concept_different_key(self):
        k1 = content_key("span",   {"domain": "linalg"}, "v1", {})
        k2 = content_key("kernel", {"domain": "linalg"}, "v1", {})
        assert k1 != k2

    def test_different_params_different_key(self):
        k1 = content_key("span", {"domain": "linalg"},  "v1", {})
        k2 = content_key("span", {"domain": "algebra"}, "v1", {})
        assert k1 != k2

    def test_different_rubric_different_key(self):
        k1 = content_key("span", {}, "v1", {})
        k2 = content_key("span", {}, "v2", {})
        assert k1 != k2

    def test_different_dep_hash_different_key(self):
        k1 = content_key("span", {}, "v1", {"vector": "aaa"})
        k2 = content_key("span", {}, "v1", {"vector": "bbb"})
        assert k1 != k2

    def test_key_has_spl3_prefix(self):
        k = content_key("span", {}, "v1", {})
        assert k.startswith("spl3:content:")

    def test_content_hash_length(self):
        h = content_hash("hello world")
        assert len(h) == 16

    def test_content_hash_deterministic(self):
        assert content_hash("foo") == content_hash("foo")

    def test_content_hash_sensitive(self):
        assert content_hash("foo") != content_hash("foo ")


# ------------------------------------------------------------------ #
# Badge-set trust model (B-4)                                          #
# ------------------------------------------------------------------ #

class TestBadges:
    def test_axes_partition_badges(self):
        assert set(ALL_BADGES) == set(CLAIM_BADGES) | set(EXPOSITION_BADGES)
        for b in CLAIM_BADGES:
            assert badge_axis(b) == "claim"
        for b in EXPOSITION_BADGES:
            assert badge_axis(b) == "exposition"
        assert badge_axis("machine_generated") is None

    def test_ranks_strict_within_axis(self):
        assert badge_rank("machine_proved") > badge_rank("machine_verified")
        assert badge_rank("human_verified") > badge_rank("ai_reviewed")
        assert badge_rank("bogus") == -1

    def test_normalize_dedupes_and_orders(self):
        assert normalize_badges(["ai_reviewed", "machine_verified", "ai_reviewed"]) == [
            "machine_verified", "ai_reviewed",
        ]

    def test_normalize_rejects_unknown(self):
        with pytest.raises(ValueError, match="Unknown badge"):
            normalize_badges(["machine_generated"])

    def test_satisfies_within_axis(self):
        assert satisfies(["machine_verified"], "machine_verified")
        assert satisfies(["machine_proved"], "machine_verified")
        assert not satisfies(["machine_verified"], "machine_proved")

    def test_satisfies_never_crosses_axes(self):
        # The pre-B-4 ordinal got this wrong: ai_reviewed outranked
        # machine_verified despite attesting a different thing.
        assert not satisfies(["ai_reviewed"], "machine_verified")
        assert not satisfies(["human_verified"], "machine_verified")
        assert not satisfies(["machine_proved"], "ai_reviewed")

    def test_satisfies_rejects_unknown_threshold(self):
        with pytest.raises(ValueError, match="Unknown badge"):
            satisfies(["machine_verified"], "machine_generated")

    def test_canonical_requires_top_of_both_axes(self):
        assert is_canonical(["machine_proved", "human_verified"])
        assert is_canonical(ALL_BADGES)
        assert not is_canonical(["machine_proved"])
        assert not is_canonical(["machine_verified", "human_verified"])
        assert not is_canonical([])

    def test_legacy_provenance_mapping(self):
        assert badges_from_provenance("machine_generated") == []
        assert badges_from_provenance("") == []
        assert badges_from_provenance("ai_reviewed") == ["ai_reviewed"]
        with pytest.raises(ValueError):
            badges_from_provenance("bogus")


# ------------------------------------------------------------------ #
# MetaStore                                                            #
# ------------------------------------------------------------------ #

class TestMetaStore:
    def _put_entry(self, meta: MetaStore, concept="span", badges=()):
        key = content_key(concept, {}, "v1", {})
        meta.put(
            key=key,
            concept=concept,
            content_hash="abc123",
            badges=list(badges),
            rubric_version="v1",
            dep_hashes={},
            params={},
            adapter="echo",
            model="test",
            token_cost=10,
        )
        return key

    def test_put_and_get(self, meta_store):
        key = self._put_entry(meta_store)
        row = meta_store.get_meta(key)
        assert row is not None
        assert row["concept"] == "span"
        assert json.loads(row["badges"]) == []
        assert row["stale"] == 0

    def test_increment_hit(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.increment_hit(key)
        meta_store.increment_hit(key)
        row = meta_store.get_meta(key)
        assert row["hit_count"] == 2

    def test_promote_adds_badge(self, meta_store):
        key = self._put_entry(meta_store)
        new = meta_store.promote(key, "machine_verified")
        assert new == ["machine_verified"]
        assert json.loads(meta_store.get_meta(key)["badges"]) == ["machine_verified"]

    def test_promote_accumulates_across_axes(self, meta_store):
        key = self._put_entry(meta_store, badges=["machine_verified"])
        meta_store.promote(key, "ai_reviewed")
        new = meta_store.promote(key, "machine_proved")
        assert new == ["machine_verified", "machine_proved", "ai_reviewed"]

    def test_promote_with_verdict(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.promote(key, "ai_reviewed", verdict={"score": 9, "pass": True})
        row = meta_store.get_meta(key)
        assert json.loads(row["badges"]) == ["ai_reviewed"]
        assert json.loads(row["verdict"])["score"] == 9

    def test_promote_without_verdict_keeps_existing(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.promote(key, "ai_reviewed", verdict={"score": 9})
        meta_store.promote(key, "machine_verified")
        assert json.loads(meta_store.get_meta(key)["verdict"])["score"] == 9

    def test_promote_rejects_held_badge(self, meta_store):
        key = self._put_entry(meta_store, badges=["machine_verified"])
        with pytest.raises(ValueError, match="already holds"):
            meta_store.promote(key, "machine_verified")

    def test_promote_rejects_unknown_badge(self, meta_store):
        key = self._put_entry(meta_store)
        with pytest.raises(ValueError, match="Unknown badge"):
            meta_store.promote(key, "machine_generated")

    def test_promote_missing_key(self, meta_store):
        with pytest.raises(KeyError):
            meta_store.promote("nope", "ai_reviewed")

    def test_invalidate_single(self, meta_store):
        key = self._put_entry(meta_store)
        affected = meta_store.invalidate("span", cascade=False)
        assert "span" in affected
        row = meta_store.get_meta(key)
        assert row["stale"] == 1

    def test_cascade_invalidation(self, meta_store):
        # Build: vector → span → eigenpair
        k_vec = content_key("vector", {}, "v1", {})
        meta_store.put(k_vec, "vector", "h1", [], "v1",
                       {}, {}, "echo", "test", 5)

        k_span = content_key("span", {}, "v1", {"vector": "h1"})
        meta_store.put(k_span, "span", "h2", [], "v1",
                       {"vector": "h1"}, {}, "echo", "test", 5)

        k_eig = content_key("eigenpair", {}, "v1", {"span": "h2"})
        meta_store.put(k_eig, "eigenpair", "h3", [], "v1",
                       {"span": "h2"}, {}, "echo", "test", 5)

        # Invalidate vector with cascade
        affected = meta_store.invalidate("vector", cascade=True)
        assert set(affected) == {"vector", "span", "eigenpair"}
        for key in (k_vec, k_span, k_eig):
            assert meta_store.get_meta(key)["stale"] == 1

    def test_dependents(self, meta_store):
        k_v = content_key("vector", {}, "v1", {})
        meta_store.put(k_v, "vector", "h1", [], "v1",
                       {}, {}, "echo", "test", 5)
        k_s = content_key("span", {}, "v1", {"vector": "h1"})
        meta_store.put(k_s, "span", "h2", [], "v1",
                       {"vector": "h1"}, {}, "echo", "test", 5)
        assert "span" in meta_store.dependents("vector")

    def test_stats(self, meta_store):
        self._put_entry(meta_store, "span")
        self._put_entry(meta_store, "kernel", badges=["machine_verified"])
        self._put_entry(meta_store, "eigen",
                        badges=["machine_proved", "human_verified"])
        s = meta_store.stats()
        assert s.total_entries == 3
        assert s.unbadged == 1
        assert s.by_badge.get("machine_verified") == 1
        assert s.by_badge.get("machine_proved") == 1
        assert s.by_badge.get("human_verified") == 1
        assert s.canonical == 1


# ------------------------------------------------------------------ #
# Pre-B-4 migration: legacy single-ordinal `provenance` → badge set    #
# ------------------------------------------------------------------ #

class TestLegacyMigration:
    _OLD_SCHEMA = """
    CREATE TABLE content_meta (
        key          TEXT PRIMARY KEY,
        concept      TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        provenance   TEXT NOT NULL DEFAULT 'machine_generated',
        rubric_ver   TEXT NOT NULL,
        dep_hashes   TEXT NOT NULL,
        params       TEXT NOT NULL,
        adapter      TEXT,
        model        TEXT,
        token_cost   INTEGER DEFAULT 0,
        hit_count    INTEGER DEFAULT 0,
        stale        INTEGER DEFAULT 0,
        verdict      TEXT,
        created_at   TEXT NOT NULL,
        updated_at   TEXT NOT NULL
    );
    CREATE TABLE dep_graph (
        dependent   TEXT NOT NULL,
        dependency  TEXT NOT NULL,
        PRIMARY KEY (dependent, dependency)
    );
    """

    def _make_old_db(self, path, tiers):
        conn = sqlite3.connect(path)
        conn.executescript(self._OLD_SCHEMA)
        for i, tier in enumerate(tiers):
            conn.execute(
                "INSERT INTO content_meta (key, concept, content_hash, provenance,"
                " rubric_ver, dep_hashes, params, created_at, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (f"k{i}", f"c{i}", "h", tier, "v1", "{}", "{}", "t0", "t0"),
            )
        conn.commit()
        conn.close()

    def test_migration_backfills_badges(self, tmp_dir):
        db = str(tmp_dir / "old_meta.db")
        self._make_old_db(db, [
            "machine_generated", "machine_verified", "ai_reviewed", "human_verified",
        ])
        meta = MetaStore(meta_path=db)
        expected = [[], ["machine_verified"], ["ai_reviewed"], ["human_verified"]]
        for i, badges in enumerate(expected):
            row = meta.get_meta(f"k{i}")
            assert json.loads(row["badges"]) == badges
            assert row["verifier"] == ""
            assert row["statement"] == ""

    def test_migration_is_idempotent(self, tmp_dir):
        db = str(tmp_dir / "old_meta.db")
        self._make_old_db(db, ["ai_reviewed"])
        MetaStore(meta_path=db).close()
        meta = MetaStore(meta_path=db)  # second open: columns already exist
        assert json.loads(meta.get_meta("k0")["badges"]) == ["ai_reviewed"]


# ------------------------------------------------------------------ #
# ContentCache — DiskCache backend                                     #
# ------------------------------------------------------------------ #

class TestContentCache:
    def _put(self, cache: ContentCache, concept="span", badges=(), **kw):
        return cache.put(
            concept=concept,
            content=f"This is the section for {concept}.",
            badges=list(badges),
            params={"domain": "linalg"},
            rubric_version="v1",
            dep_hashes={},
            adapter="echo",
            model="test",
            token_cost=20,
            **kw,
        )

    def test_put_returns_entry(self, disk_content_cache):
        entry = self._put(disk_content_cache)
        assert isinstance(entry, CacheEntry)
        assert entry.concept == "span"
        assert entry.content == "This is the section for span."
        assert entry.badges == []

    def test_get_hit(self, disk_content_cache):
        self._put(disk_content_cache)
        entry = disk_content_cache.get("span", {"domain": "linalg"}, "v1", {})
        assert entry is not None
        assert "span" in entry.content

    def test_get_miss_on_different_params(self, disk_content_cache):
        self._put(disk_content_cache)
        entry = disk_content_cache.get("span", {"domain": "algebra"}, "v1", {})
        assert entry is None

    def test_get_miss_on_stale(self, disk_content_cache):
        self._put(disk_content_cache)
        disk_content_cache.invalidate("span", cascade=False)
        entry = disk_content_cache.get("span", {"domain": "linalg"}, "v1", {})
        assert entry is None

    def test_min_badge_filter(self, disk_content_cache):
        self._put(disk_content_cache)
        entry = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_badge="machine_verified",
        )
        assert entry is None

    def test_min_badge_passes_when_met(self, disk_content_cache):
        entry = self._put(disk_content_cache, badges=["machine_verified"])
        result = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_badge="machine_verified",
        )
        assert result is not None
        assert result.key == entry.key

    def test_min_badge_satisfied_by_higher_on_axis(self, disk_content_cache):
        self._put(disk_content_cache, badges=["machine_proved"])
        result = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_badge="machine_verified",
        )
        assert result is not None

    def test_min_badge_not_satisfied_across_axes(self, disk_content_cache):
        self._put(disk_content_cache, badges=["ai_reviewed"])
        result = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_badge="machine_verified",
        )
        assert result is None

    def test_legacy_min_badge_machine_generated_is_no_filter(self, disk_content_cache):
        self._put(disk_content_cache)
        result = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_badge="machine_generated",
        )
        assert result is not None

    def test_legacy_provenance_kwarg(self, disk_content_cache):
        entry = disk_content_cache.put(
            "basis", "text", provenance="machine_verified",
            params={}, rubric_version="v1", dep_hashes={},
        )
        assert entry.badges == ["machine_verified"]

    def test_legacy_provenance_positional(self, disk_content_cache):
        # pre-B-4 callers passed the ordinal tier in the third slot
        entry = disk_content_cache.put("basis", "text", "machine_generated")
        assert entry.badges == []

    def test_statement_and_verifier_round_trip(self, disk_content_cache):
        stmt = "∀ n m : Nat, n + m = m + n"
        self._put(disk_content_cache, badges=["machine_proved"],
                  verifier="lean", statement=stmt)
        hit = disk_content_cache.get("span", {"domain": "linalg"}, "v1", {})
        assert hit.verifier == "lean"
        assert hit.statement == stmt
        assert hit.badges == ["machine_proved"]

    def test_promote(self, disk_content_cache):
        entry = self._put(disk_content_cache)
        disk_content_cache.promote(entry.key, "machine_verified")
        meta = disk_content_cache._meta.get_meta(entry.key)
        assert json.loads(meta["badges"]) == ["machine_verified"]

    def test_canonical_property(self, disk_content_cache):
        entry = self._put(disk_content_cache,
                          badges=["machine_proved", "human_verified"])
        assert entry.canonical
        assert not self._put(disk_content_cache, "other").canonical

    def test_invalidate_cascade(self, disk_content_cache):
        disk_content_cache.put(
            "vector", "vector content", [],
            {}, "v1", {}, token_cost=5,
        )
        disk_content_cache.put(
            "span", "span content", [],
            {}, "v1", {"vector": "h1"}, token_cost=5,
        )
        affected = disk_content_cache.invalidate("vector", cascade=True)
        assert "vector" in affected
        assert "span" in affected

    def test_clear_stale(self, disk_content_cache):
        self._put(disk_content_cache)
        disk_content_cache.invalidate("span", cascade=False)
        n = disk_content_cache.clear_stale()
        assert n == 1
        assert disk_content_cache.stats().total_entries == 0

    def test_clear_by_badge(self, disk_content_cache):
        self._put(disk_content_cache, "span")
        self._put(disk_content_cache, "kernel", badges=["machine_verified"])
        n = disk_content_cache.clear_by_badge("machine_verified")
        assert n == 1
        assert disk_content_cache.stats().total_entries == 1

    def test_clear_unbadged(self, disk_content_cache):
        self._put(disk_content_cache, "span")
        self._put(disk_content_cache, "kernel", badges=["machine_verified"])
        n = disk_content_cache.clear_by_badge("unbadged")
        assert n == 1
        s = disk_content_cache.stats()
        assert s.total_entries == 1
        assert s.unbadged == 0


# ------------------------------------------------------------------ #
# ttl=0 bypass (store-level)                                           #
# ------------------------------------------------------------------ #

class TestTTLSemantics:
    def test_ttl_none_persists(self, mem_cache):
        mem_cache.set("k", "v", ttl=None)
        assert mem_cache.get("k") == "v"

    def test_ttl_zero_immediate_expiry(self, mem_cache):
        """ttl=0 means expire immediately — get() returns None after set()."""
        mem_cache.set("k", "v", ttl=0)
        assert mem_cache.get("k") is None

    def test_ttl_negative_immediate_expiry(self, mem_cache):
        """dd_cache treats negative TTL as immediate expiry (no exception raised)."""
        mem_cache.set("k", "v", ttl=-1)
        assert mem_cache.get("k") is None


# ------------------------------------------------------------------ #
# Backend swap: DiskCache ↔ InMemoryCache same behaviour              #
# ------------------------------------------------------------------ #

class TestBackendSwap:
    def _round_trip(self, cache: ContentCache):
        entry = cache.put(
            concept="basis",
            content="A basis is a set of linearly independent vectors.",
            badges=[],
            params={},
            rubric_version="v1",
            dep_hashes={},
            token_cost=15,
        )
        hit = cache.get("basis", {}, "v1", {})
        assert hit is not None
        assert hit.content == entry.content
        assert hit.key == entry.key

    def test_disk_cache_round_trip(self, disk_content_cache):
        self._round_trip(disk_content_cache)

    def test_memory_cache_round_trip(self, mem_content_cache):
        self._round_trip(mem_content_cache)


# ------------------------------------------------------------------ #
# Export / Import round-trip                                           #
# ------------------------------------------------------------------ #

class TestExportImport:
    def test_export_import_roundtrip(self, tmp_dir, disk_content_cache):
        disk_content_cache.put(
            "span", "Span section text.", [],
            {"domain": "linalg"}, "v1", {}, token_cost=30,
        )
        disk_content_cache.put(
            "kernel", "Kernel section text.", ["machine_verified"],
            {"domain": "linalg"}, "v1", {}, token_cost=40,
        )

        archive = tmp_dir / "cache_export.tar.gz"
        disk_content_cache.export(archive)
        assert archive.exists()

        # Import into a fresh cache
        fresh = ContentCache(
            store=DiskCache(path=str(tmp_dir / "fresh_blobs.db")),
            meta_path=str(tmp_dir / "fresh_meta.db"),
        )
        n = fresh.import_(archive, merge=True)
        assert n == 2

        hit = fresh.get("span", {"domain": "linalg"}, "v1", {})
        assert hit is not None
        assert "Span" in hit.content
        proved = fresh.get("kernel", {"domain": "linalg"}, "v1", {},
                           min_badge="machine_verified")
        assert proved is not None

    def test_import_legacy_rows(self, meta_store):
        # pre-B-4 export rows carry `provenance`, no `badges`
        meta_store.import_rows([{
            "key": "legacy", "concept": "span", "content_hash": "h",
            "provenance": "ai_reviewed", "rubric_ver": "v1",
            "dep_hashes": "{}", "params": "{}", "adapter": None, "model": None,
            "token_cost": 0, "hit_count": 0, "stale": 0, "verdict": None,
            "created_at": "t0", "updated_at": "t0",
        }])
        assert json.loads(meta_store.get_meta("legacy")["badges"]) == ["ai_reviewed"]

    def test_import_merge_skips_conflicts(self, tmp_dir, disk_content_cache):
        disk_content_cache.put("span", "v1 text.", [], {}, "v1", {})
        archive = tmp_dir / "export.tar.gz"
        disk_content_cache.export(archive)

        # Import same data twice with merge=True — should skip on second pass
        n1 = disk_content_cache.import_(archive, merge=True)
        n2 = disk_content_cache.import_(archive, merge=True)
        assert n2 == 0  # all skipped
