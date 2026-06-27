#!/usr/bin/env python
"""VOLAURA question-bank validation harness — deterministic proof of structural
correctness + calibration sanity for every question, before it can reach prod.

This is the foundation of the "prove the questions are right" requirement
(CEO directive 2026-06-13: nothing ships until questions are proven correct,
calibrated, and agent-validated). It runs WITHOUT LLM cost — pure static checks
— so it scales to the whole bank and any generated batch, and it can gate CI.

It validates BOTH question paradigms:
  - keyword/concept (seed bank): expected_concepts + GRS via app.core.assessment.quality_gate
  - rubric/london_delta (question-evolution agent-generated): 5-level evaluation_rubric

and CROSS-CHECKS the deterministic pass-rate against the agents' voting-results
scores, so "agents said 96/100" is confirmed (or contradicted) by hard checks.

Run (UTF-8 forced for Azerbaijani ə ğ ı ö ü ş ç on Windows):
    PYTHONUTF8=1 python scripts/validate_question_bank.py
    PYTHONUTF8=1 python scripts/validate_question_bank.py --sprint sprint-5
    PYTHONUTF8=1 python scripts/validate_question_bank.py --json report.json

Exit code 0 only if every question passes every applicable check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 stdout — the seed audit crashed on cp1252 for every AZ glyph.
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

# Silence the production quality_gate's DEBUG/WARNING stream — it floods the proof.
try:
    from loguru import logger as _loguru

    _loguru.remove()
    _loguru.add(sys.stderr, level="ERROR")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
EVO = REPO / "scripts" / "question-evolution"

VALID_COMPETENCIES = {
    "communication", "reliability", "english_proficiency", "leadership",
    "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding",
}
RUBRIC_LEVELS = [f"level_{i}" for i in range(1, 6)]
# Per-option fields that must NEVER reach a candidate's browser (answer key leak,
# the 2026-06-13 bug: 22 seed MCQ rows shipped per-option `score`).
LEAKY_OPTION_FIELDS = {"score", "weight", "correct", "is_correct", "value"}


def check_question(q: dict) -> list[str]:
    """Return a list of failure strings; empty list == passes."""
    fails: list[str] = []
    qtype = q.get("type")

    # ── universal ────────────────────────────────────────────────────────────
    if not (q.get("scenario_en") or q.get("question_en")):
        fails.append("no scenario_en")
    if not (q.get("scenario_az") or q.get("question_az")):
        fails.append("no scenario_az (AZ-first platform)")
    slug = q.get("competency_slug")
    if slug not in VALID_COMPETENCIES:
        fails.append(f"competency_slug invalid: {slug!r}")

    # ── IRT calibration sanity (params present + in 3PL-valid ranges) ─────────
    a, b, c = q.get("irt_a"), q.get("irt_b"), q.get("irt_c")
    if not isinstance(a, (int, float)) or not (0.3 <= a <= 3.0):
        fails.append(f"irt_a out of range [0.3,3.0]: {a}")
    if not isinstance(b, (int, float)) or not (-4.0 <= b <= 4.0):
        fails.append(f"irt_b out of range [-4,4]: {b}")
    if not isinstance(c, (int, float)) or not (0.0 <= c <= 0.35):
        fails.append(f"irt_c out of range [0,0.35]: {c}")

    # MCQ and SJT (Situational Judgment Test) are structurally identical for
    # validation: option list with keys + a best-answer key + guessing>0.
    if qtype in ("mcq", "sjt"):
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) < 3:
            fails.append(f"{qtype} needs >=3 options")
        else:
            keys = []
            for i, o in enumerate(opts):
                if not isinstance(o, dict):
                    fails.append(f"option {i} not an object")
                    continue
                leaked = LEAKY_OPTION_FIELDS & set(o)
                if leaked:
                    fails.append(f"option {o.get('key', i)} LEAKS answer key field(s): {sorted(leaked)}")
                if not (o.get("text_en") or o.get("text")):
                    fails.append(f"option {o.get('key', i)} has no text_en")
                keys.append(str(o.get("key") or o.get("id") or ""))
            ca = q.get("correct_answer")
            if not ca:
                fails.append(f"{qtype} has no correct_answer / best option")
            elif str(ca) not in keys:
                fails.append(f"correct_answer {ca!r} not among option keys {keys}")
        if isinstance(c, (int, float)) and c == 0.0:
            fails.append(f"{qtype} irt_c==0 (option-based items have guessing ~0.12-0.25)")

    elif qtype == "open_ended":
        # Two valid open-ended evaluation models:
        #  (a) rubric/london_delta (agent-generated)  (b) expected_concepts (seed)
        rubric = q.get("evaluation_rubric")
        concepts = q.get("expected_concepts")
        if isinstance(rubric, dict) and rubric:
            missing = [lv for lv in RUBRIC_LEVELS if not str(rubric.get(lv, "")).strip()]
            if missing:
                fails.append(f"evaluation_rubric missing/empty levels: {missing}")
            if not str(q.get("london_delta", "")).strip():
                fails.append("rubric question has no london_delta reference answer")
        elif concepts:
            fails.extend(_check_concept_question(q))
        else:
            fails.append("open_ended has neither evaluation_rubric nor expected_concepts")
        if isinstance(c, (int, float)) and c != 0.0:
            fails.append(f"open_ended irt_c should be 0 (no guessing), got {c}")
    else:
        fails.append(f"unknown type: {qtype!r}")

    return fails


def _check_concept_question(q: dict) -> list[str]:
    """Run the production quality gate (GRS + adversarial + 10-point) on a
    concept/keyword question. Imported lazily so the harness still runs for the
    rubric corpus even if the API package isn't importable."""
    try:
        sys.path.insert(0, str(REPO / "apps" / "api"))
        from app.core.assessment.quality_gate import run_quality_checklist
    except Exception as e:  # pragma: no cover
        return [f"(quality_gate unavailable, concept checks skipped: {e})"]
    try:
        res = run_quality_checklist(q)
    except Exception as e:
        return [f"quality_gate raised: {e}"]
    if res.get("passed"):
        return []
    failed = [c["name"] for c in res.get("checks", []) if not c.get("passed")]
    return [f"quality_gate fail: {failed}"]


def validate_dir(sprint_dir: Path) -> dict:
    """Validate every role file in a sprint dir; return a structured report."""
    voting = {}
    vr = sprint_dir / "voting-results.json"
    if vr.exists():
        try:
            voting = json.loads(vr.read_text(encoding="utf-8")).get("scores", {})
        except Exception:
            voting = {}

    roles = {}
    for f in sorted(sprint_dir.glob("*.json")):
        if f.name.startswith("voting"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            roles[f.stem] = {"error": f"unparseable: {e}", "total": 0, "passed": 0, "failures": []}
            continue
        # Role files are either a bare list or a {questions:[...]} / {items:[...]} wrapper.
        if isinstance(data, dict):
            questions = data.get("questions") or data.get("items") or data.get("output") or []
        else:
            questions = data
        if not isinstance(questions, list) or not questions:
            roles[f.stem] = {"error": "no question list found", "total": 0, "passed": 0, "failures": []}
            continue
        failures = []
        passed = 0
        for q in questions:
            fails = check_question(q)
            if fails:
                failures.append({"id": q.get("id", "?"), "fails": fails})
            else:
                passed += 1
        agent_total = (voting.get(f.stem) or {}).get("total")
        roles[f.stem] = {
            "total": len(questions),
            "passed": passed,
            "failed": len(failures),
            "agent_score": agent_total,
            "failures": failures,
        }
    return roles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprint", default=None, help="single sprint dir name, e.g. sprint-5")
    ap.add_argument("--json", default=None, help="write full report to this path")
    args = ap.parse_args()

    sprint_dirs = (
        [EVO / args.sprint] if args.sprint else sorted(EVO.glob("sprint-*"))
    )
    report = {}
    grand_total = grand_pass = 0
    for sd in sprint_dirs:
        if not sd.is_dir():
            continue
        roles = validate_dir(sd)
        report[sd.name] = roles
        for role, r in roles.items():
            grand_total += r.get("total", 0)
            grand_pass += r.get("passed", 0)

    # ── human-readable proof ──────────────────────────────────────────────────
    print("=" * 72)
    print("VOLAURA — Question Bank Validation Harness (deterministic, no LLM)")
    print("=" * 72)
    for sprint, roles in report.items():
        print(f"\n■ {sprint}")
        for role, r in sorted(roles.items()):
            if r.get("error"):
                print(f"  ✗ {role:26s} ERROR: {r['error']}")
                continue
            mark = "✓" if r["failed"] == 0 else "✗"
            agent = f"agent {r['agent_score']}/100" if r.get("agent_score") is not None else "agent —"
            print(f"  {mark} {role:26s} {r['passed']:>2}/{r['total']:<2} pass · {agent}")
            for fail in r["failures"]:
                for msg in fail["fails"]:
                    print(f"        ! {fail['id']}: {msg}")

    pct = (grand_pass / grand_total * 100) if grand_total else 0.0
    print("\n" + "-" * 72)
    print(f"TOTAL: {grand_pass}/{grand_total} questions pass all applicable checks ({pct:.1f}%)")
    print("NOTE: IRT params here are LLM-ESTIMATED, not empirically calibrated.")
    print("      Empirical calibration needs real response data (see ADR-004 / "
          "dynamic-assessment-engine research §6).")
    print("-" * 72)

    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Full report → {args.json}")

    return 0 if grand_pass == grand_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
