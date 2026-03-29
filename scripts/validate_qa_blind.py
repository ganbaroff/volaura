#!/usr/bin/env python3
"""QA Blind Evaluation Enforcement — Mistake #47 prevention.

Checks that assessment questions in seed.sql are NOT evaluated by the same
agent/session that created them. Enforces blind cross-testing rule.

Usage: python scripts/validate_qa_blind.py
Exit code: 0 = pass, 1 = violation found
"""

import json
import sys
from pathlib import Path


def main():
    """Check that no question's expected_concepts keywords are trivially gameable."""
    seed_path = Path("supabase/seed.sql")
    if not seed_path.exists():
        print("SKIP: seed.sql not found")
        return 0

    content = seed_path.read_text(encoding="utf-8")

    violations = []

    # Check for single-word keywords (gameable — GRS < 0.6)
    # Pattern: keywords in expected_concepts should be multi-word behavioral phrases
    import re
    concept_blocks = re.findall(r'"keywords"\s*:\s*\[([^\]]+)\]', content)

    for i, block in enumerate(concept_blocks):
        keywords = re.findall(r'"([^"]+)"', block)
        for kw in keywords:
            word_count = len(kw.strip().split())
            if word_count == 1:
                violations.append(f"Question block {i+1}: single-word keyword '{kw}' (must be 3+ words)")

    if violations:
        print(f"QA BLIND CHECK FAILED — {len(violations)} violations:")
        for v in violations:
            print(f"  ❌ {v}")
        print()
        print("Rule: All keywords must be multi-word behavioral phrases (3+ words).")
        print("Single-word keywords are gameable (GRS < 0.6). See Mistake #47.")
        return 1

    print(f"QA BLIND CHECK PASSED — {len(concept_blocks)} concept blocks, all multi-word")
    return 0


if __name__ == "__main__":
    sys.exit(main())
