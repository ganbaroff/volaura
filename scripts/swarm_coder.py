"""
swarm_coder.py — Sprint S2 Step 2 — autonomous coding loop wrapper.

THIS IS THE MISSING PIECE between agent proposals and real code changes.

Built Session 91 final after CEO observed: "бот живой но агенты всё ещё
нихуя не делают в проекте". Until now: proposals.json filled with ideas,
nothing implemented. Now: this script reads a proposal, identifies files,
runs safety gate, calls Aider (autonomous CLI) to actually edit files
and commit.

WHAT IT DOES:
1. Read proposal from proposals.json by ID (or top approved)
2. Use project_qa indexer to find candidate files for the proposal
3. Run safety_gate.classify_proposal() — only AUTO level proceeds
4. Call aider headless: --model groq/llama-3.3-70b-versatile --yes-always --message
5. Parse aider output for: success/fail, commit hash, files changed
6. Update proposal status: approved → implemented (with commit ref)
7. Notify CEO via Telegram (clean Python urllib)
8. Append audit log to memory/swarm/swarm_coder_log.jsonl

WHY AIDER (not custom diff_writer):
- Production-ready (~25k stars, used by thousands)
- SEARCH/REPLACE block format (more reliable than unified diff)
- Auto-commit with conventional messages built-in
- Supports any LiteLLM provider (Groq, Cerebras, Gemini, OpenRouter)
- Battle-tested file edit + git integration
- Saves us from rebuilding 1000+ LOC of edge-case handling

DESIGN:
- Single-file CLI + importable
- DRY-RUN by default (--execute required)
- Stateless per proposal
- Idempotent (won't re-implement already-implemented proposals)
- Audit trail in JSONL

USAGE:
    # Dry run on top approved proposal
    python3 scripts/swarm_coder.py

    # Dry run specific proposal
    python3 scripts/swarm_coder.py --id <proposal_id>

    # Actually run aider (will commit if successful)
    python3 scripts/swarm_coder.py --id <proposal_id> --execute

    # Show what files would be touched without running aider
    python3 scripts/swarm_coder.py --id <proposal_id> --plan

    # Send results to CEO Telegram
    python3 scripts/swarm_coder.py --id <proposal_id> --execute --telegram
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


# UTF-8 streams (idempotent)
def _ensure_utf8(stream):
    enc = getattr(stream, "encoding", "") or ""
    if "utf" in enc.lower():
        return stream
    if hasattr(stream, "buffer"):
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
    return stream


sys.stdout = _ensure_utf8(sys.stdout)
sys.stderr = _ensure_utf8(sys.stderr)


# ── Paths ───────────────────────────────────────────────────────
def resolve_root() -> Path:
    cwd = Path.cwd()
    for c in [cwd, *cwd.parents]:
        if (c / "apps" / "api" / ".env").exists():
            return c
    return Path("C:/Projects/VOLAURA")


PROJECT_ROOT = resolve_root()
PROPOSALS_FILE = PROJECT_ROOT / "memory" / "swarm" / "proposals.json"
LOG_FILE = PROJECT_ROOT / "memory" / "swarm" / "swarm_coder_log.jsonl"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ENV_FILE = PROJECT_ROOT / "apps" / "api" / ".env"

# Aider lives on Python 3.12 because Aider's deps don't build on Python 3.14
AIDER_PYTHON = "C:/Users/user/AppData/Local/Programs/Python/Python312/python.exe"
# Gemini 2.0 Flash: 1M context window, free tier, fast.
# Groq Llama 3.3 70B fails with context_length_exceeded on multi-file edits (8K limit).
AIDER_DEFAULT_MODEL = "gemini/gemini-2.0-flash"


# ── Env loader ──────────────────────────────────────────────────
def load_env() -> dict:
    """Load apps/api/.env into a dict."""
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# ── Telegram ────────────────────────────────────────────────────
def send_telegram(text: str) -> bool:
    """Send message to CEO via clean Python urllib path. Returns True on success."""
    env = load_env()
    bot_token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CEO_CHAT_ID", "")
    if not bot_token or not chat_id:
        return False
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode("utf-8")).get("ok", False)
    except Exception as e:
        print(f"[Telegram] error: {e}", file=sys.stderr)
        return False


# ── Proposal loading ────────────────────────────────────────────
def load_proposals() -> list[dict]:
    if not PROPOSALS_FILE.exists():
        return []
    with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("proposals", [])


def get_proposal(proposal_id: str | None) -> dict | None:
    """Get specific proposal or top approved if id is None."""
    all_props = load_proposals()
    if proposal_id:
        for p in all_props:
            if p.get("id", "").startswith(proposal_id):
                return p
        return None
    # Top approved (newest first)
    approved = [p for p in all_props if p.get("status") == "approved"]
    approved.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    return approved[0] if approved else None


def update_proposal_status(proposal_id: str, new_status: str, commit_hash: str = "") -> bool:
    """Update a proposal's status + record commit hash if provided."""
    if not PROPOSALS_FILE.exists():
        return False
    with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for p in data.get("proposals", []):
        if p.get("id") == proposal_id:
            p["status"] = new_status
            p["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if commit_hash:
                p["implementation_commit"] = commit_hash
            with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    return False


# ── File discovery ──────────────────────────────────────────────
def discover_target_files(proposal: dict) -> list[str]:
    """Find candidate files for a proposal using project_qa keyword index.

    Returns relative paths (from PROJECT_ROOT) of likely-relevant files.
    Limited to 5 files max for safety.
    """
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from project_qa import load_index, find_relevant
    except ImportError:
        return []

    title = proposal.get("title", "")
    content = proposal.get("content", "")
    query = f"{title} {content[:500]}"

    index = load_index()
    if not index:
        return []

    relevant = find_relevant(query, index, top_k=5)
    files = []
    for path, _score in relevant:
        try:
            rel = Path(path).relative_to(PROJECT_ROOT)
            files.append(str(rel).replace("\\", "/"))
        except ValueError:
            files.append(str(path).replace("\\", "/"))
    return files


# ── Safety gate ─────────────────────────────────────────────────
def run_safety_gate(proposal: dict, target_files: list[str]) -> dict:
    """Classify proposal via safety_gate.py."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from safety_gate import classify_proposal
    except ImportError as e:
        return {"level": "HIGH", "reason": f"safety_gate import failed: {e}", "can_auto_execute": False}
    verdict = classify_proposal(proposal, target_files)
    return verdict.to_dict()


# ── Aider invocation ────────────────────────────────────────────
def call_aider(
    target_files: list[str],
    instruction: str,
    model: str = AIDER_DEFAULT_MODEL,
    timeout: int = 300,
) -> dict:
    """Call aider headless on target files. Returns result dict.

    Notes:
    - --map-tokens 0 disables repo map (we already pass exact target files)
    - --subtree-only limits aider's view to target file directories
    - timeout=300 because aider scans repo even with map disabled
    - Default model = Gemini 2.0 Flash (1M context, free, fast)
    """
    env = load_env()
    # Pick API key based on model provider
    sub_env = os.environ.copy()
    sub_env["PYTHONIOENCODING"] = "utf-8"

    if model.startswith("gemini/"):
        gemini_key = env.get("GEMINI_API_KEY", "")
        if not gemini_key:
            return {"ok": False, "error": "GEMINI_API_KEY not in apps/api/.env"}
        sub_env["GEMINI_API_KEY"] = gemini_key
    elif model.startswith("groq/"):
        groq_key = env.get("GROQ_API_KEY", "")
        if not groq_key:
            return {"ok": False, "error": "GROQ_API_KEY not in apps/api/.env"}
        sub_env["GROQ_API_KEY"] = groq_key
    elif model.startswith("openrouter/"):
        or_key = env.get("OPENROUTER_API_KEY", "")
        if not or_key:
            return {"ok": False, "error": "OPENROUTER_API_KEY not in apps/api/.env"}
        sub_env["OPENROUTER_API_KEY"] = or_key
    else:
        # Pass through all keys, let aider/litellm pick
        for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY"):
            v = env.get(k, "")
            if v:
                sub_env[k] = v

    # Aider on Windows expects backslash paths. Convert forward slashes.
    target_files_native = [f.replace("/", os.sep) for f in target_files]

    # Build command. --map-tokens 0 + --subtree-only avoid scanning 1175 files.
    cmd = [
        AIDER_PYTHON,
        "-m", "aider",
        "--model", model,
        "--no-pretty",
        "--no-stream",
        "--no-fancy-input",
        "--yes-always",
        "--auto-commits",
        "--map-tokens", "0",
        "--subtree-only",
        "--message", instruction,
    ] + target_files_native

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=sub_env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"aider timeout after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": f"aider invocation failed: {e}"}

    out = result.stdout or ""
    err = result.stderr or ""
    # Aider writes "Commit XXX msg" sometimes to stderr, sometimes to stdout.
    # Parse both combined.
    full = out + "\n" + err

    # Parse for commit hash anywhere in output
    commit_match = re.search(r"Commit\s+([0-9a-f]{6,40})\s+(.+?)(?:\n|$)", full)
    commit_hash = commit_match.group(1) if commit_match else ""
    commit_msg = commit_match.group(2).strip() if commit_match else ""

    # Parse for "Applied edit to <file>" anywhere
    edited_files = re.findall(r"Applied edit to\s+(\S+)", full)

    # Parse for token usage
    tokens_match = re.search(r"Tokens:\s+([\d.k]+)\s+sent,\s+([\d.k]+)\s+received", full)
    tokens_sent = tokens_match.group(1) if tokens_match else "?"
    tokens_recv = tokens_match.group(2) if tokens_match else "?"

    # Cost
    cost_match = re.search(r"Cost:\s+\$([\d.]+)", full)
    cost = cost_match.group(1) if cost_match else "?"

    # Aider may exit non-zero on warnings, so trust commit_hash presence over returncode.
    # If aider says "Commit X" the edit succeeded regardless of exit code.
    return {
        "ok": bool(commit_hash),
        "exit_code": result.returncode,
        "commit_hash": commit_hash,
        "commit_msg": commit_msg,
        "edited_files": edited_files,
        "tokens_sent": tokens_sent,
        "tokens_recv": tokens_recv,
        "cost_usd": cost,
        "stdout_tail": out[-500:],
        "stderr_tail": err[-500:],
    }


# ── Audit log ───────────────────────────────────────────────────
def log_attempt(proposal: dict, plan: dict, result: dict | None) -> None:
    """Append to swarm_coder_log.jsonl."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.time(),
        "proposal_id": proposal.get("id", "?"),
        "proposal_title": proposal.get("title", "?")[:100],
        "proposal_severity": proposal.get("severity", "?"),
        "plan": plan,
        "result": result,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Main pipeline ──────────────────────────────────────────────
def implement_proposal(
    proposal: dict,
    execute: bool = False,
    plan_only: bool = False,
) -> dict:
    """Run the full pipeline for a single proposal."""
    title = proposal.get("title", "?")
    pid = proposal.get("id", "?")
    print(f"━━━ Proposal: {pid[:12]} ━━━")
    print(f"  Title:    {title}")
    print(f"  Severity: {proposal.get('severity', '?')}")
    print(f"  Agent:    {proposal.get('agent', '?')}")
    print()

    # Step 1: discover target files
    print("[1/4] Discovering target files via project_qa index...")
    target_files = discover_target_files(proposal)
    print(f"      Found {len(target_files)} candidate files:")
    for f in target_files:
        print(f"        - {f}")
    print()

    # Step 2: safety gate
    print("[2/4] Running safety gate classification...")
    gate = run_safety_gate(proposal, target_files)
    print(f"      Level:   {gate['level']}")
    print(f"      Reason:  {gate['reason']}")
    print(f"      Can auto-execute: {gate['can_auto_execute']}")
    if gate.get("blocked_paths"):
        print(f"      Blocked: {', '.join(gate['blocked_paths'][:3])}")
    if gate.get("suggestions"):
        for s in gate["suggestions"][:2]:
            print(f"      → {s}")
    print()

    plan_dict = {
        "target_files": target_files,
        "safety_gate": gate,
    }

    if plan_only:
        log_attempt(proposal, plan_dict, None)
        return {"ok": True, "stage": "plan_only", "plan": plan_dict}

    if not gate["can_auto_execute"]:
        print(f"[STOP] Safety gate level={gate['level']} — cannot auto-execute.")
        log_attempt(proposal, plan_dict, {"stage": "blocked_by_gate"})
        return {"ok": False, "stage": "blocked_by_gate", "plan": plan_dict}

    if not execute:
        print("[3/4] DRY RUN — would call aider with these files (use --execute to actually run)")
        log_attempt(proposal, plan_dict, {"stage": "dry_run"})
        return {"ok": True, "stage": "dry_run", "plan": plan_dict}

    # Step 3: call aider
    print(f"[3/5] Calling aider with {AIDER_DEFAULT_MODEL}...")
    instruction = (
        f"{title}\n\n{proposal.get('content', '')[:2000]}\n\n"
        "IMPORTANT CONSTRAINTS:\n"
        "1. Make ONLY the minimal change requested.\n"
        "2. Do NOT modify files outside the ones provided.\n"
        "3. Do NOT add new modes, features, or refactors beyond the request.\n"
        "4. Do NOT use git reset --hard, git push --force, gh pr create, rm -rf, or any destructive commands.\n"
        "5. If the request is unclear, make the smallest possible change in the most relevant provided file."
    )
    aider_result = call_aider(target_files, instruction)

    if aider_result["ok"]:
        print(f"      [OK] commit {aider_result['commit_hash'][:12]}")
        print(f"      [OK] files reported: {', '.join(aider_result['edited_files']) or '(none parsed)'}")
        print(f"      [OK] tokens: {aider_result['tokens_sent']} sent / {aider_result['tokens_recv']} recv")
        print(f"      [OK] cost:   ${aider_result['cost_usd']}")
    else:
        print(f"      [FAIL] {aider_result.get('error', 'aider returned non-zero exit + no commit detected')}")
        print(f"      exit_code: {aider_result.get('exit_code', '?')}")
        if aider_result.get("stdout_tail"):
            print(f"      stdout tail: {aider_result['stdout_tail'][-400:]}")
        if aider_result.get("stderr_tail"):
            print(f"      stderr tail: {aider_result['stderr_tail'][-400:]}")
        log_attempt(proposal, plan_dict, aider_result)
        return {"ok": False, "stage": "aider_failed", "plan": plan_dict, "aider": aider_result}
    print()

    # Step 4: POST-EXECUTION SAFETY CHECK — verify aider stayed in scope
    print("[4/5] Post-execution safety check (verify diff stayed in scope)...")
    sys.path.insert(0, str(SCRIPTS_DIR))
    from safety_gate import verify_commit_safe
    diff_verdict = verify_commit_safe(
        commit_hash=aider_result["commit_hash"],
        expected_files=target_files,
        project_root=PROJECT_ROOT,
    )
    print(f"      Files actually changed: {diff_verdict.files_changed}")
    if diff_verdict.safe:
        print("      [SAFE] All changes within expected scope, no forbidden patterns")
    else:
        print(f"      [UNSAFE] {len(diff_verdict.violations)} violations:")
        for v in diff_verdict.violations[:5]:
            print(f"        - {v}")
        print(f"      [REVERTING] git reset --hard HEAD~1 (commit {aider_result['commit_hash'][:12]} removed)")
        try:
            subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            print("      [REVERTED] commit removed from history")
        except Exception as e:
            print(f"      [REVERT FAILED] {e} — manual cleanup required")
        log_attempt(proposal, plan_dict, {**aider_result, "post_check": diff_verdict.__dict__, "reverted": True})
        return {
            "ok": False,
            "stage": "reverted_unsafe",
            "plan": plan_dict,
            "aider": aider_result,
            "violations": diff_verdict.violations,
        }
    print()

    # Step 5: update proposal status (only if commit survived safety check)
    print("[5/5] Updating proposal status → implemented")
    update_proposal_status(pid, "implemented", aider_result["commit_hash"])
    log_attempt(proposal, plan_dict, {**aider_result, "post_check": diff_verdict.__dict__})
    return {
        "ok": True,
        "stage": "executed",
        "plan": plan_dict,
        "aider": aider_result,
        "post_check": diff_verdict.__dict__,
    }


# ── CLI ─────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sprint S2 Step 2: autonomous coding loop via Aider",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--id", default=None, help="Process specific proposal by id prefix")
    parser.add_argument("--execute", action="store_true", help="ACTUALLY run aider (default: dry run)")
    parser.add_argument("--plan", action="store_true", help="Show plan + safety gate only, no aider call")
    parser.add_argument("--telegram", action="store_true", help="Send result to CEO via Telegram")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    proposal = get_proposal(args.id)
    if not proposal:
        print(f"No proposal found (id={args.id}, looking for top approved if no id)")
        sys.exit(1)

    result = implement_proposal(proposal, execute=args.execute, plan_only=args.plan)

    if args.telegram:
        title = proposal.get("title", "?")[:80]
        gate = result.get("plan", {}).get("safety_gate", {})
        if result.get("stage") == "executed" and result["ok"]:
            aider = result["aider"]
            msg = (
                f"[SWARM_CODER] EXECUTED\n\n"
                f"Proposal: {title}\n"
                f"Commit:   {aider['commit_hash'][:12]} {aider['commit_msg'][:60]}\n"
                f"Files:    {', '.join(aider['edited_files'])}\n"
                f"Tokens:   {aider['tokens_sent']} / {aider['tokens_recv']}\n"
                f"Cost:     ${aider['cost_usd']}"
            )
        elif result.get("stage") == "blocked_by_gate":
            msg = (
                f"[SWARM_CODER] BLOCKED by safety gate\n\n"
                f"Proposal: {title}\n"
                f"Level:    {gate.get('level', '?')}\n"
                f"Reason:   {gate.get('reason', '?')}\n"
                f"Need CEO approval via /approve {proposal.get('id', '?')[:12]}"
            )
        elif result.get("stage") == "dry_run":
            msg = (
                f"[SWARM_CODER] DRY RUN ok\n\n"
                f"Proposal: {title}\n"
                f"Files:    {len(result['plan']['target_files'])}\n"
                f"Gate:     {gate.get('level', '?')} ({gate.get('reason', '?')})\n"
                f"Run with --execute to actually apply"
            )
        elif result.get("stage") == "plan_only":
            msg = (
                f"[SWARM_CODER] PLAN ONLY\n\n"
                f"Proposal: {title}\n"
                f"Files:    {len(result['plan']['target_files'])}\n"
                f"Gate:     {gate.get('level', '?')}"
            )
        else:
            msg = f"[SWARM_CODER] error\nStage: {result.get('stage', '?')}"

        if send_telegram(msg):
            print("Telegram: sent to CEO")
        else:
            print("Telegram: send failed")

    if args.json:
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
