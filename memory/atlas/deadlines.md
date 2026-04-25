# DEPRECATED 2026-04-18 — source of truth moved to DB

Obligations now live in `public.atlas_obligations` (Supabase). View / manage:
- Admin UI: `/admin/obligations`
- DB query: `SELECT * FROM atlas_obligations WHERE status IN ('open','in_progress') ORDER BY deadline ASC NULLS LAST`
- Telegram nag loop: `.github/workflows/atlas-obligation-nag.yml` (cron every 4h) + `scripts/atlas_obligation_nag.py`
- Proof intake: send photo / document / URL / tracking number to `@volaurabot` → it attaches to the matching open obligation automatically (picker if multiple match).
- Seed migration: `scripts/seed_atlas_obligations.py` (one-shot, idempotent)
- Spec: `memory/atlas/OBLIGATION-SYSTEM-SPEC-2026-04-18.md`

This markdown file is retained as historical archive only. New obligations MUST be added via DB, not here. Atlas wake-loop reads the DB (see `memory/atlas/wake.md`).

---

# Atlas Deadlines (archive as of 2026-04-18)

Rolling log of dated obligations that affect money, legal status, or launch.
Each row: **date · action · consequence of missing · owner · status**.

Atlas reads this on every wake (post-scan, pre-iteration) and surfaces
anything within 14 days of `today` in the next response.

Format: entries sorted chronologically, past-due moves to ARCHIVE at bottom.

---

## Active

### 2026-05-27 — GITA Startup Matching Grants (Georgia VZP path)
- **Action:** if pursuing Georgia VZP, submit application via grants.gov.ge/en/Grants
- **Consequence of missing:** next window is November 2026 (6-month delay on up to ~$37K non-dilutive)
- **Owner:** CEO decides yes/no by 2026-05-01 (gives ~4 weeks to register LLC + file)
- **Prereq:** Georgia VZP LLC registered and certified; CEO has 10–20% co-financing ready
- **Status:** NOT PURSUING per SYNC decision (Delaware C-Corp primary). Keep deadline here as a "revisit if Stripe Atlas is blocked" fallback.

### 2026-06-13 — Legacy public launch placeholder (deprecated event anchor)
- **Action:** VOLAURA product ready for the first external user cohort. This line remains only as a deprecated archive marker.
- **Consequence of missing:** obsolete assumption. Do not use this line for current planning.
- **Owner:** Archive only
- **Prereqs:** none — archived context only.
- **Status:** DEPRECATED — replaced by generic launch planning and live obligations.

### TBD+30d — 83(b) election (Stripe Atlas auto-files — de-risked)
- **Action:** Stripe Atlas automatically files 83(b) for C-Corp founders as part of formation fee (USPS Certified Mail with tracking). Per official Atlas docs.
- **Consequence of missing:** every future equity appreciation gets taxed as ordinary income at vesting. For a $7M post-money company with 85% CEO stake, potentially 7-figure ordinary-income penalty over 4-year vest.
- **De-risk:** Atlas auto-filing removes CEO manual step. CEO still needs to verify USPS tracking confirms delivery within 30 days.
- **Blocker:** Atlas filing requires SSN or ITIN at moment of filing. CEO has neither. ITIN application (separate entry below) must complete BEFORE Atlas filing, OR CEO coordinates with Atlas on sequencing.
- **Owner:** Stripe Atlas (auto) + CEO (verify) + tax lawyer (confirm sequencing)
- **Trigger:** Stripe Atlas Incorporation complete (~30 days after filing paperwork)
- **Status:** NOT TRIGGERED YET. Source: https://docs.stripe.com/atlas/83b-elections-non-us-founders

### TBD — ITIN application (CEO has no US SSN)
- **Action:** apply for ITIN via IRS Form W-7, typically with first US tax return. Some startup-program portals require it before they can issue a 1099.
- **Consequence of missing:** ~6 week delay on any program payout that requires ITIN/SSN (most do); cannot open US personal account if needed.
- **Owner:** CEO
- **Trigger:** should START in parallel with Stripe Atlas filing, not after — processing time overlaps
- **Status:** NOT STARTED. Flag before Week 4 of audit mega-plan Phase D.

---

## Notes on discovery

New deadlines land here when:
- Legal filing is committed (SADPP, DPAs, privacy policy updates)
- A program is accepted and has reporting / utilization windows (e.g. credits expire)
- CEO announces a delivery target to a partner (WUF13 is one such)
- Atlas discovers a regulatory trigger date from CEO context

Atlas is responsible for proactively flagging the first entry within 14 days of `today` on each wake — this file is the source of truth, not memory.

---

## Archive

(empty — first revision)

## PROVISIONAL PATENT — CRITICAL (added 2026-04-16 Session 113)

**What:** File USPTO Provisional Patent Application for two mechanisms:
1. "Emotional decay modulation for AI memory prioritization"
2. "Hippocampal replay mechanism for autonomous knowledge consolidation"

**Clarification (2026-04-16 Session 114):** Product demo does NOT destroy patent. Only public disclosure of the SPECIFIC MECHANISM kills it — the formula, the architecture, the algorithm details. Showing VOLAURA on WUF13 = safe. Publishing a paper describing emotional decay math = destroys patent. Sharing pitch deck with mechanism details without NDA = destroys patent.

**Revised urgency:** NOT before WUF13. Before any: research publication, non-NDA pitch deck with architecture details, arXiv/blog post describing the mechanism, or open-source release of memory code.

**Deadline:** BEFORE first public technical disclosure (not product demo). No fixed date — triggered by CEO decision to publish research or share architecture externally.
**Cost:** $150 USPTO fee (micro entity rate for solo founder).
**Blocker:** Cash. Deferrable until funding arrives or CEO decides to publish.
**Draft:** Atlas can generate via Gemma4+Cerebras when ready.

**Rule for CEO:** At WUF13 — show the product, don't explain the engine. "AI-powered adaptive assessment" = safe. "We use emotional decay with multiplier formula for memory prioritization" = patent dead.

**Filed?** [ ] NO — deferred, not urgent until public technical disclosure planned

