"""Comparison engine — orchestrator for multi-tier comparison."""

from __future__ import annotations
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from spl3.compare.types import ComparisonResult, GEDResult, BERTScoreResult, RougeResult
from spl3.compare.tiers.character import compare_character
from spl3.compare.tiers.ged import compare_ged
from spl3.compare.tiers.semantic import compare_semantic, compare_vision
from spl3.compare.tiers.syntactic import compare_syntactic
from spl3.compare.tiers.structural import compare_structural
from spl3.compare.tiers.embedding import compare_vector, compare_bert_score
from spl3.compare.tiers.rouge import compare_rouge

_TIER_LABELS = {
    "ged":        "Tier 1 – Topological (GED)",
    "llm":        "Tier 2 – Semantic (LLM)",
    "vision":     "Tier 2 – Semantic (Vision)",
    "ast-diff":   "Tier 3 – Syntactic (AST-diff)",
    "structural": "Tier 4 – Structural",
    "git-diff":   "Tier 5 – Character-level (git-diff)",
    "vector":     "Tier 6 – Embedding (vector cosine)",
    "bert-score": "Tier 6 – Embedding (BERTScore)",
    "rouge":      "Tier 6 – N-gram Overlap (ROUGE)",
}

async def run_comparison(
    path1: Path,
    path2: Path,
    active_modes: list[str],
    adapter_name: str,
    model: Optional[str] = None,
    adapter_embed: Optional[str] = None,
    model_embed: Optional[str] = None,
    adapter_synthesis: Optional[str] = None,
    focus: str = "all",
    diff_style: str = "unified",
    no_color: bool = False,
    output_format: str = "markdown",
    is_terminal: bool = False,
    synthesize: bool = True,
) -> ComparisonResult:
    content1 = path1.read_text(encoding="utf-8")
    content2 = path2.read_text(encoding="utf-8")
    ext1 = path1.suffix.lower()
    ext2 = path2.suffix.lower()

    from spl3.adapters import get_adapter
    llm = get_adapter(adapter_name, **({"model": model} if model else {}))

    result_obj = ComparisonResult(
        file1=str(path1),
        file2=str(path2),
        ext=ext1,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        modes=active_modes
    )

    # Character-level
    if "git-diff" in active_modes:
        result_obj.results["git-diff"] = compare_character(
            content1, content2, path1, path2, diff_style, no_color, output_format, is_terminal
        )

    # Semantic (LLM)
    if "llm" in active_modes:
        result_obj.results["llm"] = await compare_semantic(
            content1, content2, path1, path2, llm, model, focus
        )

    # Vision
    if "vision" in active_modes:
        result_obj.results["vision"] = await compare_vision(path1, path2, llm, model)

    # GED
    if "ged" in active_modes:
        if ext1 == ".mmd" and ext2 == ".mmd":
            result_obj.results["ged"] = compare_ged(content1, content2)
        else:
            result_obj.results["ged"] = "Skipped: GED requires .mmd input files."

    # Structural
    if "structural" in active_modes:
        result_obj.results["structural"] = compare_structural(content1, content2, ext1, ext2)

    # Syntactic (AST)
    if "ast-diff" in active_modes:
        result_obj.results["ast-diff"] = compare_syntactic(content1, content2, ext1, ext2)

    # Embedding / Vector
    if "vector" in active_modes:
        result_obj.results["vector"] = compare_vector(content1, content2, adapter_embed or adapter_name, model_embed)

    # BERTScore
    if "bert-score" in active_modes:
        result_obj.results["bert-score"] = compare_bert_score(content1, content2)

    # ROUGE
    if "rouge" in active_modes:
        result_obj.results["rouge"] = compare_rouge(content1, content2)

    # Fallback logic for failed tiers
    await _handle_fallbacks(result_obj, active_modes, content1, content2, llm, model)

    # Synthesis
    if synthesize:
        syn_adapter = adapter_synthesis or adapter_name
        if syn_adapter:
            syn_llm = get_adapter(syn_adapter, **({"model": model} if model else {}))
            result_obj.synthesis = await synthesize_results(result_obj, syn_llm, model)
        else:
            result_obj.synthesis = _rule_based_synthesis(result_obj)

    return result_obj

async def _handle_fallbacks(res: ComparisonResult, active_modes: list[str], c1: str, c2: str, llm: Any, model: Optional[str]):
    _FALLBACK_ASPECTS = {
        "ged":        "topological graph structure",
        "vector":     "semantic similarity and embedding-space proximity",
        "bert-score": "token-level semantic overlap",
        "vision":     "visual layout and structural differences",
        "structural": "document/code skeleton",
        "ast-diff":   "syntactic AST-level differences",
    }
    failed = [
        m for m in active_modes
        if m in _FALLBACK_ASPECTS
        and isinstance(res.results.get(m), str)
        and (res.results[m].startswith("Error:") or res.results[m].startswith("Skipped:"))
    ]
    if failed and llm and "llm" not in active_modes:
        aspects = "; ".join(_FALLBACK_ASPECTS[m] for m in failed)
        prompt = (
            f"Comparison tiers failed: {failed}. Fallback analysis on: {aspects}.\n\n"
            f"File 1:\n{c1[:2000]}\n\nFile 2:\n{c2[:2000]}"
        )
        raw = await llm.generate(prompt, **({"model": model} if model else {}))
        res.results["llm_fallback"] = raw if isinstance(raw, str) else getattr(raw, "content", str(raw))

async def synthesize_results(res: ComparisonResult, llm: Any, model: Optional[str]) -> dict:
    summary = []
    for mode in res.modes:
        r = res.results.get(mode)
        label = _TIER_LABELS.get(mode, mode)
        if isinstance(r, GEDResult):
            summary.append(f"{label}: distance={r.distance}, norm={r.normalized_distance}")
        elif isinstance(r, BERTScoreResult):
            summary.append(f"{label}: F1={r.f1:.4f}")
        elif isinstance(r, RougeResult):
            summary.append(f"{label}: ROUGE-1={r.rouge1_f1:.4f}, ROUGE-2={r.rouge2_f1:.4f}, ROUGE-L={r.rougeL_f1:.4f}")
        elif mode == "git-diff" and isinstance(r, str):
            summary.append(f"{label}: {len(r.splitlines())} lines in diff")
        else:
            summary.append(f"{label}: {str(r)[:200]}...")

    prompt = f"""Synthesize these comparison results for {res.file1} vs {res.file2}:
{chr(10).join(summary)}

Respond with JSON only:
{{
  "verdict": "EQUIVALENT|REFACTORED|DEGRADED|DIVERGED",
  "confidence": "HIGH|MEDIUM|LOW",
  "key_finding": "...",
  "cross_tier_insight": "...",
  "recommendation": "..."
}}"""
    
    raw = await llm.generate(prompt, **({"model": model} if model else {}))
    text = raw if isinstance(raw, str) else getattr(raw, "content", str(raw))
    # Try direct parse first, then extract the outermost JSON object
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"raw": text}

def _rule_based_synthesis(res: ComparisonResult) -> dict:
    ged = res.results.get("ged")
    if isinstance(ged, GEDResult):
        nd = ged.normalized_distance
        v = "EQUIVALENT" if nd == 0 else "REFACTORED" if nd < 0.1 else "DEGRADED" if nd < 0.35 else "DIVERGED"
        return {"verdict": v, "key_finding": f"Based on GED norm {nd}"}
    return {"verdict": "UNKNOWN", "key_finding": "No automated verdict possible"}
