#!/usr/bin/env python3
"""Question Generation Pipeline (Sprint Checkpoint #4).

Generates assessment questions via LLM, validates each through the quality
harness, and optionally inserts passing items into the prod question bank.

Uses Gemini Flash (free tier) via google-genai. Falls back to NVIDIA NIM.

Usage:
    python scripts/generate_questions.py --competency communication --count 5 --dry-run
    python scripts/generate_questions.py --competency leadership --role scrum_master --count 3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from uuid import uuid4

# ── Env setup ────────────────────────────────────────────────────────────────

def _load_env():
    for env_path in [
        Path(__file__).parent.parent / "apps" / "api" / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / "OneDrive" / "Documents" / "GitHub" / "ANUS" / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

# ── Competency map ───────────────────────────────────────────────────────────

COMPETENCY_IDS = {
    "communication": "11111111-1111-1111-1111-111111111111",
    "reliability": "22222222-2222-2222-2222-222222222222",
    "english_proficiency": "33333333-3333-3333-3333-333333333333",
    "leadership": "44444444-4444-4444-4444-444444444444",
    "event_performance": "55555555-5555-5555-5555-555555555555",
    "tech_literacy": "66666666-6666-6666-6666-666666666666",
    "adaptability": "77777777-7777-7777-7777-777777777777",
    "empathy_safeguarding": "88888888-8888-8888-8888-888888888888",
}

# ── LLM call ─────────────────────────────────────────────────────────────────

GENERATION_PROMPT = """You are a professional assessment item writer for VOLAURA, a talent evaluation platform.

Generate {count} multiple-choice questions (MCQ) for the competency "{competency}" at "{difficulty}" difficulty.
{role_context}

Each question MUST follow this EXACT JSON structure (array of objects):
[
  {{
    "scenario_en": "A workplace scenario in English (minimum 30 words, realistic, specific)",
    "scenario_az": "Same scenario translated to Azerbaijani (use proper ə ğ ı ö ü ş ç)",
    "options": [
      {{"key": "option_a", "text_en": "First option", "text_az": "Birinci seçim"}},
      {{"key": "option_b", "text_en": "Second option", "text_az": "İkinci seçim"}},
      {{"key": "option_c", "text_en": "Third option", "text_az": "Üçüncü seçim"}},
      {{"key": "option_d", "text_en": "Fourth option", "text_az": "Dördüncü seçim"}}
    ],
    "correct_answer": "option_a",
    "feedback_en": "Why the correct answer is best (2-3 sentences)",
    "feedback_az": "Niyə düzgün cavab ən yaxşıdır (2-3 cümlə)",
    "development_tip_en": "How to improve this skill (1-2 sentences)",
    "development_tip_az": "Bu bacarığı necə inkişaf etdirmək olar (1-2 cümlə)"
  }}
]

RULES:
- Scenarios must be REALISTIC workplace situations, not textbook definitions
- Options must all be plausible — no obviously wrong answers
- Correct answer should demonstrate the BEST professional behavior
- Difficulty "easy" = clear best choice, "medium" = requires judgment, "hard" = nuanced tradeoffs
- All Azerbaijani text must use proper AZ characters (ə ğ ı ö ü ş ç)
- Return ONLY the JSON array, no markdown, no explanation
"""


def call_gemini(prompt: str) -> str | None:
    """Call Gemini via google-genai REST (free tier)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        resp = json.loads(r.read())
        return resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  Gemini error: {e}", file=sys.stderr)
        return None


def call_nvidia(prompt: str) -> str | None:
    """Call NVIDIA NIM as Gemini fallback."""
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return None

    body = json.dumps({
        "model": "meta/llama-3.1-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 8192,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        resp = json.loads(r.read())
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  NVIDIA error: {e}", file=sys.stderr)
        return None


def call_freellmapi(prompt: str) -> str | None:
    """Call freellmapi gateway (free, 8 models available)."""
    api_key = os.environ.get("FREELLMAPI_API_KEY", "")
    base_url = os.environ.get("FREELLMAPI_BASE_URL", "")
    if not api_key or not base_url:
        return None

    body = json.dumps({
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 8192,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        resp = json.loads(r.read())
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  freellmapi error: {e}", file=sys.stderr)
        return None


def parse_questions(raw: str, competency: str, difficulty: str) -> list[dict]:
    """Parse LLM output into question dicts with all required fields."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        items = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}", file=sys.stderr)
        return []

    if not isinstance(items, list):
        items = [items]

    questions = []
    for item in items:
        q = {
            "id": str(uuid4()),
            "competency_id": COMPETENCY_IDS.get(competency, ""),
            "competency_slug": competency,
            "difficulty": difficulty,
            "type": "mcq",
            "irt_a": 1.0,
            "irt_b": {"easy": -0.5, "medium": 0.0, "hard": 0.5}.get(difficulty, 0.0),
            "irt_c": 0.05,
            "scenario_en": item.get("scenario_en", ""),
            "scenario_az": item.get("scenario_az", ""),
            "options": item.get("options", []),
            "correct_answer": item.get("correct_answer", ""),
            "feedback_en": item.get("feedback_en", ""),
            "feedback_az": item.get("feedback_az", ""),
            "development_tip_en": item.get("development_tip_en", ""),
            "development_tip_az": item.get("development_tip_az", ""),
        }
        if q["competency_id"] and q["scenario_en"] and q["options"]:
            questions.append(q)

    return questions


# ── Validation (reuse the harness) ───────────────────────────────────────────

def validate_question(q: dict) -> tuple[bool, str]:
    """Run the validation harness checks on a single question."""
    errors = []

    # Basic structure
    if not q.get("scenario_en") or len(q["scenario_en"].split()) < 15:
        errors.append("scenario_en too short (<15 words)")
    if not q.get("scenario_az"):
        errors.append("scenario_az missing")
    if not isinstance(q.get("options"), list) or len(q["options"]) < 3:
        errors.append("need >=3 options")
    if q.get("correct_answer") not in [o.get("key") for o in (q.get("options") or [])]:
        errors.append(f"correct_answer '{q.get('correct_answer')}' not in option keys")

    # Option quality
    for opt in q.get("options", []):
        if not opt.get("text_en") or len(opt["text_en"]) < 5:
            errors.append(f"option {opt.get('key')} text_en too short")

    # IRT sanity
    if not (-3 <= q.get("irt_b", 0) <= 3):
        errors.append(f"irt_b={q.get('irt_b')} out of range")
    if not (0.5 <= q.get("irt_a", 1) <= 2.5):
        errors.append(f"irt_a={q.get('irt_a')} out of range")

    # Answer key leak check (ADR-004 line 108)
    for opt in q.get("options", []):
        if "score" in opt or "weight" in opt or "correct" in opt:
            errors.append(f"option {opt.get('key')} leaks answer info")

    return (len(errors) == 0, "; ".join(errors))


# ── Supabase insert ──────────────────────────────────────────────────────────

def insert_to_supabase(questions: list[dict]) -> int:
    """Insert validated questions to prod."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        print("ERROR: SUPABASE_URL/KEY not set", file=sys.stderr)
        return 0

    rows = []
    for q in questions:
        rows.append({
            "id": q["id"],
            "competency_id": q["competency_id"],
            "difficulty": q["difficulty"],
            "type": q["type"],
            "scenario_en": q["scenario_en"],
            "scenario_az": q["scenario_az"],
            "options": q["options"],
            "correct_answer": q["correct_answer"],
            "feedback_en": q.get("feedback_en"),
            "feedback_az": q.get("feedback_az"),
            "development_tip_en": q.get("development_tip_en"),
            "development_tip_az": q.get("development_tip_az"),
            "irt_a": q["irt_a"],
            "irt_b": q["irt_b"],
            "irt_c": q["irt_c"],
            "is_ai_generated": True,
            "calibration_status": "estimated",
            "generation_source": "aig_pipeline",
            "response_count": 0,
            "is_active": True,
        })

    data = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/rest/v1/questions",
        data=data,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=30)
        return len(rows)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"ERROR: Supabase {e.code}: {body}", file=sys.stderr)
        return 0


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate assessment questions via LLM")
    parser.add_argument("--competency", required=True, choices=list(COMPETENCY_IDS.keys()))
    parser.add_argument("--difficulty", default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--role", default=None, help="Optional role context (e.g. scrum_master)")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true", help="Generate + validate, don't insert")
    args = parser.parse_args()

    role_context = f'Target role: {args.role.replace("_", " ")}. Make scenarios specific to this role.' if args.role else ""

    prompt = GENERATION_PROMPT.format(
        count=args.count,
        competency=args.competency,
        difficulty=args.difficulty,
        role_context=role_context,
    )

    print(f"Generating {args.count} {args.difficulty} questions for {args.competency}...")
    raw = call_gemini(prompt)
    if not raw:
        print("  Gemini failed, trying NVIDIA NIM...")
        raw = call_nvidia(prompt)
    if not raw:
        print("  NVIDIA failed, trying freellmapi...")
        raw = call_freellmapi(prompt)
    if not raw:
        print("ERROR: All LLM providers failed", file=sys.stderr)
        sys.exit(1)

    questions = parse_questions(raw, args.competency, args.difficulty)
    print(f"  Parsed: {len(questions)} questions from LLM output")

    # Validate each
    passed = []
    for i, q in enumerate(questions):
        ok, errs = validate_question(q)
        status = "PASS" if ok else f"FAIL: {errs}"
        print(f"  [{i+1}] {status}")
        if ok:
            passed.append(q)

    print(f"\nValidated: {len(passed)}/{len(questions)} pass")

    if not passed:
        print("No questions passed validation.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"\n[DRY RUN] {len(passed)} questions ready. Run without --dry-run to insert.")
        # Save to file for inspection
        out = Path(f"scripts/generated-{args.competency}-{args.difficulty}.json")
        out.write_text(json.dumps(passed, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved to {out}")
        return

    inserted = insert_to_supabase(passed)
    print(f"\nInserted {inserted} questions (generation_source=aig_pipeline, calibration_status=estimated)")


if __name__ == "__main__":
    main()
