# VA — Legal Track Ops Manager — VOLAURA — 2026-06-07

**Owner:** CEO (Yusif). **Operates with:** [legal-engagement-brief-2026-06-07.md](./legal-engagement-brief-2026-06-07.md).

## Why hire a VA right now

The single remaining launch blocker is **external legal/compliance** (AZ PDPA + SADPP filing, EU GDPR Art. 9 / Art. 22 / AI Act classification, vendor DPA review). The repo already contains a Legal Engagement Brief, drafts, and a counsel shortlist. What's missing is the **operational layer**: someone who calls the lawyers, schedules intro consults, sends document bundles, follows up, and tracks status.

That layer is the founder bottleneck. A Virtual Assistant ($100–160/mo via Upwork or OnlineJobs.ph) closes it without requiring a hire commitment, equity dilution, or full-time salary. ROI breakeven: ~10 founder-hours saved per month.

This doc is the recipe to post the job, screen applicants, and run the first month.

## Scope — what the VA does

1. **Counsel outreach.** Contact 3 lawyers from `docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md` (Tier 1 + Tier 4 AZ). Send the Legal Engagement Brief + the optional supporting context list. Schedule 60–90 min intro consults on CEO's calendar.
2. **Document packet prep.** For each scheduled call: assemble the exact file packet listed in §"What to review" of the brief. Convert to PDF if requested. Share via the secure channel each firm prefers (most use email + DocuSign).
3. **Follow-up.** After each call: collect the lawyer's written response (memo / redline / quote). Log in a single tracking sheet. Chase if no response within 7 days.
4. **Scheduling logistics.** Time zones (Baku UTC+4, NJ UTC-5, EU UTC+1). Calendar invites with the exact Zoom link. Reminder 24h before.
5. **Status reporting to CEO.** One short Telegram message per workday: who replied, who needs chasing, what decisions are needed from CEO this week.

## Scope — what the VA does NOT do

- Does NOT give legal advice (the VA is operational, not licensed).
- Does NOT negotiate fees beyond the engagement model in the shortlist doc.
- Does NOT access production data, secrets, or `.env` files. Read access to public-facing repo docs + the legal brief packet ONLY.
- Does NOT speak on behalf of VOLAURA, Inc. publicly (no press, no social, no LinkedIn outreach).
- Does NOT touch code, design, or product surfaces.

## Upwork job description (post verbatim)

> **Title:** Legal-Track Operations Assistant — Privacy / GDPR / Cross-Border Counsel Outreach
>
> **Hours:** ~20 hours/month, async, flexible.
>
> **Rate:** Open to proposals; my budget range is $5–8/hour.
>
> **About:** I'm the solo founder of a verified professional talent platform (assessment + AURA score + org discovery). Pre-launch. Delaware C-Corp, based in Baku, Azerbaijan. EU users in scope after AZ launch.
>
> **Task:** Help me run intro consults with 3 specific lawyers from a shortlist I'll provide. You will: send a pre-written briefing packet to each, schedule 60–90 min consults on my calendar (Baku UTC+4), follow up to collect written memos, and keep a status log.
>
> **What I'm NOT asking you to do:** give legal advice, negotiate fees, touch product code, speak publicly on my behalf.
>
> **Required skills:**
> - Native or fluent English (written, professional tone).
> - Experience scheduling across time zones (US East, EU, AZ).
> - Comfortable with email + Calendly/Google Calendar + Google Docs / Notion.
> - Discretion: you'll see business names and contract drafts — NDA on day 1.
>
> **Nice to have:**
> - Russian or Azerbaijani for local counsel calls.
> - Prior experience with US/EU privacy law projects (you're operational, not advisory).
>
> **Starter task (paid, ~1 hour):** I'll send you the briefing packet and shortlist. Draft a 5-line outreach email template I can review, and propose a scheduling cadence. If we click, we continue.
>
> **Reply with:**
> 1. Your time zone and weekly availability.
> 2. One example of similar scheduling/coordination work you've done.
> 3. Your hourly rate.

## Screening questions (5 short)

Before hiring, ask candidates to reply with 1–2 sentences each:

1. Describe a time you coordinated a multi-party call across at least 3 time zones. What broke and how did you fix it?
2. How do you handle a vendor (here: a lawyer) who hasn't replied for 7 days?
3. You receive a draft contract by email. What do you NOT do with it?
4. Translate this Russian sentence to English: «Юрист обещал ответить до пятницы». (Filter: Russian-fluent helpful but not required; English answer must be clean.)
5. What's your hard limit per week, and what's the earliest you can start?

**Red flags:**
- Asks to draft legal opinions, marketing copy, or strategic decisions ("scope creeper").
- No portfolio of prior coordination work ("first gig").
- Suggests forwarding to "their team" without naming them.

## Weekly workflow (CEO ↔ VA)

| Day | VA action | CEO action |
|---|---|---|
| Mon | Status digest (Telegram, ≤5 lines): who replied, who is chasing. | Reads digest, replies with any decisions. |
| Tue–Thu | Outreach + follow-ups + scheduling. Adds to shared tracking sheet. | None unless flagged. |
| Fri | Final wrap of the week: which lawyers responded with memos, what's blocked, what needs CEO this weekend. | 15-min review. Authorizes next-week outreach. |

## Tracking sheet (Google Sheet, VA-maintained)

Columns: lawyer name | firm | tier | first-contact date | reply date | scheduled call date | call held | memo received | quote received | follow-up due | status (open/closed/blocked).

Initial rows: prefilled with the 8 firms from `US-AZ-TAX-LAWYERS-SHORTLIST.md`. VA contacts Tier 1 + Tier 4 first (3 firms). Tier 2 and 3 only if Tier 1 doesn't engage.

## Budget envelope

| Item | Monthly |
|---|---|
| VA hours (~20h × $5–8/h) | $100–160 |
| Calendly or equivalent | $0 (free tier OK) |
| Google Workspace already paid | $0 incremental |
| **Total** | **$100–160/mo** |

Compared to: $750–$8000 flat-fee per lawyer engagement from the shortlist. VA cost is ~2% of the legal spend it unblocks.

## Confidentiality

- NDA on day 1 (template: simple mutual NDA, US+AZ jurisdiction; Bosin LLC or any of the shortlist firms can provide one for ~$200).
- VA receives ONLY: this VA doc, the Legal Engagement Brief, and the public lawyer shortlist. NOT: production secrets, `.env`, user data, financial records.
- All shared docs via Google Workspace with viewer-only permissions.
- On termination: revoke Workspace access same day.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| VA misrepresents themselves as legal counsel | JD explicitly bans this. Each outreach email signed "operational assistant to CEO." |
| Lawyer takes call, doesn't deliver memo | 7-day follow-up rule. Move to next firm after 14-day silence. |
| VA scope creep into "advice giving" | Weekly Friday review specifically asks "did the VA give advice this week? if yes, correct." |
| Time-zone disasters | All scheduling done in CEO's calendar with Baku as primary. VA must confirm timezone in writing for each call. |
| Onboarding theft / payment fraud on Upwork | Starter task is paid via Upwork escrow, never direct payment. Verify Upwork badge + 5+ five-star reviews before hiring. |
| Lawyer asks for production access | VA does NOT have it to share. Routes the request back to CEO. |

## First-month milestones

- **Week 1:** Hired + onboarded + NDA signed + outreach to Tier 1 (Bosin LLC + Faison Law) sent.
- **Week 2:** First intro call scheduled. Tier 4 (Kesikli AZ + CEO's AZ network contact) outreach sent.
- **Week 3:** At least 1 written memo received. Tracking sheet has 4+ rows in progress.
- **Week 4:** Decision point: continue past month 1, or release. By end of month 1, CEO should have written legal verdict on Art.9 + SADPP from at least one AZ-side firm.

## Failure trigger — when to fire the VA

Fire if any of:
- Gave or paraphrased legal advice to CEO or any third party.
- Shared the Legal Engagement Brief or any repo content outside the 8 firms on the shortlist.
- Missed 2 weekly digests without notice.
- Quote/memo received from 0 firms after 3 weeks of paid work.

## Hiring CEO actions (this week, in order)

1. Read `docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md` §"Recommended engagement model" + §"CEO action (this week, ~30 min)" — reconfirm Tier 1 + Tier 4 picks.
2. Post the JD above on Upwork. Set proposal limit to 10. Filter applicants by ≥90% Job Success, English-fluent, time-zone overlap with Baku 9am–6pm.
3. Shortlist 3 candidates. Send the 5 screening questions.
4. Pay the starter task to the top candidate ($5–8). Review their email draft + cadence proposal.
5. Hire if the starter task is clean. Send NDA + Legal Engagement Brief + this VA doc.

## Why this is the right shape now

The MCP-courier and signed-handoff work just removed CEO from the **Atlas↔Codex** message bus. This VA work removes CEO from the **CEO↔external-lawyer** message bus. Same shape, different axis: in both cases, the founder stops being the data path so the founder can be the decision-maker.

Both protocols co-exist with `memory/atlas/handoffs/README.md` (CEO-courier across AI tools) and `docs/AGENT-BRIEFING-TEMPLATE.md` (agent prompt). They cover different relay paths, not duplicates.

## Cross-references

- [legal-engagement-brief-2026-06-07.md](./legal-engagement-brief-2026-06-07.md) — the brief the VA carries to the lawyers
- [`docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md`](../../../docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md) — the list of 8 firms
- [`docs/PRE-LAUNCH-BLOCKERS-STATUS.md`](../../../docs/PRE-LAUNCH-BLOCKERS-STATUS.md) — what the lawyers are actually clearing (#4 Art.9, #5 SADPP, #6 vendor DPA)
- [`docs/COMPLIANCE-OPERATIONS-RUNBOOK.md`](../../../docs/COMPLIANCE-OPERATIONS-RUNBOOK.md) — operational compliance flows the lawyers will validate
