"""Unit tests for spl3/cache — Phase 1.

Covers:
- CAS key computation (content_key / content_hash)
- MetaStore: put, get, promote, invalidate (cascade), dependents
- ContentCache: get/put round-trip, min_provenance filter, ttl=0 bypass
- Provenance promotion chain
- Export/import round-trip
- Backend-swap: DiskCache → InMemoryCache same behaviour
"""

from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path

import pytest

from dd_cache import DiskCache, InMemoryCache

from spl3.cache.keys import content_key, content_hash
from spl3.cache.meta import MetaStore
from spl3.cache.content import ContentCache
from spl3.cache.types import PROVENANCE_TIERS, provenance_rank, CacheEntry


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def disk_cache(tmp_dir):
    return DiskCache(path=str(tmp_dir / "blobs.db"))


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
# Provenance helpers                                                   #
# ------------------------------------------------------------------ #

class TestProvenance:
    def test_ranks_ordered(self):
        ranks = [provenance_rank(t) for t in PROVENANCE_TIERS]
        assert ranks == sorted(ranks)

    def test_unknown_tier_minus_one(self):
        assert provenance_rank("bogus") == -1


# ------------------------------------------------------------------ #
# MetaStore                                                            #
# ------------------------------------------------------------------ #

class TestMetaStore:
    def _put_entry(self, meta: MetaStore, concept="span", provenance="machine_generated"):
        key = content_key(concept, {}, "v1", {})
        meta.put(
            key=key,
            concept=concept,
            content_hash="abc123",
            provenance=provenance,
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
        assert row["provenance"] == "machine_generated"
        assert row["stale"] == 0

    def test_increment_hit(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.increment_hit(key)
        meta_store.increment_hit(key)
        row = meta_store.get_meta(key)
        assert row["hit_count"] == 2

    def test_promote_advances_tier(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.promote(key, "machine_verified")
        row = meta_store.get_meta(key)
        assert row["provenance"] == "machine_verified"

    def test_promote_with_verdict(self, meta_store):
        key = self._put_entry(meta_store)
        meta_store.promote(key, "ai_reviewed", verdict={"score": 9, "pass": True})
        row = meta_store.get_meta(key)
        assert row["provenance"] == "ai_reviewed"
        assert json.loads(row["verdict"])["score"] == 9

    def test_promote_rejects_downgrade(self, meta_store):
        key = self._put_entry(meta_store, provenance="machine_verified")
        with pytest.raises(ValueError, match="higher"):
            meta_store.promote(key, "machine_generated")

    def test_promote_rejects_same_tier(self, meta_store):
        key = self._put_entry(meta_store, provenance="machine_verified")
        with pytest.raises(ValueError):
            meta_store.promote(key, "machine_verified")

    def test_invalidate_single(self, meta_store):
        key = self._put_entry(meta_store)
        affected = meta_store.invalidate("span", cascade=False)
        assert "span" in affected
        row = meta_store.get_meta(key)
        assert row["stale"] == 1

    def test_cascade_invalidation(self, meta_store):
        # Build: vector → span → eigenpair
        k_vec = content_key("vector", {}, "v1", {})
        meta_store.put(k_vec, "vector", "h1", "machine_generated", "v1",
                       {}, {}, "echo", "test", 5)

        k_span = content_key("span", {}, "v1", {"vector": "h1"})
        meta_store.put(k_span, "span", "h2", "machine_generated", "v1",
                       {"vector": "h1"}, {}, "echo", "test", 5)

        k_eig = content_key("eigenpair", {}, "v1", {"span": "h2"})
        meta_store.put(k_eig, "eigenpair", "h3", "machine_generated", "v1",
                       {"span": "h2"}, {}, "echo", "test", 5)

        # Invalidate vector with cascade
        affected = meta_store.invalidate("vector", cascade=True)
        assert set(affected) == {"vector", "span", "eigenpair"}
        for key in (k_vec, k_span, k_eig):
            assert meta_store.get_meta(key)["stale"] == 1

    def test_dependents(self, meta_store):
        k_v = content_key("vector", {}, "v1", {})
        meta_store.put(k_v, "vector", "h1", "machine_generated", "v1",
                       {}, {}, "echo", "test", 5)
        k_s = content_key("span", {}, "v1", {"vector": "h1"})
        meta_store.put(k_s, "span", "h2", "machine_generated", "v1",
                       {"vector": "h1"}, {}, "echo", "test", 5)
        assert "span" in meta_store.dependents("vector")

    def test_stats(self, meta_store):
        self._put_entry(meta_store, "span", "machine_generated")
        self._put_entry(meta_store, "kernel", "machine_verified")
        s = meta_store.stats()
        assert s.total_entries == 2
        assert s.by_provenance.get("machine_generated") == 1
        assert s.by_provenance.get("machine_verified") == 1


# ------------------------------------------------------------------ #
# ContentCache — DiskCache backend                                     #
# ------------------------------------------------------------------ #

class TestContentCache:
    def _put(self, cache: ContentCache, concept="span", provenance="machine_generated"):
        return cache.put(
            concept=concept,
            content=f"This is the section for {concept}.",
            provenance=provenance,
            params={"domain": "linalg"},
            rubric_version="v1",
            dep_hashes={},
            adapter="echo",
            model="test",
            token_cost=20,
        )

    def test_put_returns_entry(self, disk_content_cache):
        entry = self._put(disk_content_cache)
        assert isinstance(entry, CacheEntry)
        assert entry.concept == "span"
        assert entry.content == "This is the section for span."

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

    def test_min_provenance_filter(self, disk_content_cache):
        self._put(disk_content_cache, provenance="machine_generated")
        entry = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_provenance="machine_verified",
        )
        assert entry is None

    def test_min_provenance_passes_when_met(self, disk_content_cache):
        entry = self._put(disk_content_cache, provenance="machine_verified")
        result = disk_content_cache.get(
            "span", {"domain": "linalg"}, "v1", {},
            min_provenance="machine_verified",
        )
        assert result is not None
        assert result.key == entry.key

    def test_promote(self, disk_content_cache):
        entry = self._put(disk_content_cache)
        disk_content_cache.promote(entry.key, "machine_verified")
        meta = disk_content_cache._meta.get_meta(entry.key)
        assert meta["provenance"] == "machine_verified"

    def test_invalidate_cascade(self, disk_content_cache):
        disk_content_cache.put(
            "vector", "vector content", "machine_generated",
            {}, "v1", {}, token_cost=5,
        )
        disk_content_cache.put(
            "span", "span content", "machine_generated",
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

    def test_clear_by_provenance(self, disk_content_cache):
        self._put(disk_content_cache, "span", "machine_generated")
        self._put(disk_content_cache, "kernel", "machine_verified")
        n = disk_content_cache.clear_by_provenance("machine_generated")
        assert n == 1
        s = disk_content_cache.stats()
        assert s.total_entries == 1


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
            provenance="machine_generated",
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
            "span", "Span section text.", "machine_generated",
            {"domain": "linalg"}, "v1", {}, token_cost=30,
        )
        disk_content_cache.put(
            "kernel", "Kernel section text.", "machine_verified",
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

    def test_import_merge_skips_conflicts(self, tmp_dir, disk_content_cache):
        disk_content_cache.put("span", "v1 text.", "machine_generated", {}, "v1", {})
        archive = tmp_dir / "export.tar.gz"
        disk_content_cache.export(archive)

        # Import same data twice with merge=True — should skip on second pass
        n1 = disk_content_cache.import_(archive, merge=True)
        n2 = disk_content_cache.import_(archive, merge=True)
        assert n2 == 0  # all skipped
