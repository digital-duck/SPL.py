"""SPL tools for pocketflow-agent — web search via DuckDuckGo."""

import warnings
import os
os.environ.setdefault("PYTHONWARNINGS", "ignore::RuntimeWarning")

from spl.tools import spl_tool


@spl_tool(name="web_search")
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return formatted results.

    Accepts either a plain search query string or a YAML decision block
    (extracts search_query field automatically).

    Usage in SPL:
        CALL web_search(@query) INTO @search_results;
        CALL web_search(@decision) INTO @search_results;
    """
    import re
    import warnings
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    # Extract query from YAML decision block — try search_query first, then query
    m = re.search(r'search_query\s*:\s*["\']?([^"\'\n]+)["\']?', query)
    if not m:
        m = re.search(r'(?<!\w)query\s*:\s*["\']?([^"\'\n]+)["\']?', query)
    if m:
        query = m.group(1).strip()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            results = DDGS().text(query.strip(), max_results=5)
        if not results:
            return f"No results found for: {query}"

        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            url   = r.get("href", "")
            body  = r.get("body", "")
            lines.append(f"[{i}] {title}\n    URL: {url}\n    {body}")
        return "\n\n".join(lines)

    except Exception as e:
        return f"Search error: {e}"


if __name__ == "__main__":
    print(web_search("Nobel Prize Physics 2024"))
