"""FIX-2 step 1: export all servable questions from prod to local JSON files.

Writes one file per competency (for parallel translation agents) + a master file.
Output dir: %TEMP%/claude/fix2/. Keys from apps/api/.env; values never printed.
"""

from __future__ import annotations

import json
import os
import urllib.request

OUT_DIR = "C:/Users/user/AppData/Local/Temp/claude/fix2"
UA = "volaura-fix2-export/0.1"


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in (
        os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env"),
        "C:/Projects/VOLAURA/apps/api/.env",
    ):
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        out.setdefault(k.strip(), v.strip())
        except OSError:
            continue
    return out


def main() -> None:
    env = load_env()
    url = env["SUPABASE_URL"].rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_SERVICE_KEY"]
    req = urllib.request.Request(
        f"{url}/rest/v1/questions"
        "?select=id,type,scenario_en,scenario_az,scenario_ru,options,competencies(slug)"
        "&is_active=eq.true&needs_review=eq.false&order=id",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        rows = json.loads(r.read().decode("utf-8"))

    os.makedirs(OUT_DIR, exist_ok=True)
    by_comp: dict[str, list] = {}
    for row in rows:
        slug = (row.get("competencies") or {}).get("slug", "unknown")
        row["competency_slug"] = slug
        row.pop("competencies", None)
        by_comp.setdefault(slug, []).append(row)

    for slug, items in by_comp.items():
        with open(f"{OUT_DIR}/{slug}.json", "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    with open(f"{OUT_DIR}/_all.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    print(f"exported {len(rows)} questions into {len(by_comp)} files:")
    for slug, items in sorted(by_comp.items()):
        ru_missing = sum(1 for i in items if not (i.get("scenario_ru") or "").strip())
        print(f"  {slug}: {len(items)} items, ru_missing={ru_missing}")


if __name__ == "__main__":
    main()
