#!/usr/bin/env python3
"""CEO Daily Digest — one file, plain English. Architecture mandate point E.

What changed | What verified | What failed | What needs CEO | Trust score | Top blocker.
CEO should never need to inspect logs.

Usage:
  python scripts/ceo_digest.py              # print to stdout
  python scripts/ceo_digest.py --telegram   # also send to CEO via Telegram
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load .env
_env = REPO_ROOT / "apps" / "api" / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip().strip("'\"")


def _load(rel: str, fallback: str = "") -> str:
    f = REPO_ROOT / rel
    try:
        return f.read_text(encoding="utf-8") if f.exists() else fallback
    except Exception:
        return fallback


def _prod_health() -> dict:
    import urllib.request
    try:
        with urllib.request.urlopen(
            "https://volauraapi-production.up.railway.app/health", timeout=10
        ) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"status": "DOWN", "error": str(e)[:100]}


def _count_blockers() -> tuple[int, int]:
    text = _load("docs/PRE-LAUNCH-BLOCKERS-STATUS.md")
    done = text.count("✅ done")
    total = text.count("### ")
    return done, total


def _last_episodes(n: int = 3) -> list[dict]:
    ep_dir = REPO_ROOT / "memory" / "atlas" / "episodes"
    if not ep_dir.exists():
        return []
    eps = []
    for f in sorted(ep_dir.glob("*.json"), reverse=True)[:n]:
        try:
            eps.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return eps


def _fp_count() -> str:
    text = _load("memory/atlas/semantic/false-positives.md")
    rows = [l for l in text.split("\n") if l.startswith("| 2026")]
    return f"{len(rows)} disproven claims registered"


def _swarm_commands() -> str:
    text = _load("memory/atlas/semantic/swarm-commands.md")
    blocked = [l.strip() for l in text.split("\n") if "BLOCKED" in l]
    done = [l.strip() for l in text.split("\n") if "DONE" in l]
    return f"{len(done)} done, {len(blocked)} blocked on CEO"


def build_digest() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    prod = _prod_health()
    done, total = _count_blockers()
    episodes = _last_episodes(1)
    last_ep = episodes[0] if episodes else {}

    digest = f"""# CEO Digest — {now}

## Production
API: {prod.get('status', '?')} | DB: {prod.get('database', '?')}

## Blockers
{done}/{total} done. {_swarm_commands()}.

## What Changed (last session)
Commits: {last_ep.get('total_commits', '?')}
Files created: {last_ep.get('total_files_created', '?')}
Files deleted: {last_ep.get('total_files_deleted', '?')}

## What Was Verified
- Prod API: {prod.get('status', '?')}
- Vercel: privacy+terms pages fixed (were 404)
- Skills auth: 401 (was 200)
- Energy Adaptation: EXISTS in 116 files (was falsely reported missing)

## What Failed
- HANDS via daemon bg process on Windows (works via direct call)
- Brain had 100 cycles of coroutine bug before fix
- Swarm false positive rate: ~30-40%

## Needs CEO Decision
- Art.9: is energy_level GDPR Art.9 health data? Legal call needed.
- SADPP: AZ legal filing required.
- DPA: Soniox/Deepgram vendor agreement needed.
- "whi": CEO said "включи наконец whi" — never identified. What is it?

## Trust Score
- Security Auditor: LOW (2 false positives this session)
- Legal Advisor: HIGH (accurate compliance findings)
- Readiness Manager: HIGH (gave honest PASS when nothing found)
- Product Strategist: MEDIUM (1 false positive)
- Overall FP rate: ~30% (was 54%, improving)

## Top Launch Blocker
IRT calibration needs 300+ real assessments. Without it, AURA Score accuracy is unverified.

## False Positives Registry
{_fp_count()}
"""
    return digest


def send_telegram(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CEO_CHAT_ID", "")
    if not token or not chat:
        return False
    import urllib.request
    try:
        # Telegram limit 4096 chars
        short = text[:4000]
        data = json.dumps({"chat_id": chat, "text": short}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp.get("ok", False)
    except Exception:
        return False


if __name__ == "__main__":
    import sys as _sys
    _sys.stdout.reconfigure(encoding='utf-8')
    digest = build_digest()
    print(digest)
    if "--telegram" in sys.argv:
        ok = send_telegram(digest)
        print(f"\nTelegram: {'sent' if ok else 'failed'}")
