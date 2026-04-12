"""Azerbaijani language translation service.

Research verdict (2026-03-31, 31-tool deep search):
- Google Cloud Translation LLM (Gemini-powered, Dec 2025): best quality for AZ agglutinative structure
- DeepL / LanguageTool: do NOT support Azerbaijani — eliminated
- Raw Gemini: reliability issues (language switches) without validation gate
- Hunspell-AZ: spell-only, not grammar — supplementary at best

Architecture:
  Primary:  Google Cloud Translation LLM (if GCP_PROJECT_ID + credentials set)
  Fallback: Gemini 2.5 Flash with AZ-specialized prompt + language-detection guard
  Guard:    AZ character check (ə ğ ı ö ü ş ç) to detect language-switch hallucinations
"""

import asyncio

from loguru import logger

from app.config import settings

# AZ-specific characters — if output has none, it likely switched language
_AZ_CHARS = set("əğıöüşçƏĞIÖÜŞÇ")
_MIN_AZ_CHAR_RATIO = 0.005  # at least 0.5% of chars should be AZ-specific for meaningful text


def _has_az_characters(text: str) -> bool:
    """Detect if text contains Azerbaijani-specific characters."""
    if not text:
        return False
    az_count = sum(1 for c in text if c in _AZ_CHARS)
    # Short texts (under 20 chars) may legitimately have no AZ-specific chars
    if len(text) < 20:
        return True
    return az_count / len(text) >= _MIN_AZ_CHAR_RATIO


async def translate_en_to_az(
    text: str,
    context: str | None = None,
    max_retries: int = 2,
) -> str:
    """Translate English text to Azerbaijani.

    Args:
        text: English source text.
        context: Optional context hint (e.g., "professional assessment question for HR managers").
        max_retries: Number of retry attempts on language-switch detection.

    Returns:
        Azerbaijani translation. Falls back to original English on total failure
        (surfaces the gap rather than silently returning bad AZ).
    """
    if not text or not text.strip():
        return text

    # Path 1: Google Cloud Translation LLM (best quality, Gemini-powered)
    if settings.gcp_project_id:
        try:
            result = await _google_translation_llm(text)
            if result and _has_az_characters(result):
                return result
            logger.warning("Google Translation LLM returned suspicious output", text_preview=text[:50])
        except Exception as e:
            logger.warning("Google Translation LLM failed, falling back to Gemini", error=str(e))

    # Path 2: Gemini 2.5 Flash with AZ-specialized prompt + validation
    if settings.gemini_api_key:
        for attempt in range(max_retries):
            try:
                result = await _gemini_az_translation(text, context)
                if result and _has_az_characters(result):
                    return result
                logger.warning(
                    "Gemini AZ translation failed language check (attempt %d/%d)",
                    attempt + 1,
                    max_retries,
                    text_preview=text[:50],
                )
            except Exception as e:
                logger.warning("Gemini AZ translation error", attempt=attempt + 1, error=str(e))

    # Both paths failed — return English (visible gap, not silent bad AZ)
    logger.error("AZ translation failed on all paths, returning EN source", text=text[:100])
    return text


async def _google_translation_llm(text: str) -> str:
    """Call Google Cloud Translation LLM (Gemini-powered for AZ)."""
    # Lazy import — only needed if GCP is configured
    from google.cloud import translate_v3  # type: ignore[import]

    client = translate_v3.TranslationServiceClient()
    parent = f"projects/{settings.gcp_project_id}/locations/global"

    request = translate_v3.TranslateTextRequest(
        parent=parent,
        contents=[text],
        mime_type="text/plain",
        source_language_code="en",
        target_language_code="az",
        model=f"{parent}/models/general/translation-llm",
    )

    # Run sync client in thread pool (google-cloud-translate is sync)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, client.translate_text, request)
    return response.translations[0].translated_text


async def _gemini_az_translation(text: str, context: str | None) -> str:
    """Translate via Gemini 2.5 Flash with AZ-specialized prompt."""
    from google import genai  # type: ignore[import]

    client = genai.Client(api_key=settings.gemini_api_key)

    context_note = f"\nContext: {context}" if context else ""
    prompt = f"""You are a professional Azerbaijani linguist (Ana dili Azərbaycan dili olan mütəxəssis).
Translate the following English text to AZERBAIJANI (Latin script, as used in Azerbaijan since 1991).
{context_note}

CRITICAL RULES:
1. Output ONLY the Azerbaijani translation — no explanations, no English, no Russian
2. Use correct Azerbaijani case suffixes (vowel harmony: e.g., -da/-də, -dan/-dən, -ın/-in/-un/-ün)
3. Use natural Azerbaijani sentence structure (SOV order for formal register)
4. Use Azerbaijani-specific vocabulary, not Turkish cognates where they differ
5. Preserve technical terms in their internationally accepted form
6. Use formal (rəsmi) register appropriate for professional assessment platform

English text to translate:
{text}

Azerbaijani translation:"""

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    result = response.text.strip()
    # Strip any accidental prompt echo (if model repeated instructions)
    if "Azerbaijani translation:" in result:
        result = result.split("Azerbaijani translation:")[-1].strip()
    return result


async def batch_translate_en_to_az(
    texts: list[str],
    context: str | None = None,
    concurrency: int = 5,
) -> list[str]:
    """Translate multiple texts concurrently with rate-limiting.

    Args:
        texts: List of English source texts.
        context: Optional context applied to all translations.
        concurrency: Max parallel translation calls (default 5 to respect rate limits).

    Returns:
        List of Azerbaijani translations, same order as input.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _translate_with_semaphore(text: str) -> str:
        async with semaphore:
            return await translate_en_to_az(text, context=context)

    return await asyncio.gather(*[_translate_with_semaphore(t) for t in texts])
