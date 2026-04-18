#!/usr/bin/env python3
"""Atlas Obligation Nag — fires Telegram reminders at escalating cadence.

Spec: memory/atlas/OBLIGATION-SYSTEM-SPEC-2026-04-18.md
Workflow: .github/workflows/atlas-obligation-nag.yml (cron */4 h)

For every open/in_progress obligation in public.atlas_obligations the script:
  1. Computes days_until_deadline (NULL deadline → skip unless trigger-based
     with no deferral window).
  2. Maps to a cadence tier (weekly / 2days / daily / 2x-daily / 4h).
  3. Claims a nag slot via try_claim_obligation_nag (advisory lock + DB cooldown).
  4. Sends a Telegram message via packages.swarm.notifier (vacation + 6h gates).
  5. On Telegram 200 → writes atlas_nag_log row via log_obligation_nag RPC.

At-least-once semantics: if Telegram fails we do NOT write the log. Next tick retries.
Concurrency: workflow layer (concurrency group) + DB layer (advisory lock).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Repo root so we can import packages.swarm.notifier
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from supabase import create_client
except ImportError:
    sys.stderr.write("supabase package not installed — pip install supabase\n")
    sys.exit(2)

try:
    from packages.swarm.notifier import send_notification
except Exception:  # noqa: BLE001 — fall back to stdlib Telegram if notifier import fails
    send_notification = None  # type: ignore[assignment]

from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Cadence map — deadline proximity → (tier name, cooldown in minutes)
# Cooldown is the minimum gap between two nag rows for the same obligation.
# ─────────────────────────────────────────────────────────────────────────────
def _cadence_tier(days_until: int | None) -> tuple[str, int] | None:
    """Return (tier_name, cooldown_minutes) or None (skip — no nag this tick)."""
    if days_until is None:
        # Trigger-based obligation without a hard date. Weekly gentle ping.
        return ("weekly", 7 * 24 * 60)
    if days_until > 14:
        return None  # still comfortable — no nag
    if days_until > 7:
        return ("weekly", 7 * 24 * 60)
    if days_until > 3:
        return ("2days", 2 * 24 * 60)
    if days_until > 1:
        return ("daily", 24 * 60)
    if days_until > 0:
        return ("2x-daily", 12 * 60)
    # past-due — aggressive 4h cadence
    return ("4h", 4 * 60)


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _build_nag_text(obligation: dict, tier: str, days_until: int | None) -> str:
    title = obligation.get("title") or "—"
    category = obligation.get("category") or "other"
    consequence = obligation.get("consequence_if_missed") or ""
    proof_required = obligation.get("proof_required") or []

    if days_until is None:
        header = f"⏳ *{title}* ({category})"
        body_line = "Триггерное обязательство — без хард-дедлайна."
    elif days_until < 0:
        header = f"🟣 *{title}* — просрочено на {abs(days_until)} дн."
        body_line = f"Каденс: {tier} (каждые 4 часа до закрытия)."
    elif days_until == 0:
        header = f"🟠 *{title}* — дедлайн СЕГОДНЯ"
        body_line = f"Каденс: {tier}."
    else:
        header = f"🟡 *{title}* — осталось {days_until} дн."
        body_line = f"Каденс: {tier}."

    proof_lines = "\n".join(f"  • {p}" for p in proof_required[:6]) if proof_required else "  • (proof_required пусто)"
    parts = [
        header,
        body_line,
    ]
    if consequence:
        parts.append(f"\n*Последствие:* {consequence[:400]}")
    parts.append(f"\n*Нужны доказательства:*\n{proof_lines}")
    parts.append("\nПришли фото/документ/трекинг — привяжу к этому обязательству.")
    return "\n".join(parts)


def _fallback_telegram_send(text: str, chat_id: str, token: str) -> tuple[bool, int | None]:
    """Stdlib Telegram send as last-resort fallback (used if notifier import failed)."""
    import json as _json
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=_json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            body = _json.loads(resp.read().decode("utf-8"))
            if body.get("ok"):
                mid = body.get("result", {}).get("message_id")
                return True, int(mid) if mid else None
            return False, None
    except (urllib.error.URLError, OSError, ValueError) as e:
        logger.error("Fallback Telegram send failed: {e}", e=str(e))
        return False, None


def main() -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CEO_CHAT_ID", "").strip()

    if not url or not key:
        logger.error("SUPABASE_URL / SUPABASE_SERVICE_KEY not set — aborting.")
        return 2
    if not tg_token or not tg_chat:
        logger.warning("Telegram credentials missing — dry-run mode.")

    client = create_client(url, key)

    # Fetch open/in_progress obligations (service_role RLS bypass via SECURITY DEFINER RPC).
    try:
        result = client.rpc("list_open_obligations").execute()
        obligations = result.data or []
    except Exception as e:  # noqa: BLE001
        logger.error("list_open_obligations failed: {e}", e=str(e))
        return 3

    logger.info("Fetched {n} open obligations.", n=len(obligations))
    if not obligations:
        return 0

    now = datetime.now(UTC)
    fired = 0
    skipped = 0

    for ob in obligations:
        ob_id = ob.get("id")
        if not ob_id:
            continue

        deadline = _parse_iso(ob.get("deadline"))
        days_until = (deadline - now).days if deadline else None

        # Silent-schedule obligations are never nagged (e.g., long-deferred items).
        if (ob.get("nag_schedule") or "standard") == "silent":
            skipped += 1
            continue

        tier_info = _cadence_tier(days_until)
        if tier_info is None:
            skipped += 1
            continue
        tier, cooldown_min = tier_info

        # Aggressive schedule bumps cooldown down one tier to roughly double the cadence.
        if (ob.get("nag_schedule") or "standard") == "aggressive":
            cooldown_min = max(4 * 60, cooldown_min // 2)

        # Claim nag slot — advisory lock + DB cooldown check.
        try:
            claim = client.rpc(
                "try_claim_obligation_nag",
                {"p_obligation_id": ob_id, "p_cooldown_minutes": cooldown_min},
            ).execute()
            slot_granted = bool(claim.data)
        except Exception as e:  # noqa: BLE001
            logger.error("try_claim_obligation_nag failed for {id}: {e}", id=ob_id, e=str(e))
            continue

        if not slot_granted:
            skipped += 1
            continue

        text = _build_nag_text(ob, tier, days_until)

        # Send through the notifier (vacation + 6h cooldown gates) or fallback stdlib.
        delivered = False
        message_id: int | None = None
        try:
            if send_notification is not None and tg_token and tg_chat:
                # Severity critical for past-due and same-day tiers so vacation can't mask legal risk.
                severity = "critical" if tier in ("4h", "2x-daily") else "warning"
                delivered = send_notification(
                    category="escalation",
                    text=text,
                    severity=severity,  # type: ignore[arg-type]
                )
            elif tg_token and tg_chat:
                delivered, message_id = _fallback_telegram_send(text, tg_chat, tg_token)
            else:
                logger.info("Dry-run: would send nag for {id} tier={t}", id=ob_id, t=tier)
        except Exception as e:  # noqa: BLE001
            logger.error("Telegram send raised for {id}: {e}", id=ob_id, e=str(e))
            delivered = False

        if not delivered:
            # Release the advisory lock so the next tick can retry.
            try:
                client.rpc("release_obligation_nag_lock", {"p_obligation_id": ob_id}).execute()
            except Exception:  # noqa: BLE001
                pass
            continue

        # At-least-once log AFTER confirmed delivery.
        try:
            client.rpc(
                "log_obligation_nag",
                {
                    "p_obligation_id": ob_id,
                    "p_telegram_chat_id": int(tg_chat) if tg_chat else 0,
                    "p_telegram_message_id": message_id,
                    "p_cadence_tier": tier,
                    "p_days_until_deadline": days_until,
                },
            ).execute()
            fired += 1
        except Exception as e:  # noqa: BLE001
            logger.error("log_obligation_nag failed (nag sent, log missing): {e}", e=str(e))

        # Release lock explicitly so same connection can process next obligation.
        try:
            client.rpc("release_obligation_nag_lock", {"p_obligation_id": ob_id}).execute()
        except Exception:  # noqa: BLE001
            pass

    logger.info("Nag tick complete: fired={f} skipped={s}", f=fired, s=skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
