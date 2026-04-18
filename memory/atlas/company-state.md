# VOLAURA, Inc. — Company State

**Single source of truth for legal entity, obligations, and deadlines. Atlas + founder-ops agents read this first. CEO sees digest, not this file.**

Last updated: 2026-04-18 — 83(b) filing: DHL Express direct Баку → IRS is the SOLE path. Friend-fallback deprecated (CEO confirmed 2026-04-18: friend did not respond). 230 AZN negotiated. CEO goes to DHL Monday Apr 20. Stripe Atlas dashboard confirms: Application review ✅, Incorporation ✅ (Apr 14), Tax ID (EIN) expected Apr 29 – May 13, 83(b) postmark by Apr 28.

**Obligation tracking (2026-04-18):** deadlines + obligations now live in Postgres (`public.atlas_obligations`), not `memory/atlas/deadlines.md` (archive-only). Source of truth: `/admin/obligations` UI + Supabase table. Telegram proof intake via `@volaurabot` (photo / doc / URL / tracking number auto-matches open obligation). Nag cadence: GH Actions cron every 4h, escalates by `nag_schedule` (aggressive / standard / silent). Atlas wake-loop reads DB, not markdown, per `memory/atlas/wake.md` §10.1. Seeded rows: 83(b) aggressive (2026-05-14), ITIN standard (trigger = Atlas filing), WUF13 standard (2026-06-13), GITA deferred. **Gap remaining (2026-04-18):** migration not yet applied to prod, GH Actions secrets not yet populated, seed-script not yet run against prod — Atlas shipped the pipes, CEO opens the valve.

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
| Incorporation (DE filing) | Apr 14 | — | Stripe Atlas | ✅ COMPLETED (dashboard Apr 16) |
| Certificate of Incorporation issued | Apr 14 | — | Stripe Atlas | ✅ COMPLETED |
| 83(b) election mailed to IRS | **Postmark by Apr 28** (CEO goes to DHL Баку Mon Apr 20) | IRS statutory max: 30 calendar days (~May 14) | Founder + Atlas | **⚠️ CRITICAL P0 — 10 DAYS LEFT · DHL-direct path per 2026-04-18 pivot** |
| Tax ID (EIN) received | Apr 29 – May 13 | — | IRS via Stripe Atlas | PENDING |
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

**Procedure (revised 2026-04-18 — DHL-direct path):**
1. Verify DHL Express Worldwide is on current IRS §7502(f) designated PDS list (irs.gov → "Private Delivery Services")
2. Sign 83(b) election form from Stripe Atlas dashboard (wet signature + date ручкой, NO notarization required)
3. Ship DHL Express Worldwide direct Баку → IRS filing center (230 AZN with guarantee, negotiated from 300)
4. Include self-addressed stamped envelope inside for IRS to return stamped copy
5. DHL air waybill date = legal postmark per IRC §7502(f) / Notice 2016-30
6. Atlas stores scans in `memory/atlas/legal/83b-election/`

**Fallback path:** DEPRECATED. Friend-path (DHL Баку → friend in USA → USPS Certified) is off the table — friend did not respond (CEO confirmed 2026-04-18). Original 18-step guide in `docs/business/83b-filing-guide.html` kept as archive only. If A1 check fails (DHL Express Worldwide not on current IRS PDS list) → emergency-fallback = FedEx International Priority direct Баку → IRS (also §7502(f) designated). No friend-intermediary. Atlas must be pinged before shipping any non-DHL service.

**Postmark = legal filing date.** Not delivery date.

**EIN status:** Not yet issued. Form writes "Applied for" in EIN field — standard and IRS-accepted. 83(b) cannot wait for EIN per 30-day rule.

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
| DHL Express Worldwide for 83(b) (direct Baku → IRS) | 2026-04-20 | 230 AZN (~$135) |
| CPA for Form 5472 + 1120 | 2027-03 | $500-1,500/year |
| Delaware franchise tax | 2027-03 | $450 minimum (authorized shares method) |
| Registered agent year 2+ | 2027-04 | $100-300/year |
| Stable US address (future) | When Mercury re-opens | $59/mo monthly |
| Quo US phone (future) | When Mercury re-opens | ~$15/mo |

Stripe credits received: $2,500 (use for production processing first revenue).

## Perks & Credits Status (Session 114, 2026-04-16)

| Service | Status | Amount | Expected |
|---------|--------|--------|----------|
| Stripe payment processing | ACTIVE | $2,500 credit | Available now |
| GCP trial | ACTIVE | $300 credit | 90 days from activation |
| AWS Activate | SUBMITTED | $5,000 credit | Review 5-10 biz days |
| PostHog Startup | SUBMITTED | $50,000 credit | Review 3-5 biz days |
| Google for Startups | SUBMITTED | up to $350,000 | Review 3-10 biz days |
| Google Workspace | ACTIVE | $6/mo cost | yusif@volaura.app live |
| Cloudflare Email Routing | ACTIVE | $0 | hello@volaura.app → Gmail |
| OpenAI | BLOCKED | — | Region restriction (AZ) |

Total submitted: ~$405K potential. Total confirmed active: $2,800.

---

## Signal protocol

- **Application approved by Stripe Atlas** → CEO ping via Telegram, update this file
- **Certificate issued** → CEO ping with date (starts 30-day 83(b) clock), update calendar
- **EIN received** → CEO ping, unblock Mercury sprint
- **83(b) mailed** → CEO ping with postmark date, save tracking + receipt scans
- **Any deadline < 14 days away** → daily Telegram digest from compliance agent
- **Any deadline < 3 days away** → hourly Telegram until acknowledged
