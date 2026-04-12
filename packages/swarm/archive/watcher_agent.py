"""Watcher Agent — reacts to production errors, finds root cause, proposes fix.

Pattern: Sentry/error event → grep codebase → identify file:line → propose fix → post to shared memory.
CEO research (Session 88): "Watcher Agents monitor environments, capture stack trace,
search codebase for root cause, propose fix in new git branch."

Can be triggered by:
1. Sentry webhook → autonomous_run.py post-deploy mode
2. Manual: python -m packages.swarm.watcher_agent "error message here"
3. Scheduled: check production health every N hours

Uses swarm/tools/ for code search. Uses shared_memory for findings.
Does NOT write code — proposes file:line + suggested change. CTO implements.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "packages"))

from loguru import logger

from swarm.tools.code_tools import grep_codebase, read_file, search_code_index
from swarm.tools.deploy_tools import check_production_health
from swarm.shared_memory import post_result, broadcast


def analyze_error(error_message: str, stack_trace: str = "") -> dict:
    """Analyze an error: find relevant files, propose root cause.

    Returns dict with: file, line, root_cause, suggested_fix, severity.
    """
    findings = {
        "error": error_message[:200],
        "files_found": [],
        "root_cause": "",
        "suggested_fix": "",
        "severity": "medium",
    }

    # Extract file paths from stack trace
    file_pattern = re.compile(r'(?:File |at |in )[\"\']?([^\s\"\']+\.(?:py|tsx?|js))[\"\']?(?::(\d+))?')
    matches = file_pattern.findall(stack_trace or error_message)

    for file_path, line_num in matches[:5]:
        # Normalize path
        clean_path = file_path.replace("\\", "/")
        # Try to find in project
        for prefix in ["apps/api/app/", "apps/web/src/", "packages/swarm/"]:
            if prefix in clean_path:
                rel_path = clean_path[clean_path.index(prefix):]
                content = read_file(rel_path, max_lines=20)
                if "FILE NOT FOUND" not in content:
                    findings["files_found"].append({
                        "path": rel_path,
                        "line": line_num or "?",
                        "snippet": content[:300],
                    })
                break

    # Search code index for keywords from error
    keywords = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|\b[a-z_]+_[a-z_]+\b', error_message)
    for kw in keywords[:3]:
        index_results = search_code_index(kw, top_k=3)
        if "NO RESULTS" not in index_results:
            findings["files_found"].append({"query": kw, "index_results": index_results[:200]})

    # Grep for specific patterns
    if "500" in error_message or "Internal Server Error" in error_message:
        findings["severity"] = "critical"
        # Check for common 500 causes
        for pattern in ["raise HTTPException", ".single()", "KeyError", "AttributeError"]:
            grep_result = grep_codebase(pattern, "*.py", max_results=5)
            if "NO MATCHES" not in grep_result:
                findings["files_found"].append({"pattern": pattern, "matches": grep_result[:300]})

    elif "404" in error_message:
        findings["severity"] = "low"
    elif "422" in error_message:
        findings["severity"] = "high"
        findings["root_cause"] = "Likely schema mismatch — check Pydantic model vs request payload"
    elif "CORS" in error_message.upper():
        findings["severity"] = "high"
        findings["root_cause"] = "CORS configuration — check middleware chain in main.py"

    # Constitution check — is this a Law 1 violation?
    if any(w in error_message.lower() for w in ["red", "#ff0000", "#dc2626", "#ef4444"]):
        findings["severity"] = "critical"
        findings["root_cause"] = "Law 1 violation — red color detected"

    return findings


async def watch_production() -> dict:
    """Check production health and analyze any issues found."""
    health = check_production_health()

    if "UNHEALTHY" in health:
        findings = analyze_error(health)
        findings["source"] = "production_health_check"

        # Post to shared memory
        post_result("watcher-agent", "health-check", findings)
        broadcast("watcher-agent", f"PRODUCTION ISSUE: {health[:100]}")

        logger.warning("Watcher: production unhealthy — {h}", h=health[:100])
        return findings

    logger.info("Watcher: production healthy")
    return {"status": "healthy", "details": health}


async def watch_error(error_msg: str, stack_trace: str = "") -> dict:
    """Analyze a specific error and propose fix."""
    findings = analyze_error(error_msg, stack_trace)

    # Post to shared memory
    post_result("watcher-agent", f"error-{hash(error_msg) % 10000}", findings)

    if findings["severity"] in ("critical", "high"):
        broadcast(
            "watcher-agent",
            f"[{findings['severity'].upper()}] {error_msg[:80]} — {len(findings['files_found'])} files identified",
        )

    return findings


async def main():
    parser = argparse.ArgumentParser(description="Watcher Agent — error analysis")
    parser.add_argument("error", nargs="?", default="", help="Error message to analyze")
    parser.add_argument("--stack", default="", help="Stack trace")
    parser.add_argument("--health", action="store_true", help="Check production health")
    args = parser.parse_args()

    if args.health:
        result = await watch_production()
    elif args.error:
        result = await watch_error(args.error, args.stack)
    else:
        # Default: health check
        result = await watch_production()

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
