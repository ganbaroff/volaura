#!/usr/bin/env python3
"""
Cross-instance courier verifier — protocol v1 implementation.

Spec: docs/architecture/cross-instance-courier-signing-protocol.md (v1).

Usage from Atlas-instance (Code-Atlas verification side):

    python scripts/courier_verify.py <file_path> <expected_sha256> \
        [--sender browser-atlas] [--intent session-handoff] \
        [--nonce <uuid4>] [--courier-timestamp <ISO-8601>]

Or, if a sidecar `<file_path>.hashmeta.json` exists:

    python scripts/courier_verify.py <file_path>

Side effects on success (sha256 match + replay-ledger miss):
    - Append (nonce, timestamp, hash) to memory/atlas/courier-replay-ledger.jsonl
    - Insert atlas.governance_events row event_type='courier_handoff_verified'
    - stdout: "COURIER OK <hash> sender=<sender> intent=<intent>"
    - exit code 0

Side effects on failure (mismatch OR replay):
    - Move file to Downloads/QUARANTINE-<UTC-timestamp>/<original-name>
    - Append incident row to memory/atlas/incidents.md
    - Insert atlas.governance_events row event_type='courier_hash_mismatch'
      OR 'courier_replay_detected' (severity='high' or 'critical')
    - stderr: "COURIER MISMATCH expected=<E> got=<A>" or "REPLAY <nonce>"
    - exit code 1 (mismatch) / exit code 2 (replay)

This script is designed to run before any file open / unzip / read on the
receiver Atlas-instance side, per the protocol v1 wake-protocol-hook.

Implementation notes:
- stdlib only (hashlib, json, pathlib, datetime, uuid, sys, argparse,
  shutil, urllib.request for governance_events posting via Supabase RPC).
- Supabase RPC call is best-effort: if SUPABASE_URL or SUPABASE_SERVICE_KEY
  missing, ledger + incidents.md updates still happen (filesystem-only mode).
- 30-day replay window per spec — older nonces silently allowed (re-use OK
  after wraparound; small ledger size kept under typical session pause).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "memory" / "atlas" / "courier-replay-ledger.jsonl"
INCIDENTS_PATH = REPO_ROOT / "memory" / "atlas" / "incidents.md"
QUARANTINE_BASE = Path.home() / "Downloads"
REPLAY_WINDOW_DAYS = 30
PROTOCOL_VERSION = "courier-protocol-v1"


# ──────────────────────────  hashing  ──────────────────────────


def sha256_of_file(path: Path) -> str:
    """Compute SHA-256 of file contents (full bytes)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ──────────────────────────  sidecar  ──────────────────────────


def load_sidecar(file_path: Path) -> dict | None:
    """Load <file>.hashmeta.json sidecar if present."""
    sidecar = file_path.with_suffix(file_path.suffix + ".hashmeta.json")
    if not sidecar.exists():
        return None
    try:
        with sidecar.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[courier_verify] sidecar present but unreadable: {exc}", file=sys.stderr)
        return None


# ──────────────────────────  replay ledger  ──────────────────────────


def ensure_ledger() -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        LEDGER_PATH.touch()


def read_ledger() -> list[dict]:
    ensure_ledger()
    rows = []
    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # ledger corruption: skip line, do not fail verification
                continue
    return rows


def append_ledger(nonce: str, timestamp: str, sha256: str) -> None:
    ensure_ledger()
    row = {"nonce": nonce, "timestamp": timestamp, "sha256": sha256}
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def detect_replay(nonce: str, courier_timestamp_iso: str) -> bool:
    """
    Return True if nonce already seen AND the original sighting was
    within the REPLAY_WINDOW_DAYS window (i.e. genuine replay attempt).
    Older nonces are allowed to recur (window-aged out).
    """
    if not nonce:
        return False
    rows = read_ledger()
    cutoff = datetime.now(timezone.utc) - timedelta(days=REPLAY_WINDOW_DAYS)
    for row in rows:
        if row.get("nonce") != nonce:
            continue
        try:
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            return True
    return False


# ──────────────────────────  quarantine  ──────────────────────────


def quarantine(file_path: Path, reason: str) -> Path:
    """Move file to Downloads/QUARANTINE-<UTC>/<original-name>; return new path."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    qdir = QUARANTINE_BASE / f"QUARANTINE-{stamp}"
    qdir.mkdir(parents=True, exist_ok=True)
    target = qdir / file_path.name
    try:
        shutil.move(str(file_path), str(target))
    except (OSError, shutil.Error) as exc:
        print(f"[courier_verify] quarantine move failed: {exc}", file=sys.stderr)
        return file_path  # at least we tried; caller still aborts
    # Drop a quarantine reason note alongside
    note = qdir / "QUARANTINE-REASON.txt"
    note.write_text(f"{reason}\nFile: {file_path.name}\nUTC: {stamp}\n", encoding="utf-8")
    return target


# ──────────────────────────  incidents.md  ──────────────────────────


def append_incident(event_type: str, detail: dict) -> None:
    INCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not INCIDENTS_PATH.exists():
        INCIDENTS_PATH.write_text("# Atlas — Incident Log\n\n", encoding="utf-8")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with INCIDENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\n## {stamp} · {event_type}\n\n")
        for key, value in detail.items():
            f.write(f"- **{key}:** {value}\n")
        f.write("\n")


# ──────────────────────────  governance log  ──────────────────────────


def post_governance_event(event_type: str, severity: str, payload: dict, subject: str) -> bool:
    """
    Best-effort POST to public.log_governance_event RPC. Returns True on
    success, False on any failure (no exception bubbles up — verifier must
    not be gated on Supabase availability).
    """
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return False
    endpoint = f"{url}/rest/v1/rpc/log_governance_event"
    body = json.dumps(
        {
            "p_event_type": event_type,
            "p_severity": severity,
            "p_source": "cross-instance-courier",
            "p_actor": payload.get("sender", "unknown"),
            "p_subject": subject,
            "p_payload": payload,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"[courier_verify] governance_event post failed: {exc}", file=sys.stderr)
        return False


# ──────────────────────────  main verify  ──────────────────────────


def verify(
    file_path: Path,
    expected: str,
    sender: str,
    intent: str,
    nonce: str,
    courier_timestamp: str,
    content_summary: str | None,
) -> int:
    if not file_path.exists():
        print(f"COURIER ERROR: file not found: {file_path}", file=sys.stderr)
        return 3

    actual = sha256_of_file(file_path)
    payload_base = {
        "filename": file_path.name,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "sender": sender,
        "intent": intent,
        "nonce": nonce,
        "courier_timestamp": courier_timestamp,
        "content_summary": content_summary or "",
        "spec_version": PROTOCOL_VERSION,
    }

    # ── hash mismatch ────────────────────────────────────────────────
    if actual != expected:
        quarantined = quarantine(
            file_path,
            reason=f"SHA-256 mismatch: expected {expected}, got {actual}",
        )
        payload_base["quarantine_path"] = str(quarantined)
        append_incident("courier_hash_mismatch", payload_base)
        post_governance_event(
            event_type="courier_hash_mismatch",
            severity="high",
            payload=payload_base,
            subject=file_path.name,
        )
        print(
            f"COURIER MISMATCH expected={expected[:12]}... got={actual[:12]}... "
            f"quarantined={quarantined}",
            file=sys.stderr,
        )
        return 1

    # ── replay attack ────────────────────────────────────────────────
    if nonce and detect_replay(nonce, courier_timestamp):
        payload_base["replay_window_days"] = REPLAY_WINDOW_DAYS
        append_incident("courier_replay_detected", payload_base)
        post_governance_event(
            event_type="courier_replay_detected",
            severity="critical",
            payload=payload_base,
            subject=file_path.name,
        )
        print(f"COURIER REPLAY DETECTED nonce={nonce}", file=sys.stderr)
        return 2

    # ── success ───────────────────────────────────────────────────────
    if nonce and courier_timestamp:
        append_ledger(nonce, courier_timestamp, actual)
    post_governance_event(
        event_type="courier_handoff_verified",
        severity="info",
        payload=payload_base,
        subject=file_path.name,
    )
    print(f"COURIER OK {actual} sender={sender} intent={intent}")
    return 0


# ──────────────────────────  CLI  ──────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-instance courier verifier (protocol v1)",
    )
    parser.add_argument("file", help="Path to the courier-delivered file")
    parser.add_argument(
        "expected",
        nargs="?",
        default=None,
        help="Expected SHA-256 (omit to load from <file>.hashmeta.json)",
    )
    parser.add_argument("--sender", default="unknown")
    parser.add_argument("--intent", default="")
    parser.add_argument("--nonce", default="")
    parser.add_argument("--courier-timestamp", dest="ts", default="")
    parser.add_argument("--content-summary", dest="summary", default=None)
    args = parser.parse_args(argv)

    file_path = Path(args.file).expanduser().resolve()

    expected = args.expected
    sender = args.sender
    intent = args.intent
    nonce = args.nonce
    ts = args.ts
    summary = args.summary

    # If sidecar exists, prefer its values for any field not set on CLI
    sidecar = load_sidecar(file_path)
    if sidecar:
        expected = expected or sidecar.get("sha256")
        if sender == "unknown":
            sender = sidecar.get("sender_instance", sender)
        intent = intent or sidecar.get("intent", "")
        nonce = nonce or sidecar.get("nonce", "")
        ts = ts or sidecar.get("courier_timestamp", "")
        summary = summary if summary is not None else sidecar.get("content_summary")

    if not expected:
        print(
            "COURIER ERROR: no expected hash given (CLI arg or sidecar)",
            file=sys.stderr,
        )
        return 3

    return verify(
        file_path=file_path,
        expected=expected.lower(),
        sender=sender,
        intent=intent,
        nonce=nonce,
        courier_timestamp=ts,
        content_summary=summary,
    )


if __name__ == "__main__":
    sys.exit(main())
