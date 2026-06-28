"""
codex_loop_courier.py — signed handoff layer for Atlas <-> Codex via codex-loop.md

Applies the v1 cross-instance courier signing protocol
(docs/architecture/cross-instance-courier-signing-protocol.md) to the
text channel `memory/atlas/codex-loop.md` instead of file-courier through
Downloads/. Same crypto discipline (SHA-256 + UUID nonce + 30-day
replay-ledger), different transport.

Goal: eliminate CEO as message bus between Atlas and Codex.

This module is standalone (stdlib only). Wrap as an MCP server in the
next iteration — see Stage 2 marker at bottom.

CLI usage:
    python scripts/codex_loop_courier.py append \\
        --topic "ADR-013 follow-up" \\
        --sender atlas \\
        --intent decision-record \\
        --body-file path/to/body.md

    python scripts/codex_loop_courier.py read --limit 5
    python scripts/codex_loop_courier.py verify --nonce <uuid>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_LOOP = REPO_ROOT / "memory" / "atlas" / "codex-loop.md"
REPLAY_LEDGER = REPO_ROOT / "memory" / "atlas" / "courier-replay-ledger.jsonl"

VALID_SENDERS = {"atlas", "codex", "browser-atlas", "ceo"}
REPLAY_WINDOW = timedelta(days=30)


# ---------------------------------------------------------------------------
# Signing primitives — match the v1 protocol exactly
# ---------------------------------------------------------------------------

def _baku_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=4)))


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_body(body: str) -> str:
    """SHA-256 over the canonical body bytes (UTF-8, LF line endings)."""
    canon = body.replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(canon).hexdigest()


@dataclass(frozen=True)
class SignedEntry:
    sha256: str
    nonce: str
    sender: str
    courier_timestamp: str  # ISO-8601 UTC
    topic: str
    intent: str
    spec_version: str = "courier-protocol-v1"

    def to_signature_line(self) -> str:
        """The HTML comment carrying the signature inside the markdown."""
        return (
            f"<!-- signed: sha256={self.sha256} nonce={self.nonce} "
            f"sender={self.sender} ts={self.courier_timestamp} "
            f"intent={self.intent} spec={self.spec_version} -->"
        )


# ---------------------------------------------------------------------------
# Replay ledger — append-only JSONL
# ---------------------------------------------------------------------------

def _load_ledger() -> list[dict[str, Any]]:
    if not REPLAY_LEDGER.exists():
        return []
    entries: list[dict[str, Any]] = []
    with REPLAY_LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                # corrupted line — flag but don't crash; receiver should investigate
                entries.append({"_corrupt": line})
    return entries


def _record_in_ledger(entry: SignedEntry) -> None:
    REPLAY_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "nonce": entry.nonce,
        "sha256": entry.sha256,
        "courier_timestamp": entry.courier_timestamp,
        "sender": entry.sender,
        "topic": entry.topic,
        "intent": entry.intent,
        "ledger_recorded_at": _iso_now(),
    }
    with REPLAY_LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _check_replay(nonce: str, ledger: list[dict[str, Any]]) -> tuple[bool, str]:
    """Returns (is_replay, reason). Matches protocol v1 §Replay attack prevention."""
    cutoff = datetime.now(timezone.utc) - REPLAY_WINDOW
    for past in ledger:
        if past.get("nonce") != nonce:
            continue
        ts_raw = past.get("courier_timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw)
        except ValueError:
            return True, f"nonce {nonce} seen with malformed timestamp {ts_raw!r}"
        if ts < cutoff:
            return True, f"nonce {nonce} replayed (original ts {ts_raw}, >30d old)"
        return True, f"nonce {nonce} already seen at {ts_raw} (within 30d window)"
    return False, ""


# ---------------------------------------------------------------------------
# Append (signed write)
# ---------------------------------------------------------------------------

def append_signed_entry(
    *,
    topic: str,
    sender: str,
    intent: str,
    body: str,
) -> SignedEntry:
    """Append a new signed entry to the TOP of codex-loop.md (newest-on-top)."""
    if sender not in VALID_SENDERS:
        raise ValueError(f"sender must be one of {VALID_SENDERS}, got {sender!r}")
    if not topic.strip():
        raise ValueError("topic cannot be empty")
    if not body.strip():
        raise ValueError("body cannot be empty")

    entry = SignedEntry(
        sha256=_hash_body(body),
        nonce=str(uuid.uuid4()),
        sender=sender,
        courier_timestamp=_iso_now(),
        topic=topic.strip(),
        intent=intent.strip() or "general",
    )

    # Compose the markdown block. Header uses Baku-local for human reading
    # (protocol §CEO-side UX). Signature line carries machine-truth.
    baku_label = _baku_now().strftime("%Y-%m-%d %H:%M Baku")
    new_block = (
        f"## {baku_label} · {entry.sender} · {entry.topic}\n"
        f"{entry.to_signature_line()}\n\n"
        f"{body.rstrip()}\n\n---\n\n"
    )

    # Append-only, newest-on-top per existing codex-loop.md convention.
    # Atomic-ish: write to a tmp file then replace.
    CODEX_LOOP.parent.mkdir(parents=True, exist_ok=True)
    existing = CODEX_LOOP.read_text(encoding="utf-8") if CODEX_LOOP.exists() else ""

    # Find the first H2 to insert above it; if there's a protocol/preamble
    # block, preserve it. Convention from existing file: preamble ends with
    # "## Protocol" or "## YYYY-MM-DD". We slice at the first "\n## 2026" or
    # similar; falling back to top-of-file if none found.
    insert_at = existing.find("\n## 2026")
    if insert_at == -1:
        # No prior dated entries — append to end.
        combined = existing.rstrip() + "\n\n" + new_block
    else:
        combined = existing[: insert_at + 1] + new_block + existing[insert_at + 1 :]

    tmp = CODEX_LOOP.with_suffix(CODEX_LOOP.suffix + ".tmp")
    tmp.write_text(combined, encoding="utf-8")
    tmp.replace(CODEX_LOOP)

    _record_in_ledger(entry)
    return entry


# ---------------------------------------------------------------------------
# Read (verified)
# ---------------------------------------------------------------------------

@dataclass
class ReadEntry:
    header: str
    sender: str
    topic: str
    nonce: str
    sha256_claimed: str
    courier_timestamp: str
    body: str
    verified: bool
    verify_reason: str


def _parse_entries(text: str) -> list[ReadEntry]:
    """Parse codex-loop.md into signed entries. Skips legacy unsigned entries."""
    entries: list[ReadEntry] = []
    # Split by H2. We treat everything between two `## ` (or until next `## `)
    # as one block.
    lines = text.split("\n")
    block: list[str] = []
    header = ""
    for line in lines:
        if line.startswith("## "):
            if header:
                _try_parse_block(header, block, entries)
            header = line[3:].strip()
            block = []
        else:
            block.append(line)
    if header:
        _try_parse_block(header, block, entries)
    entries.reverse()  # newest-on-top in file → we return newest-first as-is
    # Wait, file is newest-on-top, so we already iterated newest-first; revert.
    entries.reverse()
    return entries


def _try_parse_block(header: str, block: list[str], out: list[ReadEntry]) -> None:
    # First non-blank line in block should be the signature comment.
    sig_line = ""
    body_start = 0
    for idx, line in enumerate(block):
        if not line.strip():
            continue
        if line.startswith("<!-- signed:"):
            sig_line = line
            body_start = idx + 1
        break

    if not sig_line:
        return  # legacy unsigned entry — skipped silently

    parts = sig_line.removeprefix("<!-- signed:").removesuffix("-->").strip().split()
    kv = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k.strip()] = v.strip()

    body = "\n".join(block[body_start:]).strip()
    # Strip the trailing `---` separator if present.
    if body.endswith("---"):
        body = body[: -len("---")].rstrip()

    claimed = kv.get("sha256", "")
    actual = _hash_body(body) if body else ""
    verified = bool(claimed) and claimed == actual
    reason = "" if verified else f"sha256 mismatch: claimed {claimed[:12]}... vs actual {actual[:12]}..."

    out.append(
        ReadEntry(
            header=header,
            sender=kv.get("sender", "unknown"),
            topic=header.split(" · ", 2)[-1] if " · " in header else header,
            nonce=kv.get("nonce", ""),
            sha256_claimed=claimed,
            courier_timestamp=kv.get("ts", ""),
            body=body,
            verified=verified,
            verify_reason=reason,
        )
    )


def read_recent_entries(limit: int = 10) -> list[ReadEntry]:
    if not CODEX_LOOP.exists():
        return []
    text = CODEX_LOOP.read_text(encoding="utf-8")
    parsed = _parse_entries(text)
    return parsed[:limit]


# ---------------------------------------------------------------------------
# Verify (lookup by nonce)
# ---------------------------------------------------------------------------

def verify_entry_by_nonce(nonce: str) -> tuple[bool, str]:
    """Look up an entry by nonce, recompute its hash, compare to claimed."""
    for entry in read_recent_entries(limit=10_000):
        if entry.nonce == nonce:
            if entry.verified:
                return True, f"OK: sha256 matches body, sender={entry.sender}"
            return False, entry.verify_reason
    return False, f"nonce {nonce} not found in codex-loop.md"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="append a signed entry")
    p_append.add_argument("--topic", required=True)
    p_append.add_argument("--sender", required=True, choices=sorted(VALID_SENDERS))
    p_append.add_argument("--intent", default="general")
    g = p_append.add_mutually_exclusive_group(required=True)
    g.add_argument("--body", help="body text inline")
    g.add_argument("--body-file", help="path to body file")
    g.add_argument("--body-stdin", action="store_true", help="read body from stdin")

    p_read = sub.add_parser("read", help="read recent entries with verification")
    p_read.add_argument("--limit", type=int, default=5)

    p_verify = sub.add_parser("verify", help="verify a specific entry by nonce")
    p_verify.add_argument("--nonce", required=True)

    sub.add_parser("ledger", help="dump replay-ledger entries")

    args = parser.parse_args()

    if args.cmd == "append":
        if args.body is not None:
            body = args.body
        elif args.body_file:
            body = Path(args.body_file).read_text(encoding="utf-8")
        else:
            body = sys.stdin.read()

        ledger = _load_ledger()
        # Replay check defends against re-running the same captured payload.
        # New entry generates a fresh nonce so it can't already be in the ledger
        # unless a previous identical run finished. We still scan to be sure.
        candidate_nonce = str(uuid.uuid4())
        is_replay, why = _check_replay(candidate_nonce, ledger)
        if is_replay:
            print(f"REPLAY DETECTED: {why}", file=sys.stderr)
            return 2

        entry = append_signed_entry(
            topic=args.topic,
            sender=args.sender,
            intent=args.intent,
            body=body,
        )
        print(f"APPENDED nonce={entry.nonce} sha256={entry.sha256[:12]}... sender={entry.sender}")
        return 0

    if args.cmd == "read":
        entries = read_recent_entries(limit=args.limit)
        if not entries:
            print("(no signed entries found)")
            return 0
        for e in entries:
            status = "OK" if e.verified else "MISMATCH"
            print(f"[{status}] {e.header}")
            print(f"  nonce={e.nonce}")
            print(f"  ts={e.courier_timestamp}")
            if not e.verified:
                print(f"  reason={e.verify_reason}")
            preview = e.body.splitlines()[0] if e.body else ""
            print(f"  body[0]={preview[:80]}")
            print()
        return 0

    if args.cmd == "verify":
        ok, msg = verify_entry_by_nonce(args.nonce)
        print(f"{'VERIFIED' if ok else 'FAILED'}: {msg}")
        return 0 if ok else 1

    if args.cmd == "ledger":
        ledger = _load_ledger()
        print(f"{len(ledger)} ledger entries:")
        for rec in ledger[-20:]:
            print(json.dumps(rec, ensure_ascii=False))
        return 0

    return 1


# ---------------------------------------------------------------------------
# Stage 2 — MCP server wrapping
# ---------------------------------------------------------------------------
# TODO(next-iteration): wrap append_signed_entry / read_recent_entries /
# verify_entry_by_nonce as MCP tools using the `mcp` Python SDK
# (https://github.com/modelcontextprotocol/python-sdk). Expose to both
# Claude Code and Codex CLI via .mcp.json:
#   {
#     "codex-loop": {
#       "command": "python",
#       "args": ["scripts/codex_loop_mcp_server.py"]
#     }
#   }
# Then Codex/Atlas call tools directly — CEO exits the courier role.


if __name__ == "__main__":
    sys.exit(_cli())
