"""Atlas recall helper — fetch last N session fingerprints from mem0.

Main-Atlas invokes this on wake to get a compact view of what past self was
doing across compactions. Pairs with `scripts/atlas_heartbeat.py` (store half).
stdlib-only. Never raises — mem0 down or empty returns []/None, caller handles.

Usage:
    python scripts/atlas_recall.py           # print last 10 fingerprints
    python scripts/atlas_recall.py 5         # print last 5

Mem0 endpoints used:
    POST /v2/memories/search/  body {query, filters: {user_id}}
    GET  /v1/memories/?user_id=... (fallback, no semantic scoring)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

MEM0_USER_ID = "atlas_ceo_yusif"
MEM0_V2_SEARCH = "https://api.mem0.ai/v2/memories/search/"


def _post_json(url: str, body: dict, token: str, timeout: float = 10.0) -> list | None:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "atlas-recall",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return data if isinstance(data, list) else [data]
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def fetch_recent_fingerprints(limit: int = 10, query: str = "Atlas wake") -> list[dict]:
    """Return recent session fingerprints as a list of memory dicts.

    Empty list means either (a) no memories yet, (b) auth failed, or (c) mem0
    down. Caller should not distinguish — the local inbox heartbeats are the
    primary recall surface; mem0 is the auxiliary semantic layer.
    """
    token = os.environ.get("MEM0_API_KEY", "")
    if not token:
        return []

    results = _post_json(
        MEM0_V2_SEARCH,
        {
            "query": query,
            "filters": {"user_id": MEM0_USER_ID},
            "top_k": limit,
        },
        token,
    )
    if not results:
        return []
    # Mem0 v2 returns a list of memory objects. Normalise to a minimal shape.
    normalised = []
    for item in results[:limit]:
        if not isinstance(item, dict):
            continue
        normalised.append(
            {
                "id": item.get("id"),
                "memory": item.get("memory") or item.get("content") or "",
                "created_at": item.get("created_at") or "",
                "metadata": item.get("metadata") or {},
            }
        )
    return normalised


def main() -> int:
    limit = 10
    if len(sys.argv) > 1:
        try:
            limit = max(1, int(sys.argv[1]))
        except ValueError:
            pass

    fingerprints = fetch_recent_fingerprints(limit=limit)
    if not fingerprints:
        print("(no fingerprints — mem0 empty, unreachable, or MEM0_API_KEY missing)")
        return 0

    print(f"Last {len(fingerprints)} Atlas session fingerprints (newest first):")
    print("-" * 60)
    for fp in fingerprints:
        created = fp.get("created_at", "")[:19] or "?"
        memory = (fp.get("memory") or "")[:180]
        print(f"[{created}] {memory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
