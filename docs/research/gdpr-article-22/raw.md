# Raw research — GDPR Article 22 + AZ PDPA + EU AI Act

Date: 2026-04-15
Time spent: ~25 min
Research method: WebSearch (6 queries) + repo read (auth.py, 3 migrations, Constitution grep)

## 1. Existing VOLAURA state (verified by code read)

### Migrations with consent/privacy touch
- `20260403000003_gdpr_consent_columns.sql` — profiles: `age_confirmed`, `terms_version` (default '1.0'), `terms_accepted_at`. Covers Art. 7 (proof of consent) + Art. 8 (16+ age). Does **not** cover Art. 22.
- `20260325000021_add_privacy_role_visibility.sql` — `sharing_permissions` table (user × org × permission_type). This is org-visibility consent, not automated-decision consent. Well-designed with RLS.
- `20260409000001_health_data_firewall.sql` — Art. 9 health-data blocklist at DB level. Excellent.
- No migration for: automated-decision consent, algorithm version tracking, explanation logs, human-review requests.

### auth.py state
- `/auth/register` accepts username/email/password only. No Article 22 opt-in, no privacy version, no record of automated-decision consent.
- `age_confirmed` column exists in DB but `register` endpoint does not write it — **gap**: column added but not wired into signup payload.
- `DELETE /auth/me` cascades via Supabase admin — GDPR Art. 17 (erasure) OK.

### Constitution (docs/ECOSYSTEM-CONSTITUTION.md) privacy lines
- Line 234: "Privacy panel with granular data sharing toggles (pre-org-search blocker)"
- Line 299: voice data = Art. 9 biometric → Soniox/Deepgram DPAs = PRE-LAUNCH P0
- Line 420: "Informed consent must disclose AI processing explicitly" (ISO 10667-2 gap noted)
- Line 431-432: Open Badges 3.0 Achievement objects + credentialStatus revocation endpoint (half-life decay)

**Conclusion:** Constitution already flags the gap. No code implements it.

---

## 2. GDPR Article 22 — what the law actually requires

Text: Data subject has right not to be subject to a decision based **solely** on automated processing that produces **legal effects** or **similarly significantly affects** them.

Three lawful grounds (Art 22(2)): (a) contractual necessity, (b) statutory authorization, (c) **explicit consent**.

When lawful, controller must:
- Provide meaningful information about **logic involved** + significance + envisaged consequences (Art 13(2)(f), 14(2)(g), 15(1)(h))
- Implement **suitable safeguards**: right to human intervention, right to express view, right to contest the decision (Art 22(3))
- Document DPIA (Art 35)
- Cannot use special-category data (Art 9) as basis without Art 9(2)(a) explicit consent or Art 9(2)(g) substantial public interest

"Significantly affects" — WP29 guidelines + 2023 SCHUFA CJEU C-634/21 ruling extend this to credit scores + similar automated rating where third party relies on the score. **VOLAURA AURA score is analogous to SCHUFA**: an algorithmic rating that orgs rely on for hiring-adjacent decisions. SCHUFA precedent = AURA almost certainly triggers Art. 22.

### Rubber-stamping doctrine
Human review must be **meaningful** — authority to override, access to all inputs, not a checkbox. EPIC v. HireVue (2019 FTC complaint) made this specific: if human reviewer cannot access training factors, the review is invalid.

### "Right to explanation" — academic / regulatory consensus
- GDPR text = right to **meaningful information about logic**, not line-by-line algorithmic explanation
- AI Act reinforces this for high-risk systems
- France's Loi République numérique (1970s origin) is stricter: explanation required when decision taken **on the basis of** algorithmic treatment, not just solely
- Practical standard for AURA: plain-language description of which competencies fed the score, how weights combine (already public in CLAUDE.md), the IRT concept ("you answered harder questions correctly → higher ability estimate"), uncertainty interval (SE), not θ values

### No plug-and-play OSS React/Next.js Article 22 template exists
Searched: no github repo ships "Privacy Notice + Opt-in + Explanation + Human Review" flow end-to-end.
Closest proxies:
- **Kantara Consent Receipt Specification** — open schema for machine-readable consent receipts. Good reference for our `consent_events` table.
- **DSRHub** (github.com/open-privacy/dsrhub) — DSAR workflow orchestration on top of uTask. Overkill for solo-founder pre-launch but good reference architecture.
- **CNIL PIA tool** — open-source DPIA builder, French gov. Use it to generate our DPIA document (free, no vendor lock-in).

---

## 3. EU AI Act — VOLAURA classification

### Annex III, Category 4(a) high-risk includes:
> "AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates"

VOLAURA org search = "evaluate candidates by verified AURA score." **Direct hit on Annex III.4(a).**

### Classification answer: YES, high-risk.
- We are the **provider** (we build the system) AND our B2B orgs are **deployers** (they use it for hiring decisions)
- Solo-founder, EU users via diaspora → extraterritorial reach applies (Art 2(1)(c) — output used in EU)

### Timeline
- 2 Feb 2025: prohibited practices in force (emotion recognition, social scoring, biometric inference of protected traits) — **VOLAURA does none of these today. Don't add them.**
- 2 Aug 2026: Annex III high-risk obligations **fully enforceable** — 3.5 months from today if we're EU-exposed
- EU AI Act Digital Omnibus (Nov 2025) proposed to push deadline but not enacted. Plan to hit 2 Aug 2026.

### Provider obligations (we are one)
1. **Risk management system** (Art 9) — lifecycle, documented
2. **Data governance** (Art 10) — training data bias checks, representativeness
3. **Technical documentation** (Art 11 + Annex IV) — system architecture, algorithm logic, validation data
4. **Record-keeping** (Art 12) — automatic logs, 6-month minimum retention
5. **Transparency + instructions for use** (Art 13) — given to deployers
6. **Human oversight** (Art 14) — designed into the system
7. **Accuracy, robustness, cybersecurity** (Art 15)
8. **Conformity assessment + CE marking** (Art 43) — self-assessment route available for Annex III non-biometric
9. **EU database registration** (Art 49, Art 71) — before market placement
10. **Post-market monitoring** (Art 72)
11. **Serious incident reporting** (Art 73)

### Deployer obligations (our B2B customers)
- Inform candidates AI is used
- Monitor for discrimination
- Maintain logs
- DPIA under GDPR Art 35 (AI Act requires this when AI Act + GDPR overlap)
- **Fundamental Rights Impact Assessment (FRIA)** (Art 27) — before first use
- AI literacy training for staff (Art 4 — already in force since Feb 2025)

### Penalties
- Prohibited practices: up to €35M or 7% global turnover
- High-risk violations: up to €15M or 3% global turnover
- Wrong info to authorities: up to €7.5M or 1%

---

## 4. AZ PDPA — delta from GDPR

### Baseline
Law No 998-IIIQ of 11 May 2010. Pre-dates GDPR. Enforced via Administrative Violations Code (weaker teeth).

### Rights overlap
AZ law grants: right to be informed, access, rectification, erasure, object, **right not to be subject to automated decision-making**, complaint. So AZ has an Art 22 analogue via Article 7 of the law (right to object) — but less detailed than GDPR Art 22.

### Key differences
- **Terminology:** "owner" / "operator" (not controller/processor)
- **Written consent mandatory** for transfer to/from third parties (Art 13.1) — stricter in **form** than GDPR (written or qualified e-signature). Our click-through consent likely non-compliant for third-party transfers — workaround: keep processing in-house or use enhanced e-signature via ASAN İmza.
- **Registration:** data processing systems may require registration with Ministry of Transport, Communications and High Technologies. Check if VOLAURA qualifies.
- **No formal DPO requirement**, no 72h breach notification timeline, no GDPR-scale fines.
- **Enforcement:** administrative fines only, small by EU standards. Real risk = reputational + getting pulled out of AZ market by regulator.

### VOLAURA practical stance
Ship GDPR-grade compliance; AZ layers on as a subset. Add written-consent flow for **third-party data sharing** (org discovery of candidate profile) — not just generic ToS click-through. `sharing_permissions` table already handles this structurally — need ASAN İmza integration or strengthened audit record.

### Sources
- DLA Piper Data Protection Handbook — Azerbaijan country chapter
- Deloitte AZ "Data Privacy and GDPR" analysis
- CaseGuard Azerbaijani article
- Gratanet publication on employee data
- Council of Europe archived law text (rm.coe.int/16806aef9d)

---

## 5. Peer products — what do they actually do?

### HireVue
- SOC 2 Type II + ISO 27001 + FedRAMP + US Data Privacy Framework certified
- "Glass box" AI transparency approach (Tarafdar et al., MIS Quarterly Executive 2025) — 5 types of transparency (design, development, interface, client-facing, regulator-facing)
- EPIC 2019 FTC complaint → HireVue dropped facial analysis in 2021
- Consent is part of T&Cs when applicant initiates video interview — **same mistake VOLAURA would make**. Not Art-22 explicit consent.
- 2026 compliance guidance emphasizes: candidate transparency, opt-out alternative, bias monitoring, documentation (FEHA 4-year retention), Illinois AI Act (no ZIP-code proxies)

### Pymetrics (now part of Harver)
- Multivariate ANOVA / Hotelling's T² bias testing, anonymizes candidates
- Focused on US 4/5ths rule (EEOC), not EU equality law
- No published Art 22-specific flow

### LinkedIn Skills Assessments, Coursera, Credly
- No public architecture docs on Art 22 flow — all bury consent in T&Cs
- Open Badges 3.0 (1EdTech) — Achievement object + credentialStatus revocation endpoint = formal standard we can adopt

**Takeaway:** Even billion-dollar products hide behind T&Cs click-through. Industry standard is weak. VOLAURA doing it **right** is a moat, not a blocker.

---

## 6. Vendors — solo-founder cost fit

| Vendor | Free tier? | Pricing | Art 22 coverage |
|--------|-----------|---------|-----------------|
| **iubenda** | Yes (low-traffic) | ~€4.99/mo starter, ~€27/mo Pro | Generates privacy policy w/ AI-processing clause; no Art 22-specific flow component |
| **Termly** | Yes (CMP + basic policy) | $10-15/mo | Cookie-centric, weaker Art 22 |
| **OneTrust** | No published pricing | Enterprise only (~$$$k/yr) | Full DPIA + DSR automation. Overkill. |
| **Vanta / Drata / Delve** | No | $6-20k/yr | SOC 2 + ISO focused, privacy adjacent |
| **CNIL PIA** | Free OSS | Free | DPIA builder only (French gov) |
| **DSRHub (OSS)** | Free | Self-host | DSAR workflow; needs devops |

**Recommendation:** iubenda Pro (~€27/mo) for privacy policy + consent records + multi-lingual (AZ/EN/RU). Combine with **custom** React component for Art 22 explicit opt-in + explanation (no vendor covers this well for hiring-adjacent scoring).

---

## 7. Audit-trail schema — proposed VOLAURA addition

```sql
-- New migration: 20260415000001_article_22_audit_trail.sql

-- 1. Policy / algorithm version registry (one row per published version)
CREATE TABLE public.policy_versions (
    id              TEXT PRIMARY KEY,           -- e.g. 'privacy-v1.0', 'aura-algo-v2.1'
    kind            TEXT NOT NULL CHECK (kind IN ('privacy', 'terms', 'aura_algorithm', 'ai_disclosure')),
    version         TEXT NOT NULL,
    published_at    TIMESTAMPTZ NOT NULL,
    content_hash    TEXT NOT NULL,              -- sha256 of the actual text / algo config
    content_url     TEXT,                       -- pointer to the canonical text
    superseded_by   TEXT REFERENCES public.policy_versions(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 2. Append-only consent events (explicit opt-in/opt-out/update)
CREATE TABLE public.consent_events (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    purpose         TEXT NOT NULL CHECK (purpose IN (
        'automated_decision_aura_scoring',
        'org_discoverability',
        'third_party_data_sharing',
        'marketing',
        'analytics'
    )),
    legal_basis     TEXT NOT NULL CHECK (legal_basis IN ('consent', 'contract', 'legitimate_interest', 'legal_obligation')),
    action          TEXT NOT NULL CHECK (action IN ('grant', 'withdraw', 'update')),
    policy_version  TEXT NOT NULL REFERENCES public.policy_versions(id),
    ui_locale       TEXT NOT NULL,              -- 'az', 'en', 'ru'
    source_ip       INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON public.consent_events (user_id, created_at DESC);
CREATE INDEX ON public.consent_events (purpose, action);
REVOKE UPDATE, DELETE ON public.consent_events FROM PUBLIC;  -- append-only

-- 3. Automated decision log (one row per AURA score produced)
CREATE TABLE public.automated_decision_log (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id          UUID REFERENCES public.assessment_sessions(id),
    decision_type       TEXT NOT NULL CHECK (decision_type IN ('aura_score', 'badge_tier', 'discoverability')),
    algorithm_version   TEXT NOT NULL REFERENCES public.policy_versions(id),
    input_summary       JSONB NOT NULL,          -- competency scores, item count, SE
    output              JSONB NOT NULL,          -- total score, tier, confidence
    explanation_shown   TEXT,                    -- the plain-language text user saw
    consent_event_id    BIGINT REFERENCES public.consent_events(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON public.automated_decision_log (user_id, created_at DESC);
REVOKE UPDATE, DELETE ON public.automated_decision_log FROM PUBLIC;

-- 4. Human-review requests (contest a decision)
CREATE TABLE public.human_review_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    decision_id     BIGINT NOT NULL REFERENCES public.automated_decision_log(id),
    reason          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_review', 'resolved_confirmed', 'resolved_overturned', 'withdrawn')),
    sla_due_at      TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days'),
    resolved_at     TIMESTAMPTZ,
    reviewer_id     UUID REFERENCES auth.users(id),
    reviewer_notes  TEXT,
    outcome_summary TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON public.human_review_requests (status, sla_due_at);
```

Rationale:
- `policy_versions` = single source of truth for what we published when → every consent and every decision points at it
- `consent_events` append-only = Kantara consent-receipt-compatible
- `automated_decision_log` = AI Act Art 12 (record-keeping) + GDPR Art 22 audit
- `human_review_requests` = Art 22(3) contest mechanism w/ 30-day SLA

---

## 8. Consent text drafts (AZ / EN / RU)

### Short (modal) — EN
> VOLAURA calculates your AURA score (0–100) and badge tier automatically based on your assessment answers. This score can be used by organizations that search for talent, which may affect opportunities offered to you. You can opt out, request human review of any score, and get a plain-language explanation at any time. Learn more: [link]. ☐ I understand and consent.

### AZ (20-30% longer, Azerbaijani)
> VOLAURA qiymətləndirmədəki cavablarınız əsasında AURA balınızı (0–100) və nişan səviyyənizi avtomatik olaraq hesablayır. Bu bal sizi axtaran təşkilatlar tərəfindən istifadə oluna bilər və sizə təklif olunan imkanlara təsir göstərə bilər. İstənilən vaxt imtina edə, hər hansı balın insan tərəfindən yenidən baxılmasını tələb edə və sadə dildə izahat ala bilərsiniz. Ətraflı: [link]. ☐ Başa düşürəm və razıyam.

### RU
> VOLAURA автоматически вычисляет ваш балл AURA (0–100) и уровень значка на основе ваших ответов в оценке. Этот балл могут использовать организации, ищущие таланты, что может повлиять на предлагаемые вам возможности. Вы в любой момент можете отозвать согласие, запросить человеческий пересмотр любого балла и получить объяснение простым языком. Подробнее: [link]. ☐ Понимаю и согласен.

All three must record: `policy_version`, `ui_locale`, `ip`, `user_agent`, `timestamp`, action='grant'.

---

## Sources

- [GDPR Art. 22 — gdpr-info.eu](https://gdpr-info.eu/art-22-gdpr/)
- [Securiti — Automated Decision-Making Compliance Checklist](https://securiti.ai/automated-decision-making-gdpr/)
- [Secure Privacy — GDPR 2026 Guide](https://secureprivacy.ai/blog/gdpr-compliance-2026)
- [EU AI Act Annex III](https://artificialintelligenceact.eu/annex/3/)
- [European Commission — AI Act policy page](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [Hunton — AI Act Impact on HR](https://www.hunton.com/insights/legal/the-impact-of-the-eu-ai-act-on-human-resources-activities)
- [AI Act — Staffing Businesses](https://artificialintelligenceact.eu/what-the-act-means-for-staffing-businesses/)
- [HireVue AI hiring compliance 2026](https://www.hirevue.com/blog/hiring/ai-hiring-compliance-insights-for-2026-key-insights-from-hirevue-experts)
- [Tarafdar et al. — HireVue Glass Box (MIS Quarterly Executive)](https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1623&context=misqe)
- [EPIC — In re HireVue FTC Complaint](https://epic.org/documents/in-re-hirevue/)
- [DLA Piper — Azerbaijan data protection](https://www.dlapiperdataprotection.com/index.html?t=law&c=AZ)
- [Deloitte AZ — Data Privacy and GDPR](https://www2.deloitte.com/az/en/pages/legal/articles/data-privacy-gdpr.html)
- [Gratanet — Data Protection and Employee Privacy in Azerbaijan](https://gratanet.com/publications/data-protection-and-employee-privacy-in-azerbaijan)
- [Caspian Legal Center — Data Protection Law in Azerbaijan](https://www.caspianlegalcenter.az/insights/more/personal-data-azerbaijan)
- [Council of Europe — AZ Law on Personal Data (PDF)](https://rm.coe.int/16806aef9d)
- [CNIL PIA Tool (open source DPIA)](https://www.cnil.fr/en/open-source-pia-software-helps-carry-out-data-protection-impact-assessment)
- [DSRHub — open DSAR orchestration](https://github.com/open-privacy/dsrhub)
- [iubenda](https://www.iubenda.com/en/blog/best-consent-management-platform/)
- [Termly vs iubenda](https://termly.io/resources/compare/termly-vs-iubenda/)
- [ACM — Right to Explanation under GDPR and AI Act (2025)](https://dl.acm.org/doi/10.1007/978-981-96-2071-5_14)
- [PMC — Right to Explanation in AI (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12475874/)
- [Stanford DDL — Explainable Machines GDPR](https://ddl.stanford.edu/sites/g/files/sbiybj25996/files/media/file/rethinking_explainable_machines_0.pdf)
- [Reform — Consent Records for GDPR Audits](https://www.reform.app/blog/5-steps-to-prepare-consent-records-for-gdpr-audits)
