#!/usr/bin/env python3
"""S3-G1: Coordinator Agent — structural Class 3 prevention.

First runnable Python agent in packages/swarm/agents/.
Reads task description, classifies scope, dispatches to relevant
perspectives via autonomous_run.PERSPECTIVES, returns synthesis.

Usage:
  echo "Fix assessment scoring bug in engine.py" | python -m packages.swarm.agents.coordinator
  python -m packages.swarm.agents.coordinator "Refactor profile creation flow"
  python -m packages.swarm.agents.coordinator --classify-only "Add MIRT support"
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Classification keywords -> perspective routing
ROUTE_MAP: dict[str, list[str]] = {
    "security": ["Security Auditor", "Legal Advisor"],
    "auth": ["Security Auditor"],
    "rls": ["Security Auditor", "Legal Advisor"],
    "assessment": ["Assessment Science", "Code Quality Engineer", "QA Engineer"],
    "irt": ["Assessment Science"],
    "aura": ["Assessment Science", "Product Strategist"],
    "scale": ["Scaling Engineer", "DevOps Engineer"],
    "database": ["Scaling Engineer"],
    "migration": ["Scaling Engineer", "Security Auditor"],
    "deploy": ["DevOps Engineer", "Readiness Manager"],
    "railway": ["DevOps Engineer"],
    "design": ["UX Designer", "Cultural Intelligence"],
    "ux": ["UX Designer"],
    "css": ["UX Designer"],
    "tailwind": ["UX Designer"],
    "legal": ["Legal Advisor", "Risk Manager"],
    "gdpr": ["Legal Advisor", "Risk Manager"],
    "privacy": ["Legal Advisor", "Risk Manager"],
    "constitution": ["Ecosystem Auditor", "CTO Watchdog"],
    "law": ["Ecosystem Auditor", "Legal Advisor"],
    "crystal": ["Product Strategist", "Ecosystem Auditor"],
    "brandedby": ["Product Strategist", "UX Designer"],
    "lifesim": ["Product Strategist", "UX Designer"],
    "mindshift": ["Product Strategist", "Cultural Intelligence"],
    "refactor": ["Code Quality Engineer", "Scaling Engineer"],
    "test": ["QA Engineer", "Code Quality Engineer"],
    "lint": ["Code Quality Engineer"],
    "growth": ["Growth Hacker", "Sales Director"],
    "pricing": ["Sales Director", "Risk Manager"],
    "strategy": ["Chief Strategist", "Product Strategist"],
    "risk": ["Risk Manager", "CTO Watchdog"],
    "voice": ["Cultural Intelligence", "CTO Watchdog"],
    "shame": ["Cultural Intelligence", "Ecosystem Auditor"],
    "telegram": ["DevOps Engineer", "CTO Watchdog"],
}

# Always include these for broad tasks
DEFAULT_PERSPECTIVES = ["Chief Strategist", "Code Quality Engineer", "CTO Watchdog"]


def classify_task(description: str) -> dict:
    """Classify task and determine which perspectives to consult."""
    desc_lower = description.lower()

    # Find matching keywords
    matched_keywords: list[str] = []
    perspectives: set[str] = set()

    for keyword, agents in ROUTE_MAP.items():
        if keyword in desc_lower:
            matched_keywords.append(keyword)
            perspectives.update(agents)

    # If no specific match, use defaults
    if not perspectives:
        perspectives = set(DEFAULT_PERSPECTIVES)
        matched_keywords = ["general"]

    # Estimate scope from description
    file_refs = re.findall(r"[\w/]+\.\w{2,4}", description)
    estimated_files = max(len(file_refs), 1)

    # Risk level
    high_risk_keywords = {"migration", "deploy", "auth", "rls", "gdpr", "pricing", "constitution", "delete"}
    risk = "high" if any(k in desc_lower for k in high_risk_keywords) else "medium" if len(perspectives) > 3 else "low"

    return {
        "task": description[:200],
        "matched_keywords": matched_keywords,
        "perspectives_to_consult": sorted(perspectives),
        "perspective_count": len(perspectives),
        "estimated_files": estimated_files,
        "risk_level": risk,
        "recommendation": (
            "auto_execute" if risk == "low" and estimated_files <= 3
            else "consult_swarm" if risk == "medium"
            else "requires_ceo_review"
        ),
    }


def main():
    classify_only = "--classify-only" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--classify-only"]

    if args:
        task = " ".join(args)
    elif not sys.stdin.isatty():
        task = sys.stdin.read().strip()
    else:
        print("Usage: coordinator.py <task description>", file=sys.stderr)
        sys.exit(1)

    result = classify_task(task)

    if classify_only:
        print(json.dumps(result, indent=2))
        return

    # Full output with dispatch recommendation
    print(json.dumps(result, indent=2))

    if result["recommendation"] == "auto_execute":
        print(f"\n[coordinator] LOW RISK — auto-execute OK ({result['estimated_files']} files, {result['risk_level']} risk)")
    elif result["recommendation"] == "consult_swarm":
        print(f"\n[coordinator] MEDIUM — consult these {result['perspective_count']} perspectives before implementing:")
        for p in result["perspectives_to_consult"]:
            print(f"  - {p}")
    else:
        print(f"\n[coordinator] HIGH RISK — requires CEO review before proceeding")
        for p in result["perspectives_to_consult"]:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
