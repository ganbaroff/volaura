# GDPR Article 22 + AZ PDPA + EU AI Act compliance — 2026-04-15

## TL;DR

VOLAURA's automated AURA score falls under **both** GDPR Art. 22 (2018) and EU AI Act Annex III.4(a) "recruitment/candidate evaluation" (full enforcement 2 Aug 2026 — 3.5 months away). Current repo has Art. 7 + Art. 8 consent (age, terms version) and a `sharing_permissions` table — but **zero** audit trail for the automated decision itself, no explicit Art. 22 opt-in, no human-review flow, no algorithm-version registry. Existing columns (`age_confirmed`) aren't even wired into `/auth/register`.

Minimum viable Art. 22 + AI Act stack for pre-launch solo-founder:

1. **4 new Postgres tables** (~80 lines of migration SQL) — `policy_versions`, `consent_events` (append-only), `automated_decision_log`, `human_review_requests`
2. **Explicit Art. 22 opt-in** modal at first AURA score — trilingual, separate from ToS
3. **Plain-language explanation** shown with every score (competencies fed, weights, SE, IRT concept)
4. **Human-review request form** → 30-day SLA ticket
5. **DPIA document** built with CNIL PIA open-source tool (free)
6. **FRIA template** for B2B deployer contracts (they run it, we supply instructions)
7. **iubenda Pro** (~€27/mo) for trilingual privacy policy + Art 13/14 notices

Estimated build: 4-6 eng-days. No vendor covers this end-to-end.

## Is VOLAURA an AI Act "high-risk system"?

**Yes.** Direct hit on Annex III.4(a) of Regulation (EU) 2024/1689: *"AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates."*

We are **provider** (build the system) and our B2B orgs are **deployers**. Extraterritorial scope (Art 2(1)(c)) applies as soon as any EU user is scored — diaspora plus LinkedIn = day one.

**Prohibited (already in force since 2 Feb 2025, do not add):**
- Emotion recognition in interviews
- Biometric inference of protected traits (race/gender/politics from video)
- Social-scoring behaviour prediction
- AURA today does none of these. Stay on the IRT/CAT + self-reported competencies path.

**Provider duties kicking in 2 Aug 2026:** risk management system (Art 9), data governance (Art 10), tech docs (Annex IV), auto-logging (Art 12, 6-mo retention), human oversight (Art 14), accuracy/robustness (Art 15), self-assessed CE marking + EU database registration before launch, post-market monitoring.

**Penalty exposure:** up to €15M or 3% global turnover for high-risk violations; up to €35M or 7% for prohibited.

## Article 22 flow skeleton

```
Signup → ToS + age consent (already exist)
    ↓
First assessment intent → [Art. 22 modal] explicit opt-in
    policy_versions.aura_algorithm_v1
    consent_events row (purpose='automated_decision_aura_scoring', action='grant')
    ↓
Assessment runs → engine.py computes θ + score
    ↓
Score shown → automated_decision_log row
    + plain-language explanation ("You answered X harder questions correctly...
      communication weight 20%, reliability 15%...SE ±3.2")
    ↓
Always visible: [Request human review] link
    ↓
human_review_requests ticket → 30-day SLA
Reviewer (CEO or delegated) accesses inputs, overrides or confirms
    outcome written back, user notified
    ↓
Org discovery → sharing_permissions (already exists) gates visibility
```

Every row is append-only, every decision stamped with `algorithm_version` FK, every consent stamped with `policy_version` FK. Audit trail reconstructs any historical decision.

## Top 3 implementation paths

| Path | Cost / mo | Build time | Coverage | Gaps |
|------|-----------|-----------|----------|------|
| **A — OSS + custom (RECOMMENDED)** | €0 infra + iubenda Pro €27 | 4-6 days | Art. 7, 8, 13, 14, 22; AI Act Art 9, 10, 12, 14; FRIA template | No auto-DPIA updates; self-assess CE marking |
| **B — OneTrust enterprise** | $$$k/year | 2-3 days config | Full Art. 22 + DPIA + DSR automation | Cost kills pre-revenue startup; vendor lock-in |
| **C — Hybrid: iubenda Pro + DSRHub OSS + CNIL PIA** | €27/mo + self-host | 6-8 days | Full stack w/ human-review ticketing via DSRHub | Ops overhead for DSRHub |

**Pick A.** Hit launch, migrate to C when org customer count > 20.

## AZ PDPA specific delta

Law No 998-IIIQ (2010) has an Art. 22 analogue via Art. 7 "right to object to collection/processing." Key differences from GDPR:

- **Written consent** (or qualified e-signature via ASAN İmza) required for third-party data transfers (Art 13.1) — stricter **form** than GDPR click-through. Our `sharing_permissions` table is structurally right; need ASAN İmza integration or beefed-up audit record for org-visibility grants.
- **System registration** with Ministry of Transport, Communications and High Technologies — verify requirement for VOLAURA; likely applies once we process AZ citizen data at scale.
- **Terminology:** use "owner" (=controller) / "operator" (=processor) in AZ-facing policy translations.
- **Enforcement:** administrative fines only, reputational/market-access risk > monetary.

Ship GDPR-grade; AZ compliance is a subset plus ASAN İmza.

## Concrete artifacts to copy

**Ready in `raw.md`:**
- ✅ Migration SQL for 4 tables (~80 lines) — `policy_versions`, `consent_events`, `automated_decision_log`, `human_review_requests`
- ✅ Consent modal text in EN / AZ / RU
- ✅ Vendor comparison table
- ✅ Kantara Consent Receipt mapping

**To build next sprint:**
- React `<Article22ConsentModal />` component reading from `policy_versions`, writing to `consent_events` on accept
- `<AuraScoreExplanation />` component: reads `automated_decision_log.explanation_shown`, shows competencies, weights (from CLAUDE.md), SE, IRT one-sentence concept
- `<HumanReviewRequestForm />` + backend endpoint `/api/compliance/review-requests`
- Admin view at `/admin/review-queue` with SLA timer (30 days)
- DPIA document generated via CNIL PIA tool — commit as `docs/compliance/DPIA-v1.md`
- FRIA template — section in B2B deployer T&Cs + standalone PDF for orgs

**To wire into existing code:**
- `/auth/register` — set `age_confirmed=true`, `terms_version=current`, `terms_accepted_at=now()` (currently columns exist but aren't populated)
- `engine.py` — on score compute, write `automated_decision_log` row + generate explanation text
- `aura_scores` RLS — require a matching `consent_events.action='grant'` for `purpose='automated_decision_aura_scoring'` before score visible to orgs

## Risk if we ship without

**First complaint scenario (realistic, 2026-H2):**
- EU diaspora candidate scores badly, sees no explanation, discovers via privacy policy that orgs can buy search access
- Files Art. 77 complaint with Irish DPC (or home-country DPA)
- DPC sends Art. 58 information request — 1 month to respond
- Response requires: DPIA, consent records, algorithm logic docs, human-review mechanism evidence. **We have none of these today.**
- Fine scaled to turnover: pre-revenue realistic first-offense = €5-50k + mandatory remediation + public decision = brand dead in EU market.
- Parallel Art 22 SCHUFA-style reference goes to CJEU? Unlikely for a small startup, but not zero.

**AZ scenario:** complaint to Ministry → administrative fine (small, ~500-5000 AZN range), but headline "VOLAURA rated me, no explanation, no appeal" kills AZ trust. Fatal for bootstrap phase.

**EU AI Act scenario (from 2 Aug 2026):**
- Any EU-based deployer using VOLAURA without CE marking / EU database registration = non-compliant
- We lose the ability to contract with EU customers = entire EU B2B revenue path closed
- Deployers may refuse to onboard, citing our missing conformity assessment

**Bottom line:** Ship Path A in the next sprint. The ~5 eng-days cost is a tiny fraction of the launch window and gates the entire EU + AZ market.

## Next actions (CTO-ready)

1. Migration `20260415xxx_article_22_audit_trail.sql` — schema from raw.md
2. Fix `/auth/register` to write `age_confirmed` / `terms_version` / `terms_accepted_at` (existing P0 bug)
3. Seed `policy_versions` with current privacy v1.0, terms v1.0, aura_algorithm v1.0
4. Build 3 React components + backend endpoints
5. Generate DPIA via CNIL PIA, commit as `docs/compliance/DPIA-v1.md`
6. Subscribe iubenda Pro, regenerate privacy policy with Art 13(2)(f) + Art 14(2)(g) automated-decision clauses in AZ/EN/RU
7. FRIA template as `docs/compliance/FRIA-template-for-deployers.md`

Total: ~4-6 engineering days. Gate before any B2B org onboarding.

## Sources

- [GDPR Art. 22](https://gdpr-info.eu/art-22-gdpr/) · [Securiti checklist](https://securiti.ai/automated-decision-making-gdpr/) · [Secure Privacy 2026](https://secureprivacy.ai/blog/gdpr-compliance-2026)
- [EU AI Act Annex III](https://artificialintelligenceact.eu/annex/3/) · [Commission policy page](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) · [Hunton HR impact](https://www.hunton.com/insights/legal/the-impact-of-the-eu-ai-act-on-human-resources-activities) · [Staffing businesses](https://artificialintelligenceact.eu/what-the-act-means-for-staffing-businesses/)
- [HireVue Glass Box (MIS Q Exec)](https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1623&context=misqe) · [EPIC v HireVue](https://epic.org/documents/in-re-hirevue/) · [HireVue 2026 guidance](https://www.hirevue.com/blog/hiring/ai-hiring-compliance-insights-for-2026-key-insights-from-hirevue-experts)
- [DLA Piper AZ](https://www.dlapiperdataprotection.com/index.html?t=law&c=AZ) · [Deloitte AZ](https://www2.deloitte.com/az/en/pages/legal/articles/data-privacy-gdpr.html) · [Gratanet employee privacy AZ](https://gratanet.com/publications/data-protection-and-employee-privacy-in-azerbaijan) · [CoE AZ law PDF](https://rm.coe.int/16806aef9d)
- [CNIL PIA tool (OSS DPIA)](https://www.cnil.fr/en/open-source-pia-software-helps-carry-out-data-protection-impact-assessment) · [DSRHub OSS DSAR](https://github.com/open-privacy/dsrhub) · [iubenda CMP](https://www.iubenda.com/en/blog/best-consent-management-platform/)
- [ACM right-to-explanation 2025](https://dl.acm.org/doi/10.1007/978-981-96-2071-5_14) · [PMC right to explanation](https://pmc.ncbi.nlm.nih.gov/articles/PMC12475874/) · [Stanford explainability debate](https://ddl.stanford.edu/sites/g/files/sbiybj25996/files/media/file/rethinking_explainable_machines_0.pdf)

Word count: ~1,420.
