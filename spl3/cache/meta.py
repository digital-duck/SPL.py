from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .types import CacheStats, provenance_rank


_SCHEMA = """
CREATE TABLE IF NOT EXISTS content_meta (
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

CREATE INDEX IF NOT EXISTS idx_concept    ON content_meta(concept);
CREATE INDEX IF NOT EXISTS idx_provenance ON content_meta(provenance);
CREATE INDEX IF NOT EXISTS idx_stale      ON content_meta(stale);

CREATE TABLE IF NOT EXISTS dep_graph (
    dependent   TEXT NOT NULL,
    dependency  TEXT NOT NULL,
    PRIMARY KEY (dependent, dependency)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetaStore:
    """SQLite metadata index for ContentCache.

    Stores provenance, dependency graph, hit counts, and token costs.
    Blob storage is delegated to dd-cache (BaseCacheAdapter).
    """

    def __init__(self, meta_path: str = ".spl/content_meta.db") -> None:
        os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(meta_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def put(
        self,
        key: str,
        concept: str,
        content_hash: str,
        provenance: str,
        rubric_version: str,
        dep_hashes: dict[str, str],
        params: dict,
        adapter: str,
        model: str,
        token_cost: int,
    ) -> None:
        now = _now()
        self._conn.execute(
            """INSERT INTO content_meta
               (key, concept, content_hash, provenance, rubric_ver,
                dep_hashes, params, adapter, model, token_cost,
                hit_count, stale, verdict, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,0,0,NULL,?,?)
               ON CONFLICT(key) DO UPDATE SET
                   content_hash = excluded.content_hash,
                   provenance   = excluded.provenance,
                   rubric_ver   = excluded.rubric_ver,
                   dep_hashes   = excluded.dep_hashes,
                   params       = excluded.params,
                   adapter      = excluded.adapter,
                   model        = excluded.model,
                   token_cost   = excluded.token_cost,
                   stale        = 0,
                   updated_at   = excluded.updated_at
            """,
            (
                key, concept, content_hash, provenance, rubric_version,
                json.dumps(dep_hashes, sort_keys=True),
                json.dumps(params, sort_keys=True),
                adapter, model, token_cost,
                now, now,
            ),
        )
        # Rebuild dep_graph entries for this concept
        self._conn.execute(
            "DELETE FROM dep_graph WHERE dependent = ?", (concept,)
        )
        for dep_concept in dep_hashes:
            self._conn.execute(
                "INSERT OR IGNORE INTO dep_graph (dependent, dependency) VALUES (?,?)",
                (concept, dep_concept),
            )
        self._conn.commit()

    def increment_hit(self, key: str) -> None:
        self._conn.execute(
            "UPDATE content_meta SET hit_count = hit_count + 1, updated_at = ? WHERE key = ?",
            (_now(), key),
        )
        self._conn.commit()

    def promote(
        self,
        key: str,
        new_provenance: str,
        verdict: Optional[dict] = None,
    ) -> None:
        """Advance entry to a higher provenance tier."""
        row = self._conn.execute(
            "SELECT provenance FROM content_meta WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            raise KeyError(f"No cache entry with key: {key}")
        current_rank = provenance_rank(row["provenance"])
        new_rank = provenance_rank(new_provenance)
        if new_rank <= current_rank:
            raise ValueError(
                f"Cannot promote from '{row['provenance']}' to '{new_provenance}': "
                "new tier must be higher."
            )
        self._conn.execute(
            "UPDATE content_meta SET provenance = ?, verdict = ?, updated_at = ? WHERE key = ?",
            (new_provenance, json.dumps(verdict) if verdict else None, _now(), key),
        )
        self._conn.commit()

    def invalidate(self, concept: str, cascade: bool = True) -> list[str]:
        """Mark concept (and optionally all dependents) as stale.

        Uses a recursive CTE to traverse dep_graph — no Python-side traversal.
        Returns list of affected concept names.
        """
        if cascade:
            rows = self._conn.execute(
                """
                WITH RECURSIVE affected(concept) AS (
                    SELECT ?
                    UNION
                    SELECT dg.dependent
                    FROM dep_graph dg
                    JOIN affected a ON dg.dependency = a.concept
                )
                SELECT concept FROM affected
                """,
                (concept,),
            ).fetchall()
            affected = [r["concept"] for r in rows]
        else:
            affected = [concept]

        if affected:
            placeholders = ",".join("?" * len(affected))
            self._conn.execute(
                f"UPDATE content_meta SET stale = 1, updated_at = ? "
                f"WHERE concept IN ({placeholders})",
                [_now()] + affected,
            )
            self._conn.commit()
        return affected

    def dependents(self, concept: str) -> list[str]:
        """Return all concepts whose dep_hashes reference this concept."""
        rows = self._conn.execute(
            "SELECT DISTINCT dependent FROM dep_graph WHERE dependency = ?",
            (concept,),
        ).fetchall()
        return [r["dependent"] for r in rows]

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get_meta(self, key: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM content_meta WHERE key = ?", (key,)
        ).fetchone()
        return dict(row) if row else None

    def stats(self) -> CacheStats:
        rows = self._conn.execute(
            "SELECT provenance, COUNT(*) as cnt FROM content_meta GROUP BY provenance"
        ).fetchall()
        by_provenance = {r["provenance"]: r["cnt"] for r in rows}
        total_entries = sum(by_provenance.values())

        agg = self._conn.execute(
            "SELECT SUM(hit_count) as total_hits, "
            "SUM(token_cost) as total_token_cost, "
            "SUM(hit_count * token_cost) as tokens_saved, "
            "COUNT(CASE WHEN stale = 1 THEN 1 END) as stale_count "
            "FROM content_meta"
        ).fetchone()

        concepts = [
            r["concept"]
            for r in self._conn.execute(
                "SELECT DISTINCT concept FROM content_meta ORDER BY concept"
            ).fetchall()
        ]

        return CacheStats(
            total_entries=total_entries,
            by_provenance=by_provenance,
            total_hits=agg["total_hits"] or 0,
            total_token_cost=agg["total_token_cost"] or 0,
            estimated_tokens_saved=agg["tokens_saved"] or 0,
            concepts=concepts,
            stale_count=agg["stale_count"] or 0,
        )

    # ------------------------------------------------------------------ #
    # Export / Import                                                      #
    # ------------------------------------------------------------------ #

    def export_rows(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM content_meta").fetchall()
        return [dict(r) for r in rows]

    def import_rows(self, rows: list[dict], merge: bool = True) -> int:
        """Import metadata rows. Returns count of rows written."""
        imported = 0
        for row in rows:
            exists = self._conn.execute(
                "SELECT 1 FROM content_meta WHERE key = ?", (row["key"],)
            ).fetchone()
            if exists and merge:
                continue
            if exists:
                raise ValueError(
                    f"Key conflict on import (merge=False): {row['key']}"
                )
            self._conn.execute(
                """INSERT INTO content_meta
                   (key, concept, content_hash, provenance, rubric_ver,
                    dep_hashes, params, adapter, model, token_cost,
                    hit_count, stale, verdict, created_at, updated_at)
                   VALUES (:key,:concept,:content_hash,:provenance,:rubric_ver,
                           :dep_hashes,:params,:adapter,:model,:token_cost,
                           :hit_count,:stale,:verdict,:created_at,:updated_at)
                """,
                row,
            )
            imported += 1
        self._conn.commit()
        return imported

    def delete_key(self, key: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM content_meta WHERE key = ?", (key,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_stale(self) -> int:
        cursor = self._conn.execute("DELETE FROM content_meta WHERE stale = 1")
        self._conn.commit()
        return cursor.rowcount

    def delete_by_provenance(self, provenance: str) -> int:
        cursor = self._conn.execute(
            "DELETE FROM content_meta WHERE provenance = ?", (provenance,)
        )
        self._conn.commit()
        return cursor.rowcount

    def clear_all(self) -> int:
        cursor = self._conn.execute("DELETE FROM content_meta")
        self._conn.execute("DELETE FROM dep_graph")
        self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        self._conn.close()
