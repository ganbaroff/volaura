#!/usr/bin/env python3
"""DIF Bias Audit — Mantel-Haenszel analysis for VOLAURA assessments.

Pre-launch blocker #7: detect items biased against subgroups.
Groups by language (en/az) and role_level when demographic data is available.

Usage:
  python scripts/audit_dif_bias.py                     # against prod Supabase
  python scripts/audit_dif_bias.py --supabase-url=...  # custom instance

Output: CSV with flagged items (|delta_MH| > 1.5) + summary.

Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY in apps/api/.env
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load .env
_env_file = REPO_ROOT / "apps" / "api" / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"")
            if k and v and k not in os.environ:
                os.environ[k] = v


THRESHOLD = 1.5  # |delta_MH| above this = flagged


def _compute_mantel_haenszel(
    focal_correct: int, focal_total: int,
    ref_correct: int, ref_total: int,
) -> float | None:
    """Compute Mantel-Haenszel delta for one item in one stratum.

    Returns log-odds ratio. Positive = easier for focal group.
    None if insufficient data.
    """
    if focal_total < 5 or ref_total < 5:
        return None

    focal_incorrect = focal_total - focal_correct
    ref_incorrect = ref_total - ref_correct

    # Avoid division by zero
    if ref_correct == 0 or focal_incorrect == 0:
        return None
    if focal_correct == 0 or ref_incorrect == 0:
        return None

    odds_ratio = (focal_correct * ref_incorrect) / (focal_incorrect * ref_correct)
    try:
        return -2.35 * math.log(odds_ratio)  # ETS delta scale
    except (ValueError, ZeroDivisionError):
        return None


def fetch_assessment_data() -> list[dict]:
    """Fetch completed assessment sessions with answers from Supabase."""
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase-py not installed. Run: pip install supabase")
        sys.exit(1)

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY required in apps/api/.env")
        sys.exit(1)

    client = create_client(url, key)

    # Fetch completed sessions with answers and grouping variables
    result = (
        client.table("assessment_sessions")
        .select("id, volunteer_id, competency_id, language, role_level, answers")
        .eq("status", "completed")
        .execute()
    )

    return result.data or []


def analyze_dif(sessions: list[dict], group_field: str = "language") -> list[dict]:
    """Run Mantel-Haenszel DIF analysis grouped by a field.

    Returns list of items with their delta_MH values.
    """
    # Build per-question response table
    # question_id -> group_value -> {correct: N, total: N}
    item_stats: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"correct": 0, "total": 0})
    )

    for session in sessions:
        group = session.get(group_field) or "unknown"
        answers = session.get("answers", [])
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except Exception:
                continue
        if not isinstance(answers, list):
            continue

        for ans in answers:
            if not isinstance(ans, dict):
                continue
            qid = ans.get("question_id", "")
            if not qid:
                continue
            item_stats[qid][group]["total"] += 1
            # Score > 0 = "correct" for DIF purposes
            score = ans.get("irt_score", ans.get("score", 0))
            if isinstance(score, (int, float)) and score > 0:
                item_stats[qid][group]["correct"] += 1

    # Determine reference group (largest N)
    all_groups: dict[str, int] = defaultdict(int)
    for qid_data in item_stats.values():
        for g, stats in qid_data.items():
            all_groups[g] += stats["total"]

    if len(all_groups) < 2:
        print(f"WARNING: Only {len(all_groups)} group(s) for '{group_field}'. DIF requires 2+.")
        return []

    ref_group = max(all_groups, key=lambda g: all_groups[g])
    focal_groups = [g for g in all_groups if g != ref_group]

    results = []
    for qid, groups in item_stats.items():
        ref = groups.get(ref_group, {"correct": 0, "total": 0})

        for focal_name in focal_groups:
            focal = groups.get(focal_name, {"correct": 0, "total": 0})

            delta = _compute_mantel_haenszel(
                focal["correct"], focal["total"],
                ref["correct"], ref["total"],
            )

            results.append({
                "question_id": qid,
                "group_field": group_field,
                "reference_group": ref_group,
                "focal_group": focal_name,
                "ref_correct": ref["correct"],
                "ref_total": ref["total"],
                "focal_correct": focal["correct"],
                "focal_total": focal["total"],
                "delta_MH": round(delta, 3) if delta is not None else None,
                "flagged": abs(delta) > THRESHOLD if delta is not None else False,
                "classification": (
                    "A (negligible)" if delta is not None and abs(delta) <= 1.0
                    else "B (moderate)" if delta is not None and abs(delta) <= 1.5
                    else "C (large)" if delta is not None
                    else "insufficient_data"
                ),
            })

    return results


def main() -> int:
    print("DIF Bias Audit — Mantel-Haenszel Analysis")
    print("=" * 50)

    sessions = fetch_assessment_data()
    print(f"Fetched {len(sessions)} completed sessions")

    if len(sessions) < 30:
        print(f"WARNING: {len(sessions)} sessions is below minimum 30 for reliable DIF analysis.")
        print("Results are illustrative only. Need 300+ for publishable findings.")

    output_path = REPO_ROOT / "memory" / "swarm" / "dif_audit_results.csv"
    all_results = []

    for group_field in ["language", "role_level"]:
        results = analyze_dif(sessions, group_field)
        all_results.extend(results)

        flagged = [r for r in results if r["flagged"]]
        insufficient = [r for r in results if r["classification"] == "insufficient_data"]

        print(f"\nGroup: {group_field}")
        print(f"  Items analyzed: {len(results)}")
        print(f"  Insufficient data: {len(insufficient)}")
        print(f"  Flagged (|delta| > {THRESHOLD}): {len(flagged)}")
        for f in flagged:
            print(f"    {f['question_id'][:8]}... delta={f['delta_MH']} "
                  f"({f['focal_group']} vs {f['reference_group']})")

    # Write CSV
    if all_results:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\nResults written to: {output_path.relative_to(REPO_ROOT)}")

    flagged_count = sum(1 for r in all_results if r["flagged"])
    if flagged_count > 0:
        print(f"\nVERDICT: {flagged_count} items flagged — review before launch")
        return 1
    else:
        print("\nVERDICT: No items flagged — DIF check PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
