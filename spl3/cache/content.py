from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from typing import Callable, Optional

from dd_cache import BaseCacheAdapter, DiskCache
from dd_cache.utils import serialize, deserialize

from .keys import content_key, content_hash as _content_hash
from .meta import MetaStore
from .types import CacheEntry, CacheStats, provenance_rank


class ContentCache:
    """Layer 2 content cache: verified section storage with provenance tracking.

    Wraps a dd-cache BaseCacheAdapter (blob store) and a MetaStore (SQLite
    metadata index).  TTL is never exposed to callers — entries are write-once
    immutable and invalidated by input change (CAS), not by time.
    """

    def __init__(
        self,
        store: BaseCacheAdapter,
        meta_path: str = ".spl/content_meta.db",
    ) -> None:
        self._store = store
        self._meta = MetaStore(meta_path)

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get(
        self,
        concept: str,
        params: dict,
        rubric_version: str,
        dep_hashes: dict[str, str],
        min_provenance: str = "machine_generated",
    ) -> Optional[CacheEntry]:
        """Return a cached entry or None on miss / provenance below threshold."""
        key = content_key(concept, params, rubric_version, dep_hashes)
        meta = self._meta.get_meta(key)
        if meta is None:
            return None
        if meta["stale"]:
            return None
        if provenance_rank(meta["provenance"]) < provenance_rank(min_provenance):
            return None

        raw = self._store.get(key)
        if raw is None:
            return None

        content = deserialize(raw) if isinstance(raw, bytes) else raw
        self._meta.increment_hit(key)

        return CacheEntry(
            key=key,
            concept=meta["concept"],
            content=content,
            content_hash=meta["content_hash"],
            provenance=meta["provenance"],
            rubric_version=meta["rubric_ver"],
            dep_hashes=json.loads(meta["dep_hashes"]),
            params=json.loads(meta["params"]),
            adapter=meta["adapter"] or "",
            model=meta["model"] or "",
            token_cost=meta["token_cost"] or 0,
            created_at=meta["created_at"],
            hit_count=meta["hit_count"] + 1,
            stale=bool(meta["stale"]),
            verdict=json.loads(meta["verdict"]) if meta["verdict"] else None,
            verifier=meta["verifier"] or "",
        )

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def put(
        self,
        concept: str,
        content: str,
        provenance: str,
        params: dict,
        rubric_version: str,
        dep_hashes: dict[str, str],
        adapter: str = "",
        model: str = "",
        token_cost: int = 0,
        verifier: str = "",
    ) -> CacheEntry:
        """Store a generated+verified section. Always ttl=None (write-once immutable).

        `verifier` records the engine-of-record that checked the content
        ("sympy", "sage", ...) — see docs/DEV/sage_lean_integration_plan.md §A.2.
        """
        key = content_key(concept, params, rubric_version, dep_hashes)
        chash = _content_hash(content)

        # Store blob — ttl=None enforced; callers cannot override
        self._store.set(key, serialize(content), ttl=None)

        self._meta.put(
            key=key,
            concept=concept,
            content_hash=chash,
            provenance=provenance,
            rubric_version=rubric_version,
            dep_hashes=dep_hashes,
            params=params,
            adapter=adapter,
            model=model,
            token_cost=token_cost,
            verifier=verifier,
        )

        from datetime import datetime, timezone
        return CacheEntry(
            key=key,
            concept=concept,
            content=content,
            content_hash=chash,
            provenance=provenance,
            rubric_version=rubric_version,
            dep_hashes=dep_hashes,
            params=params,
            adapter=adapter,
            model=model,
            token_cost=token_cost,
            created_at=datetime.now(timezone.utc).isoformat(),
            hit_count=0,
            stale=False,
            verdict=None,
            verifier=verifier,
        )

    def get_or_put(
        self,
        concept: str,
        params: dict,
        rubric_version: str,
        dep_hashes: dict[str, str],
        fn: Callable[[], tuple[str, str, int]],
        min_provenance: str = "machine_generated",
    ) -> CacheEntry:
        """Return cached entry or call fn() → (content, provenance, token_cost) on miss."""
        entry = self.get(concept, params, rubric_version, dep_hashes, min_provenance)
        if entry is not None:
            return entry
        content, provenance, token_cost = fn()
        return self.put(
            concept=concept,
            content=content,
            provenance=provenance,
            params=params,
            rubric_version=rubric_version,
            dep_hashes=dep_hashes,
            token_cost=token_cost,
        )

    # ------------------------------------------------------------------ #
    # Provenance promotion                                                 #
    # ------------------------------------------------------------------ #

    def promote(
        self,
        key: str,
        new_provenance: str,
        verdict: Optional[dict] = None,
    ) -> None:
        """Advance entry to a higher provenance tier. verdict stored for auditability."""
        self._meta.promote(key, new_provenance, verdict)

    # ------------------------------------------------------------------ #
    # Invalidation                                                         #
    # ------------------------------------------------------------------ #

    def invalidate(self, concept: str, cascade: bool = True) -> list[str]:
        """Mark concept stale. cascade=True propagates via dep_graph recursive CTE."""
        return self._meta.invalidate(concept, cascade)

    def dependents(self, concept: str) -> list[str]:
        """All concepts whose dep_hashes reference this concept."""
        return self._meta.dependents(concept)

    # ------------------------------------------------------------------ #
    # Stats / inspection                                                   #
    # ------------------------------------------------------------------ #

    def stats(self) -> CacheStats:
        return self._meta.stats()

    # ------------------------------------------------------------------ #
    # Clear                                                                #
    # ------------------------------------------------------------------ #

    def clear_stale(self) -> int:
        """Delete all stale-flagged entries from both store and metadata."""
        stale_keys = [
            r["key"]
            for r in self._meta._conn.execute(
                "SELECT key FROM content_meta WHERE stale = 1"
            ).fetchall()
        ]
        for key in stale_keys:
            self._store.delete(key)
        return self._meta.delete_stale()

    def clear_by_provenance(self, provenance: str) -> int:
        keys = [
            r["key"]
            for r in self._meta._conn.execute(
                "SELECT key FROM content_meta WHERE provenance = ?", (provenance,)
            ).fetchall()
        ]
        for key in keys:
            self._store.delete(key)
        return self._meta.delete_by_provenance(provenance)

    def clear_all(self) -> int:
        self._store.clear()
        return self._meta.clear_all()

    # ------------------------------------------------------------------ #
    # Export / Import                                                      #
    # ------------------------------------------------------------------ #

    def export(self, path: Path) -> None:
        """Export all entries (metadata + blobs) to a .tar.gz archive."""
        rows = self._meta.export_rows()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            meta_file = tmp_path / "meta.json"
            meta_file.write_text(json.dumps(rows, indent=2), encoding="utf-8")

            blobs_dir = tmp_path / "blobs"
            blobs_dir.mkdir()
            for row in rows:
                raw = self._store.get(row["key"])
                if raw is not None:
                    (blobs_dir / row["key"].replace(":", "_")).write_bytes(
                        raw if isinstance(raw, bytes) else serialize(raw)
                    )

            with tarfile.open(path, "w:gz") as tar:
                tar.add(meta_file, arcname="meta.json")
                tar.add(blobs_dir, arcname="blobs")

    def import_(self, path: Path, merge: bool = True) -> int:
        """Import entries from a .tar.gz archive. Returns count of entries written."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(tmp_path)

            rows = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
            blobs_dir = tmp_path / "blobs"

            imported = self._meta.import_rows(rows, merge=merge)
            for row in rows:
                blob_file = blobs_dir / row["key"].replace(":", "_")
                if blob_file.exists():
                    raw = blob_file.read_bytes()
                    self._store.set(row["key"], raw, ttl=None)

        return imported

    def close(self) -> None:
        self._meta.close()


def get_content_cache(
    store_path: str = ".spl/content_cache.db",
    meta_path: str = ".spl/content_meta.db",
) -> ContentCache:
    """Convenience factory: DiskCache-backed ContentCache with default paths."""
    return ContentCache(
        store=DiskCache(path=store_path),
        meta_path=meta_path,
    )
