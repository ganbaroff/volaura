"""Persona simulation harness — N synthetic candidates take the LIVE assessment end-to-end.

Proves (or refutes) on PROD, through the real API, no mocks:
  1. Score ordering: perfect > random > worst  (answers actually drive the score)
  2. MIN_ITEMS gate: early /complete -> 409    (D-1 fix live)
  3. Anti-gaming: rapid-fire run -> gaming_flags / timing warnings
  4. Energy adaptation: energy_level=low completes at the lower floor (Constitution Law 2)
  5. Language surface: AZ texts served; question_ru null (RC-1); AZ open answer grading path
  6. Content integrity: served texts contain no rebrand mangles (FIX-1 live through API)

Synthetic users are clearly marked: atlas-sim-<persona>-<ts>@sim.volaura.app.
They are NOT deleted (D-2 GDPR-delete defect would 500); documented residue.

Usage: python scripts/sim_assessment_personas.py --out results.json
Keys read from apps/api/.env (or C:/Projects/VOLAURA/apps/api/.env); never printed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
import urllib.error
import urllib.request

API = "https://volauraapi-production.up.railway.app/api"
# NOT a browser UA: Supabase rejects secret API keys when the UA looks like a
# browser ("Forbidden use of secret API key in browser", hit 2026-06-10).
UA = "volaura-sim-harness/0.1"
MANGLES = ["team member team", "team membered", "komanda üzvü komanda", "signed up to team member"]


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


def http(method: str, url: str, headers: dict, body: dict | None = None, timeout: int = 30) -> tuple[int, dict | str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


class Supa:
    def __init__(self, env: dict[str, str]):
        self.url = env["SUPABASE_URL"].rstrip("/")
        self.anon = env.get("SUPABASE_ANON_KEY", "")
        self.service = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_SERVICE_KEY", "")

    def create_user(self, email: str, password: str) -> tuple[int, dict | str]:
        return http(
            "POST",
            f"{self.url}/auth/v1/admin/users",
            {"apikey": self.service, "Authorization": f"Bearer {self.service}", "Content-Type": "application/json"},
            {"email": email, "password": password, "email_confirm": True},
        )

    def sign_in(self, email: str, password: str) -> tuple[int, dict | str]:
        return http(
            "POST",
            f"{self.url}/auth/v1/token?grant_type=password",
            {"apikey": self.anon, "Content-Type": "application/json"},
            {"email": email, "password": password},
        )

    def oracle(self, qid: str) -> dict:
        st, body = http(
            "GET",
            f"{self.url}/rest/v1/questions?id=eq.{qid}&select=correct_answer,type,options",
            {"apikey": self.service, "Authorization": f"Bearer {self.service}"},
        )
        if st == 200 and isinstance(body, list) and body:
            return body[0]
        return {}


def p3pl(theta: float, a: float, b: float, c: float) -> float:
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))


def pick_answer(persona: str, q: dict, oracle: dict, rng: random.Random) -> str:
    qtype = q.get("question_type", "mcq")
    options = q.get("options") or []
    keys = [o.get("key") for o in options if o.get("key")] or ["A", "B", "C", "D"]
    correct = (oracle.get("correct_answer") or "").strip()
    if qtype != "mcq" and not options:
        if persona == "lang_az":
            return (
                "Ilk olaraq komandani sakitlesdirib veziyyeti qiymetlendirerdim. Prioritetleri "
                "mueyyen edib tapsiriqlari bolusdurerdim, koordinatorla elaqe yaratmaga calisardim "
                "ve her addimi qisa sekilde komandaya bildirerdim. Sonda netessiceleri yoxlayardim."
            )
        if persona == "worst":
            return "I do not know."
        return (
            "First I would stay calm and assess the situation, prioritize the stations by impact, "
            "delegate clear tasks to each available person, communicate the plan briefly to the team, "
            "try to reach the coordinator through alternate channels, and verify coverage afterwards."
        )
    if persona == "perfect" or persona == "rapid":
        return correct if correct in keys else keys[0]
    if persona == "worst":
        wrong = [k for k in keys if k != correct]
        return wrong[0] if wrong else keys[0]
    return rng.choice(keys)


def run_persona(name: str, supa: Supa, cfg: dict, rng: random.Random) -> dict:
    rec: dict = {"persona": name, "events": []}
    ts = int(time.time())
    email = f"atlas-sim-{name}-{ts}@sim.volaura.app"
    password = "Sim-" + "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(14)) + "-1A"

    st, body = supa.create_user(email, password)
    rec["create_user_status"] = st
    if st not in (200, 201):
        rec["fatal"] = f"create_user failed: {body if isinstance(body, str) else json.dumps(body)[:200]}"
        return rec

    st, tok = supa.sign_in(email, password)
    rec["sign_in_status"] = st
    if st != 200 or not isinstance(tok, dict) or "access_token" not in tok:
        rec["fatal"] = "sign_in failed"
        return rec
    auth = {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}

    st, sess = http(
        "POST",
        f"{API}/assessment/start",
        auth,
        {
            "competency_slug": "communication",
            "language": cfg.get("language", "en"),
            "role_level": "professional",
            "energy_level": cfg.get("energy", "full"),
            "automated_decision_consent": True,
        },
    )
    rec["start_status"] = st
    if st != 201 or not isinstance(sess, dict):
        rec["fatal"] = f"start failed: {sess if isinstance(sess, str) else json.dumps(sess)[:300]}"
        return rec
    session_id = sess["session_id"]
    rec["session_id"] = session_id
    q = sess.get("next_question")

    served_texts: list[str] = []
    ru_nulls = 0
    answered = 0
    early_gate: dict | None = None

    while q and answered < 14:
        served_texts.append((q.get("question_en") or "") + " || " + (q.get("question_az") or ""))
        if q.get("question_ru") in (None, ""):
            ru_nulls += 1
        oracle = supa.oracle(q["id"]) if name in ("perfect", "worst", "rapid") else {}
        ans = pick_answer(name, q, oracle, rng)
        rt = 300 if name == "rapid" else rng.randint(6500, 21000)
        st, fb = http(
            "POST",
            f"{API}/assessment/answer",
            auth,
            {"session_id": session_id, "question_id": q["id"], "answer": ans, "response_time_ms": rt},
        )
        if st != 200 or not isinstance(fb, dict):
            rec["events"].append({"answer_status": st, "body": fb if isinstance(fb, str) else json.dumps(fb)[:200]})
            break
        answered += 1
        if fb.get("timing_warning"):
            rec.setdefault("timing_warnings", []).append(fb["timing_warning"])
        s = fb.get("session") or {}
        if answered == 1 and cfg.get("probe_early_complete"):
            gst, gbody = http("POST", f"{API}/assessment/complete/{session_id}", auth, {})
            early_gate = {"status": gst, "body": gbody if isinstance(gbody, str) else gbody}
        if s.get("is_complete"):
            q = None
        else:
            q = s.get("next_question")
        time.sleep(0.4 if name == "rapid" else 1.0)

    rec["questions_answered"] = answered
    rec["early_gate_probe"] = early_gate
    rec["ru_nulls_served"] = ru_nulls
    rec["mangles_in_served_texts"] = sum(1 for t in served_texts for m in MANGLES if m.lower() in t.lower())

    st, result = http("POST", f"{API}/assessment/complete/{session_id}", auth, {})
    rec["complete_status"] = st
    rec["result"] = result if isinstance(result, dict) else str(result)[:300]

    st, breakdown = http("GET", f"{API}/assessment/results/{session_id}/questions", auth)
    rec["breakdown_status"] = st
    if isinstance(breakdown, dict):
        rec["breakdown_count"] = len(breakdown.get("questions", []))
    st, verify = http("GET", f"{API}/assessment/verify/{session_id}", auth)
    rec["verify_status"] = st
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    env = load_env()
    supa = Supa(env)
    rng = random.Random(42)

    personas = [
        ("perfect", {"probe_early_complete": True}),
        ("worst", {}),
        ("random", {}),
        ("rapid", {}),
        ("lang_az", {"language": "az"}),
        ("lowenergy", {"energy": "low"}),
    ]
    results = []
    for name, cfg in personas:
        print(f"--- running persona: {name}")
        try:
            results.append(run_persona(name, supa, cfg, rng))
        except Exception as e:  # noqa: BLE001 — harness must finish all personas
            results.append({"persona": name, "fatal": f"exception: {e!r}"})
        time.sleep(3)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n=== SUMMARY (ASCII) ===")
    for r in results:
        res = r.get("result") if isinstance(r.get("result"), dict) else {}
        print(
            f"{r['persona']:<10} answered={r.get('questions_answered', 0):<3} "
            f"score={res.get('competency_score', 'n/a'):<6} aura={res.get('aura_updated', 'n/a'):<5} "
            f"flags={res.get('gaming_flags', [])} gate={(r.get('early_gate_probe') or {}).get('status', '-')} "
            f"mangles={r.get('mangles_in_served_texts', '-')} ru_nulls={r.get('ru_nulls_served', '-')} "
            f"fatal={r.get('fatal', '-')[:60]}"
        )


if __name__ == "__main__":
    main()
