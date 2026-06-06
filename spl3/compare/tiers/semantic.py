"""Semantic comparison using LLM and Vision."""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Any

_FOCUS_PROMPTS = {
    "all":      "Provide a comprehensive comparison covering structure, logic, quality, and syntax.",
    "structure":"Focus on architectural and organizational differences.",
    "logic":    "Focus on logical flow, decision points, and process sequences.",
    "quality":  "Focus on completeness, sophistication, and best practices.",
    "syntax":   "Focus on syntax correctness, formatting, and technical accuracy.",
    "spl":      (
        "Focus on SPL-specific semantics: "
        "WORKFLOW/PROCEDURE identity (are the same workflows present?); "
        "GENERATE function signatures — these are the semantic heart (what the LLM is asked to do); "
        "CALL dependencies (which sub-workflows are invoked); "
        "WHILE/EVALUATE conditions (control-flow logic); "
        "EXCEPTION handlers (safety contracts — their presence or absence matters); "
        "@variable names (consistency of data flow). "
        "Treat operation signatures as primary evidence; syntax details as secondary."
    ),
}


def build_semantic_prompt(
    content1: str,
    content2: str,
    path1: Path,
    path2: Path,
    focus: str = "all",
) -> str:
    ext1 = path1.suffix.lower()
    ext2 = path2.suffix.lower()
    focus_text = _FOCUS_PROMPTS.get(focus, _FOCUS_PROMPTS["all"])
    return f"""Compare these two files semantically and provide a detailed analysis.

**File 1**: {path1.name} ({ext1})
**File 2**: {path2.name} ({ext2})
**Focus**: {focus_text}

**File 1 Content:**
```
{content1}
```

**File 2 Content:**
```
{content2}
```

Please provide a structured comparison analysis with sections for Summary, \
Content Analysis, Detailed Comparison, Recommendations, and Scoring (1-10)."""


async def compare_semantic(
    content1: str,
    content2: str,
    path1: Path,
    path2: Path,
    adapter: Any,
    model: Optional[str] = None,
    focus: str = "all",
) -> str:
    prompt = build_semantic_prompt(content1, content2, path1, path2, focus)
    result = await adapter.generate(prompt, **({"model": model} if model else {}))
    return result if isinstance(result, str) else getattr(result, "content", str(result))


async def compare_vision(
    path1: Path,
    path2: Path,
    adapter: Optional[Any] = None,
    model: Optional[str] = None,
) -> dict:
    vision_result: dict = {}
    ext1 = path1.suffix.lower()
    ext2 = path2.suffix.lower()

    try:
        from PIL import Image as _PIL_Image
        import numpy as _np
        im1 = _PIL_Image.open(path1)
        im2 = _PIL_Image.open(path2)
        vision_result["metadata"] = {
            "file1": {"size": list(im1.size), "mode": im1.mode},
            "file2": {"size": list(im2.size), "mode": im2.mode},
        }
        if im1.size == im2.size:
            arr1 = _np.array(im1.convert("RGB")).astype(float)
            arr2 = _np.array(im2.convert("RGB")).astype(float)
            diff = _np.abs(arr1 - arr2)
            vision_result["pixel_diff"] = {
                "mean_delta":         round(float(diff.mean()), 3),
                "max_delta":          round(float(diff.max()), 1),
                "changed_pixels_pct": round(float((diff.sum(axis=2) > 10).mean() * 100), 2),
            }
            h1 = _np.histogram(arr1.ravel(), bins=64, range=(0, 256))[0].astype(float)
            h2 = _np.histogram(arr2.ravel(), bins=64, range=(0, 256))[0].astype(float)
            n1, n2 = _np.linalg.norm(h1), _np.linalg.norm(h2)
            if n1 > 0 and n2 > 0:
                vision_result["histogram_similarity"] = round(float(_np.dot(h1 / n1, h2 / n2)), 4)
    except ImportError:
        vision_result["note"] = "Install Pillow for pixel-level comparison: pip install Pillow"
    except Exception as exc:
        vision_result["error"] = str(exc)

    # LLM vision analysis via generate_multimodal (works with any multimodal adapter)
    if adapter:
        try:
            import base64 as _b64
            _MIME = {".png": "image/png", ".jpg": "image/jpeg",
                     ".jpeg": "image/jpeg", ".webp": "image/webp"}
            _vision_prompt = (
                f"Compare these two diagrams: '{path1.name}' (Image 1) vs '{path2.name}' (Image 2).\n\n"
                "Analyze: (1) structural elements present in one but absent in the other, "
                "(2) flow/control differences — loops, branches, exception handlers, "
                "(3) label/operation differences — function names, variable names, conditions, "
                "(4) overall verdict: EQUIVALENT, REFACTORED, DEGRADED, or DIVERGED.\n\n"
                "Focus on logical/semantic differences, not visual styling."
            )
            _mime1 = _MIME.get(ext1, "image/png")
            _mime2 = _MIME.get(ext2, "image/png")
            _img1_b64 = _b64.standard_b64encode(path1.read_bytes()).decode()
            _img2_b64 = _b64.standard_b64encode(path2.read_bytes()).decode()
            content_parts = [
                {"type": "text",  "text": _vision_prompt},
                {"type": "image", "source": "base64", "media_type": _mime1, "data": _img1_b64},
                {"type": "image", "source": "base64", "media_type": _mime2, "data": _img2_b64},
            ]
            if hasattr(adapter, "generate_multimodal"):
                raw = await adapter.generate_multimodal(
                    content_parts,
                    **({"model": model} if model else {}),
                )
                vision_result["llm_analysis"] = (
                    raw if isinstance(raw, str) else getattr(raw, "content", str(raw))
                )
        except Exception:
            pass  # vision LLM is best-effort

    return vision_result
