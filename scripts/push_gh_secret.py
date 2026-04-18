#!/usr/bin/env python3
"""Push VERTEX_API_KEY to GitHub repo secrets via REST API + libsodium.

Sidesteps the CRLF-in-.env bash-sourcing bug by reading the .env file
directly with Python (strips \r) and making urllib.request calls.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from base64 import b64encode
from pathlib import Path

from nacl import encoding, public

ENV_PATH = Path("/sessions/elegant-fervent-carson/mnt/VOLAURA/apps/api/.env")
REPO = "ganbaroff/volaura"
SECRET_NAME = "VERTEX_API_KEY"


def load_env(path: Path) -> dict[str, str]:
    """Parse .env, stripping any trailing \r and matching KEY=VALUE lines."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z0-9_]+)\s*=\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        out[key] = val
    return out


def gh_get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "atlas-ctso/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_put(url: str, token: str, body: dict) -> int:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "atlas-ctso/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status


def encrypt_for_repo(public_key_b64: str, secret_value: str) -> str:
    """Sodium sealed-box encryption required by GitHub Actions Secrets API."""
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed = public.SealedBox(public_key)
    ciphertext = sealed.encrypt(secret_value.encode("utf-8"))
    return b64encode(ciphertext).decode("utf-8")


def main() -> int:
    env = load_env(ENV_PATH)
    token = env.get("GH_PAT_ACTIONS")
    secret_value = env.get(SECRET_NAME)

    if not token:
        print(f"ERROR: GH_PAT_ACTIONS not found in {ENV_PATH}", file=sys.stderr)
        return 1
    if not secret_value:
        print(f"ERROR: {SECRET_NAME} not found in {ENV_PATH}", file=sys.stderr)
        return 1

    # Auth probe
    who = gh_get("https://api.github.com/user", token)
    print(f"auth ok as: {who.get('login')} (id={who.get('id')})")

    # Repo public key
    key_info = gh_get(
        f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", token
    )
    key_id = key_info["key_id"]
    pubkey_b64 = key_info["key"]
    print(f"repo pubkey fetched: key_id={key_id}")

    # Encrypt
    encrypted_value = encrypt_for_repo(pubkey_b64, secret_value)
    print(f"encrypted secret (len={len(encrypted_value)})")

    # PUT secret
    status = gh_put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
        token,
        {"encrypted_value": encrypted_value, "key_id": key_id},
    )
    print(f"PUT {SECRET_NAME} -> HTTP {status}")

    # Verify by listing (metadata only — value never exposed by API)
    meta = gh_get(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}", token
    )
    print(f"verified: name={meta.get('name')} updated_at={meta.get('updated_at')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
