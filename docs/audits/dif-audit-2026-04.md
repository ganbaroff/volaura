# Semantic DIF Audit — VOLAURA Assessment Item Bank

**Date:** 2026-04-15
**Scope:** 120 active items across 8 competencies (15 each)
**Source of truth:** `docs/audits/questions-export-2026-04-15.json` (119 items in export — 120 claimed active; 1-item delta to reconcile separately)
**Author:** CTO, reviewed against ISO 10667-2 §7 and AZ PDPA
**Prior work:** `docs/audits/dif-audit-methodology-2026-04-14.md`

---

> **APPLIED 2026-04-15 Baku** — the 3 worst items from §E have been
> soft-deleted (is_active=FALSE, needs_review=TRUE, kept for audit) and
> replaced in prod. Pre-check showed all 3 had times_shown=0, so no IRT
> calibration was lost and no session answer history points to them.
>
> New active item IDs:
> - english_proficiency (E1 email, CEFR B1): `ca78d3c2-35e1-41e9-8abf-58608c28acf6`
> - empathy_safeguarding (E2 icebreaker): `df1275ea-f1dc-4760-b213-7fdd5f8ebc48`
> - tech_literacy (E3 undo): `d7b51c66-bab1-4b94-9c16-d9045fc901fc`
>
> Per-competency active counts re-verified: 15 / 15 / 15 on the three
> touched competencies. Total active 120. New items carry needs_review=TRUE
> and zeroed IRT — adaptive engine will treat them as high-uncertainty
> until ~30 answers per item land.

---

## A. Executive Summary

- **12 items flagged** across 6 of 8 competencies. Three systemic patterns dominate: (1) `english_proficiency` is miscalibrated to business/corporate English without CEFR anchoring, privileging English-medium private-school graduates; (2) `leadership` is operationalized only as corporate leadership, ignoring community/family/NGO contexts where most AZ respondents exercise leadership; (3) `tech_literacy` presumes Windows-laptop office-work environment, disadvantaging mobile-first, non-office, and motor-accessibility profiles.
- **3 items recommended for full replacement** before launch: `e5000077-...0005` (corporate-jargon translation), `e5000012-...0004` (primes stereotype threat for observant Muslim women), `60000001-...0002` (keyboard-shortcut dependent).
- **P0 gap beyond items themselves:** `scenario_ru` is null for 100% of 120 items, and `cefr_level` is null for 100% of items. Both block "CIS-region verified talent platform" positioning and any defensible english_proficiency scoring. Item-level DIF fixes cannot ship without these two data-completeness fixes.

---

## B. Methodology Note — Why Semantic Not Statistical

Statistical DIF (Mantel-Haenszel, Raju area, logistic-regression DIF) requires, per Zumbo's minimum power guidance and the AERA/APA/NCME *Standards*, **N ≥ 200 per focal/reference group per item**, with stable reference groups. For a 120-item bank with 6 demographic axes and 4 age bands, the realistic floor is **~2,000 completed, full-bank assessments** before any DIF statistic is defensible.

**Current state (2026-04-15):** 39 completed sessions in production. With adaptive routing (CAT engine exposes each examinee to ~20 items, not 120), per-item response counts are in single digits. Statistical DIF would generate noise indistinguishable from bias and give false confidence.

**Therefore this review is semantic/cultural/linguistic.** It flags items whose wording would plausibly produce group-level performance gaps unrelated to the target construct, using the 8-tag taxonomy in `dif-audit-methodology-2026-04-14.md`.

**Re-run trigger for statistical DIF:**
- N ≥ 2,000 completed assessments, AND
- Each demographic group ≥ 200 completions, AND
- Per-item response count ≥ 100 for the most-exposed 30 items.
Expected earliest calendar: Q4 2026 assuming B2B pilot + 2 org events.

---

## C. Flagged Items

| # | Item ID (prefix) | Competency | Red-flag tag | Reason (1 sentence) | Suggested rewording |
|---|---|---|---|---|---|
| 1 | `e5000077` (ending `...0005`) | english_proficiency | 4. Class/education | "Per our previous discussion, please action the deliverables by EOD" uses four pieces of corporate-professional English jargon in one sentence; this is CEFR C1 business register, far above the `easy` tag and inaccessible to state-school graduates with B1/B2 English who nonetheless communicate effectively. | Replace with plain-register email: "Hi, following up on yesterday — please finish the two tasks we agreed on by end of day. Thanks." Test comprehension, not corporate-jargon exposure. |
| 2 | `e5000077` (ending `...0001`) | english_proficiency | 4. Class/education | "Dear Sir/Madam..." vs "Dear [Name], I am writing to introduce [Organization]" — correct answer encodes Anglo-American business-letter convention that state-school AZ English curriculum does not teach; graders of B1-level speakers with strong pragmatic competence are penalized. | Keep the item but re-tag as `medium` difficulty, add CEFR B2, and rewrite option A as "Salam, I'd like to introduce our team" — a register that AZ-professional English users actually produce. |
| 3 | `e5000077` (ending `...0002`) | english_proficiency | 6. Bilingual asymmetry | Pure grammar item ("Each of the participants have submitted...") has no AZ translation of the options — the four English sentences are presented untranslated, which is fine for the construct, but the `scenario_az` field simply says "Hansı cümlədə qrammatik xəta var?" with no guidance that this is a grammar-identification task. AZ-first test-takers may misinterpret the task. | Add an AZ framing sentence: "Aşağıdakı İngiliscə cümlələrdən hansında qrammatik xəta var? (Cümlələr tərcümə edilməyib — bu İngilis dili bilik yoxlamasıdır.)" |
| 4 | `e5000012` (ending `...0004`) | empathy_safeguarding | 2. Gender coding + 8. Regional/ethnic | "A volunteer from a conservative cultural background expresses discomfort with a mixed-gender team activity" — in AZ context, this near-unambiguously codes to an observant Muslim woman. Scoring penalizes "Excuse them from the activity entirely" (0.3) and rewards "try it first and see if they feel comfortable" (0.6) — a coercive nudge that primes stereotype threat and punishes culturally protective answers. | Full replacement (see §E). Retain construct (design for inclusion) but strip group coding and remove the "try it first" option. |
| 5 | `60000001` (ending `...0002`) | tech_literacy | 5. Ableism + 4. Class/education | Correct answer requires `Ctrl+Z` keyboard shortcut on Google Sheets. Test-takers who use the product predominantly on tablet/phone, or who have motor impairments requiring alternative input, or who simply use Edit → Undo menu, are marked wrong despite having the correct mental model. | Rewrite options: A "Close tab and reopen", B "Immediately undo the change (Ctrl+Z, or Edit menu → Undo) before any other action", C "Notify team and wait", D "Re-enter manually". Scoring unchanged; knowledge construct preserved; input-modality neutral. |
| 6 | `60000001` (ending `...0005`) | tech_literacy | 5. Ableism + 3. Urban bias | "Press the display toggle shortcut (Windows+P or Fn+F key)" — Windows-only solution; a Mac user, Linux user, or someone who has only worked on tablets is penalized. Also assumes speaker-owned-laptop event format, which is a corporate-conference assumption. | Add platform-neutral phrasing: "Use the display mirroring / external screen toggle on the laptop (Windows+P on Windows, Cmd+F1 or Display Preferences on Mac)." |
| 7 | `d0000006` (ending `...0011`) | tech_literacy | 4. Class/education | "Check the tool's privacy policy, verify whether it stores uploaded data, and consult your IT or compliance team" — assumes the test-taker has an IT/compliance team to consult, framing tech literacy through the lens of corporate governance. Solo-practitioner, freelancer, and small-NGO respondents have no such team. | Reword option B: "Check the tool's privacy policy and whether it stores uploaded data; if you have an IT or compliance lead, consult them; if not, do not upload real client data — use fake test data to verify, then re-evaluate." |
| 8 | `d0000006` (ending `...0015`) | tech_literacy | 4. Class/education | GDPR-specific incident-response procedure as the correct answer. AZ test-takers working for purely domestic employers have no legal duty to know GDPR notification assessment; the `ABP hüquqi məxfiliyi` framework differs. Rewards respondents with multinational-employer exposure. | Generalize: replace "potential GDPR notification assessment" with "legal and regulatory notification assessment per your jurisdiction (e.g. GDPR for EU data, AZ PDPA for Azerbaijani subjects)". |
| 9 | `e5000044` (ending `...0004`) | leadership | 3. Urban bias + corporate framing | "Cross-functional team of 12 people... three subgroups... project board with cross-group dependencies" — exclusively corporate vocabulary. A village-event coordinator, family-business leader, or NGO section head exercising the same leadership construct has no mapping. | Rewrite scenario once in corporate frame, once as "community event coordinator leading 12 people across three sub-teams" — randomize per examinee. |
| 10 | `a0000007` (ending `...0015`) | adaptability | 3. Urban bias + 4. Class/education | "Department is merging... direct manager is leaving... half of team reports to new leader... role may evolve" — white-collar career scenario. Gig-workers, freelancers, and rural respondents face *different* adaptability challenges (seasonal demand swings, extended family economic shocks, migration). | Keep as one variant; add a parallel-construct item: "Your small family business loses its main supplier; you must rebuild the supply chain in 3 months with limited information." Same construct, different surface. |
| 11 | `c0000001` (ending `...0008`) | communication | 7. Age bias | "Students (21-25 years old)" get "technical app terminology"; "seniors (60+)" get "slow your pace, physical demos, avoid jargon" — the correct answer encodes a stereotype about age-tech relationship. A 63-year-old software engineer and a 22-year-old farmer with no smartphone both exist; the item trains the scorer to reward stereotype adherence. | Reframe around *observed learning preferences* not age: "You are explaining the app to two groups: Group X communicates rapidly in messaging apps and expects jargon; Group Y has never used the app and asks to 'see it done first.' Adjust for each." |
| 12 | `e0000001` (ending `...0010`) | english_proficiency | 4. Class/education | "Simultaneous translation in Room B was poor" — entire scenario presumes the test-taker is familiar with international-conference infrastructure (interpretation booths, rooms lettered A-B-C, escalation paths to tech team). Baku-megaevent volunteers recognize this instantly; rural respondents do not. | Replace "simultaneous translation in Room B was poor" with "the English interpreter in the main session was hard to understand all afternoon" — strips insider vocabulary, preserves construct. |

**Not flagged but noted:**
- `80000001-...0003` (prayer room) — treats a culturally universal AZ request respectfully; option A is the clearly wrong distractor. Item is sound.
- `e0000001-...0006` (Azerbaijani folk music, English) — construct-relevant cultural content; good example of localization done right.
- `80000001-...0005` (16-year-old safeguarding) — structurally sound; correct answer aligns with AZ child-protection guidance. Could add "escalate to same-gender staff member where available" as an option to be maximally culturally sensitive, but current item is defensible.

---

## D. Systemic Patterns

1. **Russian-language gap is 100%.** `scenario_ru: null` on all 120 items. The stated positioning targets AZ + CIS region; a CIS respondent who speaks Russian as L1 and AZ/EN as L2 faces compounded disadvantage: the assessment is bilingual AZ+EN only, and the russification gap alone will drive DIF against native-Russian-speaking applicants regardless of construct. **This is the single largest semantic-DIF risk in the bank** and has priority over any individual item rewrite.

2. **`english_proficiency` is a private-school proxy, not a competency test.** Five of the 15 items reward corporate/business register (jargon idioms, formal business-letter conventions, conference-infrastructure vocabulary). No item tests functional English at CEFR A2-B1 (directions, simple requests, basic workplace safety) despite A2-B1 being the realistic ceiling for ~60% of AZ working-age population per State Statistics Committee 2024 education data. The competency as seeded will score "can you afford English-medium schooling" more than "can you communicate effectively in English."

3. **`leadership` is operationalized exclusively as corporate leadership.** Zero items test leadership in family-business, NGO, community-event, religious-community, or informal-group contexts — all of which are normative leadership venues in AZ, especially for women and rural respondents. This systematically underscores construct-valid leadership in groups that cannot show their work in a corporate scenario.

4. **`tech_literacy` assumes Windows + office + internet + ownership.** Ctrl+Z, Windows+P/Fn+F, Google Workspace, YouTube access, no-code tool exposure, GDPR familiarity — all assume a specific device, platform, employer type, and connectivity profile. Mobile-first, kiosk-workers, and rural respondents face surface-level DIF on items whose construct (basic digital problem-solving) they would otherwise pass.

5. **CEFR anchoring is missing from every english_proficiency item** (`cefr_level: null`, 15/15). Without CEFR tags, difficulty calibration is subjective; IRT parameters cannot be validated against an external standard; and post-launch, a respondent cannot see "you scored at B2" — which is the *actual* professional currency in AZ/CIS job markets.

6. **Lingering "volunteer" / "team member" surface artifacts.** Many scenarios contain awkward phrasings like "you are a team member team lead" (c0000001 item 0006), "lead team member for an accreditation desk" (20000001 item 0009), "volunteer from a conservative cultural background" (e5000012 item 0004) — evidence of an incomplete find-replace when the platform pivoted from volunteer-focused to verified-talent positioning. Not a DIF issue per se, but degrades construct validity and signals to test-takers that the assessment is unpolished.

7. **No item rewards disability-adapted answers** as the correct response. Disability appears once (visually impaired delegate, d0000001 item 0008, open-ended) but never as a scored option across 120 MCQ items. Respondents with disability-sensitive instincts have no item that explicitly values their perspective.

---

## E. Top 3 Items to REPLACE Before Launch

### E1. Replace `e5000077-...0005` (english_proficiency, easy, corporate-jargon translation)

**Current:** "Per our previous discussion, please action the deliverables by EOD." Options ask the test-taker to recognize this as "complete agreed tasks by end of today."

**Problem:** Four pieces of corporate-English jargon ("per our previous discussion", "action" as verb, "deliverables", "EOD") in one sentence. Functionally tests exposure to native-English-speaker corporate culture, not English comprehension. State-school CEFR-B1 graduates who work in AZ firms will fail this despite having fully functional workplace English.

**Replacement:**
```
scenario_en: "A colleague sends you this message at 16:30 on Friday: 'Hi, one quick thing — could you send me the meeting notes from Tuesday before you leave today? Thanks!' What should you do?"
scenario_az: "[AZ translation]"
scenario_ru: "[RU translation]"
cefr_level: "B1"
options:
  A: "Send the meeting notes before leaving today" (score 1.0)
  B: "Reply that you will send them Monday" (score 0.2)
  C: "Ignore the message since it is not urgent" (score 0.0)
  D: "Ask what meeting they mean" (score 0.5 — partial credit: context-aware but should check own notes first)
difficulty: easy
```
Construct preserved (can you act on a polite English email request). Jargon removed. CEFR explicit.

### E2. Replace `e5000012-...0004` (empathy_safeguarding, medium, mixed-gender activity)

**Current:** "A volunteer from a conservative cultural background expresses discomfort with a mixed-gender team activity. You need all team members to participate. What do you do?" Correct: redesign activity. Scored distractor: "Ask them to try it first" (0.6).

**Problem:** Scenario ethnically/religiously codes the "problem person" as observant-Muslim-woman in AZ context; primes stereotype threat; the 0.6-scored "try it first" option is a coercive nudge that punishes culturally protective thinking (which *is* the empathetic answer for many AZ test-takers).

**Replacement:**
```
scenario_en: "You are running a team-building workshop and one participant tells you privately that the planned physical-contact icebreaker makes them uncomfortable. They do not explain why. You need the full team aligned by the end of the session. What do you do?"
scenario_az: "[AZ translation]"
scenario_ru: "[RU translation]"
options:
  A: "Tell them participation is mandatory — discomfort is part of growth" (score 0.1)
  B: "Redesign the icebreaker so everyone can participate without physical contact" (score 1.0)
  C: "Excuse them from the icebreaker and run it for the rest of the group" (score 0.5 — partial: protective but leaves them out)
  D: "Ask what specifically would make them more comfortable, then adjust" (score 0.9 — agency-first)
difficulty: medium
```
Construct preserved (inclusive design under pressure). Group-coding stripped. No coercive option.

### E3. Replace `60000001-...0002` (tech_literacy, easy, Ctrl+Z)

**Current:** "You accidentally delete a row with 12 names. What do you do IMMEDIATELY?" Correct: "Press Ctrl+Z (undo)."

**Problem:** Keyboard-shortcut-specific; penalizes tablet/mobile/motor-accessibility users who know the concept but use menu/gesture.

**Replacement:**
```
scenario_en: "You accidentally delete a row containing 12 names from a shared Google Sheet. What do you do IMMEDIATELY?"
scenario_az: "[AZ translation]"
scenario_ru: "[RU translation]"
options:
  A: "Close the browser tab and reopen the file" (score 0.2)
  B: "Undo the deletion before doing anything else — via keyboard shortcut, the Edit menu, or mobile undo gesture" (score 1.0)
  C: "Notify the team and wait for someone more experienced to fix it" (score 0.5 — partial: safe but slow)
  D: "Re-enter the 12 names manually from memory" (score 0.1)
difficulty: easy
```
Construct preserved (knowing undo is the correct first action). Input-modality neutral.

---

## F. Action Items (ordered by blocker severity)

1. **[P0, launch blocker] Add `scenario_ru` to all 120 items.** Translate AZ → RU via native-Russian-speaker reviewer (not MT-only). Budget: ~20 hours of reviewer time at $25/h = $500. Without this, the "CIS-region verified talent platform" claim is marketing, not product.

2. **[P0, launch blocker] Replace 3 worst items (§E).** Approximately 3 hours of content work + bilingual translation. Must land before first paid B2B pilot.

3. **[P1, launch blocker] Reword 9 remaining flagged items (§C items 1-12 minus the 3 replacements).** Approximately 6 hours of content work.

4. **[P1] Add `cefr_level` to all 15 `english_proficiency` items.** Required for defensible scoring and for exposing respondent-facing CEFR results. Use CEFR-Companion Volume 2020 descriptors as reference. Approximately 4 hours of tagging + review.

5. **[P2] Re-do find-replace cleanup.** Fix lingering "team member team lead" / "volunteer from a..." / "lead team member for" awkward phrasings across all items. Purely cosmetic but signals professionalism.

6. **[P2] Add 2-person AZ-native review board for all future items.** Proposed: one urban Baku reviewer, one regional reviewer (Ganja or Sheki). Both review every new item before it enters `active=true` state. Logged in `memory/swarm/review-board.md`. Standing review slot: 30 min/week.

7. **[P3] Schedule statistical DIF re-run after N ≥ 2,000 completions.** Set a `character_events` consumer that fires an alert when per-item response count clears N=100 for the top 30 items. Expected trigger: Q4 2026. Use Mantel-Haenszel with Holm correction; focal groups as listed in §B.

8. **[P3] Add one construct-parallel item per competency in a non-corporate frame.** Same construct, rural/NGO/family surface. Begins rebalancing systemic pattern §D.3.

---

## Appendix — Per-competency flag counts

| Competency | Items | Flagged | Replacement proposed |
|---|---|---|---|
| communication | 15 | 1 | 0 |
| reliability | 15 | 0 | 0 |
| english_proficiency | 15 | 3 | 1 |
| leadership | 15 | 1 | 0 |
| event_performance | 15 | 0 | 0 |
| tech_literacy | 15 | 4 | 1 |
| adaptability | 15 | 1 | 0 |
| empathy_safeguarding | 15 | 2 | 1 |
| **Total** | **120** | **12** | **3** |

`reliability` and `event_performance` pass semantic DIF review — items are construct-focused and demographically neutral. `tech_literacy` is the most biased competency in the bank (4 flagged + 1 replacement) and requires the deepest rewrite post-launch.

---

**Sign-off:** This document is advisory until reviewed by an AZ-native assessment specialist. Items listed are candidates for rework, not mandatory removals. All `needs_review: false` flags should be flipped to `true` on the 12 flagged item IDs in the next migration.
