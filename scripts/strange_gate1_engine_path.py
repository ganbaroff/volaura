"""strange-protocol Gate 1: external adversarial model call on the ADR-017 engine path.

Asks an external (non-Anthropic) model to attack the two-layer plan vs alternatives
(license a bank / work-samples / pure-LLM assessment). Output -> file for Gate 2
counter-evidence work. Key read from apps/api/.env, never printed.
"""

from __future__ import annotations

import json
import os
import urllib.request

OUT = "C:/Users/user/AppData/Local/Temp/claude/strange_gate1.txt"

PROMPT = """You are an adversarial assessment-industry expert (psychometrics + HR-tech GTM). \
ATTACK this engine-development plan; find where it loses to alternatives.

CONTEXT: VOLAURA, pre-beta verified-talent platform, solo founder + AI agents, ~$0 inference \
budget, $60k cloud credits, beachhead AZ/CIS. CURRENT ENGINE (verified live today): own IRT \
3PL/EAP/MFI adaptive engine on prod; 117-item static bank (8 competencies, EN+AZ, no RU yet); \
expert-prior IRT params (not empirically calibrated); anti-gaming flags proven live \
(rushing/identical-response caught); energy-adaptive stopping; LLM+BARS grading for open answers.

THE PLAN TO ATTACK (ADR-017): two layers - (1) keep the calibrated CAT core as the only AURA \
input; (2) add a CV-grounded "Experience Interview" generated per-candidate by a multi-agent \
LLM pipeline (generator -> content/linguistic/bias reviewers -> reviser), grounded in the \
candidate's own CV claims, output = verified-experience signals (not theta). The same pipeline \
continuously drafts standardized bank items into a needs_review human-approval queue to grow \
the bank to 30+/competency and enable empirical calibration.

ALTERNATIVES to weigh: (a) license an existing calibrated item bank / white-label an assessment \
provider, (b) skip SJT expansion; verify via work-samples/portfolio + structured-interview kits, \
(c) pure-LLM conversational assessment with no IRT, (d) something better you propose.

Return EXACTLY:
FAILURE MODE 1 - (claim / why it bites / early signal)
FAILURE MODE 2 - (same)
FAILURE MODE 3 - (same)
VERDICT - one paragraph: is the two-layer plan the right call for THIS company, or name the \
superior alternative and why."""


def load_key() -> str:
    for p in (
        os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env"),
        "C:/Projects/VOLAURA/apps/api/.env",
    ):
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except OSError:
            continue
    raise SystemExit("GROQ_API_KEY not found")


def main() -> None:
    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.6,
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": PROMPT}],
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {load_key()}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VOLAURA/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read().decode("utf-8"))
    out = body["choices"][0]["message"]["content"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print("WRITTEN", len(out), "chars; model:", body.get("model"))


if __name__ == "__main__":
    main()
