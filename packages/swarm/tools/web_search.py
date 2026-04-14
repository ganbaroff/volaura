"""Tavily web search — gives swarm agents internet access.

Setup: pip install tavily-python
       Set TAVILY_API_KEY in .env (free: 1000 req/mo at app.tavily.com)
"""

import os

_client = None


def _get_client():
    """Lazy-init async Tavily client."""
    global _client
    if _client is None:
        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            raise RuntimeError("pip install tavily-python")
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY not set — get free key at app.tavily.com")
        _client = AsyncTavilyClient(api_key=api_key)
    return _client


async def web_search(query: str, max_results: int = 5, topic: str = "general") -> str:
    """Search the web and return clean text for LLM consumption.

    Args:
        query: Search query string.
        max_results: Number of results (1-20, default 5).
        topic: "general", "news", or "finance".

    Returns:
        Formatted string with answer + top results.
    """
    client = _get_client()
    response = await client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer="basic",
        topic=topic,
    )

    parts: list[str] = []

    if answer := response.get("answer"):
        parts.append(f"Answer: {answer}\n")

    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        parts.append(f"[{i}] {title}\n    {url}\n    {content}\n")

    return "\n".join(parts) if parts else "No results found."


def web_search_sync(query: str, max_results: int = 5) -> str:
    """Synchronous wrapper for agents that don't use asyncio."""
    import asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    return asyncio.run(web_search(query, max_results))
