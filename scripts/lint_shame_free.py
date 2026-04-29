#!/usr/bin/env python3
"""Lint locale files for Constitution Law 3 (Shame-Free Language) violations.

Usage:
  python scripts/lint_shame_free.py              # exits 1 if violations found
  python scripts/lint_shame_free.py --fix-hints  # also prints suggested fixes

Add to CI:
  - name: Shame-free language check
    run: python scripts/lint_shame_free.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALE_DIR = REPO_ROOT / "apps" / "web" / "src" / "locales"

# Constitution Law 3 banned patterns (EN)
# Each: (pattern, reason, severity)
BANNED_EN = [
    (r"\byou haven'?t\b", "Shame: 'you haven't done X'", "BLOCK"),
    (r"\byou have not\b", "Shame: 'you have not done X'", "BLOCK"),
    (r"\bprofile\s+\d+%\s*complete\b", "Shame: progress % on profile", "BLOCK"),
    (r"\b\d+%\s*complete\b", "Shame: progress % display", "WARN"),
    (r"\byou'?re\s+\w+\s+behind\b", "Shame: 'you're X behind'", "BLOCK"),
    (r"\bdays?\s+behind\b", "Shame: days behind", "BLOCK"),
    (r"\byou failed\b", "Shame: 'you failed'", "BLOCK"),
    (r"\bwrong answer\b", "Shame: 'wrong answer'", "BLOCK"),
    (r"\bremaining\b", "Law 3: show 'completed' not 'remaining'", "WARN"),
    (r"\b0 of \d+\b", "Shame: '0 of X completed'", "BLOCK"),
    (r"\byou should\b", "Directive language", "WARN"),
    (r"\bdanger\b", "Law 1: no red/danger language", "WARN"),
]

# Exemptions: keys where certain patterns are OK
EXEMPTIONS = {
    "remaining": {"assessment.timeRemaining", "timer"},  # countdown timer OK
    "streak": {"tribe.streak", "dashboard.streak"},  # tribe streaks approved if 0/1 hidden
}


def scan_locale(path: Path, patterns: list) -> list[tuple[str, str, str, str]]:
    """Returns list of (key, value_snippet, pattern, severity)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    violations = []

    def walk(obj: object, prefix: str = "") -> None:
        if isinstance(obj, str):
            for pat, reason, sev in patterns:
                if re.search(pat, obj, re.IGNORECASE):
                    # Check exemptions
                    pat_key = pat.split(r"\b")[1] if r"\b" in pat else pat
                    exempt_keys = EXEMPTIONS.get(pat_key, set())
                    if any(prefix.lstrip(".").startswith(ek) for ek in exempt_keys):
                        continue
                    violations.append((prefix.lstrip("."), obj[:80], reason, sev))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{prefix}.{k}")

    walk(data)
    return violations


def main() -> int:
    exit_code = 0

    for locale_dir in sorted(LOCALE_DIR.iterdir()):
        if not locale_dir.is_dir():
            continue
        for json_file in sorted(locale_dir.glob("*.json")):
            violations = scan_locale(json_file, BANNED_EN)
            if violations:
                rel = json_file.relative_to(REPO_ROOT)
                for key, val, reason, sev in violations:
                    marker = "BLOCK" if sev == "BLOCK" else "WARN"
                    print(f"[{marker}] {rel}:{key} — {reason}")
                    print(f"         \"{val}\"")
                    if sev == "BLOCK":
                        exit_code = 1

    if exit_code == 0:
        print("Shame-free language check: PASS")
    else:
        print("\nShame-free language check: FAIL — fix BLOCK items above")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
