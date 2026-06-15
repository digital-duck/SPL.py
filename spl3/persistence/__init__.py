"""SPL workflow persistence backends.

Backends
--------
sqlite   : zero-dependency local durability (~/.spl/workflows.db)
postgres : production PostgreSQL backend (pip install asyncpg)
dbos     : cloud-grade durable execution via DBOS + PostgreSQL (pip install dbos)

Usage
-----
    from spl3.persistence import get_backend
    backend = get_backend("sqlite")                      # local dev
    backend = get_backend("postgres", dsn="...")         # production
    backend = get_backend("dbos")                        # requires DBOS_DATABASE_URL
"""

from __future__ import annotations
from .base import PersistenceBackend


def get_backend(name: str, **kwargs) -> PersistenceBackend:
    name = name.lower().strip()
    if name == "sqlite":
        from .sqlite_backend import SQLitePersistenceBackend
        return SQLitePersistenceBackend(**kwargs)
    if name in ("postgres", "postgresql"):
        from .postgres_backend import PostgresPersistenceBackend
        return PostgresPersistenceBackend(**kwargs)
    if name == "dbos":
        from .dbos_backend import DBOSPersistenceBackend
        return DBOSPersistenceBackend(**kwargs)
    raise ValueError(
        f"Unknown persistence backend: {name!r}. "
        f"Choose 'sqlite', 'postgres', or 'dbos'."
    )


__all__ = ["PersistenceBackend", "get_backend"]
