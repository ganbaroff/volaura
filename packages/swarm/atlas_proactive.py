"""Atlas Proactive Loop Worker — Phase 2.

Runs every 15 minutes via .github/workflows/atlas-proactive.yml on GitHub-hosted
runners. Picks the next-due topic from memory/atlas/proactive_queue.json, runs one
focused research dive via Groq or NVIDIA NIM (Article 0 hierarchy — never Claude),
writes the result to memory/atlas/inbox/, updates the queue, and commits to main.

Spec: memory/atlas/proactive_loop.md
Atlas CTO identity: memory/atlas/bootstrap.md (minimum), memory/atlas/identity.md (full)

Phase 1 (complete): heartbeat-only skeleton proving cron pipeline alive.
Phase 2 (this): real LLM research call via stdlib urllib (no extra deps on GH runner).
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = REPO_ROOT / "memory" / "atlas" / "proactive_queue.json"
INBOX_DIR = REPO_ROOT / "memory" / "atlas" / "inbox"
BOOTSTRAP_PATH = REPO_ROOT / "memory" / "atlas" / "bootstrap.md"

WAKE_NUMBER_MARKER = REPO_ROOT / "memory" / "atlas" / ".wake-counter"


def _load_queue() -> dict:
    if not QUEUE_PATH.exists():
        raise SystemExit(f"proactive queue not found at {QUEUE_PATH}")
    with QUEUE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_queue(queue: dict) -> None:
    queue["last_updated"] = datetime.now(timezone.utc).date().isoformat()
    with QUEUE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(queue, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _next_wake_number() -> int:
    if WAKE_NUMBER_MARKER.exists():
        current = int(WAKE_NUMBER_MARKER.read_text(encoding="utf-8").strip() or "0")
    else:
        current = 0
    nxt = current + 1
    WAKE_NUMBER_MARKER.write_text(str(nxt), encoding="utf-8")
    return nxt


def _pick_topic(queue: dict) -> dict | None:
    # If ATLAS_TOPIC_ID env var is set, process that specific topic on-demand
    # instead of queue selection. This is the webhook-wake path — any caller
    # that fires the workflow with a topic_id input gets a focused run.
    requested_id = os.environ.get("ATLAS_TOPIC_ID", "").strip()
    if requested_id:
        for t in queue.get("topics", []):
            if t.get("id") == requested_id:
                return t
        # Requested topic not found in queue — return None, worker will log
        # empty and exit cleanly rather than crash.
        return None

    now = datetime.now(timezone.utc)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    due = []
    for t in queue.get("topics", []):
        next_due = datetime.fromisoformat(t["next_due"].replace("Z", "+00:00"))
        if next_due <= now:
            due.append(t)
    if not due:
        return None
    due.sort(
        key=lambda t: (
            priority_order.get(t.get("priority", "medium"), 1),
            t.get("last_researched") or "0000-00-00",
        )
    )
    return due[0]


def _topic_refresh(topic: dict) -> None:
    now = datetime.now(timezone.utc)
    topic["last_researched"] = now.isoformat().replace("+00:00", "Z")
    hours = topic.get("refresh_interval_hours", 168)
    topic["next_due"] = (now + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _write_inbox_note(topic: dict, wake_number: int, body: str, provider: str) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = topic["id"][:60]
    filename = f"{today}-{wake_number:04d}-{slug}.md"
    path = INBOX_DIR / filename
    header = (
        f"# Atlas Proactive — {topic['title']}\n\n"
        f"**Date:** {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}\n"
        f"**Wake number:** {wake_number:04d}\n"
        f"**Topic ID:** {topic['id']}\n"
        f"**Priority:** {topic.get('priority', 'medium')}\n"
        f"**Provider used:** {provider}\n"
        f"**Follow-up action:** pending main Atlas review\n\n"
        f"---\n\n"
    )
    footer = (
        f"\n\n---\n\n"
        f"**Consumed by main Atlas:** pending\n"
        f"**Result:** pending\n"
    )
    path.write_text(header + body + footer, encoding="utf-8")
    return path


def _call_llm(prompt: str) -> tuple[str, str]:
    """Call an LLM via HTTP. Returns (response_text, provider_used).

    Tries Groq first (fast, free tier 14400 req/day), then NVIDIA NIM.
    Uses only stdlib — no extra deps needed on GitHub Actions runner.
    Falls back to heartbeat message if both fail.
    """
    providers = [
        {
            "name": "nvidia/llama-3.1-8b",
            "url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "key_env": "NVIDIA_API_KEY",
            "model": "meta/llama-3.1-8b-instruct",
        },
        {
            "name": "deepseek/chat",
            "url": "https://api.deepseek.com/chat/completions",
            "key_env": "DEEPSEEK_API_KEY",
            "model": "deepseek-chat",
        },
        {
            "name": "groq/llama-3.3-70b",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key_env": "GROQ_API_KEY",
            "model": "llama-3.3-70b-versatile",
        },
    ]

    ctx = ssl.create_default_context()

    for p in providers:
        api_key = os.environ.get(p["key_env"], "").strip()
        if not api_key:
            continue
        payload = json.dumps({
            "model": p["model"],
            "messages": [
                {"role": "system", "content": "You are Atlas, CTO of VOLAURA — a verified professional talent platform. Write concise research notes in markdown. Stay under 800 words."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1500,
            "temperature": 0.3,
        }).encode("utf-8")

        req = urllib.request.Request(
            p["url"],
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["choices"][0]["message"]["content"]
                return text, p["name"]
        except Exception as e:
            print(f"atlas-proactive: {p['name']} failed: {e}", file=sys.stderr)
            continue

    return "(No LLM providers available — heartbeat only)", "none/fallback"


def _research_body(topic: dict) -> tuple[str, str]:
    """Generate real research for a topic via LLM call."""
    prompt = (
        f"Research topic: {topic['title']}\n\n"
        f"Context: {topic.get('context_hint', 'No additional context.')}\n\n"
        f"Write a focused research note covering:\n"
        f"1. Current state of this topic (2025-2026)\n"
        f"2. Key findings with specific names, URLs, versions\n"
        f"3. Relevance to VOLAURA (verified professional talent platform)\n"
        f"4. Recommended next action for Atlas CTO\n\n"
        f"Be specific. Cite repos, papers, or tools by name. No filler."
    )
    return _call_llm(prompt)


def main() -> int:
    if not BOOTSTRAP_PATH.exists():
        print(f"bootstrap.md missing at {BOOTSTRAP_PATH}", file=sys.stderr)
        return 2

    queue = _load_queue()
    topic = _pick_topic(queue)
    if topic is None:
        print("proactive queue empty or no topics due — writing empty heartbeat")
        empty_note = (
            "# Atlas Proactive — Queue Empty\n\n"
            f"**Date:** {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}\n"
            f"**Wake number:** {_next_wake_number():04d}\n"
            f"**Status:** No topics due. Loop is alive, waiting for next cycle.\n"
        )
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        p = INBOX_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6]}-queue-empty.md"
        p.write_text(empty_note, encoding="utf-8")
        return 0

    wake_number = _next_wake_number()
    body, provider = _research_body(topic)
    path = _write_inbox_note(topic, wake_number, body, provider)
    _topic_refresh(topic)
    _save_queue(queue)

    print(f"atlas-proactive: wake {wake_number:04d} wrote {path.name} for topic '{topic['id']}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
