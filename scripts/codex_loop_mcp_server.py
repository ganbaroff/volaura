"""
codex_loop_mcp_server.py — MCP server wrapping the signed handoff courier.

Stage 2 of the Atlas <-> Codex direct handoff. Exposes the three core
operations from codex_loop_courier.py as MCP tools, so Claude Code and
Codex CLI invoke them as tool calls instead of going through CEO.

Install on Atlas side (Claude Code):
    pip install "mcp[cli]>=1.0"
    # add to .mcp.json:
    # "codex-loop": {
    #   "command": "python",
    #   "args": ["scripts/codex_loop_mcp_server.py"]
    # }

Install on Codex side: same pattern, same .mcp.json snippet in Codex's
config dir.

After both sides reload, the courier loop is closed at the protocol
level — CEO is no longer the message bus.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the courier module importable without packaging the repo
REPO_SCRIPTS = Path(__file__).resolve().parent
if str(REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(REPO_SCRIPTS))

import codex_loop_courier as courier  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        "ERROR: `mcp` package is not installed.\n"
        "Install with: pip install 'mcp[cli]>=1.0'\n"
        f"Original ImportError: {e}\n"
    )
    sys.exit(1)


app = FastMCP("codex-loop")


@app.tool()
def append_signed_entry(
    topic: str,
    sender: str,
    intent: str,
    body: str,
) -> dict:
    """
    Append a signed entry to memory/atlas/codex-loop.md.

    Atomically writes a new section to the top of codex-loop.md with a
    signature comment carrying sha256 / nonce / sender / timestamp / intent.
    Records the nonce in the append-only replay ledger.

    Args:
      topic: short topic slug for the entry header
      sender: one of {"atlas", "codex", "browser-atlas", "ceo"}
      intent: free-form intent string (e.g. "decision", "task-delegation")
      body: markdown body. Use #### sub-headers freely. SHA-256 hashes the
            canonicalized body bytes (UTF-8, LF line endings).

    Returns:
      {"nonce": str, "sha256": str, "sender": str, "courier_timestamp": str}
    """
    entry = courier.append_signed_entry(
        topic=topic, sender=sender, intent=intent, body=body,
    )
    return {
        "nonce": entry.nonce,
        "sha256": entry.sha256,
        "sender": entry.sender,
        "courier_timestamp": entry.courier_timestamp,
        "topic": entry.topic,
        "intent": entry.intent,
    }


@app.tool()
def read_recent_entries(limit: int = 10) -> list[dict]:
    """
    Read recent signed entries from codex-loop.md with verification.

    Parses signed entries newest-first. Recomputes SHA-256 against the
    body and reports per-entry verification status. Legacy entries with
    no signature line are silently skipped — soft migration.

    Args:
      limit: max number of entries to return (default 10)

    Returns:
      list of dicts: {header, sender, topic, nonce, sha256_claimed,
                      courier_timestamp, body, verified, verify_reason}
    """
    entries = courier.read_recent_entries(limit=limit)
    return [
        {
            "header": e.header,
            "sender": e.sender,
            "topic": e.topic,
            "nonce": e.nonce,
            "sha256_claimed": e.sha256_claimed,
            "courier_timestamp": e.courier_timestamp,
            "body": e.body,
            "verified": e.verified,
            "verify_reason": e.verify_reason,
        }
        for e in entries
    ]


@app.tool()
def verify_entry_by_nonce(nonce: str) -> dict:
    """
    Verify a specific entry in codex-loop.md by its nonce.

    Looks up the entry, recomputes its SHA-256 against the parsed body,
    compares against the claimed hash from the signature comment.

    Args:
      nonce: the UUIDv4 nonce from a prior append

    Returns:
      {"verified": bool, "reason": str}
    """
    ok, reason = courier.verify_entry_by_nonce(nonce)
    return {"verified": ok, "reason": reason}


if __name__ == "__main__":
    # FastMCP exposes a `run()` that handles stdio JSON-RPC.
    app.run()
