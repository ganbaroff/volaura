-- =============================================================================
-- VOLAURA SEED DATA
-- Run: supabase db reset (local) or via Supabase SQL editor
-- =============================================================================

-- =============================================================================
-- 1. COMPETENCIES (8 — weights MUST sum to 1.0 — DO NOT CHANGE)
-- =============================================================================
INSERT INTO public.competencies (id, slug, name_en, name_az, description_en, description_az, weight, display_order) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'communication',
    'Communication',
    'Kommunikasiya',
    'Ability to convey information clearly, listen actively, and adapt communication style to different audiences and situations.',
    'Məlumatı aydın şəkildə çatdırmaq, fəal dinləmək və müxtəlif auditoryalara uyğun ünsiyyət tərzi seçmək bacarığı.',
    0.20,
    1
),
(
    '22222222-2222-2222-2222-222222222222',
    'reliability',
    'Reliability',
    'Etibarlılıq',
    'Consistently showing up on time, completing commitments, and being dependable under pressure and changing conditions.',
    'Vaxtında gəlmək, öhdəlikləri yerinə yetirmək və çətin şəraitdə etibarlı olmaq.',
    0.15,
    2
),
(
    '33333333-3333-3333-3333-333333333333',
    'english_proficiency',
    'English Proficiency',
    'İngilis dili səviyyəsi',
    'Ability to communicate effectively in English in professional event environments (B1-C1 range).',
    'Peşəkar tədbir mühitlərində ingilis dilində effektiv ünsiyyət qurmaq bacarığı (B1-C1 səviyyəsi).',
    0.15,
    3
),
(
    '44444444-4444-4444-4444-444444444444',
    'leadership',
    'Leadership',
    'Liderlik',
    'Ability to motivate and guide others, take initiative, make decisions under uncertainty, and manage small teams.',
    'Başqalarını motivasiya etmək, qərar qəbul etmək, kiçik komandaları idarə etmək bacarığı.',
    0.15,
    4
),
(
    '55555555-5555-5555-5555-555555555555',
    'event_performance',
    'Event Performance',
    'Tədbir performansı',
    'Assessed from coordinator ratings after real events. Reflects punctuality, task completion, and professionalism on-site.',
    'Real tədbirlərdən sonra koordinator reytinqləri əsasında qiymətləndirilir.',
    0.10,
    5
),
(
    '66666666-6666-6666-6666-666666666666',
    'tech_literacy',
    'Tech Literacy',
    'Texnoloji savadlılıq',
    'Comfort with digital tools, event management software, communication platforms, and basic IT troubleshooting.',
    'Rəqəmsal alətlər, kommunikasiya platformaları və əsas İT problemlərinin həlli ilə bağlı bacarıqlar.',
    0.10,
    6
),
(
    '77777777-7777-7777-7777-777777777777',
    'adaptability',
    'Adaptability',
    'Uyğunlaşma qabiliyyəti',
    'Ability to handle unexpected changes, stay calm under pressure, switch roles quickly, and maintain quality.',
    'Gözlənilməz dəyişikliklərə uyğunlaşmaq, təzyiq altında sakit qalmaq və keyfiyyəti qorumaq.',
    0.10,
    7
),
(
    '88888888-8888-8888-8888-888888888888',
    'empathy_safeguarding',
    'Empathy & Safeguarding',
    'Empatiya və qoruma',
    'Sensitivity to diverse needs, cultural awareness, ability to handle vulnerable participants with care and respect.',
    'Müxtəlif ehtiyaclara həssaslıq, mədəni fərqindəlik, zəif iştirakçılara hörmətlə yanaşmaq.',
    0.05,
    8
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 2. BADGES (tier badges)
-- =============================================================================
INSERT INTO public.badges (slug, name_en, name_az, description_en, description_az, badge_type) VALUES
('bronze', 'Bronze Professional', 'Bürünc Peşəkar', 'Completed initial assessment with AURA score 40-59.', 'AURA balı 40-59 olan ilkin qiymətləndirməni tamamladı.', 'tier'),
('silver', 'Silver Professional', 'Gümüş Peşəkar', 'Proven professional with AURA score 60-74.', 'AURA balı 60-74 olan sübut edilmiş peşəkar.', 'tier'),
('gold', 'Gold Professional', 'Qızıl Peşəkar', 'Elite professional with AURA score 75-89.', 'AURA balı 75-89 olan elit peşəkar.', 'tier'),
('platinum', 'Platinum Professional', 'Platin Peşəkar', 'Top-tier professional with AURA score 90+.', 'AURA balı 90+ olan ən yüksək səviyyəli peşəkar.', 'tier'),
('first_event', 'First Event', 'İlk Tədbir', 'Completed first professional event successfully.', 'İlk peşəkar tədbirini uğurla tamamladı.', 'achievement'),
('elite', 'Elite Professional', 'Elit Peşəkar', 'AURA 75+ with 2 or more competencies above 75.', 'AURA 75+ və 2 və ya daha çox kompetensiya 75 üzərindədir.', 'special')
ON CONFLICT (slug) DO NOTHING;


-- =============================================================================
-- 3. QUESTIONS — Communication Competency
-- 5 REAL questions (calibrated) + 15 placeholders
-- IRT params: irt_a=discrimination, irt_b=difficulty, irt_c=guessing
-- =============================================================================

-- ---- REAL QUESTIONS (5) ----

-- Q1: MCQ — Active Listening (Easy)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'During a briefing, a participant asks you a question you didn''t fully understand. What is the BEST response?',
    'Brifinq zamanı bir iştirakçı sizə tam başa düşmədiyiniz bir sual verir. Ən YAXŞI cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Give a general answer to avoid awkwardness", "text_az": "Yöndəmsizlikdən qaçmaq üçün ümumi cavab ver"},
        {"key": "B", "text_en": "Politely ask them to repeat or clarify the question", "text_az": "Nəzakətlə soruşun ki, sualı təkrarlasın və ya aydınlaşdırsın"},
        {"key": "C", "text_en": "Redirect them to your supervisor immediately", "text_az": "Dərhal onları rəhbərinizə yönləndir"},
        {"key": "D", "text_en": "Nod and pretend you understood", "text_az": "Başını tərpət və başa düşdüyünü iddia et"}
    ]',
    'B',
    1.5, -1.2, 0.1,
    'Active listening includes asking for clarification when needed. This demonstrates respect and ensures accurate communication.',
    'Fəal dinləmə lazım olduqda aydınlaşdırma istəməyi əhatə edir. Bu hörmət göstərir və dəqiq ünsiyyəti təmin edir.',
    'Practice paraphrasing: repeat what you heard in your own words to confirm understanding.',
    'Başa düşdüyünüzü təsdiqləmək üçün eşitdiklərinizi öz sözlərinizlə təkrarlayın.'
)
ON CONFLICT (id) DO NOTHING;

-- Q2: MCQ — Conflict Communication (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'Two attendees at an event are having a heated argument that is disturbing others. You are the nearest team member. What do you do FIRST?',
    'Tədbirde iki iştirakçı başqalarını narahat edən qızğın mübahisə aparır. Siz ən yaxın komanda üzvüsünüz. İlk olaraq nə edərdiniz?',
    '[
        {"key": "A", "text_en": "Call security immediately without approaching", "text_az": "Yaxınlaşmadan dərhal təhlükəsizlik xidmətini çağır"},
        {"key": "B", "text_en": "Approach calmly, introduce yourself, and acknowledge both parties before de-escalating", "text_az": "Sakit şəkildə yaxınlaş, özünü tanıt və sakinləşdirməzdən əvvəl hər iki tərəfi tanı"},
        {"key": "C", "text_en": "Tell them to be quiet or leave", "text_az": "Onlara sakit olmalarını və ya çıxmalarını söylə"},
        {"key": "D", "text_en": "Ignore it — it''s not your responsibility", "text_az": "Nəzərə alma — bu sənin məsuliyyətin deyil"}
    ]',
    'B',
    1.8, 0.1, 0.15,
    'De-escalation starts with calm presence and acknowledgment. Jumping to authority figures can escalate tension.',
    'Sakinləşdirmə sakit mövcudluq və tanınmayla başlayır. Dərhal səlahiyyətlilərə müraciət gərginliyi artıra bilər.',
    'Study basic conflict resolution: LEAP method (Listen, Empathize, Agree, Partner).',
    'Əsas münaqişə həlli metodlarını öyrənin: LEAP metodu (Dinlə, Empatiya qur, Razılaş, Əməkdaşlıq et).'
)
ON CONFLICT (id) DO NOTHING;

-- Q3: Open-ended — Cross-cultural Communication (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000003',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'open_ended',
    'You are coordinating a registration desk at an international conference. A foreign delegate approaches and appears confused — they speak limited English and seem frustrated. Describe exactly what you would do.',
    'Siz beynəlxalq konfranslarda qeydiyyat masasını koordinasiya edirsiniz. Xarici bir nümayəndə yaxınlaşır və çaşqın görünür — onun ingilis dili məhduddur və əsəblilik hiss olunur. Dəqiq nə edərdiniz?',
    '[
        {"name": "calm_tone", "weight": 0.20, "keywords": ["spoke slowly and clearly", "kept my voice soft", "maintained a calm demeanor", "reduced my speaking pace", "stayed patient despite the frustration", "sakit ton saxladım", "yavaş danışdım"]},
        {"name": "nonverbal_support", "weight": 0.20, "keywords": ["used hand gestures to indicate", "drew a quick sketch", "pointed to a map", "used visual aids to guide", "showed them the registration form", "əl hərəkətlərindən istifadə etdim", "xəritəni göstərdim"]},
        {"name": "simplify_language", "weight": 0.20, "keywords": ["used short simple sentences", "avoided technical jargon", "spoke one step at a time", "repeated key information more slowly", "used basic words they might know", "qısa sadə cümlələr işlətdim", "texniki terminlərdən çəkindim"]},
        {"name": "seek_help", "weight": 0.20, "keywords": ["found a bilingual colleague to assist", "used a translation app", "called over a team member who spoke their language", "asked a nearby colleague to help translate", "used Google Translate as a bridge", "ikidilli həmkar tapdım", "tərcümə proqramından istifadə etdim"]},
        {"name": "follow_through", "weight": 0.20, "keywords": ["confirmed they completed registration successfully", "checked they had everything they needed", "ensured the delegate was no longer confused", "stayed with them until the issue was resolved", "followed up after handing them to a colleague", "qeydiyyatı tamamladıqlarını təsdiqlədi", "nəticəni yoxladım"]}
    ]',
    2.0, 0.3, 0.0,
    'Excellent cross-cultural communication uses calm tone, non-verbal cues, simplified language, seeks help when needed, and follows through.',
    'Mükəmməl mədəniyyətlərarası ünsiyyət sakit ton, sözsüz işarələr, sadə dil, lazım olduqda kömək axtarmaq və nəticəni izləməyi əhatə edir.',
    'Practice the 3 S''s: Slow down, Smile, Simplify. Use Google Translate as a bridge tool at events.',
    '3S-i məşq edin: Yavaşlayın, Gülümsəyin, Sadələşdirin. Tədbirlərdə körpü aləti kimi Google Translate-dən istifadə edin.'
)
ON CONFLICT (id) DO NOTHING;

-- Q4: Open-ended — Written Communication (Hard)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    is_sjt_reliability, lie_detector_flag,
    feedback_en, feedback_az
) VALUES (
    'c0000001-0000-0000-0000-000000000004',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'open_ended',
    'Your team coordinator just texted: "The session room changed to B-14, inform all attendees ASAP." You have 10 minutes and 50 attendees scattered across the venue. Describe your communication plan.',
    'Komanda koordinatorunuz yazı yazdı: "Sessiya otağı B-14-ə dəyişdirildi, bütün iştirakçıları dərhal xəbərdar edin." Binanın hər yerinə səpələnmiş 50 iştirakçı üçün 10 dəqiqəniz var. Kommunikasiya planınızı təsvir edin.',
    '[
        {"name": "prioritize_channels", "weight": 0.25, "keywords": ["sent a group message to all attendees", "used the event app to broadcast", "made an announcement over the public address system", "contacted attendees simultaneously through multiple channels", "reached everyone at once via messaging platform", "bütün iştirakçılara qrup mesajı göndərdim", "ictimai elan sistemi ilə xəbər verdim"]},
        {"name": "delegate", "weight": 0.20, "keywords": ["split the venue into sections and assigned each team member a zone", "sent a different team member to each floor", "divided the team to cover the whole building", "each team member took responsibility for a different area", "coordinated with my team to cover all areas simultaneously", "binayı bölgələrə bölüb hər komanda üzvünə sahə təyin etdim", "komandanı müxtəlif əraziləri əhatə etmək üçün böldüm"]},
        {"name": "clear_message", "weight": 0.25, "keywords": ["clearly stated the new room is B-14", "gave exact directions to room B-14", "specified the floor and building of the new location", "included the room number in every message", "made sure the message had the room number and timing", "yeni otağın B-14 olduğunu bildirdim", "hər mesajda otaq nömrəsini göstərdim"]},
        {"name": "confirm_coverage", "weight": 0.15, "keywords": ["each team member reported back once their area was covered", "confirmed all 50 attendees were reached", "collected confirmation from each zone member", "verified no one was missed before the session started", "did a headcount at the new room to verify everyone arrived", "hər komanda üzvü öz ərazisini əhatə etdikdən sonra bildirdi", "50 iştirakçının hamısına çatdığımı təsdiqlədi"]},
        {"name": "stay_calm", "weight": 0.15, "keywords": ["maintained composure despite the time pressure", "stayed focused and worked systematically through each zone", "kept the team calm while moving quickly", "communicated urgency without causing panic", "worked through the problem in an organized manner", "vaxt təzyiqi altında özünü itirmədi", "panikaya yol vermədən təcililik hissini çatdırdım"]}
    ]',
    2.2, 0.8, 0.0,
    FALSE, FALSE,
    'Effective crisis communication requires multi-channel approach, delegation, clear message, and confirmation of coverage.',
    'Effektiv böhran kommunikasiyası çoxkanallı yanaşma, tapşırıq paylaşımı, aydın mesaj və əhatənin təsdiqlənməsini tələb edir.'
)
ON CONFLICT (id) DO NOTHING;

-- Q5: MCQ — SJT Reliability (masked — tests reliability, not communication)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    is_sjt_reliability, lie_detector_flag,
    feedback_en, feedback_az
) VALUES (
    'c0000001-0000-0000-0000-000000000005',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'You confirmed your shift 3 days ago. The morning of the event you realize you have a personal commitment conflict. What do you do?',
    'Siz 3 gün əvvəl növbənizi təsdiqlədiz. Tədbir günü səhər şəxsi bir öhdəlik münaqişəsi olduğunu başa düşürsünüz. Nə edərdiniz?',
    '[
        {"key": "A", "text_en": "Simply don''t show up — they''ll manage without you", "text_az": "Sadəcə gəlmə — onsuz da idarə edərlər"},
        {"key": "B", "text_en": "Text a friend to cover for you without informing the coordinator", "text_az": "Koordinatora xəbər vermədən onu örtmək üçün bir dostuna yazın"},
        {"key": "C", "text_en": "Immediately notify the coordinator, explain the situation, and help find a replacement", "text_az": "Dərhal koordinatoru xəbərdar edin, vəziyyəti izah edin və əvəzedici tapmağa kömək edin"},
        {"key": "D", "text_en": "Go to the event and leave early once no one is watching", "text_az": "Tədbirə get və heç kim baxmayanda tez çıx"}
    ]',
    'C',
    2.5, -0.5, 0.1,
    TRUE, FALSE,
    'Reliability means proactively communicating issues early, not disappearing. Option C demonstrates responsibility and team respect.',
    'Etibarlılıq problemləri erkən proaktiv şəkildə bildirməyi bildirir. C seçimi məsuliyyəti və komandaya hörmət nümayiş etdirir.'
)
ON CONFLICT (id) DO NOTHING;


-- ---- PLACEHOLDER QUESTIONS (15) ----
-- These have is_ai_generated=true and needs_review=true
-- Replace with real questions as you build the question bank
-- Guard: only insert if fewer than 15 placeholders exist for this competency

DO $$
BEGIN
    IF (
        SELECT COUNT(*) FROM public.questions
        WHERE competency_id = '11111111-1111-1111-1111-111111111111'
          AND is_ai_generated = TRUE
    ) < 15 THEN
        INSERT INTO public.questions (
            competency_id, difficulty, type,
            scenario_en, scenario_az,
            options, correct_answer,
            irt_a, irt_b, irt_c,
            is_ai_generated, needs_review
        )
        SELECT
            '11111111-1111-1111-1111-111111111111',
            difficulty,
            'mcq',
            'PLACEHOLDER: Communication scenario ' || n || ' (' || difficulty || ') — replace with real question.',
            'YER TUTUCU: Kommunikasiya ssenarisi ' || n || ' (' || difficulty || ') — həqiqi sual ilə əvəz edin.',
            '[
                {"key": "A", "text_en": "Option A — best practice response", "text_az": "A seçimi — ən yaxşı təcrübə cavabı"},
                {"key": "B", "text_en": "Option B — acceptable response", "text_az": "B seçimi — qəbul edilə bilən cavab"},
                {"key": "C", "text_en": "Option C — poor response", "text_az": "C seçimi — zəif cavab"},
                {"key": "D", "text_en": "Option D — incorrect response", "text_az": "D seçimi — yanlış cavab"}
            ]',
            'A',
            1.0 + (n::FLOAT * 0.05),
            -1.0 + (n::FLOAT * 0.15),
            0.10,
            TRUE,
            TRUE
        FROM (
            SELECT
                gs AS n,
                CASE
                    WHEN gs <= 5 THEN 'easy'
                    WHEN gs <= 10 THEN 'medium'
                    ELSE 'hard'
                END AS difficulty
            FROM generate_series(1, 15) AS gs
        ) series;
    END IF;
END $$;


-- =============================================================================
-- 4. TEST ORGANIZATION — SKIPPED
-- =============================================================================
-- Removed: FK constraint requires real auth.users entry for owner_id.
-- Organizations are created through the app registration flow.
-- To test org features: register a user → POST /api/organizations.
