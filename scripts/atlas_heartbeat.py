"""Atlas self-wake heartbeat — runs every 30 minutes via GitHub Actions cron.

Purpose: keep Atlas's external state fresh without waiting for CEO to wake him.
Each tick does a tiny set of read-only probes and writes one inbox note.

Scope guard enforced at workflow level — heartbeat can ONLY touch:
  memory/atlas/inbox/
  memory/atlas/.wake-counter

Interruption protection: GitHub Actions concurrency group on the workflow file
means a new tick waits for the previous one to finish (cancel-in-progress: false).
No tick overlap, no half-written state.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INBOX_DIR = REPO_ROOT / "memory" / "atlas" / "inbox"
WAKE_COUNTER = REPO_ROOT / "memory" / "atlas" / ".wake-counter"

PROD_HEALTH_URL = "https://volauraapi-production.up.railway.app/health"
GH_REPO = "ganbaroff/volaura"


def _fetch_json(url: str, timeout: float = 10.0) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "atlas-heartbeat"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def _ci_status() -> str:
    """Return 'green' / 'red' / 'unknown' for the latest CI run on main."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return "unknown"
    url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/ci.yml/runs?per_page=1&branch=main"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "atlas-heartbeat"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return "unknown"
    runs = data.get("workflow_runs", [])
    if not runs:
        return "unknown"
    conclusion = runs[0].get("conclusion")
    if conclusion == "success":
        return "green"
    if conclusion in ("failure", "cancelled", "timed_out"):
        return "red"
    return "unknown"


def _read_wake_counter() -> int:
    if not WAKE_COUNTER.exists():
        return 0
    try:
        return int(WAKE_COUNTER.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def _write_wake_counter(n: int) -> None:
    WAKE_COUNTER.write_text(str(n), encoding="utf-8")


def _store_fingerprint_to_mem0(wake_n: int, content: str) -> bool:
    """Best-effort write of session fingerprint to mem0 cloud memory.

    Returns True if mem0 accepted the memory, False otherwise. Never raises —
    mem0 being down or key missing is non-fatal, heartbeat still writes the
    local inbox note.

    Why: Cowork's MEMORY-HOLE-AUDIT flagged that mem0 MCP was registered with
    key but zero workers called store/recall. This is the store half. Retrieve
    on wake is a separate helper for main-Atlas, not this cron script.
    """
    key = os.environ.get("MEM0_API_KEY", "")
    if not key:
        return False
    try:
        payload = json.dumps(
            {
                "messages": [{"role": "user", "content": content}],
                "user_id": "atlas_ceo_yusif",
                "metadata": {"source": "atlas_heartbeat", "wake_n": wake_n},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.mem0.ai/v1/memories/",
            data=payload,
            headers={
                "Authorization": f"Token {key}",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "atlas-heartbeat",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    stamp = now.strftime("%Y-%m-%dT%H%M")
    wake_n = _read_wake_counter() + 1
    _write_wake_counter(wake_n)

    prod = _fetch_json(PROD_HEALTH_URL)
    prod_line = (
        f"Prod /health -> {prod.get('status')} (db={prod.get('database')}, llm={prod.get('llm_configured')})"
        if prod
        else "Prod /health -> UNREACHABLE"
    )

    ci = _ci_status()

    note = INBOX_DIR / f"{stamp}-heartbeat-{wake_n:04d}.md"
    note.write_text(
        f"""# Atlas Heartbeat — wake #{wake_n}

**When:** {now.isoformat()}
**Kind:** scheduled self-wake (every 30 min via atlas-self-wake.yml)

## Observations

- {prod_line}
- CI main branch: **{ci}**
- Inbox notes ahead of this one: {len(list(INBOX_DIR.glob('*.md'))) - 1}

## What main Atlas should do on next wake

Read the latest 3 heartbeat notes. If they all show prod=ok and CI=green for
2+ hours, no action — scope is healthy. If any line degraded, cross-reference
with `memory/atlas/journal.md` last entry to decide whether it was an in-flight
change or a real regression.

---

**Consumed by main Atlas:** pending
""",
        encoding="utf-8",
    )

    # Best-effort mem0 fingerprint — compact recall surface for future wakes.
    # Non-fatal on failure.
    mem0_content = f"wake #{wake_n} at {now.isoformat()}. {prod_line}. CI: {ci}."
    mem0_ok = _store_fingerprint_to_mem0(wake_n, mem0_content)

    print(f"wake #{wake_n} written -> {note.relative_to(REPO_ROOT)}")
    print(prod_line)
    print(f"CI: {ci}")
    print(f"mem0 fingerprint: {'stored' if mem0_ok else 'skipped/failed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
