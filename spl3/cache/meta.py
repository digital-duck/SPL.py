from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .types import (
    ALL_BADGES,
    CacheStats,
    badges_from_provenance,
    is_canonical,
    normalize_badges,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS content_meta (
    key          TEXT PRIMARY KEY,
    concept      TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    badges       TEXT NOT NULL DEFAULT '[]',
    rubric_ver   TEXT NOT NULL,
    dep_hashes   TEXT NOT NULL,
    params       TEXT NOT NULL,
    adapter      TEXT,
    model        TEXT,
    token_cost   INTEGER DEFAULT 0,
    hit_count    INTEGER DEFAULT 0,
    stale        INTEGER DEFAULT 0,
    verdict      TEXT,
    verifier     TEXT NOT NULL DEFAULT '',
    statement    TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_concept ON content_meta(concept);
CREATE INDEX IF NOT EXISTS idx_stale   ON content_meta(stale);

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

    Stores trust badges, dependency graph, hit counts, and token costs.
    Blob storage is delegated to dd-cache (BaseCacheAdapter).
    """

    def __init__(self, meta_path: str = ".spl/content_meta.db") -> None:
        os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(meta_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(content_meta)")}
        # Migration: DBs created before the engine-of-record column (A-3)
        if "verifier" not in cols:
            self._conn.execute(
                "ALTER TABLE content_meta ADD COLUMN verifier TEXT NOT NULL DEFAULT ''"
            )
        # Migration: DBs created before the badge-set model (B-4). The old
        # single-ordinal `provenance` column is left in place but ignored;
        # each legacy tier becomes the badge set attesting only what it
        # attested ('machine_generated' = no badge).
        if "badges" not in cols:
            self._conn.execute(
                "ALTER TABLE content_meta ADD COLUMN badges TEXT NOT NULL DEFAULT '[]'"
            )
            if "provenance" in cols:
                for tier in ALL_BADGES:
                    self._conn.execute(
                        "UPDATE content_meta SET badges = ? WHERE provenance = ?",
                        (json.dumps([tier]), tier),
                    )
        if "statement" not in cols:
            self._conn.execute(
                "ALTER TABLE content_meta ADD COLUMN statement TEXT NOT NULL DEFAULT ''"
            )
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def put(
        self,
        key: str,
        concept: str,
        content_hash: str,
        badges: list[str],
        rubric_version: str,
        dep_hashes: dict[str, str],
        params: dict,
        adapter: str,
        model: str,
        token_cost: int,
        verifier: str = "",
        statement: str = "",
    ) -> None:
        badges = normalize_badges(badges)
        now = _now()
        self._conn.execute(
            """INSERT INTO content_meta
               (key, concept, content_hash, badges, rubric_ver,
                dep_hashes, params, adapter, model, token_cost,
                hit_count, stale, verdict, verifier, statement,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,0,0,NULL,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET
                   content_hash = excluded.content_hash,
                   badges       = excluded.badges,
                   rubric_ver   = excluded.rubric_ver,
                   dep_hashes   = excluded.dep_hashes,
                   params       = excluded.params,
                   adapter      = excluded.adapter,
                   model        = excluded.model,
                   token_cost   = excluded.token_cost,
                   verifier     = excluded.verifier,
                   statement    = excluded.statement,
                   stale        = 0,
                   updated_at   = excluded.updated_at
            """,
            (
                key, concept, content_hash, json.dumps(badges), rubric_version,
                json.dumps(dep_hashes, sort_keys=True),
                json.dumps(params, sort_keys=True),
                adapter, model, token_cost,
                verifier, statement, now, now,
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
        badge: str,
        verdict: Optional[dict] = None,
        statement: str = "",
    ) -> list[str]:
        """Add a trust badge to an entry's set; returns the new set.

        Badges only accumulate — there is no downgrade, and adding a badge
        the entry already holds is an error. A provided verdict replaces the
        stored one (the audit record of the latest promotion); None keeps it.
        A non-empty *statement* records the formal statement backing the
        badge (the machine_proved promotion path).
        """
        row = self._conn.execute(
            "SELECT badges, verdict, statement FROM content_meta WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            raise KeyError(f"No cache entry with key: {key}")
        held = json.loads(row["badges"])
        if badge in held:
            raise ValueError(f"Entry already holds badge '{badge}'.")
        new_badges = normalize_badges(held + [badge])
        verdict_json = json.dumps(verdict) if verdict else row["verdict"]
        self._conn.execute(
            "UPDATE content_meta SET badges = ?, verdict = ?, statement = ?, "
            "updated_at = ? WHERE key = ?",
            (json.dumps(new_badges), verdict_json,
             statement or row["statement"], _now(), key),
        )
        self._conn.commit()
        return new_badges

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
        badge_rows = self._conn.execute(
            "SELECT badges FROM content_meta"
        ).fetchall()
        by_badge: dict[str, int] = {}
        unbadged = 0
        canonical = 0
        for r in badge_rows:
            held = json.loads(r["badges"])
            if not held:
                unbadged += 1
            for b in held:
                by_badge[b] = by_badge.get(b, 0) + 1
            if is_canonical(held):
                canonical += 1

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
            total_entries=len(badge_rows),
            by_badge=by_badge,
            unbadged=unbadged,
            canonical=canonical,
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
        """Import metadata rows. Returns count of rows written.

        Accepts pre-B-4 exports: a row carrying only the legacy single
        `provenance` tier is converted to the equivalent badge set.
        """
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
            row = dict(row)
            if not row.get("badges"):
                row["badges"] = json.dumps(
                    badges_from_provenance(row.get("provenance", ""))
                )
            row.setdefault("verifier", "")
            row.setdefault("statement", "")
            self._conn.execute(
                """INSERT INTO content_meta
                   (key, concept, content_hash, badges, rubric_ver,
                    dep_hashes, params, adapter, model, token_cost,
                    hit_count, stale, verdict, verifier, statement,
                    created_at, updated_at)
                   VALUES (:key,:concept,:content_hash,:badges,:rubric_ver,
                           :dep_hashes,:params,:adapter,:model,:token_cost,
                           :hit_count,:stale,:verdict,:verifier,:statement,
                           :created_at,:updated_at)
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

    def delete_by_badge(self, badge: str) -> int:
        """Delete entries holding a badge; 'unbadged' deletes the badge-less."""
        if badge == "unbadged":
            cursor = self._conn.execute(
                "DELETE FROM content_meta WHERE badges = '[]'"
            )
        else:
            normalize_badges([badge])
            cursor = self._conn.execute(
                "DELETE FROM content_meta WHERE badges LIKE ?",
                (f'%"{badge}"%',),
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
