# Legal Compliance Checklist — Azerbaijan Launch
**Updated:** 2026-04-13 | **Status:** Research complete. Action items ready.
**Decision:** Do ourselves, no external lawyer (CEO, 2026-04-12).

## 1. Azerbaijan Personal Data Law (Law No. 998-IIIQ, 2010)

### Registration (BLOCKING — must do before launch)
- [ ] **Register in State Register of Personal Data Operators** with Ministry of Digital Development and Transport
- Application must include: categories of data processed, purposes, storage location, security measures
- Processing is ILLEGAL without registration. Absence = administrative liability regardless of harm.
- Timeline: 1 month from written application
- Portal: https://www.e-gov.az/en/content/read/13

### Consent
- [ ] **Written consent required** for collection and processing (electronic signature acceptable)
- [ ] Consent must be revocable — implement "delete my data" flow
- [ ] Consent form must state: what data, what purpose, how long, who has access
- [ ] Separate consent per purpose (assessment ≠ marketing ≠ cross-product sharing)

### DPO Equivalent
- [ ] **Appoint a responsible person** for personal data protection within org
- Functionally similar to GDPR DPO. Can be CEO initially.

### Automated Decision-Making
- [ ] Users have right NOT to be subject to automated decisions
- AURA score = automated assessment = directly affected
- [ ] Implement: "Request human review" button on assessment results
- [ ] Disclose in ToS: "Your score is calculated by AI. You can request human review."

### Cross-Border Transfer
- [ ] Verify Supabase region (AWS eu-central-1) = adequate protection country
- [ ] If hosting outside AZ: document legal basis for transfer
- [ ] No transfer that compromises national security or public order

### Penalties
- Administrative fines: AZN 300-50,000 ($180-$29,400)
- Criminal: up to 7 years imprisonment for serious violations
- Risk level for VOLAURA: LOW if registered and consented. HIGH if not registered.

## 2. GDPR Compliance (for EU users / EU data subjects)

### Why It Applies
If ANY EU citizen uses VOLAURA (diaspora, travelers, partner orgs), GDPR applies. We must comply even without EU entity.

### Key Requirements
- [ ] **Article 5(1)(b) — Purpose limitation:** Data collected for assessment CANNOT be used for cross-product features without separate consent
- [ ] **Article 22 — Automated individual decision-making:** AURA score used for hiring recommendations = Art 22. Must provide: meaningful info about logic, significance, envisaged consequences
- [ ] **Article 9 — Special categories:** If assessment touches health, religion, political opinion → explicit consent required
- [ ] **Privacy Policy:** Must be GDPR-compliant (already drafted: `docs/legal/Privacy-Policy-draft.md`)
- [ ] **Right to erasure (Art 17):** Implement account deletion that removes ALL data
- [ ] **Data minimization:** Don't collect more than needed. Audit: what fields in profiles table are actually necessary?

### Cross-Product Data (from blind-spots #4)
- [ ] **DPA (Data Processing Agreement)** per cross-product data flow
- Game behavior (Life Simulator) → hiring decisions (VOLAURA) = GDPR Art 22 violation
- [ ] Each product must have own privacy notice
- [ ] Cross-product data sharing requires EXPLICIT opt-in, not default

## 3. ToS and Privacy Policy

### Current State
- Draft ToS: `docs/legal/ToS-draft.md`
- Draft Privacy Policy: `docs/legal/Privacy-Policy-draft.md`
- [ ] Review and update both with AZ law specifics
- [ ] Add automated decision-making disclosure
- [ ] Add cross-border data transfer disclosure
- [ ] Add crystal economy terms (virtual currency, no real money value)
- [ ] AZ language version required (primary market)

## 4. Assessment-Specific Legal

### IRT/CAT Engine
- [ ] Document that IRT parameters are currently UNCALIBRATED (assessment-science-audit)
- [ ] Do NOT market scores as "verified" until 1000+ calibration responses collected
- [ ] DIF (Differential Item Functioning) analysis before expanding to non-AZ markets
- [ ] If selling assessment to organizations (B2B): additional employer liability considerations

### AI Evaluation (Gemini LLM grading)
- [ ] Disclose that open-text answers are evaluated by AI, not humans
- [ ] Implement appeal process for disputed AI evaluations
- [ ] Log all AI evaluation inputs/outputs for audit trail (Langfuse when activated)

## 5. BrandedBy-Specific Legal (from blind-spots #2)

- [ ] NO FAKES Act (USA, April 2025) — likeness rights
- [ ] TAKE IT DOWN Act (USA, May 2025) — non-consensual imagery
- [ ] EU AI Act — high-risk category for AI-generated video
- [ ] **DO NOT launch BrandedBy commercially** until IP attorney reviews likeness licensing
- For now: BrandedBy = research prototype only. No public users.

## Priority Order

1. **NOW (before any users):** Register as data operator + consent flow + Privacy Policy + ToS in AZ
2. **Before B2B:** Automated decision disclosure + human review mechanism + IRT calibration
3. **Before cross-product:** DPA per data flow + separate consent per product
4. **Before BrandedBy:** IP attorney on likeness rights (exception to "no external lawyer" — this needs specialist)

## Sources
- Azerbaijan Law on Personal Data (No. 998-IIIQ, 2010)
- State Register portal: https://www.e-gov.az/en/content/read/13
- blind-spots-analysis.md (items #2, #4)
- assessment-science-audit-2026-04-12.md (IRT calibration)
- DLA Piper Data Protection Laws of the World: Azerbaijan overview
