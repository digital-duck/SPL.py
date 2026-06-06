"""ROUGE score comparison tier.

Computes ROUGE-1, ROUGE-2, and ROUGE-L between two text documents.
Suitable for comparing spec files where n-gram overlap at the sentence
level captures intent similarity without requiring an LLM or model download.

Optional dependency::

    pip install rouge-score

Returns a RougeResult or an error string if the library is unavailable.
"""

from __future__ import annotations
from spl3.compare.types import RougeResult


def compare_rouge(content1: str, content2: str) -> "RougeResult | str":
    """Compute ROUGE-1, ROUGE-2, ROUGE-L F1 scores between two texts."""
    try:
        from rouge_score import rouge_scorer  # type: ignore
    except ImportError:
        return "Error: rouge-score not installed: pip install rouge-score"

    try:
        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        scores = scorer.score(content1, content2)
        return RougeResult(
            rouge1_precision=scores["rouge1"].precision,
            rouge1_recall=scores["rouge1"].recall,
            rouge1_f1=scores["rouge1"].fmeasure,
            rouge2_precision=scores["rouge2"].precision,
            rouge2_recall=scores["rouge2"].recall,
            rouge2_f1=scores["rouge2"].fmeasure,
            rougeL_precision=scores["rougeL"].precision,
            rougeL_recall=scores["rougeL"].recall,
            rougeL_f1=scores["rougeL"].fmeasure,
        )
    except Exception as e:
        return f"Error: {e}"
