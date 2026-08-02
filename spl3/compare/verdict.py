"""Deterministic (no-LLM) verdict derivation for `spl3 compare`.

Maps tier results to a single label — EQUIVALENT | REFACTORED | DEGRADED | DIVERGED
(or UNKNOWN) — without calling an LLM. Two uses:

1. Rule-based fallback when no synthesis LLM runs (`--no-synthesize`), so code files
   still receive a labeled verdict instead of nothing.
2. A stable top-level ``verdict`` field in the JSON report, so downstream tools
   (e.g. BOM/manifest batch compare, or external harnesses) do not have to parse
   prose or guess from the diff.
"""
from __future__ import annotations

from spl3.compare.types import ComparisonResult, GEDResult, BERTScoreResult, RougeResult


def _band(x: float, eq: float, ref: float, deg: float) -> str:
    return ("EQUIVALENT" if x >= eq else
            "REFACTORED" if x >= ref else
            "DEGRADED" if x >= deg else "DIVERGED")


def deterministic_verdict(res: ComparisonResult) -> dict:
    """Best deterministic verdict from whichever tiers ran. Priority: identity →
    topology (GED) → structural skeleton → AST symbols → embedding/overlap bands."""
    r = res.results

    # 1. Character identity — the strongest signal.
    gd = r.get("git-diff")
    if isinstance(gd, str) and gd.strip() == "":
        return {"verdict": "EQUIVALENT", "confidence": "HIGH",
                "key_finding": "No character-level differences", "basis": "git-diff"}

    # 2. Graph edit distance (topology) — same thresholds as the GED tier report.
    ged = r.get("ged")
    if isinstance(ged, GEDResult):
        nd = ged.normalized_distance
        v = ("EQUIVALENT" if nd == 0 else "REFACTORED" if nd < 0.10 else
             "DEGRADED" if nd < 0.35 else "DIVERGED")
        return {"verdict": v, "confidence": "HIGH",
                "key_finding": f"GED normalized distance {nd:.3f}", "basis": "ged"}

    # 3. Structural skeleton — same interface, different text ⇒ REFACTORED.
    st = r.get("structural")
    if isinstance(st, dict):
        s1, s2 = st.get("file1"), st.get("file2")
        if s1 and s2:
            if s1 == s2:
                return {"verdict": "REFACTORED", "confidence": "MEDIUM",
                        "key_finding": "Identical structural skeleton; implementation differs",
                        "basis": "structural"}
            return {"verdict": "DEGRADED", "confidence": "LOW",
                    "key_finding": "Structural skeletons differ", "basis": "structural"}

    # 4. AST symbol set — no symbols added/removed ⇒ REFACTORED; else interface changed.
    ast = r.get("ast-diff")
    if isinstance(ast, dict) and ast:
        changed = any(isinstance(d, dict) and (d.get("added") or d.get("removed"))
                      for d in ast.values())
        if not changed:
            return {"verdict": "REFACTORED", "confidence": "MEDIUM",
                    "key_finding": "Same public symbols; bodies differ", "basis": "ast-diff"}
        return {"verdict": "DIVERGED", "confidence": "MEDIUM",
                "key_finding": "Public symbols added/removed", "basis": "ast-diff"}

    # 5. Embedding / n-gram overlap — soft bands, low confidence.
    vec = r.get("vector")
    if isinstance(vec, (int, float)):
        return {"verdict": _band(float(vec), 0.995, 0.95, 0.80), "confidence": "LOW",
                "key_finding": f"Cosine similarity {float(vec):.3f}", "basis": "vector"}
    bs = r.get("bert-score")
    if isinstance(bs, BERTScoreResult):
        return {"verdict": _band(bs.f1, 0.995, 0.95, 0.85), "confidence": "LOW",
                "key_finding": f"BERTScore F1 {bs.f1:.3f}", "basis": "bert-score"}
    ro = r.get("rouge")
    if isinstance(ro, RougeResult):
        return {"verdict": _band(ro.rougeL_f1, 0.99, 0.90, 0.60), "confidence": "LOW",
                "key_finding": f"ROUGE-L F1 {ro.rougeL_f1:.3f}", "basis": "rouge"}

    return {"verdict": "UNKNOWN", "confidence": "LOW",
            "key_finding": "No deterministic verdict available "
                           "(add a structural/ast-diff/ged tier, or use --synthesize)",
            "basis": None}


def verdict_of(res: ComparisonResult) -> dict:
    """Prefer an existing (LLM) synthesis verdict; otherwise derive deterministically."""
    if isinstance(res.synthesis, dict) and res.synthesis.get("verdict"):
        return res.synthesis
    return deterministic_verdict(res)
