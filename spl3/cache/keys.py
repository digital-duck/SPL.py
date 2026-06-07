from __future__ import annotations

import json
from hashlib import sha256

from dd_cache.utils import make_key


def content_key(
    concept: str,
    params: dict,
    rubric_version: str,
    dep_hashes: dict[str, str],
) -> str:
    """Compute the Layer 2 cache key (CAS model).

    Key = make_key("spl3", "content", sha256(canonical_json)).
    Any change to concept, params, rubric version, or upstream dep hashes
    produces a different key → automatic cache miss without bookkeeping.
    """
    payload = json.dumps(
        {
            "concept": concept,
            "params": params,
            "rubric": rubric_version,
            "deps": dep_hashes,
        },
        sort_keys=True,
    )
    h = sha256(payload.encode()).hexdigest()
    return make_key("spl3", "content", h)


def content_hash(content: str) -> str:
    """Short hash of generated content — used as dep_hash by downstream concepts."""
    return sha256(content.encode()).hexdigest()[:16]
