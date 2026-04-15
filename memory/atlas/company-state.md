# VOLAURA, Inc. — Company State

**Single source of truth for legal entity, obligations, and deadlines. Atlas + founder-ops agents read this first. CEO sees digest, not this file.**

Last updated: 2026-04-15 — Stripe Atlas dashboard confirms Application review ✅ COMPLETED. Incorporation expected Apr 15-16.

---

## Entity

| Field | Value |
|-------|-------|
| Legal name | VOLAURA, Inc. |
| Structure | Delaware C-Corporation |
| Formation agent | Stripe Atlas |
| Paid | 2026-04-14, AZN 881.79 (~$500 USD) via Tam Digicard (Kapital) |
| Incorporation date | **Apr 15-16 2026** (Stripe Atlas dashboard 2026-04-15: Application review ✅, Incorporation step PENDING) |
| EIN | PENDING (expected 2-4 weeks, foreign responsible party path via SS-4) |
| Registered agent | Stripe Atlas (included year 1) |
| Authorized shares | 10,000,000 common |
| Issued to founder | 9,000,000 (90%) |
| Equity pool | 1,000,000 (10%) unissued, reserved |
| Founder vesting | 4 years, 1-year cliff, start = Date of incorporation |
| Board | Yusif Ganbarov (sole member) |
| Officers | Yusif Ganbarov — President, Secretary |
| SSN/ITIN | None (must apply for ITIN via Form W-7) |
| Registered address | Aliyar Aliyev 26, Apt 636, AZ 1100 Baku, Azerbaijan (home) |
| Website | https://volaura.app |
| Phone | +994 55 585 77 91 |

---

## Timeline from 2026-04-14 payment

| Milestone | Expected | Deadline | Owner | Status |
|-----------|----------|----------|-------|--------|
| Application review | Apr 14-15 | — | Stripe Atlas | ✅ COMPLETED (dashboard 2026-04-15) |
| Incorporation (DE filing) | Apr 15-16 | — | Stripe Atlas | PENDING (confirmed dashboard) |
| Certificate of Incorporation issued | Apr 15-16 | — | Stripe Atlas | PENDING |
| 83(b) election mailed to IRS | **Within 10 business days** (Stripe Atlas SLA — ~Apr 29-30) | IRS statutory max: 30 calendar days (~May 15) | Founder + Atlas | **CRITICAL P0 — Stripe deadline TIGHTER than IRS by 2+ weeks** |
| Tax ID (EIN) received | 2-4 weeks (May 5-12) | — | IRS via Stripe Atlas | PENDING |
| ITIN application (Form W-7) | Immediately after incorporation | — | Founder | P0 (needed for 83(b) + taxes) |
| Mercury Bank application | After EIN received (~May 5-12) | — | Founder + Atlas | QUEUED |
| Stripe Atlas Perks review | **Apr 15-16** (available now per dashboard) | — | Atlas | **NEW — free credits potential (AWS, Notion, etc) — cash save** |
| Tax deadline reminders setup | **Apr 15-16** (available now per dashboard) | — | Compliance agent | NEW — auto-reminders via Stripe Atlas |
| State registration (DE founder lives abroad) | After Incorporation | Check if AZ triggers nexus | Compliance agent | REVIEW |
| Delaware franchise tax filing | — | March 1, 2027 | Compliance agent | RECURRING |
| Form 5472 + 1120 filing | — | April 15, 2027 (first full year) | Compliance agent + CPA | RECURRING, penalty $25k if missed |
| Registered agent renewal | Year 2 | ~Apr 2027 | Compliance agent | RECURRING |

---

## 83(b) Election — CRITICAL

**Why it matters:** Without timely 83(b), founder pays income tax on stock appreciation as it vests. If VOLAURA reaches $10M valuation in 4 years, tax bill could be 7-figure.

**Procedure:**
1. Sign 83(b) election form (Stripe Atlas provides)
2. Mail to IRS via USPS Certified Mail with Return Receipt, within 30 days of incorporation
3. Keep postmarked copy + green card forever
4. Atlas stores scans in `memory/atlas/legal/83b-election/`

**Postmark = legal filing date.** Not delivery date.

---

## Obligations calendar (recurring)

| Month | What | Who |
|-------|------|-----|
| March 1 | Delaware franchise tax | Compliance agent |
| April 15 | Form 5472 + 1120 (federal) | Compliance agent + CPA |
| March-April | Delaware annual report | Compliance agent |
| Rolling | Registered agent renewal | Compliance agent |
| Quarterly | Review company-state.md health | Atlas |

---

## Founder-ops agents (assigned)

| Agent | File | Owns |
|-------|------|------|
| founder-ops-incorporator | `.claude/agents/founder-ops-incorporator.md` | Stripe Atlas flow, 83(b), ITIN application |
| founder-ops-banker | `.claude/agents/founder-ops-banker.md` | Mercury/Relay/Brex/Wise |
| founder-ops-compliance | `.claude/agents/founder-ops-compliance.md` | 83(b) tracking, franchise tax, Form 5472/1120, registered agent renewals |

All three read Atlas memory + this file on wake. All three write personal lessons to `memory/agents/<name>/lessons.md` after each action.

---

## Outstanding costs to anticipate

| Item | When | Rough cost |
|------|------|------------|
| ITIN filing (CAA agent) | 2026-05 | $150-400 one-time |
| USPS Certified Mail for 83(b) | 2026-04/05 | ~$10 |
| CPA for Form 5472 + 1120 | 2027-03 | $500-1,500/year |
| Delaware franchise tax | 2027-03 | $450 minimum (authorized shares method) |
| Registered agent year 2+ | 2027-04 | $100-300/year |
| Stable US address (future) | When Mercury re-opens | $59/mo monthly |
| Quo US phone (future) | When Mercury re-opens | ~$15/mo |

Stripe credits received: $2,500 (use for production processing first revenue).

---

## Signal protocol

- **Application approved by Stripe Atlas** → CEO ping via Telegram, update this file
- **Certificate issued** → CEO ping with date (starts 30-day 83(b) clock), update calendar
- **EIN received** → CEO ping, unblock Mercury sprint
- **83(b) mailed** → CEO ping with postmark date, save tracking + receipt scans
- **Any deadline < 14 days away** → daily Telegram digest from compliance agent
- **Any deadline < 3 days away** → hourly Telegram until acknowledged
