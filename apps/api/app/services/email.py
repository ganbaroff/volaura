"""Transactional email service via Resend.

Kill switch: email_enabled=False (default) — no emails sent.
CEO sets RESEND_API_KEY + EMAIL_ENABLED=true on Railway when account is ready.

Never raises — email failure must never block product flows.

Usage:
    from app.services.email import send_aura_ready_email

    asyncio.create_task(send_aura_ready_email(
        to_email="user@example.com",
        display_name="Leyla",
        competency_slug="adaptability",
        competency_score=78.5,
        badge_tier="Gold",
        crystals_earned=15,
    ))
"""

from __future__ import annotations

import httpx
from loguru import logger

from app.config import settings

# Resend API base URL
_RESEND_URL = "https://api.resend.com/emails"

# Badge tier display labels
_BADGE_LABELS: dict[str, str] = {
    "bronze": "Bronze",
    "silver": "Silver",
    "gold": "Gold",
    "platinum": "Platinum",
}

# Competency slug → human-readable name (EN)
_COMPETENCY_NAMES: dict[str, str] = {
    "adaptability": "Adaptability",
    "communication": "Communication",
    "leadership": "Leadership",
    "teamwork": "Teamwork",
    "problem_solving": "Problem Solving",
    "time_management": "Time Management",
    "initiative": "Initiative",
}


def _build_html(
    display_name: str,
    competency_name: str,
    competency_score: float,
    badge_tier: str,
    crystals_earned: int,
) -> str:
    score_int = round(competency_score)
    badge_label = _BADGE_LABELS.get(badge_tier.lower(), badge_tier)
    crystal_line = (
        f"<p style='color:#a855f7;'>+{crystals_earned} crystals earned 💎</p>"
        if crystals_earned > 0
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f1117;font-family:system-ui,-apple-system,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:40px auto;">
    <tr><td style="background:#1a1d2e;border-radius:12px;padding:40px;">
      <p style="color:#6b7280;font-size:13px;margin:0 0 24px;">VOLAURA · Your AURA score is ready</p>
      <h1 style="color:#e8e8f0;font-size:24px;font-weight:700;margin:0 0 8px;">
        {display_name}, your {competency_name} score is in
      </h1>
      <p style="color:#9ca3af;font-size:16px;margin:0 0 32px;">
        You completed the assessment. Here's what we found.
      </p>
      <div style="background:#252840;border-radius:8px;padding:24px;margin-bottom:24px;">
        <p style="color:#8b8ba7;font-size:13px;margin:0 0 4px;">{competency_name.upper()}</p>
        <p style="color:#7b72ff;font-size:48px;font-weight:800;margin:0 0 4px;">{score_int}</p>
        <p style="color:#4ecdc4;font-size:14px;margin:0;">
          {badge_label} · <span style="color:#8b8ba7;">out of 100</span>
        </p>
        {crystal_line}
      </div>
      <a href="{settings.app_url}/az/assessment" style="display:inline-block;background:#7b72ff;color:#fff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;font-size:15px;margin-bottom:32px;">
        View full results →
      </a>
      <p style="color:#6b7280;font-size:13px;margin:0;">
        You can take assessments in other competencies to build a complete AURA profile.
        Organizations searching for talent will find you based on your verified scores.
      </p>
      <hr style="border:none;border-top:1px solid #252840;margin:32px 0 24px;">
      <p style="color:#4b5563;font-size:12px;margin:0;">
        VOLAURA · Baku, Azerbaijan · <a href="{settings.app_url}" style="color:#6b7280;">{settings.app_url}</a>
      </p>
    </td></tr>
  </table>
</body>
</html>"""


async def send_aura_ready_email(
    to_email: str,
    display_name: str,
    competency_slug: str,
    competency_score: float,
    badge_tier: str,
    crystals_earned: int = 0,
) -> None:
    """Send AURA score ready notification email via Resend.

    Kill switch: if email_enabled=False or resend_api_key is empty, silently skips.
    Never raises — email failure is logged as WARNING and does not propagate.
    """
    if not settings.email_enabled:
        logger.debug(
            "email disabled (EMAIL_ENABLED=false) — skipping send_aura_ready_email",
            to=to_email,
        )
        return

    if not settings.resend_api_key:
        logger.warning(
            "send_aura_ready_email called but RESEND_API_KEY not set",
            to=to_email,
        )
        return

    competency_name = _COMPETENCY_NAMES.get(competency_slug, competency_slug.replace("_", " ").title())

    try:
        html_body = _build_html(
            display_name=display_name or "there",
            competency_name=competency_name,
            competency_score=competency_score,
            badge_tier=badge_tier,
            crystals_earned=crystals_earned,
        )
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                _RESEND_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": "VOLAURA <noreply@volaura.app>",
                    "to": [to_email],
                    "subject": f"Your {competency_name} AURA score is ready",
                    "html": html_body,
                },
            )
            if resp.status_code == 200:
                logger.info(
                    "aura_ready_email sent",
                    to=to_email,
                    competency=competency_slug,
                    score=round(competency_score),
                )
            else:
                logger.warning(
                    "aura_ready_email Resend error",
                    to=to_email,
                    status=resp.status_code,
                    body=resp.text[:200],
                )
    except Exception as exc:
        logger.warning(
            "aura_ready_email failed (non-fatal)",
            to=to_email,
            error=str(exc)[:200],
        )
