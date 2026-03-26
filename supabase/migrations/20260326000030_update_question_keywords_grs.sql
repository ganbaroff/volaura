-- =============================================================================
-- Migration: Update open-ended question keyword sets for GRS compliance
-- Reason: Original single-word keywords (estimated GRS 0.28–0.35) fail the
--         Gaming Resistance Score threshold of 0.60. Replaced with multi-word
--         behavioral phrases that require genuine competence to produce naturally.
-- See: apps/api/app/core/assessment/quality_gate.py — compute_grs()
-- ADR-010: keyword_fallback is degraded mode; question design is primary defense.
-- =============================================================================

-- Q3: Cross-cultural Communication (medium, open_ended)
-- Old keywords: single words ("calm", "smile", "gesture", "point", "colleague")
-- New keywords: behavioral phrases (GRS estimated 0.82)
UPDATE public.questions
SET expected_concepts = '[
    {"name": "calm_tone", "weight": 0.20, "keywords": ["spoke slowly and clearly", "kept my voice soft", "maintained a calm demeanor", "reduced my speaking pace", "stayed patient despite the frustration", "sakit ton saxladım", "yavaş danışdım"]},
    {"name": "nonverbal_support", "weight": 0.20, "keywords": ["used hand gestures to indicate", "drew a quick sketch", "pointed to a map", "used visual aids to guide", "showed them the registration form", "əl hərəkətlərindən istifadə etdim", "xəritəni göstərdim"]},
    {"name": "simplify_language", "weight": 0.20, "keywords": ["used short simple sentences", "avoided technical jargon", "spoke one step at a time", "repeated key information more slowly", "used basic words they might know", "qısa sadə cümlələr işlətdim", "texniki terminlərdən çəkindim"]},
    {"name": "seek_help", "weight": 0.20, "keywords": ["found a bilingual colleague to assist", "used a translation app", "called over a team member who spoke their language", "asked a nearby colleague to help translate", "used Google Translate as a bridge", "ikidilli həmkar tapdım", "tərcümə proqramından istifadə etdim"]},
    {"name": "follow_through", "weight": 0.20, "keywords": ["confirmed they completed registration successfully", "checked they had everything they needed", "ensured the delegate was no longer confused", "stayed with them until the issue was resolved", "followed up after handing them to a colleague", "qeydiyyatı tamamladıqlarını təsdiqlədi", "nəticəni yoxladım"]}
]'::jsonb
WHERE id = 'c0000001-0000-0000-0000-000000000003';


-- Q4: Written Communication / Crisis (hard, open_ended)
-- Old keywords: single words ("team", "split", "calm", "check") + "B-14" (only specific one)
-- New keywords: scenario-anchored behavioral phrases (GRS estimated 0.85)
UPDATE public.questions
SET expected_concepts = '[
    {"name": "prioritize_channels", "weight": 0.25, "keywords": ["sent a group message to all attendees", "used the event app to broadcast", "made an announcement over the public address system", "contacted attendees simultaneously through multiple channels", "reached everyone at once via messaging platform", "bütün iştirakçılara qrup mesajı göndərdim", "ictimai elan sistemi ilə xəbər verdim"]},
    {"name": "delegate", "weight": 0.20, "keywords": ["split the venue into sections and assigned each volunteer a zone", "sent a different volunteer to each floor", "divided the team to cover the whole building", "each team member took responsibility for a different area", "coordinated with my team to cover all areas simultaneously", "binayı bölgələrə bölüb hər könüllüyə sahə təyin etdim", "komandanı müxtəlif əraziləri əhatə etmək üçün böldüm"]},
    {"name": "clear_message", "weight": 0.25, "keywords": ["clearly stated the new room is B-14", "gave exact directions to room B-14", "specified the floor and building of the new location", "included the room number in every message", "made sure the message had the room number and timing", "yeni otağın B-14 olduğunu bildirdim", "hər mesajda otaq nömrəsini göstərdim"]},
    {"name": "confirm_coverage", "weight": 0.15, "keywords": ["each volunteer reported back once their area was covered", "confirmed all 50 attendees were reached", "collected confirmation from each zone volunteer", "verified no one was missed before the session started", "did a headcount at the new room to verify everyone arrived", "hər könüllü öz ərazisini əhatə etdikdən sonra bildirdi", "50 iştirakçının hamısına çatdığımı təsdiqlədi"]},
    {"name": "stay_calm", "weight": 0.15, "keywords": ["maintained composure despite the time pressure", "stayed focused and worked systematically through each zone", "kept the team calm while moving quickly", "communicated urgency without causing panic", "worked through the problem in an organized manner", "vaxt təzyiqi altında özünü itirmədi", "panikaya yol vermədən təcililik hissini çatdırdım"]}
]'::jsonb
WHERE id = 'c0000001-0000-0000-0000-000000000004';
