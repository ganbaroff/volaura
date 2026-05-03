#!/usr/bin/env python3
"""S2-G1: Journal rotation — keep current month, archive older entries.

Moves journal entries older than current month to:
  memory/atlas/archive/journal-YYYY-MM.md

Keeps header (lines before first ## entry) + current month entries inline.
Target: journal.md never exceeds ~30KB after rotation.

Usage:
  python scripts/rotate_journal.py              # dry-run (show what would move)
  python scripts/rotate_journal.py --execute    # actually rotate
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOURNAL = REPO / "memory" / "atlas" / "journal.md"
ARCHIVE_DIR = REPO / "memory" / "atlas" / "archive"

ENTRY_RE = re.compile(r"^## (\d{4}-\d{2})-\d{2}", re.MULTILINE)


def main():
    execute = "--execute" in sys.argv

    if not JOURNAL.exists():
        print("journal.md not found")
        return

    text = JOURNAL.read_text(encoding="utf-8")
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # Split into header + entries
    first_entry = ENTRY_RE.search(text)
    if not first_entry:
        print("No entries found")
        return

    header = text[: first_entry.start()]
    body = text[first_entry.start() :]

    # Split body into individual entries
    entries = []
    for match in ENTRY_RE.finditer(text):
        entries.append((match.start(), match.group(1)))

    # Group by month
    months: dict[str, list[str]] = {}
    for i, (start, month) in enumerate(entries):
        end = entries[i + 1][0] if i + 1 < len(entries) else len(text)
        chunk = text[start:end]
        months.setdefault(month, []).append(chunk)

    # Separate current vs old
    current_entries = months.pop(current_month, [])
    old_months = sorted(months.keys())

    if not old_months:
        print(f"Nothing to rotate — all entries are from {current_month}")
        return

    old_size = sum(len(c) for m in old_months for c in months[m])
    print(f"Current month ({current_month}): {len(current_entries)} entries")
    print(f"Old months to archive: {len(old_months)} ({old_size:,} bytes)")
    for m in old_months:
        print(f"  {m}: {len(months[m])} entries")

    if not execute:
        print("\nDry run. Pass --execute to rotate.")
        return

    # Archive old entries by month
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for month_key in old_months:
        archive_path = ARCHIVE_DIR / f"journal-{month_key}.md"
        content = f"# Journal Archive — {month_key}\n\n"
        content += "\n".join(months[month_key])
        if archive_path.exists():
            # Append to existing archive
            existing = archive_path.read_text(encoding="utf-8")
            content = existing.rstrip() + "\n\n" + "\n".join(months[month_key])
        archive_path.write_text(content, encoding="utf-8")
        print(f"  Archived -> {archive_path.name}")

    # Rewrite journal with header + current month only
    new_journal = header
    if current_entries:
        new_journal += "\n".join(current_entries)
    else:
        new_journal += f"## {current_month} — (rotated, no entries yet)\n"

    JOURNAL.write_text(new_journal, encoding="utf-8")
    new_size = len(new_journal.encode("utf-8"))
    print(f"\njournal.md: {old_size + len(header):,} -> {new_size:,} bytes")


if __name__ == "__main__":
    main()
