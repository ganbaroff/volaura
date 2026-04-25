# Privacy Policy + ToS — Delaware C-Corp Diff (Pre-stage)

**Author:** Atlas (CTO-Hands) | **For:** CEO + US-AZ cross-border tax/privacy lawyer
**Date:** 2026-04-14
**Status:** DRAFT diff — not applied. Apply only when Stripe Atlas incorporation completes and DE C-Corp entity name + EIN are issued.

**Scope:** this document enumerates every concrete text change the current privacy policy (`docs/privacy-policy.md` + rendered at `apps/web/src/app/[locale]/(public)/privacy-policy/page.tsx`) will need once the Delaware C-Corp is the data controller. It does not change the controller responsibility — GDPR/AZ PDPA obligations follow the data, not the entity form.

**Companion document:** `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` #4 (Art. 9 health data consent) remains a legal review item; this diff is about entity-name / controller-address hygiene, not consent architecture.

---

## Section 1 — Who We Are

### Current (`docs/privacy-policy.md:11`)
> Volaura ("we", "our", "the Platform") is a verified competency platform for volunteers, operated by [Legal Entity Name Pending — GoldenByte LLC or new entity] in Azerbaijan. We help volunteers prove their skills and help organizations find verified talent.

### Proposed (post-DE incorporation)
> VOLAURA ("we", "our", "the Platform") is a verified professional talent platform operated by **VOLAURA Inc.**, a Delaware C-Corporation (Registered Agent: Stripe Atlas / A Registered Agent Inc., 1209 Orange Street, Wilmington, Delaware 19801, USA; EIN: [EIN_PENDING_ISSUANCE]). Day-to-day operations are run from our office in Baku, Azerbaijan, which is where product development, assessment engineering, and user support take place. For EU/EEA and UK users, our EU representative is [TBD — required under GDPR Art. 27, recommend Proton's EU Rep or Vercel's reseller].

### Rationale
- "verified competency platform for volunteers" — wrong positioning (Constitution lock: "verified professional talent platform"). Also count: 9 occurrences of "volunteer" need replacement.
- `[Legal Entity Name Pending]` — must name the actual data controller.
- DE C-Corp is the legal person; AZ office is operational location. Separate clearly — GDPR cares about the controller, not the server room.
- Art. 27 EU representative is mandatory once a non-EU controller offers services to EU users. Not nice-to-have.

---

## Section 2 — Contact / Address

### Current (`docs/privacy-policy.md:13-14`)
> **Contact:** privacy@volaura.az
> **Address:** Baku, Azerbaijan (full address on entity registration)

### Proposed
> **Data Protection Contact:** privacy@volaura.app
> **Legal Entity:** VOLAURA Inc., Delaware C-Corp, Registered Agent 1209 Orange Street, Wilmington DE 19801, USA
> **EU Representative (GDPR Art. 27):** [TBD_EU_REP]
> **Operational address:** Baku, Azerbaijan — [full address]

### Rationale
- `.az` → `.app`: our user-facing domain is `volaura.app`, policy should match (reduces phishing-lookalike confusion).
- Two-address model: Delaware for legal service, Baku for operations. Both visible so a regulator or user knows where to send mail.

---

## Section 3 — International Transfers (NEW SECTION)

Current policy has NO international-transfer section. GDPR Art. 46 requires one.

### Proposed new section (insert after §3 "How We Use Your Data")
> ### 3a. International Data Transfers
>
> Your personal data is primarily processed in the United States (our backend is hosted on Railway, US region; our primary database is Supabase, US region) and Azerbaijan (where our operational team reviews support and assessment quality).
>
> **EU/EEA → US transfers** rely on the EU-US Data Privacy Framework (2023/1795) through our sub-processors where available, and Standard Contractual Clauses (EU 2021/914, Module 1) where it is not. We maintain a current list of sub-processors at [TBD_SUBPROCESSOR_LIST_URL] and update it at least quarterly.
>
> **Azerbaijan transfers** are made under Article 15 of the AZ "On Personal Data" Law (2010) with a cross-border transfer notification filed with SADPP (State Agency for Personal Data Protection).
>
> You can request the full text of our SCCs or the DPF self-certification by emailing privacy@volaura.app.

### Rationale
- Once DE is the controller and Railway/Supabase are US sub-processors, every EU user's data crosses the Atlantic. Silent transfers = GDPR violation.
- AZ PDPA cross-border notification is current launch P0 #5 — connects this diff to the broader pre-launch tracking.

---

## Section 4 — LLM Processor Disclosure (NEW SECTION)

Catalog audit §5 flagged that accepting Google AI / OpenAI / Anthropic credits means LLM vendor processes user text. Privacy policy currently has no mention of this.

### Proposed new section (insert after §2.3 "Technical Data")
> ### 2.5 Automated Decision-Making and LLM Processing (GDPR Art. 22)
>
> When you complete an assessment, open-ended answers are evaluated by large-language models operated by third parties acting as our data processors under Article 28 agreements:
>
> - **Google (Gemini)** — US, DPA: https://cloud.google.com/terms/data-processing-addendum
> - **Groq** — US, DPA: https://groq.com/data-processing-addendum
> - **NVIDIA (NIM)** — US, DPA: https://www.nvidia.com/nvidia-dpa
> - **OpenAI** — US (used only when Gemini/Groq rate-limit, one-call passthrough), DPA: https://openai.com/policies/data-processing-addendum
> - **Anthropic** — US (used ONLY in internal development / support workflow, never to evaluate your answers)
>
> Each processor is bound by a written agreement (GDPR Art. 28) that prohibits training on your data or using it outside the scope of our instructions. You can object to automated evaluation at any time by contacting privacy@volaura.app — in which case your assessment is reviewed manually within 30 days, subject to GDPR Art. 22 safeguards.

### Rationale
- Constitution Article 0 provider hierarchy is operational truth — policy must match.
- Art. 22 "right to human review" is a must-have before first user completes assessment. Current launch P0 #4.
- Explicit DPA links let a regulator verify our sub-processor chain in minutes, not days.

---

## Section 5 — Data Retention Matrix (UPDATE)

### Current (`docs/privacy-policy.md:40-44`)
| Data | Purpose | Retention |
|------|---------|-----------|
| IP address | Rate limiting, fraud prevention | 30 days |
| Session logs | Security auditing | 90 days |
| Error logs | Platform reliability | 30 days |

### Proposed additions
Add rows:
| Data | Purpose | Retention |
|------|---------|-----------|
| Assessment answers (raw text) | AURA score computation + audit trail for grievance (Art. 22) | Until user deletes account OR 7 years (whichever is shorter, ISO 10667-2 §6 recordkeeping) |
| Grievance records | Regulatory audit (ISO 10667-2) | 7 years from resolution |
| LLM evaluation logs (concept_scores, no raw answer) | Calibration, transparency page "show your work" | Until user deletes account |
| character_events stream (cross-product bus) | Ecosystem sync with MindShift / Life Sim / BrandedBy | Until user deletes account from VOLAURA |

### Rationale
- ISO 10667-2 §6 requires a 7-year recordkeeping minimum for psychometric test results — longer than my initial draft, but not negotiable for "verified" positioning.
- Grievance records (added this session, commit `9e19d47`) inherit the same 7-year minimum.
- character_events already flows to other products; retention must be disclosed (user can't delete MindShift records by deleting VOLAURA account, or vice versa).

---

## Section 6 — Supervisory Authority (UPDATE)

### Current (`docs/privacy-policy.md:169`)
> In Azerbaijan: [relevant authority TBD on entity registration].

### Proposed
> **Azerbaijan:** State Agency for Personal Data Protection (SADPP), Baku.
> **EU/EEA:** your local Data Protection Authority (contact list: https://edpb.europa.eu/about-edpb/about-edpb/members_en).
> **UK:** Information Commissioner's Office (ICO), https://ico.org.uk/global/contact-us/.
> **US:** Federal Trade Commission (FTC) — for complaints about unfair or deceptive data practices: https://www.ftc.gov/. Delaware Attorney General's Consumer Protection Unit for state-level issues.

### Rationale
- Once DE C-Corp is the entity, US regulators have jurisdiction alongside GDPR/AZ PDPA. Must list them.

---

## Terms of Service — parallel diff (docs/tos.md — not yet written)

Current state: no ToS document in repo. This is itself a blocker. When DE C-Corp activates, CEO must add a ToS that:

1. Names VOLAURA Inc. as the contracting party.
2. Choice of law: Delaware. Choice of forum: state courts of New Castle County OR arbitration under AAA Commercial Rules (pick one — binding arbitration reduces class-action exposure but annoys some EU users).
3. Explicit user consent for automated decision-making under Art. 22 (matches Privacy Policy §2.5).
4. Export restrictions acknowledgment (US CISA / OFAC — Azerbaijan is not sanctioned, but our sub-processors may restrict certain jurisdictions).
5. Account termination + deletion procedures (already specified operationally via `DELETE /api/auth/me`, needs textual surface).

**Recommendation:** commission a template from the US-AZ cross-border lawyer shortlist (Phase C deliverable). Template cost: $500–1500. Review cost: 1 hour at lawyer hourly rate.

---

## Application procedure

1. CEO files Stripe Atlas (Phase D in audit mega-plan)
2. DE entity certificate + EIN issued (~30 days)
3. On issuance day: apply this diff to `docs/privacy-policy.md` + corresponding `apps/web/src/app/[locale]/(public)/privacy-policy/page.tsx` + i18n AZ/RU translations
4. Add ToS (new file, based on lawyer template)
5. Update CookieConsent banner + signup flow consent copy to match new ToS/Policy version string
6. Bump policy version from 1.0 → 2.0
7. Email all existing registered users with "our legal entity has changed" notice — GDPR Art. 13(3) requires notifying when the controller changes, even if services unchanged

---

## What this diff does NOT cover

- GDPR Art. 9 "health data" consent architecture — that's a separate legal decision (is `energy_level` Art. 9 sensitive? probably yes under broad reading). Needs counsel, not text hygiene.
- Children under 16 — current policy doesn't restrict age. If any EU/UK user signup <16 triggers GDPR-K consent mechanism. Needs age gate decision.
- Crystal economy monetary characterization — if crystals ever become redeemable for fiat, this becomes a FinCEN/CBAR issue, not a privacy one. Out of scope here.
- Criminal background checks for reliability signals — if this ever ships, Art. 10 "special category" unlocks. Hypothetical.
