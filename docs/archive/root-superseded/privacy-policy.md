# Volaura Privacy Policy

**Effective date:** 2026-04-01
**Last updated:** 2026-03-24
**Version:** 1.0

---

## 1. Who We Are

Volaura ("we", "our", "the Platform") is a verified competency platform for volunteers, operated by [Legal Entity Name Pending — GoldenByte LLC or new entity] in Azerbaijan. We help volunteers prove their skills and help organizations find verified talent.

**Contact:** privacy@volaura.az
**Address:** Baku, Azerbaijan (full address on entity registration)

---

## 2. What Data We Collect

### 2.1 Data You Provide
| Data | Why We Collect It | Legal Basis |
|------|------------------|-------------|
| Name, email, username | Account creation and identity | Contract (Art. 6(1)(b) GDPR) |
| Password (hashed, never stored plain) | Authentication | Contract |
| Location (city/region) | Matching volunteers to local opportunities | Legitimate interest |
| Languages spoken | Matching quality | Legitimate interest |
| Assessment answers | Computing your AURA score | Contract |
| Self-description / bio | Org matching, profile completeness | Contract |

### 2.2 Data We Compute
| Data | Description |
|------|-------------|
| AURA Score (0–100) | Weighted competency score across 8 dimensions |
| Badge tier | Derived from AURA score (Bronze/Silver/Gold/Platinum) |
| Theta (IRT ability) | Internal assessment calibration — **never shown to organizations** |
| Anti-gaming signals | Timing patterns to detect spoofed responses — used for quality only |
| Competency embeddings | 768-dim vector for semantic volunteer search — not identifiable alone |

### 2.3 Technical Data
| Data | Purpose | Retention |
|------|---------|-----------|
| IP address | Rate limiting, fraud prevention | 30 days |
| Session logs | Security auditing | 90 days |
| Error logs | Platform reliability | 30 days |

### 2.4 Data We Do NOT Collect
- Payment card details (no payment processing in v1)
- Government IDs or passports
- Biometric data
- Location tracking / GPS
- Contacts or social graph

---

## 3. How We Use Your Data

1. **Deliver the service** — run assessments, compute AURA scores, issue badges
2. **Volunteer–organization matching** — orgs search for you by competency + location + languages
3. **Platform improvement** — aggregate analytics (non-identifiable) to improve IRT question calibration
4. **Security** — rate limiting, anti-fraud, preventing score manipulation
5. **Communications** — assessment results, badge notifications (opt-in)

**We do NOT:**
- Sell your data to third parties
- Use your data for advertising targeting
- Share raw assessment answers with organizations (orgs see scores, not answers)
- Use your profile for any purpose outside Volaura without explicit consent

---

## 4. Who Can See Your Data

| Party | What They See | Conditions |
|-------|--------------|------------|
| You | Everything about yourself | Always |
| Organizations (verified) | Your username, AURA score, badge tier, location, languages | Only if you have a public profile |
| Volaura team | All data for support/security purposes | Role-based access, logged |
| Supabase (infrastructure) | All stored data | Data Processing Agreement in place |
| Google (Gemini API) | Assessment answers sent for evaluation | Gemini Enterprise DPA; no training on your data |
| Railway (hosting) | API request logs | SOC 2 compliant |
| Vercel (hosting) | Frontend request logs | SOC 2 compliant |

---

## 5. Your Rights (GDPR + Local Law)

You have the right to:

- **Access** — request a copy of all data we hold about you
- **Rectification** — correct inaccurate data
- **Erasure** ("right to be forgotten") — delete your account and all associated data
- **Portability** — export your AURA history and badges in JSON format
- **Objection** — object to processing based on legitimate interest
- **Restrict** — limit how we process your data while a dispute is resolved
- **Withdraw consent** — for any processing based on consent (e.g., marketing emails)

**To exercise rights:** email privacy@volaura.az with subject "Data Rights Request — [your username]". We respond within 30 days.

---

## 6. Data Retention

| Data type | Retention | Why |
|-----------|-----------|-----|
| Active account data | Until account deletion | Service delivery |
| Assessment sessions | 2 years after completion | Score recalibration, disputes |
| AURA score history | 3 years | Longitudinal competency tracking |
| Deleted account data | 30 days (soft delete) | Recovery window |
| Security logs | 90 days | Incident investigation |
| Anonymized analytics | Indefinite | Platform improvement |

When you delete your account, we permanently erase all personally identifiable data within 30 days. Anonymized aggregate data may be retained.

---

## 7. Security Measures

We take security seriously (this is literally in our sprint backlog):

- **Authentication** — JWT tokens verified via Supabase Auth admin API (not client-side)
- **Row Level Security** — all database tables have RLS policies; you can only see your own data
- **Encryption at rest** — Supabase encrypts all data at rest (AES-256)
- **Encryption in transit** — TLS 1.3 on all connections
- **Secret detection** — automated pre-commit hooks block API keys from code
- **Rate limiting** — all endpoints rate-limited per IP and per user
- **Security headers** — HSTS, CSP, X-Frame-Options on all responses
- **Prompt injection defense** — user answers wrapped in `<user_answer>` tags, LLM instructed to ignore embedded instructions
- **No logging of answers** — raw assessment answers are evaluated and discarded; only scores are persisted

---

## 8. Cookies and Tracking

We use:
- **Session cookies** (strictly necessary) — Supabase Auth session management
- **No advertising cookies**
- **No cross-site tracking**
- **No third-party analytics** (no Google Analytics, no Hotjar in v1)

---

## 9. Children's Privacy

Volaura is not intended for children under 16. We do not knowingly collect data from users under 16. If you believe a minor has registered, contact privacy@volaura.az and we will delete the account.

---

## 10. International Data Transfers

Your data is stored in Supabase's EU region (Frankfurt). Processing may involve:
- Google Gemini API (US-based) — covered by EU SCCs and Gemini Enterprise DPA
- Railway (US-based) — processing runtime logs only, covered by DPA

If you are in the EU/EEA, these transfers comply with GDPR Chapter V via Standard Contractual Clauses.

---

## 11. Changes to This Policy

We will notify registered users by email at least 14 days before material changes take effect. The "Last updated" date at the top reflects the most recent revision. Continued use of Volaura after the effective date constitutes acceptance.

---

## 12. Contact and Complaints

**Privacy questions:** privacy@volaura.az
**Response time:** Within 30 days

If you believe we have violated your rights and we have not resolved your complaint, you may lodge a complaint with your local data protection authority. In Azerbaijan: [relevant authority TBD on entity registration].

---

*This policy was drafted with reference to GDPR (EU 2016/679), the Law of the Republic of Azerbaijan "On Personal Data" (2010), and Volaura's security architecture (docs/engineering/skills/SECURITY-REVIEW.md).*
