"""Rubric loader for spl3 judge."""

from __future__ import annotations
from pathlib import Path

from spl3.judge.types import Rubric

_RUBRICS_DIR = Path(__file__).parent


def load_rubric(name_or_path: str) -> Rubric:
    """Load a built-in rubric by name or a custom rubric from a YAML path."""
    import yaml

    p = Path(name_or_path)
    if not p.exists():
        # Try built-in — normalise hyphens to underscores (spl-compliance → spl_compliance)
        normalised = name_or_path.replace("-", "_")
        p = _RUBRICS_DIR / f"{normalised}.yaml"
        if not p.exists():
            available = [f.stem for f in _RUBRICS_DIR.glob("*.yaml")]
            raise ValueError(
                f"Rubric '{name_or_path}' not found. "
                f"Built-ins: {available}. Or pass a path to a .yaml file."
            )

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Rubric(
        name=data["name"],
        criteria=data["criteria"],
        pass_threshold=float(data["pass_threshold"]),
        weight=data.get("weight", {}),
        prompt_template=data.get("prompt_template", ""),
    )


def list_rubrics() -> list[str]:
    return sorted(f.stem for f in _RUBRICS_DIR.glob("*.yaml"))
