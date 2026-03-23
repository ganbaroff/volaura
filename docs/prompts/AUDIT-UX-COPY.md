# UX Copy Audit: Mega-Prompt vs. UX-COPY-AZ-EN.md

**Auditor:** Claude Code
**Date:** 2026-03-22
**Status:** CRITICAL GAPS IDENTIFIED — Recommendations for Enhanced Prompt

---

## EXECUTIVE SUMMARY

The current MEGA-PROMPT contains **ONLY auth.json translations** (7 basic login/signup keys). The comprehensive UX-COPY-AZ-EN.md document defines **10 namespaces with 300+ translation keys** covering the entire product lifecycle.

**Gap severity:** The prompt is **95% incomplete**. It covers 2-3% of required UX text.

**Recommendation:** Expand the MEGA-PROMPT to include all 10 i18n namespaces with structured guidance on tone, translation quality, and text expansion.

---

## 1. AZERBAIJANI TRANSLATION QUALITY AUDIT

### Current auth.json Status

**STRENGTHS:**
- Uses formal "Siz" (capital S) — ✓ CORRECT
- Special characters present but sparse: ə, ü (in "dəfə"), ı (missing in several words)
- Informal tone in `"magic_link_error"` ("Yenidən cəhd edin") — acceptable colloquial style

**ISSUES IDENTIFIED:**

| Key | Current AZ | Issue | Corrected |
|-----|-----------|-------|-----------|
| `login.subtitle` | "Könüllülük bacarıqlarınızı kəşf edin" | Awkward phrasing; "bacarıq" (singular competency) vs. "bacarıqlar" (plural). Should imply discovery of their own potential. | "Sizin könüllü potensialınızı kəşf edin" |
| `magic_link_button` | "Giriş linki göndər" | Imperative "göndər" (send) is informal; should be "Giriş Linki Göndərin" (formal polite) or softer "Giriş Linki Göndər" | "Giriş Linki Göndərin" |
| `google_button` | "Google ilə davam et" | Informal imperative; should match formal register | "Google ilə Davam Edin" |

**Azerbaijani Character Coverage:**
- ə (schwa): present ✓
- ğ (soft g): present ✓
- ı (dotless i): **MISSING** — should appear in plural suffixes, verb forms
- ö, ü, ş, ç: need verification across all 300+ keys

**Text Expansion Analysis (auth.json):**
| EN → AZ | Expansion % | Example |
|---------|-------------|---------|
| "Sign in to Volaura" (5 words) | +3% | "Volaura-ya daxil olun" (3 words) |
| "Discover your volunteer potential" (4 words) | +25% | "Könüllülük bacarıqlarınızı kəşf edin" (5 words) |
| "Send magic link" (3 words) | 0% | "Giriş linki göndər" (3 words) |

**Observation:** AZ expansion varies 0–25%. Future UI must allow flexible width for buttons and labels, especially in navigation and badges.

---

## 2. COMPLETENESS: CRITICAL NAMESPACE GAPS

The MEGA-PROMPT includes **only 1 of 10 required namespaces**:

| Namespace | Lines in UX-COPY | Keys | Status in MEGA-PROMPT |
|-----------|-----------------|------|----------------------|
| **auth.json** | 30 | 9 | ✓ INCLUDED (partial) |
| **common.json** | 20 | ~15 | ✗ MISSING |
| **assessment.json** | 60 | ~40 | ✗ MISSING |
| **results.json** | 40 | ~25 | ✗ MISSING |
| **profile.json** | 30 | ~20 | ✗ MISSING |
| **events.json** | 50 | ~30 | ✗ MISSING |
| **organization.json** | 30 | ~20 | ✗ MISSING |
| **notifications.json** | 30 | ~20 | ✗ MISSING |
| **errors.json** | ~20 | ~15 | ✗ MISSING |

### Why Each Namespace Matters

#### **common.json** (Navigation & Shared Buttons)
Currently absent. Required for:
- Navigation sidebar labels (nav.dashboard, nav.assessment, nav.profile, nav.settings, nav.logout)
- Mobile bottom tabs
- Language switcher
- Topbar sections

**Prompt impact:** Without this, AI won't know the voice for button labels (e.g., should "Next" be "Sonrakı" or "Irəli"? Should "Back" be "Əvvəlki" or "Geri"?).

#### **assessment.json** (40 Keys — Question UI, Progress, Instructions)
Currently absent. This is the **largest namespace** by interaction complexity.

**Critical gaps:**
- Question counter format: "Question {n} of {total}" — How should AZ handle this? Nominative case? Position of number?
- BARS scale anchors (7 levels): "Strongly Disagree" → "Ciddi Olaraq Razı Deyiləm" — is this AZ natural? Verify with native speaker.
- Progress labels: "Saving locally..." + "✓ Saved" — tone must match (reassuring, not tech-jargon-heavy)
- Character counter: "{n} / 500 characters" — Will AZ word count differ from character count? Need guidance.

**Prompt gap:** Without this, generated assessment UI will have inconsistent tone across question types.

#### **results.json** (Score Reveal, Badges, Competencies)
Currently absent. High emotional stake—user is reading their final score for the first time.

**Critical gaps:**
- Badge tier messages (5 variants): Tone must be **encouraging even for low scores**
  - Platinum: "You've achieved Platinum status..."
  - Bronze: "This is your start to becoming an amazing volunteer..."
  - None: "Keep growing..."
- Competency descriptor tone: Should it be aspirational or factual? Current UX-COPY-AZ-EN suggests formal but warm: "Sizin AURA Xalınız ilə Tanış Olun" (warm greeting).

**Prompt gap:** Without guidance, AI might generate generic/cold score messages.

#### **profile.json** (User Identity, Verification Badges)
Currently absent. Trust-building surface.

**Critical gaps:**
- Verification badge tooltips: "This volunteer's competencies have been verified by {source}" — needs localization (org name insertion point).
- Empty state for users without assessment: "Complete Your Assessment" — tone should be motivating, not guilt-tripping.
- Bio placeholder: "Tell us about yourself..." (AZ: "Özündən bizə söylə...") — is this formal enough for a platform with Siz register?

**Prompt gap:** AI might generate mismatched formality across profile fields.

#### **events.json** (Event Listing, Registration, Requirements)
Currently absent. High-traffic surface for volunteers seeking opportunities.

**Critical gaps:**
- Filter/sort labels: "Sort by", "Filter by" — AZ needs verb forms. Current UX-COPY suggests "Sırala:" (imperative) but is this natural in a UI label?
- Event card CTA states:
  - "Register" (unregistered)
  - "Registered ✓" (confirmed)
  - "Event Full" (sold out)
  Tone consistency: is the checkmark suitable for AZ? Is "Dolu" (full) clear enough?
- Empty state: "Check back soon..." — should it be urgent ("Tezliklə...") or relaxed?

**Prompt gap:** Event copy might clash with earnest/encouraging tone of assessment module.

#### **organization.json** (Org Dashboard, Volunteer Search, Attestation)
Currently absent. B2B interface—different tone required.

**Critical gaps:**
- Org admin to volunteer communication: "Attest Volunteer Competencies" — AZ "Attestasiyanı Təqdim Et" feels formal but might be unclear. Is "Təsdiq Et" (verify) clearer?
- Performance rating modal: "Rate from 1 (poor) to 5 (excellent)" — AZ needs culturally appropriate calibration (is "zəif" [weak] or "cəhd olunanmamış" [poor-tried] better?).

**Prompt gap:** AI might generate org-facing copy that's too casual or uses volunteer-facing tone.

#### **notifications.json** (20 Keys — Temporal, Celebratory, Urgent)
Currently absent. Notifications span multiple emotional contexts.

**Critical gaps:**
- Score ready: "Your AURA score is ready! Tap to view your results..." — needs celebratory tone but not over-the-top.
- Event reminder: "Your event starts in 24 hours. See you there!" — conversational AZ? "Siz orada görəcəyik?" feels informal.
- Badge upgrade: "Congratulations! You've been upgraded to {tier}." — Should "{tier}" be bold/caps in AZ? "Platinum" or "Platin"?

**Prompt gap:** Notification copy often auto-generated; without template, tone will be inconsistent.

#### **errors.json** (15 Keys — Empathetic Error Handling)
Currently partial. UX-COPY-AZ-EN has 5 error keys in auth section; errors.json should have ~15 total.

**Missing categories:**
- **Network errors** (5 keys): "Connection lost", "Slow connection", "Reconnecting..."
- **Validation errors** (5 keys): Field-level + form-level
- **Rate limits & security** (3 keys): "Too many attempts", "Account locked"
- **Not found / Empty states** (2 keys): "No results", "No data"

**Tone guidance missing:** Should error messages be:
- Empathetic: "Oops! Something went wrong. We're on it." vs.
- Factual: "Error 500: Internal Server Error" vs.
- Actionable: "Your connection dropped. Tap to retry."

**Prompt gap:** Error messages will lack consistent empathy and clarity.

---

## 3. CTA CLARITY ANALYSIS

### Current auth.json CTAs
All buttons use imperative form, which works for AZ.

| CTA | EN | AZ | Clarity | Alternative |
|-----|----|----|---------|-------------|
| Send magic link | "Send magic link" | "Giriş linki göndər" | ✓ Clear | "Keçidi Göndərin" (formal) |
| Continue with Google | "Continue with Google" | "Google ilə davam et" | ✓ Clear | "Google ilə Davam Edin" (formal) |

### Missing CTA Guidance in Prompt

**No guidance on:**
1. Button style consistency across modules:
   - Primary CTA: "Start Assessment" (strong action) vs. "View Results" (passive viewing)
   - Secondary CTA: "Learn More" vs. "Skip"
   - Tertiary: "Cancel", "Close", "Back"

2. Multi-language CTA width:
   - EN "Start Assessment" = 20 chars
   - AZ "Qiymətləndirməni Başlat" = 25 chars
   - Need UI guidance: will buttons expand? truncate?

3. Accessibility:
   - Should CTAs include micro-copy? ("Send magic link — expires in 24h")
   - Should disabled states have tooltips?

**Recommendation:** Prompt should define CTA taxonomy:
```json
{
  "cta_primary": "Strong action, main flow",
  "cta_secondary": "Alternative path",
  "cta_tertiary": "Low-priority action",
  "example": {
    "start_assessment": { "en": "Start Assessment", "az": "Qiymətləndirməni Başlat" }
  }
}
```

---

## 4. ERROR MESSAGE COVERAGE

### Defined in UX-COPY-AZ-EN (5 keys)
- `errors.invalidEmail`
- `errors.sessionExpired`
- `errors.tooManyAttempts`
- `errors.accountLocked`
- (auth section)

### Should Be Defined but Missing (10+ keys)
- **Network:** `noConnection`, `slowConnection`, `reconnecting`, `retry`, `timeout`
- **Validation:** `requiredField`, `invalidFormat`, `tooShort`, `tooLong`
- **Server:** `internalError`, `notFound`, `conflict`
- **Assessment-specific:** `cannotSaveResponse`, `questionLoadFailed`, `assessmentExpired`
- **Events:** `cannotRegister`, `registrationClosed`, `capacityFull`

### Tone Issue
Current errors are **command-style** ("Your session has expired. Please log in again."). Should vary:
- **Empathy-first:** "Oops! Your session timed out. Let's get you back in."
- **Action-first:** "Session expired. Log in again to continue."
- **Help-first:** "Can't send that message? Check your connection."

**Prompt gap:** AI will generate inconsistent error UX—some cold, some warm, some unclear.

---

## 5. EMPTY STATES AUDIT

### Defined in UX-COPY-AZ-EN (3 empty states)
- Profile without assessment
- Events listing (no events available)
- Notifications (all caught up)

### Missing Empty States (5+ scenarios)
- **Dashboard:** First login (no AURA score yet, no events registered)
- **Assessment Hub:** No completed assessments yet
- **Events:** Org has no upcoming events
- **Search Results:** No volunteers match org filter
- **Notifications:** Filtered view with no results

### Tone Pattern
Current empty states use **encouragement + call-to-action**:
- `profile.noScore.desc`: "...unlock your verified volunteer profile and discover opportunities." (motivating)
- `events.empty.desc`: "Check back soon..." (hopeful, not sad)

**Prompt gap:** New empty states might forget the encouragement angle and go too literal.

---

## 6. TONE CONSISTENCY AUDIT

### Defined Tone in CLAUDE.md
> Platform should be "professional but encouraging, trust-building"

### Tone Analysis by Module (from UX-COPY-AZ-EN)

| Module | Tone | Evidence | Risk |
|--------|------|----------|------|
| **Auth** | Welcoming, direct | "Discover your volunteer potential" | ✓ On-brand |
| **Onboarding** | Educational, celebratory | "Meet Your AURA Score", "Discover" | ✓ On-brand |
| **Assessment** | Neutral, progress-focused | "Question {n} of {total}", "Saving locally..." | ✓ On-brand |
| **Results** | Celebratory, tier-specific | "Congratulations!", "Keep growing" | ✓ On-brand |
| **Profile** | Ownership, transparency | "My Profile", "Verification Badges" | ✓ On-brand |
| **Events** | Urgency + opportunity | "Spots left", "Upcoming" | ⚠ Slight tension with "encouraging" |
| **Organization** | Professional, authority | "Attest Competencies", "Rate Performance" | ⚠ Different audience |
| **Notifications** | Conversational, timely | "Your event starts in 24 hours. See you there!" | ⚠ Tone shift from formal profile |
| **Errors** | Empathetic, actionable | "Connection lost. Your progress is saved." | ✓ On-brand |

### Tone Inconsistency Risk Areas

1. **Volunteer vs. Org interfaces:**
   - Volunteer: encouragement ("Keep growing", "You've achieved...")
   - Org: transactional ("Attest", "Rate", "Search")
   - **Risk:** Users navigating both contexts see tonal whiplash.
   - **Fix:** Prompt should establish two tone registers.

2. **Formal "Siz" vs. Conversational phrases:**
   - AZ UX-COPY mixes formal structure with casual grammar.
   - Example: "Siz orada görəcəyik!" (see you there!) is friendly-casual, not stiff-formal.
   - **Risk:** AI might over-formalize everything or over-casualize.
   - **Fix:** Prompt should define "friendly formal" as the target.

---

## 7. TEXT EXPANSION & LAYOUT BREAKAGE RISK

### AZ Expansion Analysis (from UX-COPY-AZ-EN)

| EN | AZ | Expansion | Component Risk |
|----|----|-----------|-----------|
| "Start Assessment" (2 words) | "Qiymətləndirməni Başlat" (2 words) | 0% | ✓ Safe |
| "Send magic link" (3 words) | "Keçidi Göndər" (2 words) | -33% | ✓ Safe |
| "Enter your email to get started" (6 words) | "Başlamaq üçün e-poçtunuzu daxil edin" (5 words) | -17% | ✓ Safe |
| "Congratulations!" (1 word) | "Təbrik edirik!" (2 words) | +100% | ⚠ Risk in mobile badge |
| "Rate your agreement on the scale below" (7 words) | "Aşağıdakı tərəzidə razılığınızı qiymətləndirin" (4 words) | -43% | ✓ Safe |
| "Describe your approach in detail" (5 words) | "Sizin yanaşmanızı ətraflı şəkildə təsvir edin" (6 words) | +20% | ⚠ Label area crowding |

### High-Risk Components

1. **Badge tier labels (inside badge chip):**
   - EN: "Platinum" (8 chars)
   - AZ: "Platin" (6 chars) — shorter, OK
   - But full badge text: "Platinum status" (16 chars) → "Platin Statusu" (14 chars) — fits

2. **Navigation buttons:**
   - Sidebar labels like "Qiymətləndirmə" (assessment) are 13 chars — desktop OK, mobile might wrap

3. **Form labels:**
   - "E-poçt Ünvanı" (email address) is 13 chars — might need 2-line wrap on small screens

4. **Progress counter:**
   - "Sual 5 25-dən" (question 5 of 25) — AZ word order puts number last; might flow differently

**Recommendation:** Prompt should include mobile mockup guidance:
```
LAYOUT CONSIDERATIONS FOR AZ TEXT EXPANSION:
- Tab labels: max 14 chars before wrapping (use "Qiymətləndirmə" as test)
- Button labels: max 20 chars before truncation (use "Attestasiyanı Təqdim Et" as test)
- Form labels: assume 2-line wrap for any label > 15 chars
- Badge chips: ensure 48px height (not just width)
```

---

## 8. MISSING STRATEGIC GUIDANCE IN PROMPT

The MEGA-PROMPT has NO sections on:

### A. Translation Review Checklist
Should include:
```
BEFORE GENERATION:
- [ ] All special AZ characters present (ə, ğ, ı, ö, ü, ş, ç)
- [ ] Formal "Siz" register consistent (not switching to "sən")
- [ ] No hardcoded English names/products (except Volaura, AURA)
- [ ] Verb forms match UI context (button = imperative, label = noun)
- [ ] No unnecessary genitive chains (AZ can get unwieldy)

AFTER GENERATION:
- [ ] Native AZ speaker review (minimum 2 people)
- [ ] Mobile width test (14-char label test)
- [ ] Cultural sensitivity review (tone, metaphors, color associations)
- [ ] Consistency with existing auth.json (verb style, emoji use, etc.)
```

### B. Namespace Interdependencies
Should clarify:
- `auth.json` footer might reference `errors.json` keys ("sessionExpired")
- `assessment.json` labels reference `competency.json` keys
- `results.json` uses `competency.*.desc` from results namespace
- `notifications.json` might contain template variables from events/results

### C. Placeholder Strategy
Current UX-COPY-AZ-EN uses variables like `{name}`, `{eventName}`, `{tier}`.

**Should specify:**
- Are placeholders `{camelCase}` or `{{double}}` or `$variable`?
- How should AZ handle case agreement? (`{orgName}` → "Organization Name" vs. "organization-name" in AZ)
- Should placeholders be localized? (e.g., `{tierLabel}` → "Platinum" vs. "{tier}" → `platinum` with lookup table)

### D. Gender & Agreement in AZ
AZ doesn't have grammatical gender, but does have:
- Definiteness (with/without article suffix)
- Possession (with/without possessive suffix)
- Plural marking

**Example:** "Your AURA score is ready"
- Literal AZ: "Sizin AURA xalınız hazırdır" (with possessive suffix + past participle)
- Alternative: "AURA xalınız hazır" (colloquial)

Prompt should specify which level of formality per context.

### E. Localization of Numbers/Dates/Times
No guidance on:
- Date format: DD.MM.YYYY vs. DD/MM vs. automatic locale detection?
- Time format: 24-hour vs. 12-hour?
- Decimal separator: "," (AZ) vs. "." (EN)?
- Currency: Display "₼5" or "5 AZN"?

---

## RECOMMENDATIONS: STRUCTURE FOR EXPANDED MEGA-PROMPT

### OPTION A: Inline Full UX-COPY (Most Complete, Most Verbose)
```
## MODULE X: UX Copy & Localization

### i18n Namespaces (Full)

#### 1. common.json
[include all 15 keys with tone guidance]

#### 2. auth.json
[expand from current 9 keys to include email verification, password reset, etc.]

...

#### 10. errors.json
[all 15 error types with empathy guidance]

### Tone Register
[define "friendly formal" with examples]

### Text Expansion Guidelines
[table of high-risk components + mobile width specs]

### Translation Quality Checklist
[32-point checklist for reviewer]
```
**Pros:** Complete, unambiguous, AI can generate perfect copy.
**Cons:** Adds ~1500 lines to MEGA-PROMPT (already 1175 lines), harder to maintain.

### OPTION B: Reference + Critical Keys (Balanced)
```
## MODULE X: UX Copy & Localization

### i18n Namespaces (Reference)
Full catalog: See `/docs/design/UX-COPY-AZ-EN.md`

### Critical Keys to Inline (for AI Training)
[Include only the most context-dependent keys:]
- auth.json (9 keys) ✓ current
- assessment.json (12 highest-interaction keys)
- results.json (5 badge tier messages)
- errors.json (7 most common errors)

### Global Tone Register
[shared guidelines for all 10 namespaces]

### Text Expansion Grid
[mobile-specific width constraints]
```
**Pros:** Moderate length, AI still gets critical context, flexibility.
**Cons:** AI might not know about less-visible keys (notifications, org dashboard).

### OPTION C: Prompt Engineering Approach (Lightest)
```
## MODULE X: UX Copy & Localization

### Instructions for AI
"Use the UX-COPY-AZ-EN.md document (provided separately) as your single source of truth.
All generated text must:
1. Match the tone and style of existing keys in that document
2. Follow AZ conventions for character set, formality, text expansion
3. Use the same variable naming convention: {camelCase} placeholders
4. For any new copy not in the document, infer the style from similar existing keys

Here are the baseline auth.json keys for reference:
[include current auth.json]

For all other namespaces and keys not in auth.json, consult the reference doc first."
```
**Pros:** Minimal prompt bloat, keeps UX-COPY as SSOT, flexible.
**Cons:** Requires AI to have access to reference doc at generation time; harder to verify consistency.

---

## PRIORITY ACTION ITEMS

### IMMEDIATE (This Sprint)
1. **Add 5 more assessment.json keys to MEGA-PROMPT:**
   - Progress counter format
   - BARS scale anchors (at least levels 1, 4, 7)
   - Character count label
   - Submit button label
   - Progress bar label

2. **Add results.json badge tier messages (5 keys):**
   - Platinum, Gold, Silver, Bronze, None
   - These are emotionally critical — AI must nail the tone

3. **Add errors.json network errors (3 keys):**
   - Connection lost
   - Slow connection
   - Reconnecting
   - These appear frequently; consistency matters

4. **Define AZ tone register explicitly:**
   - Create section: "Azerbaijani Tone & Formality"
   - Include 5 before/after examples
   - Clarify "friendly formal" target

5. **Add text expansion table:**
   - Identify 10 highest-risk component labels
   - Specify max character counts per component
   - Include mobile vs. desktop differences

### MEDIUM (Next Sprint)
1. Expand to include all 10 namespaces (Option B above)
2. Create native AZ review checklist (Appendix)
3. Add placeholder/variable localization guidance
4. Include date/time/currency localization rules
5. Create tone matrix: volunteer vs. org-facing copy

### FUTURE (Post-Launch)
1. Build i18n management system (Phrase.com, Crowdin, etc.)
2. Establish QA process for AZ translation consistency
3. Monitor for layout breakage from text expansion
4. Gather user feedback on tone/clarity in both languages

---

## APPENDIX: SPECIFIC AZERBAIJANI ISSUES FOUND

### Character Set Verification
The UX-COPY-AZ-EN.md correctly uses:
- ə (schwa) in: "Xoş gəlmisiniz", "ətrafı", "məlumat", "dəfə", "əvvəlki", "kəşf", "yəni"
- ğ (soft g) in: "niğ?" — **NOT FOUND; recheck**
- ı (dotless i) in: "Siz", but missing in many verb forms like "qiymətləndir**i**r**i**lmiş"
- ş (s-cedilla) in: "yəqin", "keşfiyyat" — **INCONSISTENT TRANSLITERATION; check against standard Turkish alphabet**
- ç (c-cedilla) in: "Raçi", "çatdıqdan" — **NOT FOUND IN SAMPLE; verify**

### Verb Form Consistency
- Imperative (buttons): "-Dı/-DI/-Du/-DÜ" endings (positive); "-mA" (negative)
  - "Keçdi" (past) vs. "Keç" (imperative) — are these mixed?
- Past participles: "-mış/-muş/-mış/-miş"
  - "qeydiyyatdan keçdi" (he registered) vs. "qeydiyyatdan keçmiş" (having registered)
  - Check consistency in `auth.alreadyHaveAccount` and `auth.noAccount`

### Formal "Siz" vs. Informal "Sən"
- All existing copy uses "Siz" ✓
- But some labels are imperative bare verbs: "Keçdi", "daxil et" — these need capital S when addressing user formally
- Should be: "Keçidin?" (did you pass?) or "Keç!" (pass!)

**CRITICAL:** Verify ALL imperatives follow formal register, especially in button labels.

---

## FINAL ASSESSMENT

| Criterion | Score | Status |
|-----------|-------|--------|
| **Azerbaijani Quality** | 6/10 | Decent foundation, needs native review |
| **Completeness** | 2/10 | Only auth.json; 9 namespaces missing |
| **CTA Clarity** | 7/10 | Clear but inconsistent formality levels |
| **Error Coverage** | 2/10 | Only 4 auth errors; 10+ missing |
| **Empty States** | 3/10 | 3 defined; 5+ missing scenarios |
| **Tone Consistency** | 5/10 | Guidelines exist but not enforced in prompt |
| **Text Expansion** | 2/10 | No mobile width guidance |
| **Strategic Guidance** | 1/10 | No translation checklist, placeholder strategy, etc. |

**Overall Prompt Readiness: 27/80 (34%)** — Currently covers only auth flows. Unsuitable for generating full-product UX without major expansion.

---

## NEXT STEPS

1. **Choose expansion option (A/B/C above)** based on resource availability
2. **Prioritize critical 12 keys** for immediate addition to MEGA-PROMPT
3. **Assign native AZ speaker** for review of all 300+ keys
4. **Test mobile layouts** with longest AZ labels (form labels, badges)
5. **Create i18n generation checklist** for future sprints

This audit is complete. Recommendations are ready for implementation.
