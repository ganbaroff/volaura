#!/usr/bin/env python3
"""
translate_ru.py — Batch-translate assessment questions to Russian (scenario_ru column).

Uses Gemini 2.0 Flash to translate scenario_en → scenario_ru for all questions
where scenario_ru is NULL. Safe to re-run: skips already-translated rows.

Usage:
    python scripts/translate_ru.py               # dry-run (prints translations)
    python scripts/translate_ru.py --apply       # writes to Supabase
    python scripts/translate_ru.py --apply --limit 10  # translate first 10

Requirements:
    pip install supabase google-genai python-dotenv

Env vars (loaded from apps/api/.env):
    SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Fix Windows console encoding for Cyrillic output
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Load env from api project
_root = Path(__file__).parent.parent
load_dotenv(_root / "apps" / "api" / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
GEMINI_KEY   = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.0-flash"
BATCH_SIZE   = 5   # parallel Gemini calls per batch


async def translate_batch(scenarios: list[str]) -> list[str]:
    """Translate a batch of scenario_en strings to Russian via Gemini."""
    from google import genai  # type: ignore[import]
    client = genai.Client(api_key=GEMINI_KEY)

    async def translate_one(text: str) -> str:
        prompt = (
            "Translate the following professional assessment scenario from English to Russian. "
            "Keep the professional tone. Return ONLY the Russian translation, no explanation.\n\n"
            f"{text}"
        )
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            ),
        )
        return response.text.strip()

    tasks = [translate_one(s) for s in scenarios]
    return await asyncio.gather(*tasks)


async def run(apply: bool, limit: int | None) -> None:
    from supabase import create_client  # type: ignore[import]

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch questions missing scenario_ru
    query = db.table("questions").select("id, scenario_en").is_("scenario_ru", "null")
    if limit:
        query = query.limit(limit)
    result = query.execute()
    rows = result.data or []

    if not rows:
        print("No questions need translation.")
        return

    print(f"Found {len(rows)} questions to translate{' (dry-run)' if not apply else ''}.")

    # Process in batches
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        scenarios = [r["scenario_en"] for r in batch]
        translations = await translate_batch(scenarios)

        for row, ru_text in zip(batch, translations):
            print(f"\n[{row['id'][:8]}]")
            print(f"  EN: {row['scenario_en'][:80]}...")
            print(f"  RU: {ru_text[:80]}...")
            if apply:
                db.table("questions").update({"scenario_ru": ru_text}).eq("id", row["id"]).execute()

        print(f"Batch {i // BATCH_SIZE + 1} done ({min(i + BATCH_SIZE, len(rows))}/{len(rows)})")

    if apply:
        print(f"\nDone. {len(rows)} questions updated.")
    else:
        print(f"\nDry-run complete. Run with --apply to write to Supabase.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate assessment questions to Russian")
    parser.add_argument("--apply", action="store_true", help="Write translations to Supabase (default: dry-run)")
    parser.add_argument("--limit", type=int, default=None, help="Max questions to translate")
    args = parser.parse_args()

    try:
        asyncio.run(run(apply=args.apply, limit=args.limit))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
