"""FIX-2 step 3: apply RU translations to prod via PostgREST PATCH (one row at a time).

Reads _ru_payload.json ({id, scenario_ru, options?}) and PATCHes each questions row
with the service key. Keeps the migration SQL out of the agent context (200KB).
Prints per-row status; exits non-zero if any row fails. Keys from apps/api/.env.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

PAYLOAD = "C:/Users/user/AppData/Local/Temp/claude/fix2/_ru_payload.json"
UA = "volaura-fix2-apply/0.1"


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
    base = env["SUPABASE_URL"].rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_SERVICE_KEY"]
    with open(PAYLOAD, encoding="utf-8") as f:
        rows = json.load(f)

    ok = 0
    fails: list[str] = []
    for row in rows:
        qid = row["id"]
        body = {"scenario_ru": row["scenario_ru"]}
        if "options" in row:
            body["options"] = row["options"]
        req = urllib.request.Request(
            f"{base}/rest/v1/questions?id=eq.{qid}",
            data=json.dumps(body).encode("utf-8"),
            method="PATCH",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
                "User-Agent": UA,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status in (200, 204):
                    ok += 1
                else:
                    fails.append(f"{qid}:{r.status}")
        except urllib.error.HTTPError as e:
            fails.append(f"{qid}:{e.code}:{e.read().decode('utf-8', 'replace')[:80]}")

    print(f"patched ok: {ok}/{len(rows)}")
    if fails:
        print("FAILURES:")
        for x in fails[:20]:
            print(" ", x)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
