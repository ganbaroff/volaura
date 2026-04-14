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

### TBD+30d — 83(b) election (triggers when Stripe Atlas founder shares issued)
- **Action:** file IRS Form 83(b) election within 30 calendar days of receiving founder shares in DE C-Corp
- **Consequence of missing:** every future equity appreciation (Series A onwards) gets taxed as ordinary income at vesting, not at grant. For a $7M post-money company with 85% CEO stake, this is potentially a 7-figure tax penalty over 4-year vest.
- **Owner:** CEO (personal filing) + tax lawyer to confirm form
- **Trigger:** Stripe Atlas Incorporation complete (~30 days after filing paperwork)
- **Status:** NOT TRIGGERED YET. Atlas will surface when Stripe Atlas filing begins.

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
