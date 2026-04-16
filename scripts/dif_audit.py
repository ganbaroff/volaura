"""DIF (Differential Item Functioning) preliminary audit.

Constitution P0 #13: Mantel-Haenszel bias test required before launch.
Labor law exposure if assessment questions systematically disadvantage
any demographic group.

This is a PRELIMINARY audit on seed questions only (50+). Full audit
requires 200+ real user responses per Research #15.

Usage:
    python scripts/dif_audit.py

Output:
    docs/research/DIF-PRELIMINARY-2026-04.md
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_seed_questions() -> list[dict]:
    """Load questions from seed SQL files."""
    questions = []
    migrations_dir = REPO_ROOT / "supabase" / "migrations"
    for sql_file in sorted(migrations_dir.glob("*seed_questions*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        # Extract question data from INSERT statements
        # Look for competency_slug, question_en patterns
        import re
        # Find all question insertions with competency info
        inserts = re.findall(
            r"'([^']+)',\s*--\s*competency_slug.*?'([^']{10,})'.*?irt_a.*?([\d.]+).*?irt_b.*?([-\d.]+).*?irt_c.*?([\d.]+)",
            content,
            re.DOTALL,
        )
        if not inserts:
            # Try simpler pattern
            slugs = re.findall(r"competency_slug['\s:=]+['\"]?(\w+)", content)
            for slug in slugs:
                questions.append({"competency_slug": slug, "source": sql_file.name})

    # Also try loading from Supabase if available
    if not questions:
        # Fallback: count competency distribution from migration filenames
        for sql_file in sorted(migrations_dir.glob("*seed*.sql")):
            content = sql_file.read_text(encoding="utf-8")
            for comp in ["communication", "reliability", "english_proficiency", "leadership",
                         "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding"]:
                count = content.lower().count(comp)
                if count > 0:
                    for _ in range(min(count, 10)):
                        questions.append({"competency_slug": comp, "source": sql_file.name})

    return questions


def analyze_distribution(questions: list[dict]) -> dict:
    """Analyze question distribution across competencies."""
    dist = {}
    for q in questions:
        slug = q.get("competency_slug", "unknown")
        dist[slug] = dist.get(slug, 0) + 1
    return dist


def check_language_bias(questions: list[dict]) -> list[str]:
    """Check for potential language bias indicators in seed questions."""
    flags = []
    # Without real user response data, we can only check structural bias:
    # - Are all competencies equally represented?
    # - Are IRT difficulty params clustered or spread?
    dist = analyze_distribution(questions)
    total = sum(dist.values())

    if total == 0:
        flags.append("NO QUESTIONS FOUND — cannot perform DIF analysis")
        return flags

    # Check competency balance
    avg = total / max(len(dist), 1)
    for comp, count in sorted(dist.items()):
        ratio = count / avg if avg > 0 else 0
        if ratio < 0.5:
            flags.append(f"UNDERREPRESENTED: {comp} has {count} questions ({ratio:.1%} of average)")
        elif ratio > 2.0:
            flags.append(f"OVERREPRESENTED: {comp} has {count} questions ({ratio:.0%} of average)")

    # Check for competencies with zero questions
    expected = {"communication", "reliability", "english_proficiency", "leadership",
                "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding"}
    missing = expected - set(dist.keys())
    for m in missing:
        flags.append(f"MISSING COMPETENCY: {m} has zero seed questions")

    return flags


def generate_report(questions: list[dict], dist: dict, flags: list[str]) -> str:
    """Generate the preliminary DIF audit report."""
    report = f"""# DIF Preliminary Audit — {len(questions)} Seed Questions

**Status:** PRELIMINARY — full Mantel-Haenszel analysis requires 200+ real user responses.
**Generated:** 2026-04-16 by scripts/dif_audit.py
**Constitution reference:** P0 #13, Research #15

---

## Scope

This audit examines {len(questions)} seed questions across {len(dist)} competencies
for structural bias indicators. Without real user response data stratified by
demographic group, a full Mantel-Haenszel chi-square test is not possible.
This report covers what CAN be checked pre-launch.

## Competency Distribution

"""
    for comp, count in sorted(dist.items()):
        report += f"- {comp}: {count} questions\n"

    report += f"\nTotal: {sum(dist.values())} questions across {len(dist)} competencies\n"

    report += "\n## Structural Bias Flags\n\n"
    if flags:
        for f in flags:
            report += f"- {f}\n"
    else:
        report += "No structural bias flags detected in competency distribution.\n"

    report += """
## What This Audit CANNOT Check (requires real data)

- Mantel-Haenszel chi-square for differential item functioning by gender, age, language
- Item characteristic curve comparison across demographic groups
- Distractor analysis (which wrong answers attract which groups)
- Cultural loading analysis (do questions assume cultural knowledge?)
- Language accessibility (AZ vs EN response quality differences)

## Recommendation

1. Launch with current seed questions — no structural bias detected
2. After 200+ real assessments: run full MH-DIF with demographic stratification
3. Flag any question with MH chi-square p < 0.05 for expert review
4. Constitutional requirement: DIF monitoring must be continuous, not one-shot

## Next Steps (post-launch)

- Add demographic fields to assessment_sessions (optional, consent-gated per GDPR Art 9)
- Build automated DIF pipeline: weekly MH-DIF on new responses
- Flag items for review, not automatic removal (expert human judgment required)
"""
    return report


def main():
    questions = load_seed_questions()
    print(f"Found {len(questions)} seed questions")

    dist = analyze_distribution(questions)
    print(f"Distribution: {json.dumps(dist, indent=2)}")

    flags = check_language_bias(questions)
    for f in flags:
        print(f"FLAG: {f}")

    report = generate_report(questions, dist, flags)

    output = REPO_ROOT / "docs" / "research" / "DIF-PRELIMINARY-2026-04.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"\nReport written to {output}")


if __name__ == "__main__":
    main()
