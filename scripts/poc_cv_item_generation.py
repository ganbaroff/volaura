"""PoC: CV-grounded assessment item generation (ADR-017 Experience Interview layer).

Reads a candidate CV (plain text), generates situational-judgment items grounded
in the CV's SPECIFIC claims, mapped to VOLAURA's 8 competencies. Output = strict
JSON to stdout-file. Provider: Groq free tier (money rules: credits/free first).

Usage:
    python scripts/poc_cv_item_generation.py --cv /path/to/cv.txt --out items.json
    (GROQ_API_KEY read from env or apps/api/.env — value never printed)

This is the PoC for the production pipeline described in
docs/adr/ADR-017-cv-grounded-item-generation.md. Production version moves into
apps/api/app/services/item_generation.py behind the reeval_worker pattern.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # Groq free tier

COMPETENCIES = {
    "communication": "clear, audience-adapted information exchange under pressure",
    "reliability": "follow-through, deadline discipline, ownership of commitments",
    "english_proficiency": "professional English comprehension and expression",
    "leadership": "directing, motivating and developing people without/with authority",
    "event_performance": "on-site operational execution: venues, crowds, vendors, protocol",
    "tech_literacy": "competent use of digital tools, data accuracy, troubleshooting",
    "adaptability": "effective response to change, ambiguity and setbacks",
    "empathy_safeguarding": "care for people's wellbeing, de-escalation, safeguarding",
}

SYSTEM_PROMPT = """You are a senior psychometric item writer for VOLAURA, a verified \
professional talent platform. You write situational-judgment test items for the \
EXPERIENCE INTERVIEW layer: items grounded in the candidate's OWN CV claims, used to \
verify claimed experience (NOT for the calibrated comparable score).

Item-writing standards (Duolingo English Test-style AIG, human-review pending):
- Each item must be grounded in ONE specific, verifiable claim from the CV (name it).
- Scenario: second person, professional register, realistic detail consistent with the claim, 2-4 sentences.
- MCQ: exactly 4 options A-D. One clearly best per the competency rubric. Distractors plausible \
(things a less-experienced person would genuinely pick), never absurd, similar length.
- A person who actually DID what the CV claims should find the item familiar; a person who \
faked the claim should struggle. Probe specifics (scale, tools, stakeholders, sequencing).
- No trivia, no gotchas, no culture-specific knowledge beyond the CV's own context.
- Difficulty: easy = routine judgment; medium = competing priorities; hard = trade-off under \
pressure with stakeholder cost either way.
Return STRICT JSON only, no markdown fences."""


def build_user_prompt(cv_text: str) -> str:
    comp_lines = "\n".join(f"- {k}: {v}" for k, v in COMPETENCIES.items())
    return f"""CANDIDATE CV:
---
{cv_text}
---

COMPETENCY MODEL (use these slugs only):
{comp_lines}

TASK: Generate 8 items: 7 MCQ + 1 open-ended. Cover at least 5 different competencies.
Every item grounded in a DIFFERENT specific CV claim.

Output JSON schema:
{{"items": [{{
  "competency": "<slug>",
  "grounded_claim": "<verbatim-ish CV fact this item probes>",
  "type": "mcq" | "open",
  "scenario_en": "<the situational item text>",
  "options": [{{"key": "A", "text_en": "..."}}, ... 4 options]  (mcq only),
  "correct_answer": "A|B|C|D"  (mcq only),
  "expected_concepts": ["concept_token", ...]  (open only, 4-6 snake_case tokens),
  "rationale": "<why the correct option is best / what the open answer must show>",
  "difficulty": "easy|medium|hard",
  "suggested_irt_b": <float -1.5..1.5>
}}]}}"""


def load_groq_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    for env_path in (
        os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env"),
        "C:/Projects/VOLAURA/apps/api/.env",
    ):
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except OSError:
            continue
    raise SystemExit("GROQ_API_KEY not found (env or apps/api/.env)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", required=True, help="path to plain-text CV")
    ap.add_argument("--out", required=True, help="path to write generated items JSON")
    args = ap.parse_args()

    with open(args.cv, encoding="utf-8") as f:
        cv_text = f.read()

    payload = {
        "model": MODEL,
        "temperature": 0.7,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(cv_text)},
        ],
    }
    req = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {load_groq_key()}",
            # Cloudflare bot-blocks urllib's default UA with 403 (verified 2026-06-10);
            # a browser UA is required even with a valid key.
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VOLAURA-AIG-PoC/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    items = json.loads(content)  # raises if model broke JSON — PoC fails loudly
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    n = len(items.get("items", []))
    comps = sorted({i.get("competency", "?") for i in items.get("items", [])})
    print(f"OK: {n} items written to {args.out}")
    print(f"competencies covered: {', '.join(comps)}")
    print(f"model: {body.get('model', MODEL)}; usage: {json.dumps(body.get('usage', {}))}")


if __name__ == "__main__":
    main()
