"""Deploy tools — agents can check production health and deployment status.

Agents use these to verify that code changes actually reached production,
not just passed local tests. Constitution Rule 3: test on production URL.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path



_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def check_vercel_status() -> str:
    """Check Vercel deployment status for the frontend."""
    try:
        result = subprocess.run(
            ["npx", "vercel", "ls", "--limit=3"],
            capture_output=True, text=True, timeout=15,
            cwd=str(_PROJECT_ROOT / "apps" / "web"),
        )
        return result.stdout[:500] if result.stdout else f"Vercel error: {result.stderr[:200]}"
    except FileNotFoundError:
        return "Vercel CLI not found. Install: npm i -g vercel"
    except subprocess.TimeoutExpired:
        return "Vercel CLI timed out (15s)"
    except Exception as e:
        return f"Vercel check failed: {e}"


def check_production_health() -> str:
    """Curl the production API health endpoint."""
    import urllib.request
    import json

    api_url = os.environ.get(
        "RAILWAY_PRODUCTION_URL",
        "https://volauraapi-production.up.railway.app",
    )

    try:
        req = urllib.request.Request(f"{api_url}/health", method="GET")
        req.add_header("User-Agent", "swarm-health-check/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return f"API HEALTHY: {json.dumps(body, indent=2)}"
    except Exception as e:
        return f"API UNHEALTHY: {e}"


def run_typescript_check() -> str:
    """Run tsc --noEmit on the frontend. Returns errors or 'PASS'."""
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            capture_output=True, text=True, timeout=120,
            cwd=str(_PROJECT_ROOT / "apps" / "web"),
        )
        if result.returncode == 0:
            return "TSC PASS: no type errors"
        return f"TSC FAIL:\n{result.stdout[:1000]}"
    except subprocess.TimeoutExpired:
        return "TSC timed out (120s)"
    except Exception as e:
        return f"TSC check failed: {e}"


def check_git_status() -> str:
    """Return current git status: branch, uncommitted changes, last 5 commits."""
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=str(_PROJECT_ROOT),
        ).stdout.strip()

        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=str(_PROJECT_ROOT),
        ).stdout.strip()

        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, cwd=str(_PROJECT_ROOT),
        ).stdout.strip()

        return f"Branch: {branch}\nUncommitted:\n{status or '(clean)'}\nRecent:\n{log}"
    except Exception as e:
        return f"Git check failed: {e}"
