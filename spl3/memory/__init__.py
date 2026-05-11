"""SPL Memory — unified persistence layer.

Quick start::

    from spl3.memory import get_memory_db, MemoryDB

    db = get_memory_db()                  # SQLite singleton (default path)
    db.config_set("splc", "adapter", "claude_cli")

    sid = db.session_start("self_refine", adapter="ollama", model="gemma3")
    db.session_complete(sid, output="...", latency_ms=1400, tokens_used=512)

    run_id = db.pipeline_upsert("neurips_ndd", "R1-agent/claude",
                                recipe="agent", model_alias="claude",
                                adapter="claude_cli", model_id="claude-sonnet-4-6",
                                phase=1)
    db.step_upsert(run_id, "S6", status="complete", score=0.87,
                   artifact_path="/path/to/S6-agent-claude-spec-diff.md")
    db.step_checkpoint(run_id, "S6", passed=True, note="Scores good")

Backend selection::

    SPL_MEMORY_URL=sqlite:///~/.spl/memory.db   (default)
    SPL_MEMORY_URL=postgresql://user:pass@host/spl
"""

from spl3.memory.db import MemoryDB, get_memory_db

__all__ = ["MemoryDB", "get_memory_db"]
