from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from typing import Callable, Optional, Union

from dd_cache import BaseCacheAdapter, DiskCache
from dd_cache.utils import serialize, deserialize

from .keys import content_key, content_hash as _content_hash
from .meta import MetaStore
from .types import (
    CacheEntry,
    CacheStats,
    badges_from_provenance,
    normalize_badges,
    satisfies,
)


class ContentCache:
    """Layer 2 content cache: verified section storage with trust badges.

    Wraps a dd-cache BaseCacheAdapter (blob store) and a MetaStore (SQLite
    metadata index).  TTL is never exposed to callers — entries are write-once
    immutable and invalidated by input change (CAS), not by time.

    Trust is a badge *set* on two orthogonal axes (B-4, see cache.types):
    claim badges (machine_verified → machine_proved) attest the mathematical
    content; exposition badges (ai_reviewed → human_verified) attest the
    prose. An empty set is the machine_generated baseline.
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
        min_badge: Optional[str] = None,
    ) -> Optional[CacheEntry]:
        """Return a cached entry or None on miss / badge below threshold.

        `min_badge` filters on the badge's own axis only: requiring
        'machine_verified' is satisfied by machine_verified or machine_proved,
        never by exposition badges (and vice versa). None or the legacy
        'machine_generated' means no filter.
        """
        key = content_key(concept, params, rubric_version, dep_hashes)
        meta = self._meta.get_meta(key)
        if meta is None:
            return None
        if meta["stale"]:
            return None
        badges = json.loads(meta["badges"])
        if min_badge and min_badge != "machine_generated":
            if not satisfies(badges, min_badge):
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
            badges=badges,
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
            statement=meta["statement"] or "",
        )

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def put(
        self,
        concept: str,
        content: str,
        badges: Union[list[str], str, None] = None,
        params: Optional[dict] = None,
        rubric_version: str = "v1",
        dep_hashes: Optional[dict[str, str]] = None,
        adapter: str = "",
        model: str = "",
        token_cost: int = 0,
        verifier: str = "",
        statement: str = "",
        provenance: Optional[str] = None,
    ) -> CacheEntry:
        """Store a generated+verified section. Always ttl=None (write-once immutable).

        `badges` is the trust badge set ([] / None = machine_generated
        baseline); a bare string — including the legacy `provenance=` kwarg
        and its 'machine_generated' value — is accepted and converted.
        `verifier` records the engine-of-record that checked the content
        ("sympy", "sage", "lean", ...) — see
        docs/DEV/sage_lean_integration_plan.md §A.2. `statement` carries the
        kernel-checked Lean proposition backing a machine_proved badge, so
        it can be rendered alongside the prose (§B.4).
        """
        if isinstance(badges, str):
            provenance = badges
            badges = None
        if badges is None:
            badges = badges_from_provenance(provenance or "machine_generated")
        else:
            badges = normalize_badges(badges)
        params = params or {}
        dep_hashes = dep_hashes or {}

        key = content_key(concept, params, rubric_version, dep_hashes)
        chash = _content_hash(content)

        # Store blob — ttl=None enforced; callers cannot override
        self._store.set(key, serialize(content), ttl=None)

        self._meta.put(
            key=key,
            concept=concept,
            content_hash=chash,
            badges=badges,
            rubric_version=rubric_version,
            dep_hashes=dep_hashes,
            params=params,
            adapter=adapter,
            model=model,
            token_cost=token_cost,
            verifier=verifier,
            statement=statement,
        )

        from datetime import datetime, timezone
        return CacheEntry(
            key=key,
            concept=concept,
            content=content,
            content_hash=chash,
            badges=badges,
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
            statement=statement,
        )

    def get_or_put(
        self,
        concept: str,
        params: dict,
        rubric_version: str,
        dep_hashes: dict[str, str],
        fn: Callable[[], tuple[str, Union[list[str], str], int]],
        min_badge: Optional[str] = None,
    ) -> CacheEntry:
        """Return cached entry or call fn() → (content, badges, token_cost) on miss."""
        entry = self.get(concept, params, rubric_version, dep_hashes, min_badge)
        if entry is not None:
            return entry
        content, badges, token_cost = fn()
        return self.put(
            concept=concept,
            content=content,
            badges=badges,
            params=params,
            rubric_version=rubric_version,
            dep_hashes=dep_hashes,
            token_cost=token_cost,
        )

    # ------------------------------------------------------------------ #
    # Badge promotion                                                      #
    # ------------------------------------------------------------------ #

    def promote(
        self,
        key: str,
        badge: str,
        verdict: Optional[dict] = None,
    ) -> list[str]:
        """Add a trust badge to an entry; returns the new badge set.

        verdict stored for auditability (latest promotion wins)."""
        return self._meta.promote(key, badge, verdict)

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

    def clear_by_badge(self, badge: str) -> int:
        """Delete entries holding a badge; 'unbadged' deletes the badge-less."""
        if badge == "unbadged":
            where, args = "badges = '[]'", ()
        else:
            where, args = "badges LIKE ?", (f'%"{badge}"%',)
        keys = [
            r["key"]
            for r in self._meta._conn.execute(
                f"SELECT key FROM content_meta WHERE {where}", args
            ).fetchall()
        ]
        for key in keys:
            self._store.delete(key)
        return self._meta.delete_by_badge(badge)

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
