"""SPL 3.0 Image Operations — img2mmd and img2text.

Uses multimodal LLMs (Claude, Gemini, GPT-4o) to extract structured
information from images.

Adapter notes
-------------
- openrouter  (default): native multimodal via MultiModalDDLLMBridge; requires OPENROUTER_API_KEY.
- claude_cli            : uses Anthropic SDK for vision; requires ANTHROPIC_API_KEY.
- anthropic / google / openai: native multimodal via generate_multimodal().
- Text-only adapters (ollama without vision model, echo): will log a warning and
  return a best-effort text-only response.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from spl3.adapters import get_adapter
from spl3.codecs.image_codec import encode_image

_log = logging.getLogger("spl.image_ops")

_MMD_SYNTAX_RULES = """\
MANDATORY Mermaid syntax rules:
1. Start with: flowchart TD
2. Every node must have an ID and a label: A[Label Text]
3. Decision/branch node: use SINGLE braces — C{Decision?}
4. Terminal/start/end node: use stadium shape — S([Start])
5. Connections: A --> B  or  A -->|edge label| B  (two dashes, not ->)
6. Multi-word labels: A["First line<br/>Second line"]
7. Do NOT use \\n inside labels — use <br/> inside quotes instead.
8. Do NOT use Unicode arrows (→) inside labels.
9. Subgraphs: subgraph SG1["Title"]\n  ...\nend
10. Output ONLY the mermaid code block — no explanation text before or after.
"""


async def img2mmd(
    image_path: str,
    adapter_name: str = "openrouter",
    model: Optional[str] = None,
) -> str:
    """Extract Mermaid flowchart logic from an image.

    Args:
        image_path:   Path to the image file or a public URL.
        adapter_name: Multimodal adapter to use (default: openrouter).
        model:        Model name override.

    Returns:
        Mermaid diagram code (without fences), or "(No workflow logic detected)".
    """
    adapter = get_adapter(adapter_name, **({"model": model} if model else {}))

    if not hasattr(adapter, "generate_multimodal"):
        raise ValueError(
            f"Adapter '{adapter_name}' does not implement generate_multimodal. "
            "Use --adapter claude_cli / anthropic / google / openai."
        )

    image_part = encode_image(image_path)

    prompt = (
        "You are a technical diagram analyst.\n\n"
        "Analyze the image and reconstruct its logic as valid Mermaid flowchart code.\n"
        "The image may contain: a flowchart, a workflow diagram, an architecture diagram, "
        "a sequence diagram, a process map, pseudo-code, or a hand-drawn sketch.\n\n"
        + _MMD_SYNTAX_RULES
        + "\nIf the image contains NO workflow, diagram, or logical structure "
        "(e.g. it is a photo, screenshot of plain text, or unstructured content), "
        "return ONLY the string: (No workflow logic detected)\n\n"
        "Generate the Mermaid code now:"
    )

    result = await adapter.generate_multimodal(
        content=[
            {"type": "text",  "text": prompt},
            image_part,
        ],
        model=model or "",
    )

    content = result.content.strip() if hasattr(result, "content") else str(result).strip()

    if "(no workflow logic detected)" in content.lower():
        return "(No workflow logic detected)"

    # Extract from ```mermaid ... ``` fence
    m = re.search(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Generic code fence fallback
    m = re.search(r"```[^\n]*\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Bare "flowchart" / "graph" keyword — LLM returned code without fences
    if re.match(r"\s*(flowchart|graph|sequenceDiagram|classDiagram)\b", content, re.IGNORECASE):
        return content

    # Short ambiguous response that reads as "no diagram found"
    if len(content) < 120 and any(
        w in content.lower() for w in ["no diagram", "no logic", "cannot find", "no workflow"]
    ):
        return "(No workflow logic detected)"

    return content


async def img2text(
    image_path: str,
    adapter_name: str = "openrouter",
    model: Optional[str] = None,
) -> str:
    """Extract text and pseudo-code from an image (OCR + structure preservation).

    Args:
        image_path:   Path to the image file or a public URL.
        adapter_name: Multimodal adapter to use (default: openrouter).
        model:        Model name override.

    Returns:
        Extracted text with structure preserved, or "(No text detected)".
    """
    adapter = get_adapter(adapter_name, **({"model": model} if model else {}))

    if not hasattr(adapter, "generate_multimodal"):
        raise ValueError(
            f"Adapter '{adapter_name}' does not implement generate_multimodal. "
            "Use --adapter claude_cli / anthropic / google / openai."
        )

    image_part = encode_image(image_path)

    prompt = (
        "You are a precise OCR and text extraction tool.\n\n"
        "Extract ALL text, pseudo-code, code fragments, annotations, and labels "
        "visible in the image.\n\n"
        "Rules:\n"
        "- Preserve indentation and code structure exactly as shown.\n"
        "- If you see code or pseudo-code, wrap it in an appropriate fenced code block "
        "(e.g. ```python, ```java, ```pseudocode).\n"
        "- Preserve bullet points, numbering, and section headings.\n"
        "- If mathematical notation is present, render it in LaTeX ($...$) or plain ASCII.\n"
        "- Do NOT add any commentary, interpretation, or explanation — output only "
        "what is written in the image.\n"
        "- If NO text or code is visible, return ONLY: (No text detected)\n\n"
        "Extract the text now:"
    )

    result = await adapter.generate_multimodal(
        content=[
            {"type": "text",  "text": prompt},
            image_part,
        ],
        model=model or "",
    )

    return result.content.strip() if hasattr(result, "content") else str(result).strip()
