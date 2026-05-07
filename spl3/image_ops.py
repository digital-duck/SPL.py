"""SPL 3.0 Image Operations — img2mmd and img2text.

Uses multimodal LLMs (Gemini, Claude 3, GPT-4o) to extract structured
information from images.
"""

from __future__ import annotations

import logging
from typing import Optional

from spl3.adapters import get_adapter
from spl3.codecs.image_codec import encode_image

_log = logging.getLogger("spl.image_ops")


async def img2mmd(
    image_path: str,
    adapter_name: str = "google",
    model: Optional[str] = None,
) -> str:
    """Extract Mermaid flowchart logic from an image.

    Args:
        image_path: Path to the image file or URL.
        adapter_name: Multi-modal adapter to use (default: google/gemini).
        model: Model name override.

    Returns:
        The extracted Mermaid code.
    """
    adapter = get_adapter(adapter_name)
    
    # Check if adapter supports multimodal (has generate_multimodal)
    if not hasattr(adapter, "generate_multimodal"):
         raise ValueError(f"Adapter '{adapter_name}' does not support multimodal input.")

    image_part = encode_image(image_path)
    
    prompt = (
        "Analyze this image and extract its logic into a Mermaid flowchart (.mmd). "
        "The image may contain a diagram, a flowchart, or a technical process. "
        "Return ONLY the Mermaid code block, starting with ```mermaid and ending with ```. "
        "If no workflow logic or diagram structure is found, return ONLY the string: (No workflow logic detected)"
    )

    result = await adapter.generate_multimodal(
        content=[
            {"type": "text", "text": prompt},
            image_part,
        ],
        model=model or "",
    )
    
    content = result.content.strip()
    
    # Check for negative case first
    if "(no workflow logic detected)" in content.lower():
        return "(No workflow logic detected)"

    # Extract from ```mermaid block if present
    import re
    mermaid_match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
    if mermaid_match:
        return mermaid_match.group(1).strip()
    
    # Fallback to generic code block
    code_match = re.search(r"```\n(.*?)\n```", content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
            
    # If the LLM returned text but no block, and it looks like a "no logic" message
    if len(content) < 100 and any(word in content.lower() for word in ["no diagram", "no logic", "cannot find"]):
        return "(No workflow logic detected)"

    return content


async def img2text(
    image_path: str,
    adapter_name: str = "google",
    model: Optional[str] = None,
) -> str:
    """Extract text and pseudo-code from an image.

    Args:
        image_path: Path to the image file or URL.
        adapter_name: Multi-modal adapter to use (default: google/gemini).
        model: Model name override.

    Returns:
        The extracted text.
    """
    adapter = get_adapter(adapter_name)
    
    if not hasattr(adapter, "generate_multimodal"):
         raise ValueError(f"Adapter '{adapter_name}' does not support multimodal input.")

    image_part = encode_image(image_path)
    
    prompt = (
        "Perform OCR on this image. Extract all text, pseudo-code, and code fragments. "
        "Preserve the indentation and layout as much as possible to maintain the structure. "
        "If NO text or code is found in the image, return ONLY the string: (No text detected)"
    )

    result = await adapter.generate_multimodal(
        content=[
            {"type": "text", "text": prompt},
            image_part,
        ],
        model=model or "",
    )
    
    return result.content.strip()
