"""Embedding-based comparison using vector similarity and BERTScore."""

from __future__ import annotations
from typing import Optional, Any
from spl3.compare.types import BERTScoreResult

def compare_vector(
    content1: str,
    content2: str,
    adapter_name: str,
    model_name: Optional[str] = None,
) -> float | str:
    try:
        try:
            from dd_embed import get_adapter as get_embed_adapter
        except ImportError:
            return "Error: dd-embed not installed: pip install dd-embed"
        
        import numpy as np
        embed_llm = get_embed_adapter(adapter_name, model_name=model_name)
        
        emb1 = embed_llm.embed([content1]).embeddings[0]
        emb2 = embed_llm.embed([content2]).embeddings[0]
        
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        similarity = np.dot(emb1, emb2) / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
        return float(similarity)
    except Exception as e:
        return f"Error: {e}"

def compare_bert_score(content1: str, content2: str) -> BERTScoreResult | str:
    try:
        try:
            import bert_score
            import torch
        except ImportError:
            return "Error: bert-score not installed: pip install bert-score torch"
        
        device = "cpu"
        P, R, F1 = bert_score.score([content2], [content1], lang="en", verbose=False, device=device)
        return BERTScoreResult(
            precision=float(P[0]),
            recall=float(R[0]),
            f1=float(F1[0])
        )
    except Exception as e:
        return f"Error: {e}"
