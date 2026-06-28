"""FIX-2 step 2: build the RU UPDATE migration from agent translations + verify
against ACTUAL prod option keys.

For each translated item:
  - scenario_ru  <- agent RU
  - options      <- prod options, with text_ru spliced in BY KEY (case-insensitive
    match against the real option key/id field). We do NOT trust the agent's key
    casing; we read prod's own options and attach text_ru to the matching entry.

Writes the migration SQL + a review report. Does NOT apply. Idempotent guard:
each UPDATE matches on id AND scenario_ru IS DISTINCT FROM the new value is NOT
used (we always set); instead the migration is safe to re-run (sets same values).
"""

from __future__ import annotations

import json
import os

FIX = "C:/Users/user/AppData/Local/Temp/claude/fix2"
MIG = "C:/Projects/VOLAURA-docs-archive-banner-clean/supabase/migrations/20260610234500_add_russian_question_translations.sql"
REVIEW = "C:/Users/user/AppData/Local/Temp/claude/fix2/_ru_review.md"
PAYLOAD = "C:/Users/user/AppData/Local/Temp/claude/fix2/_ru_payload.json"

COMPS = [
    "communication", "reliability", "leadership", "adaptability",
    "event_performance", "tech_literacy", "empathy_safeguarding", "english_proficiency",
]


def sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def opt_key(o: dict) -> str:
    return (o.get("key") or o.get("id") or "").strip()


def main() -> None:
    src_by_id: dict[str, dict] = {}
    with open(f"{FIX}/_all.json", encoding="utf-8") as f:
        for row in json.load(f):
            src_by_id[row["id"]] = row

    stmts: list[str] = []
    payload: list[dict] = []
    review: list[str] = ["# RU translation review — splice report\n"]
    n_items = 0
    n_opt_mismatch = 0
    missing_ru: list[str] = []

    for comp in COMPS:
        path = f"{FIX}/ru_{comp}.json"
        if not os.path.exists(path):
            review.append(f"\n## {comp}: MISSING translation file\n")
            continue
        with open(path, encoding="utf-8") as f:
            translations = json.load(f)
        review.append(f"\n## {comp}: {len(translations)} items\n")

        for tr in translations:
            qid = tr["id"]
            src = src_by_id.get(qid)
            if not src:
                review.append(f"- {qid}: NOT IN PROD EXPORT — skipped\n")
                continue
            scen_ru = (tr.get("scenario_ru") or "").strip()
            if not scen_ru:
                missing_ru.append(qid)
                continue
            n_items += 1

            prod_opts = src.get("options")
            set_clauses = [f"scenario_ru = {sql_str(scen_ru)}"]
            payload_row: dict = {"id": qid, "scenario_ru": scen_ru}

            if isinstance(prod_opts, list) and prod_opts:
                ru_map = {opt_key(o).lower(): (o.get("text_ru") or "").strip()
                          for o in (tr.get("options_ru") or [])}
                new_opts = []
                local_mismatch = 0
                for o in prod_opts:
                    k = opt_key(o)
                    ru_text = ru_map.get(k.lower(), "")
                    o2 = dict(o)
                    if ru_text:
                        o2["text_ru"] = ru_text
                    else:
                        local_mismatch += 1
                    new_opts.append(o2)
                if local_mismatch:
                    n_opt_mismatch += 1
                    review.append(
                        f"- {qid}: {local_mismatch}/{len(prod_opts)} options had no RU match "
                        f"(prod keys={[opt_key(o) for o in prod_opts]}, "
                        f"ru keys={[opt_key(o) for o in (tr.get('options_ru') or [])]})\n"
                    )
                set_clauses.append("options = " + sql_str(json.dumps(new_opts, ensure_ascii=False)) + "::jsonb")
                payload_row["options"] = new_opts

            stmts.append(
                "UPDATE public.questions SET\n    "
                + ",\n    ".join(set_clauses)
                + f"\nWHERE id = '{qid}';"
            )
            payload.append(payload_row)

    header = (
        "-- FIX-2: add Russian translations (scenario_ru + options[].text_ru) to all\n"
        "-- servable questions. Built from agent translations spliced onto PROD options\n"
        "-- BY OPTION KEY (case-insensitive) — option text_en/text_az/correct_answer\n"
        "-- semantics are preserved; only text_ru is added. Idempotent: re-run sets\n"
        "-- the same values. Source: scripts/fix2_build_ru_migration.py.\n\n"
    )
    with open(MIG, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(stmts) + "\n")
    review.append(
        f"\n---\nTOTAL items with scenario_ru: {n_items}\n"
        f"items with >=1 unmatched option (text_ru missing, kept en/az): {n_opt_mismatch}\n"
        f"items missing scenario_ru entirely: {missing_ru}\n"
    )
    with open(REVIEW, "w", encoding="utf-8") as f:
        f.write("".join(review))
    with open(PAYLOAD, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    print(f"migration written: {MIG}")
    print(f"payload rows: {len(payload)}")
    print(f"UPDATE statements: {len(stmts)}")
    print(f"items with scenario_ru: {n_items}")
    print(f"items with unmatched options: {n_opt_mismatch}")
    print(f"items missing scenario_ru: {missing_ru}")


if __name__ == "__main__":
    main()
