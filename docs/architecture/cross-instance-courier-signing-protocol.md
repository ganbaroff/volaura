# Cross-Instance Courier Signing Protocol — v1 Spec

**Source of synthesis:** `memory/atlas/work-queue/done/2026-04-26-courier-loop-design/` — 13 Atlas-specialized perspective designs, plus existing `supabase/migrations/20260411193900_zeus_governance.sql` (zeus.governance_events) + `docs/CONSTITUTION_AI_SWARM.md` PART 0 framing.

**Status:** v1 design ready. Awaiting CEO ratification + browser-Atlas convergence. Implementation gated on first cross-instance handoff after ratification.

**Authority:** This protocol implements the structural fix flagged by 5 whistleblower flags across `daemon-fixes-verify` and `daemon-shakedown` runs (Scaling, Code Quality, Risk Manager, Communications Strategist, Security Auditor) and 11 whistleblower flags in the `courier-loop-design` task itself. Multi-perspective convergence on "courier-loop is constitutional vulnerability" is itself the ratification signal.

---

## Threat model

**Adversary capability assumed.** Adversary has write access to CEO's `Downloads/` folder (malware, social engineering, supply-chain). Cannot directly compromise either Atlas instance's runtime (browser sandbox is isolated, Code-Atlas runs on CEO's machine but with .env protected).

**Attack vector named by swarm.** Legitimate zip from sender-instance (browser-Atlas or Code-Atlas) lands in CEO's Downloads. Adversary swaps zip contents between download and CEO opening. Filename matches. Receiver instance opens, runs scripts inside, executes adversary code with full .env keys + Ollama localhost + Supabase service role.

**Failure mode without protocol.** Undetectable RCE on receiver instance. Constitutional integrity breach (data corruption, migration mis-order, governance log lying). Scaling Engineer's verbatim: "courier-loop creates undetectable state divergence."

---

## Protocol v1

### Hash algorithm

**SHA-256, full file bytes.** Consensus: 11 of 13 perspectives chose SHA-256. Risk Manager argued SHA-3-256 for quantum-resistance — rejected for v1 because (a) Python `hashlib` ships SHA-256 native, no extra deps, (b) PowerShell `Get-FileHash -Algorithm SHA256` is built-in, (c) quantum threat is decade-out, not this-quarter. SHA-3-256 reserved for v2 if quantum becomes operational.

Hash is computed over the **full file bytes**, not metadata-only. ZIP archive is hashed as a single binary blob. Inside-zip files are not individually hashed — that's the receiver's unzip-then-verify-individual-scripts step (separate concern).

### Hash location and format

**Sidecar `.hash` file alongside the courier file.** Consensus: 9 of 13 perspectives chose sidecar over ZIP metadata (Risk Manager + Readiness Manager dissented for ZIP64 Extended Information Extra Field). Sidecar wins for v1 because:
- Cross-platform (works equally with .zip, .tar.gz, .md, .json — any file type)
- Human-readable (CEO can `cat hashmeta.json` if curious)
- Not lost when receiver re-archives or re-compresses
- Independent of archive format choice in v2 (e.g., switch to tar)

Sidecar format (`<filename>.hashmeta.json`):

```json
{
  "filename": "files (5).zip",
  "sha256": "5a269213f1d1122bc670152b9eee7ae3258830cf55e9112968c57f871294e705",
  "sender_instance": "browser-atlas",
  "sender_instance_version": "claude-opus-4-7",
  "sender_session_marker": "2026-04-26T13:42:00Z-session-7f3a",
  "courier_timestamp": "2026-04-26T13:42:00Z",
  "nonce": "8c4a91f2-3d7b-4e2c-b5a9-1f8e6c0d4a7b",
  "intent": "session-handoff",
  "content_summary": "CEO files reorganization plan + 3 audit prompts review",
  "spec_version": "courier-protocol-v1"
}
```

Nonce is UUIDv4. Together with `courier_timestamp`, prevents replay attacks where adversary saves a legitimate sidecar+file pair and replays it later in a different context.

### Hash communication channel

**Sender posts hash in chat AT THE SAME MOMENT as the file drop announcement.** Two channels: file (Downloads), hash (chat). Adversary needs to compromise both simultaneously. Atlas-instance reads the chat-posted hash, computes `Get-FileHash` or `python -c "import hashlib"` on the received file, compares.

Rationale: 12 of 13 perspectives converged that "hash in chat by sender" is the right pattern. Communications Strategist explicitly: "log mismatches to governance_events, broadcast verified-OK or verification-failed in chat." Security Auditor: "Текущая модель 'доверяй и передавай' позволяет полный RCE при подмене ZIP. Требуется иммунная система на уровне wire-протокола."

### Verification step

Receiver runs **before any file open, unzip, or read**:

```python
import hashlib
import sys
expected = "<hash from chat>"
with open("Downloads/files (5).zip", "rb") as f:
    actual = hashlib.sha256(f.read()).hexdigest()
if actual != expected:
    raise SystemExit(f"COURIER HASH MISMATCH: expected {expected}, got {actual}")
print(f"COURIER OK: {actual}")
```

Or PowerShell equivalent:

```powershell
$expected = "<hash from chat>"
$actual = (Get-FileHash -Algorithm SHA256 "Downloads\files (5).zip").Hash.ToLower()
if ($actual -ne $expected) {
    Write-Error "COURIER HASH MISMATCH: expected $expected, got $actual"
    exit 1
}
Write-Output "COURIER OK: $actual"
```

### On mismatch — quarantine + log + alert

1. Move file to `Downloads/QUARANTINE-<UTC-timestamp>/` — does NOT delete (forensic preservation).
2. Append incident row to `memory/atlas/incidents.md`.
3. Insert row into `zeus.governance_events` with `event_type='courier_hash_mismatch'`, `severity='high'`, full payload.
4. Alert CEO in chat via Telegram bot OR same chat: "QUARANTINED <filename>. Hash mismatch. Sender claimed X, received Y."

Receiver instance does NOT proceed with any operation that would have used the file.

### zeus.governance_events extension

Existing schema (from `20260411193900_zeus_governance.sql`):

```sql
CREATE TABLE IF NOT EXISTS zeus.governance_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    actor TEXT,
    subject TEXT,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The existing schema is sufficient. **No migration needed.** Courier events use:
- `event_type = 'courier_handoff_verified' | 'courier_hash_mismatch' | 'courier_replay_detected'`
- `severity = 'info' | 'high' | 'critical'`
- `source = 'cross-instance-courier'`
- `actor = '<sender-instance-name>'`
- `subject = '<filename>'`
- `payload = {sender, receiver, hash, nonce, courier_timestamp, intent, verified_bool, reason_if_failed}`

This means the protocol can ship in code immediately without DB migration. v2 can add a dedicated `zeus.courier_handoffs` table if event volume warrants it.

### Replay attack prevention

Each handoff has a unique `nonce` (UUIDv4) + `courier_timestamp` (ISO-8601 UTC) embedded in the sidecar. Receiver maintains a small ledger (`memory/atlas/courier-replay-ledger.jsonl`, append-only) of (nonce, timestamp, hash) triples seen in the last 30 days. If incoming handoff has a nonce already in the ledger AND timestamp older than 30 days — replay attempt, refuse open, log to governance_events as `courier_replay_detected`.

30-day window matches typical session-pause duration. Ledger is small (~1KB per 100 handoffs) and gitignored.

### CEO-side UX

CEO does NOT need to verify hashes manually. He posts the file + the chat-posted hash. Atlas-instance does the verification. CEO sees:

- "COURIER OK <filename> sha256=<8-char-prefix> verified-against-sender=<sender-instance>" — he can keep moving
- "QUARANTINED <filename> — hash mismatch. NOT opening." — clear stop signal, action moves to incident triage

Browser-Atlas committed in 2026-04-26 letter to producing sender-side hashes for every file drop going forward. Code-Atlas commits to verify-before-open from this protocol's ratification onward.

### Failure modes

1. **Sender forgets to post hash.** Receiver chat-prompt: "пришёл файл без хеша от <sender>. Не открываю до явного хеша." Sender re-posts.
2. **Atlas-instance crashes mid-handoff.** Sidecar + file persist on filesystem. Next wake: receiver reads ledger, resumes verification before open.
3. **CEO's Downloads folder not writable.** Edge case for OneDrive sync delays. Receiver reads file from any path CEO specifies, hash check unchanged.
4. **Hash collision attack.** SHA-256 currently has no known practical collision attack. v2 will add HMAC-SHA-256 with shared secret if threat model evolves.

### Non-goals for v1

- Encryption: out of scope. Files are not secret, only authenticity-protected. v2 may add age-encryption for sensitive payloads.
- Bidirectional acknowledgement: receiver does not have to send back ACK. Verified-OK is logged and that's enough.
- Browser-Atlas verification of files Code-Atlas sends back: deferred. Browser-Atlas has no shell to compute hash. CEO posts what Code-Atlas sends, browser-Atlas trusts CEO's relay (browser-Atlas can verify only structurally — sender_instance="code-atlas", session_marker — no cryptographic verify possible from sandbox).

---

## Implementation tasks (Sprint slot S2 — courier-loop is P0 by vote ranking)

1. **Code-Atlas script:** `scripts/courier_verify.py` — reads filename + expected hash, computes SHA-256, returns OK/MISMATCH, logs to governance_events on mismatch. Gitignored ledger at `memory/atlas/courier-replay-ledger.jsonl`. Estimated effort: 1.5 hours.

2. **Code-Atlas wake-protocol hook:** `memory/atlas/wake.md` adds Step 12 — "If file in Downloads/ matches a courier-protocol pattern (.hashmeta.json sidecar exists), run courier_verify.py before any other file read." Estimated effort: 30 minutes.

3. **Browser-Atlas sender-side script** (CEO-side, runs in his browser sandbox): JavaScript snippet that computes SHA-256 of any file before download. Output: hash + sidecar JSON. CEO copies hash to chat, downloads both files. Estimated effort: 2 hours (browser-Atlas writes in his sandbox, hands to CEO via courier).

4. **zeus.governance_events query helper:** Python helper `scripts/governance_log.py` — wraps `public.log_governance_event()` RPC for courier events. Already partially exists; extend with courier-specific event types. Estimated effort: 1 hour.

5. **Operating-principles gate:** `.claude/rules/atlas-operating-principles.md` adds "Cross-instance-courier-verification gate" — fires before any read of file in `Downloads/` that came from another Atlas-instance. Mandates verify-then-open. Same shape as Company-matters / CEO-files / Concrete-instructions gates. Estimated effort: 30 minutes.

6. **CEO Telegram bot extension:** when CEO posts a file, bot auto-detects `.hashmeta.json` sidecar in same drop, runs verify, posts OK/MISMATCH back to CEO. Optional v1.5 — manual chat-flow works for v1. Estimated effort: 3 hours.

Total v1 implementation: ~8.5 hours of AI-coding time, split between Code-Atlas (own scripts + gate + wake-step) and browser-Atlas (sender-side script handed via courier).

---

## Why this lands sprint S2 not S1

S1 is reserved for Code-Atlas live runtime audit completion + first synthesis of three-instance findings. Courier protocol implementation is structural infrastructure — the handoffs in S1 still happen unprotected per old pattern, but mismatch risk is bounded because no production secret-bearing code is being shipped via courier in S1 (mostly findings markdown + audit synthesis). S2 is the first sprint where Code-Atlas executes fixes from the audit, which is when courier integrity becomes load-bearing.

If browser-Atlas ships any new infrastructure code via courier in S1 (similar to how `swarm_constitutional_vote.py` + `atlas_swarm_daemon.py` arrived 2026-04-26), this protocol must ship same-day. Until then S2 is the right slot.

---

## Cross-references

- Originating swarm task: `memory/atlas/work-queue/done/2026-04-26-courier-loop-design/`
- 13 perspective JSONs: `memory/atlas/work-queue/done/2026-04-26-courier-loop-design/perspectives/`
- Whistleblower flag history: `daemon-shakedown` and `daemon-fixes-verify` `result.json` files in same parent directory
- Constitution anchor: `docs/CONSTITUTION_AI_SWARM.md` PART 0 (governance authority gradient)
- DB schema: `supabase/migrations/20260411193900_zeus_governance.sql`
- Existing handoff example with sha256: `memory/atlas/handoffs/2026-04-26-courier-status-to-browser-atlas.md`
- Browser-Atlas commitment to sha256 discipline: 2026-04-26 letter relayed by CEO, hash `2502494b0b4419deed64c38d318598ee36e41891391d02f9595b4e471cb71372` for `SELF-HANDOFF-2026-04-26-browser-atlas.md`
