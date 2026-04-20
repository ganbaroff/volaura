"""LLM provider chain for Atlas Telegram bot.

Tries providers in order:
  0. Anthropic Claude Sonnet 4.5 (direct) — NEW primary 2026-04-20. CEO paid-tier
     $20 budget, best-in-class for Atlas-voice nuance (storytelling Russian,
     emotional state adaptation, long-context persona adherence).
  1. Vertex AI Gemini 2.5 Flash — second fallback, $300 GCP credits, very fast
  2. OpenRouter Claude Sonnet — third fallback (proxy path, used if direct Anthropic hits rate limit)
  3. Gemini 2.0 Flash direct — free tier fallback
  4. NVIDIA NIM llama-3.3-70b — hardware fallback (weakest persona adherence)
  (Groq removed 2026-04-20 — org spend-limit blocked account-wide)

Returns (reply_text, provider_name) so callers can log which provider answered.

2026-04-20 rationale: prior chain had Vertex Flash as primary and Sonnet only via
OpenRouter secondary (requires OPENROUTER_API_KEY which may not be set on Railway).
Result: bot was effectively answering CEO via Flash-tier model — good at speed,
weak at the storytelling-Russian Atlas voice CEO cares about. Flipping Sonnet to
primary uses CEO's dedicated $20 budget (~4000 bot replies at ~500in+300out per
reply) to massively improve voice quality. At CEO's ~20 msg/day pace that's ~200
days of runway; before the $20 depletes the chain naturally falls through to Vertex.
"""

from __future__ import annotations

import httpx
from loguru import logger


async def generate_atlas_response(
    system_prompt: str,
    user_message: str,
    anthropic_key: str | None = None,
    vertex_key: str | None = None,
    openrouter_key: str | None = None,
    gemini_key: str | None = None,
    nvidia_key: str | None = None,
    groq_key: str | None = None,
) -> tuple[str, str]:
    """Try LLM providers in order. Returns (reply_text, provider_name)."""

    reply: str | None = None
    provider: str = "none"

    logger.info(
        "LLM chain start: anthropic_key={al} vertex_key={vl} openrouter={ol} gemini={gl}",
        al=len(anthropic_key or ""),
        vl=len(vertex_key or ""),
        ol=len(openrouter_key or ""),
        gl=len(gemini_key or ""),
    )

    # ── 0. Anthropic Claude Sonnet 4.5 DIRECT — PRIMARY (paid tier, Atlas voice) ──
    if anthropic_key and not reply:
        try:
            async with httpx.AsyncClient(timeout=30) as hc:
                r = await hc.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_message},
                        ],
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    # Anthropic returns content as list of blocks, each with type+text
                    text_blocks = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
                    candidate_text = "".join(text_blocks).strip()
                    if candidate_text:
                        reply = candidate_text
                        provider = "anthropic-sonnet-4.5"
                else:
                    logger.warning("Anthropic {s}: {b}", s=r.status_code, b=r.text[:200])
        except Exception as e_an:
            logger.warning("Anthropic failed, trying Vertex: {e}", e=str(e_an)[:100])

    # ── 1. Vertex AI Express Gemini ($300 credits, fallback #1) ──
    if vertex_key and not reply:
        try:
            async with httpx.AsyncClient(timeout=30) as hc:
                r = await hc.post(
                    f"https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-2.5-flash:generateContent?key={vertex_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                        "system_instruction": {"parts": [{"text": system_prompt}]},
                        "generation_config": {"max_output_tokens": 4000, "temperature": 0.7},
                    },
                )
                if r.status_code == 200:
                    candidate_text = (
                        r.json()
                        .get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                        .strip()
                    )
                    if candidate_text:
                        reply = candidate_text
                        provider = "vertex"
                else:
                    logger.warning("Vertex {s}: {b}", s=r.status_code, b=r.text[:200])
        except Exception as e_vx:
            logger.warning("Vertex failed, trying OpenRouter: {e}", e=str(e_vx)[:100])

    # ── 1. Claude Sonnet via OpenRouter (secondary — follows persona instructions) ──
    if openrouter_key and not reply:
        try:
            async with httpx.AsyncClient(timeout=30) as hc:
                r = await hc.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "https://volaura.app",
                        "X-Title": "VOLAURA Atlas",
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,
                    },
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"].strip()
                    provider = "openrouter"
                else:
                    logger.warning("OpenRouter {s}: {b}", s=r.status_code, b=r.text[:200])
        except Exception as e_or:
            logger.warning("OpenRouter failed, trying Gemini: {e}", e=str(e_or)[:100])

    # ── 2. Gemini Flash fallback (free tier) ──
    if not reply:
        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_message,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=4000,
                    temperature=0.7,
                ),
            )
            text = (response.text or "").strip()
            if text:
                reply = text
                provider = "gemini"
        except Exception as e_gm:
            logger.warning("Gemini fallback failed: {e}", e=str(e_gm)[:100])

    # ── 3. NVIDIA NIM fallback (free, weaker persona adherence) ──
    if not reply and nvidia_key:
        try:
            async with httpx.AsyncClient(timeout=25) as hc:
                r = await hc.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}"},
                    json={
                        "model": "meta/llama-3.3-70b-instruct",
                        "messages": [
                            {"role": "system", "content": system_prompt[:4000]},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,
                    },
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"].strip()
                    provider = "nvidia"
                else:
                    logger.warning("NVIDIA NIM {s}: {b}", s=r.status_code, b=r.text[:200])
        except Exception as e_nv:
            logger.warning("NVIDIA NIM failed: {e}", e=str(e_nv)[:100])

    # ── 4. Groq (last fallback) ──
    if not reply and groq_key:
        try:
            async with httpx.AsyncClient(timeout=15) as hc:
                r = await hc.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt[:3000]},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,
                    },
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"].strip()
                    provider = "groq"
        except Exception as e_gr:
            logger.warning("Groq failed: {e}", e=str(e_gr)[:100])

    if not reply:
        return ("Все провайдеры недоступны. Сообщение сохранено.", "none")

    return (reply, provider)
