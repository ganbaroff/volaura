"""LLM provider chain for Atlas Telegram bot.

Tries providers in order: Vertex AI → OpenRouter → Gemini → NVIDIA NIM → Groq.
Returns (reply_text, provider_name) so callers can log which provider answered.
"""

from __future__ import annotations

import httpx
from loguru import logger


async def generate_atlas_response(
    system_prompt: str,
    user_message: str,
    vertex_key: str | None = None,
    openrouter_key: str | None = None,
    gemini_key: str | None = None,
    nvidia_key: str | None = None,
    groq_key: str | None = None,
) -> tuple[str, str]:
    """Try LLM providers in order. Returns (reply_text, provider_name)."""

    reply: str | None = None
    provider: str = "none"

    # ── 0. Vertex AI Express Gemini ($300 credits, enterprise SLA) ──
    logger.info(
        "LLM chain start: vertex_key={vl} openrouter={ol} gemini={gl}",
        vl=len(vertex_key or ""),
        ol=len(openrouter_key or ""),
        gl=len(gemini_key or ""),
    )
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
