"""Volunteer embedding generation via Gemini text-embedding-004.

Embeddings are vector(768) stored in `volunteer_embeddings` and used
for semantic volunteer search via the `match_volunteers` RPC.
"""

from __future__ import annotations

from loguru import logger

from app.config import settings


async def generate_embedding(text: str) -> list[float] | None:
    """Generate a 768-dim embedding using Gemini text-embedding-004.

    Returns None if generation fails (caller should skip upsert).
    """
    if not text.strip():
        return None

    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.embed_content(
            model="models/text-embedding-004",
            contents=text[:8000],  # model input limit
        )
        embedding = response.embeddings[0].values
        return list(embedding)
    except Exception as e:
        logger.warning("Embedding generation failed", text_length=len(text), error=str(e)[:200])
        return None


def build_profile_text(profile: dict, aura: dict | None) -> str:
    """Build the text representation of a volunteer profile for embedding.

    Combines profile fields and AURA competency scores into a rich
    natural-language description so semantic search works well.
    """
    parts: list[str] = []

    if profile.get("display_name"):
        parts.append(f"Name: {profile['display_name']}")

    if profile.get("bio"):
        parts.append(f"Bio: {profile['bio']}")

    if profile.get("location"):
        parts.append(f"Location: {profile['location']}")

    if profile.get("languages"):
        parts.append(f"Languages: {', '.join(profile['languages'])}")

    if aura:
        parts.append(f"AURA score: {aura.get('total_score', 0):.1f}")
        parts.append(f"Badge: {aura.get('badge_tier', 'none')}")
        if aura.get("elite_status"):
            parts.append("Elite volunteer")

        comp = aura.get("competency_scores", {})
        if comp:
            scores = ", ".join(f"{k}: {v:.0f}" for k, v in comp.items() if v > 0)
            if scores:
                parts.append(f"Competencies: {scores}")

    return ". ".join(parts)


async def upsert_volunteer_embedding(
    db_admin,
    volunteer_id: str,
    profile: dict,
    aura: dict | None,
) -> bool:
    """Generate and store an embedding for a volunteer profile.

    Returns True on success.
    """
    text = build_profile_text(profile, aura)
    embedding = await generate_embedding(text)

    if embedding is None:
        return False

    result = (
        await db_admin.table("volunteer_embeddings")
        .upsert(
            {
                "volunteer_id": volunteer_id,
                "embedding": embedding,
                "model_version": "text-embedding-004",
            }
        )
        .execute()
    )

    return bool(result.data)
