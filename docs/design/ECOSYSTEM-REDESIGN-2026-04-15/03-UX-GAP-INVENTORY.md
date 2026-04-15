# UX Gap Inventory — VOLAURA Ecosystem Redesign 2026-04-15

**Date:** 2026-04-15 · **Author:** Agent `product-ux` (invoked by Terminal-Atlas) · **Model:** Claude via Task subagent
**Input files:** 00-BASELINE.md, 01-TOKENS-AUDIT.md, 02-FIGMA-RECONCILIATION.md, ECOSYSTEM-CONSTITUTION.md, DESIGN-SYSTEM-AUDIT.md, 68 screenshots (public + authed)

---

## 1. Summary Verdict

Overall ecosystem UX coherence score: **41 / 100**

The platform has three genuine strengths locked in code: AZ-language copy across most authed flows is present and mostly correct; the AURA empty-state ("Hələ AURA balınız yoxdur. / Qiymətləndirməyə başlamaq") correctly follows Constitution Law 3 with a single warm CTA; and the token architecture is structurally 3-tier and sound. Those are the ceilings.

The floor is much lower on three themes. First, the ecosystem surfaces — MindShift, ATLAS, BrandedBy, and Life Sim — all render as identical "Coming soon" placeholder screens inside the VOLAURA shell, with no product-accent differentiation, no cross-product value narrative, and no estimated timeline. A user who clicks four of the five nav items hits a dead end. Second, the landing page has zero conversion infrastructure for the AZ market: no social proof, no org logos, no user count with real numbers (shows "0" on two of three stat counters), no testimonial from anyone who looks like Leyla or Kamal, and a section in English ("What your profile could look like") mid-page inside an otherwise AZ-language flow. Third, the discover and leaderboard routes require auth but redirect to a login form rather than a public teaser — Nigar (HR, step 1 in her journey) cannot see any talent evidence before signing up, which breaks the B2B acquisition funnel entirely.

The March 2026 audit scored 62/100 on 18 pages. The 29 additional pages added since then skew mostly toward placeholder states and org flows that are structurally present but UX-thin. Adjusted for real scope (47 pages), the score drops to approximately 41/100.

---

## 2. P0 Blockers

### P0-01 — Three stat counters show "0" on the landing page
- **Pages:** `landing-desktop.png`, `landing-mobile.png`
- **Harm:** For Leyla (AZ, 22, low trust), a platform showing 0 verified members and 0 completed assessments reads as abandoned or fake. AZ collectivist trust model requires proof that real people have already taken the risk. "0 Doğrulanmış mütəxəssis" is an anti-social-proof signal.
- **Constitution:** Law 3 (shame-free framing) — zero counters quantify incompleteness in the same neural pathway as "0% complete".
- **Evidence:** `landing-desktop.png` — ImpactTicker section shows three stats: "0 Doğrulanmış mütəxəssis", "0 Tamamlanmış tədbirlər", "325 Yeni verilən suallar". The third counter has real data; the first two do not.
- **Fix direction:** Gate the stat display — if count < threshold, replace with a qualitative statement ("Bakıda yoxlanmış mütəxəssislərin böyüyən ictimaiyyəti") rather than showing raw zeros. Or seed with accurate data before going to production visibility.

### P0-02 — Leaderboard and Discover show login form to unauthenticated users with no teaser
- **Pages:** `leaderboard-desktop.png`, `leaderboard-mobile.png`, `discover-desktop.png`
- **Harm:** Nigar (HR manager, step 6 of her journey) cannot see any talent before signing up. This kills the "verify value before commitment" path that B2B SaaS requires. Also harms Leyla — if a friend shares the leaderboard URL, she hits a login wall instead of seeing social proof.
- **Constitution:** Law 5 (one primary action) — the screen presents a full auth form when the primary action for this visitor is "see if this platform is worth trying".
- **Evidence:** `leaderboard-desktop.png` and `discover-desktop.png` render the full `/{locale}/login` UI instead of any public teaser.
- **Fix direction:** Create a read-only public teaser for both routes — top 3 anonymized profiles with badge tiers and a single "Sign up to see full list" CTA. Gate smart search behind auth, not browse.

### P0-03 — BrandedBy surface shows loading spinner indefinitely
- **Pages:** `brandedby-surface-desktop.png`
- **Harm:** Any user who navigates to "Süni İntellekt Əkizi" sees a perpetual spinner, not even a "Coming soon" placeholder. Broken experience, not a stub.
- **Constitution:** Implicit trust contract of every Foundation Law violated.
- **Evidence:** `brandedby-surface-desktop.png` — full page is dark with a single spinner in the center.
- **Fix direction:** Convert to a consistent "Coming soon" pattern matching ATLAS and MindShift (product logo + name + 1-line description + single disabled CTA button).

### P0-04 — Subscription-cancelled uses English copy + destructive-looking X icon
- **Pages:** `subscription-cancelled-desktop.png`
- **Harm:** "No Charge Made" in English breaks language coherence at a high-anxiety moment. Circled-X icon reads as failure/error state — may trigger RSD in ADHD users who cannot distinguish "nothing went wrong" from "something failed".
- **Constitution:** Law 1 (never red — X is same semantic category), Law 3 (shame-free — "You cancelled" framing).
- **Evidence:** Large circled-X icon at center, "No Charge Made", "You cancelled the checkout", two equal-weight CTAs.
- **Fix direction:** Replace circled-X with neutral checkmark or neutral icon. Translate to AZ: "Heç bir xərc tutulmadı — siz istədiyiniz vaxt abunəliyi aktiv edə bilərsiniz." Promote "Back to Dashboard" as sole primary action.

### P0-05 — Profile-edit form has mixed-language fields
- **Pages:** `profile-edit-mobile.png`
- **Harm:** Field label "About you" in English inside an AZ-language session breaks cognitive continuity for Leyla. Placeholder "What do you do? What are you passionate about?" is English while surrounding labels are AZ.
- **Constitution:** Law 3 (shame-free AZ extension).
- **Evidence:** Label "About you", "Public profile" remain English; "Məkan", "Danışdığınız dillər", "Təşkilatlar tərəfindən tapıla bilər" in AZ.
- **Fix direction:** Pass all form labels and placeholders through i18n — missing keys `about_you`, `public_profile`, `org_discoverable`.

### P0-06 — Two competing primary CTAs on subscription-cancelled
- **Pages:** `subscription-cancelled-desktop.png`
- **Harm:** ADHD users face decision paralysis between two visually equal filled-weight buttons.
- **Constitution:** Law 5 (one primary action per screen).
- **Evidence:** "Back to Dashboard" (filled lavender gradient) and "Go to Settings" (dark outline, nearly equal visual weight).
- **Fix direction:** Primary = "Back to Dashboard". "Go to Settings" becomes text link beneath it.

---

## 3. P1 High-Impact Gaps

### P1-01 — AURA empty state lacks identity framing from Figma spec
- **Pages:** `aura-desktop.png`, `aura-mobile.png`
- **Harm:** Current empty state is Constitution-compliant but misses Figma "Identity Headline, Score as Context". Empty AURA = moment to frame what the user will become, not just what they must do.
- **Fix direction:** Add aspiration line above CTA: "Az ərzində Qızıl Kommunikator ola bilərsiniz — bir qiymətləndirmə ilə başlayın."

### P1-02 — Onboarding step counter ("ADDIM 1 / 3") quantifies incompleteness
- **Pages:** `onboarding-desktop.png`
- **Harm:** "ADDIM 1 / 3" literally states "2/3 not done." Triggers same cognitive load as "67% incomplete" for ADHD users.
- **Constitution:** Law 3.
- **Fix direction:** Replace fraction with progress dots (3 dots, 1 filled). Remove text counter. Optional: "Başlanğıc / Demək olar ki hazırsınız / Son addım."

### P1-03 — Assessment list shows English social proof in AZ session
- **Pages:** `assessment-list-mobile.png`
- **Evidence:** "33 professionals took an assessment this week" in English, rest AZ.
- **Fix direction:** Add `assessment.social_proof` → "Bu həftə 33 mütəxəssis qiymətləndirmə keçdi."

### P1-04 — Life Sim character stats show raw "Pul: 0"
- **Pages:** `life-surface-mobile.png`
- **Harm:** Constitution Crystal Law 4 (Identity > Currency) — "0" money violates same principle as showing zero AURA score. Punishing visual for gamified character.
- **Fix direction:** Gate Pul display until first crystal earned. Or show "Başlanğıc" instead of 0.

### P1-05 — Energy mode picker not visible in any screenshot
- **Pages:** all authed views
- **Harm:** Constitution Law 2 (Energy Adaptation) requires Full/Mid/Low picker accessible from every screen. Infrastructure exists (globals.css + `useEnergyMode()` hook) but UI is unreachable. Three icons in mobile top bar (lightning, cloud, moon) may be the picker but labels/active states invisible.
- **Fix direction:** Confirm those three icons are the picker. Add visible label or tooltip. If not, build Law 2-required picker as persistent bottom-sheet.

### P1-06 — Signup form has 6+ fields visible simultaneously on mobile
- **Pages:** `signup-mobile.png`, `signup-desktop.png`
- **Harm:** Decision paralysis. ADHD working memory ≈ 1.5 items. Visible: role cards + ad + soyad + e-poçt + şifrə + referral + checkbox.
- **Constitution:** Law 5, Law 2 (Low energy must simplify).
- **Fix direction:** Split into 2 steps — Step 1: email + password + role. Step 2: name, referral (collapsible).

### P1-07 — Notifications empty state has no actionable CTA
- **Pages:** `notifications-mobile.png`
- **Harm:** Correct Law 3 framing ("Hər şey nəzərdən keçirilib") but dead end. Needs warm exit path.
- **Fix direction:** Secondary CTA: "Qiymətləndirmənizi paylaşın — dostlarınız sizi tapsın."

---

## 4. P2 Polish Items

- **P2-01** Glass card spec drift — Figma `blur(16px) · 6% border · 70% surface opacity`, CSS `blur(12px) · 12% border`. (02-FIGMA §4)
- **P2-02** `--color-success` token mismatch — CSS `#6ee7b7`, Figma `#34d399`. Two stops lighter in code. (02-FIGMA §2)
- **P2-03** `aura-glow-*` vs `badge-glow-*` duplicate utility families. Rename to `-hero-` / `-inline-`. (01-TOKENS §4)
- **P2-04** Typography scale tokens absent from globals.css — 5 size tiers in Figma, zero `--text-*` tokens in code. (02-FIGMA §3, 01-TOKENS §5)
- **P2-05** No focus ring token. WCAG 2.2 requires 3:1. (01-TOKENS §5)
- **P2-06** `--color-surface` == `--color-surface-dim` (both `#13131b`). M3 convention broken. (01-TOKENS §2)
- **P2-07** 12 hardcoded color literals in utility classes. (01-TOKENS §3)
- **P2-08** `tabular-nums` not applied to AURA score display — digits will shift.
- **P2-09** "INVITE FRIENDS" section on profile is English-only.
- **P2-10** Leaderboard route shows login page — middleware too aggressive or route not marked public.

---

## 5. Cross-Ecosystem Coherence

Five surfaces have structural presence in sidebar + bottom nav, but UX is incoherent in three specific ways.

**Identical stub pattern for four of five products.** ATLAS, MindShift, and BrandedBy all share: centered product icon, product name in accent color, English tagline, "Coming soon" button. Only differentiator is icon + accent color. No cross-product narrative — no sentence tells user why these products exist together or what VOLAURA score unlocks in MindShift.

Life Sim is the exception — `life-surface-desktop.png` shows actual character stats and a crystal shop — but data connection to VOLAURA's AURA score is invisible. "Pul: 0" and "Enerji: 70" shown without attribution to completed assessments. The `character_events` integration is built per CLAUDE.md architecture but invisible to user.

**Bottom nav on mobile treats all 5 products as equal priority.** "Ana Səhifə / AURA Xalı / MindShift / Həyat Sim / ATLAS" — equal visual weight. For Leyla (22, mobile, first-week), three stub products add cognitive noise at the moment she's trying to understand her AURA score. Law 5 applies.

**No cross-ecosystem discovery path from the AURA screen.** After earning first AURA score, no visual path from `aura-desktop.png` to "here is how MindShift helps improve this score" or "here is how Life Sim reflects this achievement." Peak emotional moment (AURA reveal) has no ecosystem onward journey.

---

## 6. AZ Cultural Audit

- **AZ-01** Landing has "What your profile could look like" in English mid-page. Hero is AZ; this breaks for Leyla from Telegram share.
- **AZ-02** "EKSPERT DOGRULAMALARI" section label missing Ğ diacritic (should be "DOĞRULAMALARI"). Signals incomplete AZ uppercase rendering — critical for Kamal, brand-conscious.
- **AZ-03** "Qurucu Üzv" #0066 founding member badge — positive signal, preserve. AZ collectivist honor framing lands correctly.
- **AZ-04** Referral section "INVITE FRIENDS / Share this link..." entirely English inside AZ page. In AZ "tövsiyyə edin" (recommend) > "invite friends" — the mechanic is strong for AZ (mutual reward), English copy kills the warmth.
- **AZ-05** AURA privacy "Gizli — Yalnız siz görə bilərsiniz" — "hiding" a professional score maps poorly to AZ culture (şərəf/həya runs opposite direction — hide weak things, display strong). UI shouldn't present hiding as neutral equal option.
- **AZ-06** "Necə işləyir" section on landing has no content rendered — blank below heading.

---

## 7. Open Question for CEO

One bundled decision on the four "Coming soon" ecosystem surfaces (MindShift, ATLAS, BrandedBy, Life Sim stubs). Choice affects user trust, dev scope, positioning.

- **Option A — Rebrand as "Preview" with waitlist CTA.** Product-specific value prop in AZ, replace "Coming soon" with "Bildiriş al" + email capture. Minimal dev.
- **Option B — Gate stubs behind "coming soon" interstitial only for new users.** Bottom nav = 3 items for first 30 days. Requires feature-flag work.
- **Option C — Invest Phase 1 in making Life Sim surface fully data-driven from VOLAURA events.** First cross-ecosystem bridge: "Your AURA became your character's stat." Others stay as-is. High narrative value.
- **Option D — Remove ecosystem surfaces from VOLAURA web entirely until real interaction exists.** Ship VOLAURA standalone. Ecosystem linkage separate phase. Clearest for Nigar.

Phase 1 scope is undetermined on ecosystem coherence dimension without this decision.

---

**Screenshots cited:** landing, signup, aura, profile, profile-edit, mindshift-surface, atlas-surface, brandedby-surface, life-surface, assessment-list, notifications, aura-contest, subscription-cancelled, settings, leaderboard, discover (each × desktop + mobile where available).
