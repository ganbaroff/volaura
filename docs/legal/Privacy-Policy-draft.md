# Volaura — Privacy Policy

> **DRAFT — needs legal review before publication.**
>
> **Flags for legal counsel:**
> - [ ] Legal entity and data controller name is TBD. Placeholder "[Volaura Ltd]" used throughout — replace with actual registered name, address, and jurisdiction before publishing.
> - [ ] AZ PDPA (Azerbaijan Law on Personal Data #998-IIIQ, July 11, 2010, as amended): Article references below are best-effort approximations — verify exact article citations with AZ-licensed counsel before publishing.
> - [ ] GDPR adequacy: Azerbaijan does not currently have EU adequacy status. If EU users are accepted, a lawful transfer mechanism (e.g., Standard Contractual Clauses) must be in place. Flag this before enabling EU sign-up.
> - [ ] Data Processor agreements: if Supabase (US), Railway (US), or Vercel (US) process personal data of EU/AZ users, Data Processing Agreements (DPAs) must be in place with each. Supabase has a DPA — verify others.
> - [ ] Gemini API (Google): assessment answers are sent to Google's Gemini API for AI evaluation. This is a material third-party disclosure. Verify Google's DPA covers this use case.
> - [ ] Cookie consent: if Vercel Analytics or any tracking cookies are added later, a cookie banner may be required under GDPR. Current draft assumes no third-party tracking cookies.
> - [ ] Retention periods: 30-day deletion after account closure is stated. Confirm this is technically implemented and that backup purge cycles match.
> - [ ] DPO requirement: GDPR requires a Data Protection Officer if processing at scale. Not required at beta stage, but flag for when user count exceeds ~5,000 EU users.

---

**Last updated:** April 2, 2026
**Version:** 0.1 (BETA)

---

## 1. Introduction

This is what we know about you, how we use it, and what you can do about it.

We try to collect only what we need. We don't sell data. We don't share it with people who don't need it.

Volaura is operated by **[Volaura Ltd]** (legal entity TBD). We are the data controller under GDPR and the personal data operator under Azerbaijan's Personal Data Protection Law (AZ PDPA).

---

## 2. What Data We Collect

### Data you give us directly

| Data | Why we collect it |
|------|-------------------|
| Name, email address | Account creation and communication |
| Profile information (job title, location, bio) | Public professional profile |
| Assessment responses | To calculate your AURA score |
| Profile visibility settings | To control who can see your data |

### Data we generate from your activity

| Data | Why we collect it |
|------|-------------------|
| AURA score and badge tier | Core platform output |
| Competency scores per dimension | Your skill breakdown |
| Assessment session metadata (timestamps, completion time) | Quality assurance and anti-gaming |
| Login timestamps | Security and account management |

### Data we collect automatically

| Data | Why |
|------|-----|
| IP address | Security, fraud prevention |
| Browser/device type | Platform compatibility |
| Session logs | Debugging, error tracking |

We do **not** use advertising trackers. We do not use Google Analytics, Meta Pixel, or similar ad-tech. We use minimal analytics (platform-level, not user-level) for performance monitoring.

---

## 3. How We Use Your Data

We use your data to:

1. **Run the platform** — assessments, scoring, profile display
2. **Improve the AI** — your assessment answers help train and calibrate our adaptive assessment engine. This is disclosed and required for the platform to work. Answers used for training are processed in aggregate and not linked to your public identity in training datasets.
3. **Communicate with you** — account notifications, policy updates, product news (you can opt out of product news)
4. **Keep the platform secure** — detect gaming, fraud, and abuse
5. **Comply with law** — when required by applicable law or a valid legal process

We do **not** use your data for:
- Advertising targeting
- Selling to third parties
- Profiling you for purposes outside of professional competency assessment

**Legal basis (GDPR):** For EU users, our processing is based on:
- **Contract performance** (Art. 6(1)(b)) — processing necessary to provide the service you signed up for
- **Legitimate interests** (Art. 6(1)(f)) — security, fraud prevention, product improvement
- **Consent** (Art. 6(1)(a)) — where explicitly requested (e.g., optional marketing emails)

**Legal basis (AZ PDPA):** Processing is conducted with your consent (provided at registration) and as necessary for service delivery, consistent with Articles 7-8 of the AZ PDPA *(flag: verify exact articles with local counsel).*

---

## 4. Tribe Data — Special Section

Tribes deserve their own section because we made deliberate privacy decisions here.

### What is stored

- Tribe membership (which 3 users are in a tribe together)
- Kudo records: that a kudo was sent, when, and who received it — **but not who sent it**
- Activity status: a boolean flag ("active recently" or not)

### What is NOT stored

- Sender identity on kudos — anonymity is permanent and by design. There is no way to look up who sent a kudo, including by us.
- AURA scores in the tribe context — tribe members do not see each other's scores
- Detailed competency data
- Assessment answers

### Consent

Joining a tribe is voluntary. By joining, you consent to your tribe members seeing:
- Your activity status (active/inactive — not timestamps, not details)
- Kudos you have received (not who sent them)

You can leave a tribe at any time. Leaving removes your membership. Kudo records that were sent to you remain (they don't contain your sender's identity and they belong to your record).

---

## 5. Organization Access to Your Data

Organizations on Volaura are recruiting or discovery accounts. Here is exactly what they can and cannot see:

### What orgs can access

If you have set `visible_to_orgs = true` on your profile:
- Your AURA score (overall)
- Your badge tier (Bronze / Silver / Gold / Platinum)
- Your public profile fields (name, title, bio — what you chose to make public)
- Skills you have made visible

### What orgs cannot access

- Your assessment answers
- Your individual question responses
- Your tribe data
- Your login activity
- Any field you have not explicitly made public

**If `visible_to_orgs = false` (the default), organizations cannot find you in search at all.**

Organizations do not get raw data exports of your profile. They interact with you through the platform.

---

## 6. Third-Party Services

We use the following third-party services that may process your data:

| Service | Purpose | Location | DPA in place? |
|---------|---------|----------|---------------|
| Supabase | Database and authentication | US (EU hosting option available) | Yes |
| Railway | API hosting | US | Flag: verify |
| Vercel | Frontend hosting | US/Global CDN | Flag: verify |
| Google Gemini API | AI evaluation of assessment answers | US | Flag: verify |
| Telegram (optional) | Notifications (if opted in) | EU | N/A — standard |

We do not use advertising networks, data brokers, or social media tracking pixels.

---

## 7. Data Retention

| Data type | Retention period |
|-----------|-----------------|
| Active account data | As long as your account exists |
| Assessment sessions | As long as your account exists |
| Account data after deletion | Deleted within 30 days of account closure |
| Security logs (IP, login timestamps) | 90 days |
| Anonymised aggregate data | Indefinitely (cannot be linked to you) |
| Backup copies | Purged within 60 days of account deletion |

When you delete your account, we remove:
- Your name and email
- Your profile data
- Your assessment answers
- Your AURA scores (personal record)

We retain anonymised statistical data (e.g., aggregate assessment difficulty metrics) that cannot identify you.

---

## 8. Your Rights

### GDPR rights (for EU/EEA residents)

Under GDPR, you have the right to:

- **Access** — request a copy of all personal data we hold about you
- **Rectification** — correct inaccurate data
- **Erasure** ("right to be forgotten") — request deletion of your data
- **Portability** — receive your data in a machine-readable format (JSON)
- **Objection** — object to processing based on legitimate interests
- **Restriction** — request we limit processing while a dispute is resolved
- **Withdraw consent** — where processing is based on consent, withdraw it at any time

To exercise any of these rights: **privacy@volaura.az**

We will respond within 30 days. We may ask you to verify your identity before acting.

You also have the right to lodge a complaint with your national data protection authority. For EU residents, this is your country's DPA. For Estonian or German users, that's the Estonian DPA (AKI) or the German Federal Commissioner for Data Protection (BfDI), respectively.

### AZ PDPA rights (for Azerbaijan residents)

Under Azerbaijan's Personal Data Protection Law, you have the right to:

- Obtain information about your personal data and how it is processed *(AZ PDPA, approx. Art. 12 — flag: verify)*
- Request correction of inaccurate data *(approx. Art. 13)*
- Request deletion of your data *(approx. Art. 14)*
- Withdraw consent for data processing *(approx. Art. 9)*

To exercise these rights: **privacy@volaura.az**

---

## 9. Cookies

Volaura uses the following cookies:

| Cookie | Type | Purpose |
|--------|------|---------|
| Authentication token (Supabase) | Essential | Keeps you logged in |
| Session state | Essential | Platform functionality |

We do **not** use:
- Analytics cookies (Google Analytics, etc.)
- Advertising/tracking cookies
- Social media pixel cookies

Essential cookies cannot be disabled without breaking the platform. You can clear them at any time by logging out or clearing your browser's cookies.

If we add any non-essential cookies in the future, we will update this section and display a consent banner.

---

## 10. Security

We take reasonable technical and organisational measures to protect your data:

- All data transmitted over HTTPS
- Passwords hashed (never stored in plain text — handled by Supabase Auth)
- Row-Level Security (RLS) policies on all database tables
- Access controls limiting which team members can access production data
- Assessment sessions time-limited and validated server-side

We are a small team in BETA. We are honest: no system is 100% secure. If we discover a data breach that affects your personal data, we will notify you within 72 hours of discovery, consistent with GDPR Art. 34 requirements.

To report a security vulnerability: **security@volaura.az**

---

## 11. Children

Volaura is not intended for users under 16. We do not knowingly collect data from anyone under 16. If you believe we have data from a minor, contact us at privacy@volaura.az and we will delete it promptly.

---

## 12. Changes to This Policy

We will notify you of material changes via email or in-platform notification at least 14 days before they take effect. The "Last updated" date at the top of this document will change.

Minor changes (typos, clarifications that don't affect your rights) may be made without notice.

---

## 13. Contact

**Data controller:** [Volaura Ltd] — full address to be added after entity formation

**Privacy requests:** privacy@volaura.az

**Security disclosures:** security@volaura.az

**General contact:** support@volaura.az

---

*This policy was drafted with reference to GDPR (EU 2016/679), the Azerbaijan Law on Personal Data (#998-IIIQ, 2010 as amended), and current industry practice for SaaS platforms. It has not yet been reviewed by licensed legal counsel. Do not publish without legal review.*
