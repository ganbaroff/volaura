# Atlas Deadlines

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

### 2026-06-13 — WUF13 Baku (public launch anchor)
- **Action:** VOLAURA product ready for first external user cohort. WUF13 is the press/partnership moment.
- **Consequence of missing:** no alternative launch moment with equivalent AZ-local media weight. Next window is roughly 12 months.
- **Owner:** CEO + Atlas
- **Prereqs:** all WUF13 P0 items in `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` closed (4 of 8 Atlas items done as of 2026-04-16; 4 still open: grievance admin UI, landing sample profile, ghosting grace, Art. 9 legal)
- **Status:** ON TRACK — Atlas items manageable. CEO legal items (SADPP, Soniox DPA) are the harder half.

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

**Why urgent:** ANY public disclosure (WUF13 demo, LinkedIn post, pitch deck, arXiv paper) before filing DESTROYS patent eligibility. Provisional costs $150, gives 12-month protection window.

**Deadline:** BEFORE WUF13 (May 15-17 2026). Ideally BEFORE any public mention.
**Cost:** $150 USPTO fee (micro entity rate for solo founder).
**Blocker:** Cash (CEO ~1000 AZN to month-end per Session 111).
**Draft:** Atlas can generate via Gemma4+Cerebras. CEO reviews + files through VOLAURA Inc. (Delaware C-Corp).

**Trigger for Atlas:** Every session start, check this deadline. If WUF13 < 14 days away and provisional NOT filed — escalate to CEO via Telegram.

**Filed?** [ ] NO — waiting for funds
