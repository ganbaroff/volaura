-- Seed the 8 canonical AURA competencies with stable UUIDs.
-- Must run before any question-seed migrations that reference these UUIDs via FK.
-- Uses ON CONFLICT (id) DO NOTHING — safe to apply on prod where data already exists.

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
