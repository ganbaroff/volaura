-- =============================================================================
-- VOLAURA SEED DATA — BATCH 2
-- Competencies: Reliability, English Proficiency, Leadership
-- 15 questions total (5 per competency)
--
-- Research sources used for psychometric calibration:
--   • SHL Situational Judgement Test format (shl.com/shldirect) — scenario realism,
--     plausible distractor design, Universal Competency Framework behavioral anchors
--   • Hogan Personality Inventory Reliability/Prudence scale — dependability, rule
--     compliance under social desirability pressure, conscientiousness facets
--   • IELTS Band Descriptors B1–C1 (British Council) — lexical resource, grammatical
--     range/accuracy, coherence criteria for professional writing/speaking tasks
--   • Hersey-Blanchard Situational Leadership model — tell/sell/participate/delegate
--     style selection based on follower maturity, event-crisis decision patterns
--
-- IRT parameter notes:
--   irt_a = discrimination (how well item separates high vs low trait scorers)
--   irt_b = difficulty (theta level where P(correct) = 0.5 for c=0)
--   irt_c = guessing (pseudo-chance lower asymptote)
--
-- UUID prefix key: r = Reliability, e = English, l = Leadership
-- =============================================================================


-- =============================================================================
-- COMPETENCY: Reliability (22222222-2222-2222-2222-222222222222, weight: 15%)
-- "Consistently showing up on time, completing commitments, being dependable under pressure"
-- 5 questions: 2 MCQ (easy, medium) + 2 open-ended (medium, hard) + 1 SJT
-- =============================================================================

-- R1: MCQ — Commitment Follow-Through (Easy)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'r0000002-0000-0000-0000-000000000001',
    '22222222-2222-2222-2222-222222222222',
    'easy', 'mcq',
    'You volunteered for the registration desk at a 200-person corporate conference starting at 09:00. The evening before, a close friend invites you to a late-night gathering. What do you do?',
    'Siz 09:00-da başlayan 200 nəfərlik korporativ konfransda qeydiyyat masasına könüllü olmusunuz. Bir gün əvvəl axşam yaxın dostunuz sizi gec gecə məclisə dəvət edir. Nə edərdiniz?',
    '[
        {"key": "A", "text_en": "Attend the gathering and plan to leave early enough to rest", "text_az": "Məclisə get və kifayət qədər erkən ayrılmağı planlaşdır"},
        {"key": "B", "text_en": "Skip the gathering — your commitment to the event comes first", "text_az": "Məclisi burax — tədbirə olan öhdəliyin birinci yerdə durur"},
        {"key": "C", "text_en": "Go to the gathering and ask a friend to cover your shift if you oversleep", "text_az": "Məclisə get və gec oyanarsan deyə bir dostundan növbəni örtməsini xahiş et"},
        {"key": "D", "text_en": "Tell the coordinator you might be late and let them arrange backup", "text_az": "Koordinatora gecikə biləcəyini söylə və ehtiyat planlaşdırmasını onlara burax"}
    ]',
    'B',
    1.4, -0.8, 0.12,
    'Reliability means protecting commitments proactively — including managing personal energy the night before. Option B demonstrates that dependable volunteers treat confirmed shifts as non-negotiable.',
    'Etibarlılıq öhdəlikləri əvvəlcədən qorumaq deməkdir — o cümlədən bir gün əvvəl şəxsi enerjini idarə etmək. B seçimi göstərir ki, etibarlı könüllülər təsdiqlənmiş növbələrə dəyişdirilməz kimi baxır.',
    'Use a simple rule: if you have a 09:00 commitment, nothing goes past 22:00 the night before. Treat volunteer shifts the same as paid work obligations.',
    'Sadə bir qayda tətbiq edin: 09:00 öhdəliyiniz varsa, bir gün əvvəl saat 22:00-dan sonra heç bir planınız olmamalıdır. Könüllü növbələrə ödənişli iş öhdəlikləri kimi yanaşın.'
)
ON CONFLICT (id) DO NOTHING;

-- R2: MCQ — Reliability Under Task Ambiguity (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'r0000002-0000-0000-0000-000000000002',
    '22222222-2222-2222-2222-222222222222',
    'medium', 'mcq',
    'Halfway through an event, your coordinator leaves unexpectedly and does not assign tasks for the remaining 2 hours. Other volunteers begin chatting and waiting. What is the MOST reliable approach?',
    'Tədbirин ortasında koordinatorunuz gözlənilmədən gedir və qalan 2 saat üçün tapşırıqlar vermir. Digər könüllülər söhbət edib gözləməyə başlayır. Ən ETİBARLI yanaşma hansıdır?',
    '[
        {"key": "A", "text_en": "Wait for a new coordinator to arrive before doing anything", "text_az": "Yeni koordinator gələnə qədər gözlə"},
        {"key": "B", "text_en": "Identify what still needs to be done and take ownership of specific tasks without waiting", "text_az": "Hələ nəyin edilməli olduğunu müəyyən edin və gözləmədən konkret tapşırıqların məsuliyyətini öz üzərinizə götürün"},
        {"key": "C", "text_en": "Follow what other volunteers are doing — coordination decisions are above your role", "text_az": "Digər könüllülərin nə etdiyini izlə — koordinasiya qərarları sənin rolunun üstündədir"},
        {"key": "D", "text_en": "Contact the event organizer on social media to report the gap in coordination", "text_az": "Koordinasiyadakı boşluğu bildirmək üçün sosial mediadan tədbir təşkilatçısı ilə əlaqə saxla"}
    ]',
    'B',
    1.7, 0.2, 0.15,
    'Reliable volunteers do not need external direction to act. Identifying remaining tasks and self-assigning demonstrates ownership and dependability even without supervision — a key Hogan Prudence indicator.',
    'Etibarlı könüllülər fəaliyyət göstərmək üçün xarici rəhbərliyə ehtiyac duymur. Qalan tapşırıqları müəyyən etmək və özünə mənimsəmək nəzarət olmadan belə sahiblik və etibarlılığı nümayiş etdirir.',
    'Practice "task ownership" thinking: at any event, always know the 3 things that would fall apart if no one did them. Those are your defaults when coordination breaks down.',
    '"Tapşırıq sahibliyi" düşüncəsini məşq edin: istənilən tədbirde, koordinasiya çatışmasa da 3 şeyi həmişə bilin. Bunlar koordinasiya pozulduqda defolt seçimlərinizdir.'
)
ON CONFLICT (id) DO NOTHING;

-- R3: Open-ended — Reliability Under Conflicting Deadlines (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'r0000002-0000-0000-0000-000000000003',
    '22222222-2222-2222-2222-222222222222',
    'medium', 'open_ended',
    'You are responsible for preparing name badges for 80 attendees before a conference opens at 10:00. At 09:15 the badge printer jams and IT support says it will take at least 45 minutes to fix. You have 45 minutes until doors open. Describe exactly what you would do.',
    'Siz konfrans saat 10:00-da açılmazdan əvvəl 80 iştirakçı üçün ad nişanı hazırlamaqdan məsulsunuz. Saat 09:15-də nişan printeri sıradan çıxır, İT dəstək isə ən azı 45 dəqiqə çəkəcəyini bildirir. Qapıların açılmasına 45 dəqiqəniz var. Dəqiq nə edərdiniz?',
    '[
        {"name": "escalate_immediately", "weight": 0.20, "keywords": ["told my supervisor immediately", "notified the event coordinator right away", "escalated to the organizer within minutes", "informed my team lead of the situation", "did not wait — reported to management at once", "dərhal rəhbərimi xəbərdar etdim", "koordinatoru dərhal bildirdim"]},
        {"name": "alternative_solution", "weight": 0.25, "keywords": ["printed from a different device", "used a backup laptop to print", "hand-wrote the most critical badges first", "found another printer in the building", "used a mobile print service", "formatted a plain text list as temporary badges", "fərqli cihazdan çap etdim", "ən vacib nişanları əl ilə yazdım", "binada başqa printer tapdım"]},
        {"name": "prioritize_key_attendees", "weight": 0.20, "keywords": ["VIPs and speakers first", "prioritized speakers and panelists over general attendees", "focused on keynote speakers badges", "sorted by importance", "handled VIP list first while others worked on general attendees", "natiqləri prioritet verdim", "VIP qonaqlardan başladım"]},
        {"name": "communicate_with_attendees", "weight": 0.20, "keywords": ["placed a sign at the registration desk explaining the delay", "told arriving attendees there would be a brief wait", "set up a verbal check-in process while badges were being prepared", "announced the workaround to early arrivals", "kept attendees informed and managed expectations", "gözləyən iştirakçılara vəziyyəti izah etdim", "giriş masasında izahat bildirişi qoydum"]},
        {"name": "stay_composed", "weight": 0.15, "keywords": ["remained calm and focused on solutions", "did not panic", "kept my team calm and focused", "worked methodically through the problem", "stayed professional despite the time pressure", "sakit qaldım", "əziyyət altında sakinliyimi qorudum"]}
    ]',
    1.9, 0.4, 0.0,
    'High reliability under failure means: escalate immediately, find workarounds fast, prioritize by impact, communicate with affected parties, and stay composed. All five dimensions must appear in a strong answer.',
    'Yüksək etibarlılıq sıradan çıxma zamanı: dərhal eskalasiya, sürətli alternativ tapma, təsirə görə prioritet, əlaqədar tərəflərlə ünsiyyət və sakin qalma deməkdir.',
    'Build a "failure playbook" for common event tools: what do you do if the printer fails? If WiFi drops? If a speaker cancels? Having mental templates means you act, not freeze.',
    'Ümumi tədbir alətləri üçün "nasazlıq ssenari kitabı" qurun: printer sıradan çıxsa nə edərsiniz? WiFi kəsilsə? Natiq ləğv etsə? Zehni şablonlara sahib olmaq donmadan hərəkət etməyə imkan verir.'
)
ON CONFLICT (id) DO NOTHING;

-- R4: Open-ended — Reliability vs Social Pressure (Hard)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'r0000002-0000-0000-0000-000000000004',
    '22222222-2222-2222-2222-222222222222',
    'hard', 'open_ended',
    'Three of your fellow volunteers — including one you consider a close friend — decide to take an unofficial break 90 minutes into a 4-hour shift, saying "nothing is happening anyway." The event floor still has unattended areas and attendees with questions. They invite you to join them. What do you do, and how do you handle the social pressure without damaging team relationships?',
    'Üç həmkar könüllünüz — biri yaxın dostunuz — 4 saatlıq növbənin 90 dəqiqəsindən sonra "elə bir şey olmur ki" deyərək qeyri-rəsmi fasilə etməyə qərar verirlər. Tədbirдə hələ nəzarətsiz ərazilər və sualı olan iştirakçılar var. Onlar sizi özləri ilə dəvət edirlər. Nə edərdiniz və komanda münasibətlərini korlamadan sosial təzyiqlə necə başa çıxardınız?',
    '[
        {"name": "maintain_position", "weight": 0.25, "keywords": ["declined politely but firmly", "stayed at my post", "chose to remain on the floor", "told them I would stay and cover", "did not join the break", "nəzakətlə ancaq qətiyyətlə rədd etdim", "postumda qaldım", "onlara qatılmadım"]},
        {"name": "explain_rationale", "weight": 0.20, "keywords": ["explained there were still unattended areas", "pointed out attendees needed assistance", "mentioned it was not fair to leave the floor empty", "noted that our role was still needed", "explained my reasoning without lecturing them", "hələ nəzarətsiz ərazilərin olduğunu izah etdim", "iştirakçıların yardıma ehtiyacı olduğunu göstərdim"]},
        {"name": "protect_relationship", "weight": 0.20, "keywords": ["did not lecture or judge them", "kept my tone light and respectful", "avoided making them feel guilty", "offered to cover so they could take turns properly", "suggested a structured rotation break later", "mühazirə oxumadım", "tonumu yüngül və hörmətli saxladım", "onları günahkar hiss etdirməkdən çəkindim"]},
        {"name": "report_or_suggest_structure", "weight": 0.20, "keywords": ["suggested to the coordinator that we establish a formal break rotation", "mentioned the situation to my supervisor", "proposed a 10-minute staggered break system", "suggested that one person cover while others rest briefly", "recommended a proper break schedule to the team lead", "koordinatora rəsmi fasilə növbəsi qurmağı təklif etdim", "nəzarətçiyə vəziyyəti bildirdim"]},
        {"name": "self_awareness", "weight": 0.15, "keywords": ["acknowledged the social pressure was real", "understood why they wanted a break", "recognized it was not easy to say no to friends", "noted the discomfort but stayed aligned with my values", "was honest about the difficulty of the situation", "sosial təzyiqin real olduğunu qəbul etdim", "dostlara xeyr demənin asan olmadığını anladım"]}
    ]',
    2.2, 1.0, 0.0,
    'This question tests the hardest dimension of reliability: maintaining commitment under peer pressure. Strong answers show: holding position, explaining without preaching, protecting the relationship, and recommending structural solutions.',
    'Bu sual etibarlılığın ən çətin boyutunu yoxlayır: həmyaşıd təzyiqi altında öhdəliyə sadiq qalmaq. Güclü cavablar: mövqeni qorumaq, oxutmadan izah etmək, münasibəti qorumaq və struktur həll tövsiyə etmək.',
    'Read about "principled disagreement" — how to say no to people you like without creating conflict. The best volunteers are respected precisely because their yes means something.',
    '"Prinsipial razılaşmazlıq" haqqında oxuyun — sevdiyiniz insanlara münaqişə yaratmadan xeyr demə. Ən yaxşı könüllülər tam olaraq buna görə hörmət görür: çünki onların bəli bir şey ifadə edir.'
)
ON CONFLICT (id) DO NOTHING;

-- R5: SJT/MCQ — Reliability Disguised as Prioritization (SJT — tests reliability, appears to test time management)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    is_sjt_reliability, lie_detector_flag,
    feedback_en, feedback_az
) VALUES (
    'r0000002-0000-0000-0000-000000000005',
    '22222222-2222-2222-2222-222222222222',
    'medium', 'mcq',
    'During setup for a large gala, you are assigned to arrange chairs in Hall A. Halfway through, a senior organizer passes and casually asks if you could "help out in the kitchen for a bit." Hall A is not finished. What do you do?',
    'Böyük bir qalanın hazırlığı zamanı A Zalında stulları düzəltmək üçün təyin edilmisiniz. Yarısında baş təşkilatçı yan keçib "bir az mətbəxə kömək edə bilərsən?" deyə sərbəst şəkildə soruşur. A Zalı hələ hazır deyil. Nə edərsiniz?',
    '[
        {"key": "A", "text_en": "Go to the kitchen immediately — a senior organizer asked", "text_az": "Dərhal mətbəxə get — baş təşkilatçı istədi"},
        {"key": "B", "text_en": "Politely tell them you were assigned to Hall A and ask if you should formally reassign after finishing", "text_az": "Nəzakətlə A Zalına təyin olunduğunuzu bildirin və bitirdikdən sonra rəsmi yenidən təyin edilib-edilməyəcəyini soruşun"},
        {"key": "C", "text_en": "Abandon Hall A entirely and help in the kitchen", "text_az": "A Zalını tamamilə tərk et və mətbəxdə kömək et"},
        {"key": "D", "text_en": "Ignore the request — it was only casual, not a formal instruction", "text_az": "Xahişi nəzərə alma — bu rəsmi göstəriş deyil, sadəcə sərbəst söhbətdi"}
    ]',
    'B',
    1.8, 0.3, 0.12,
    TRUE, FALSE,
    'This tests reliability under authority pressure — a social desirability trap. Abandoning an assigned task without formal reassignment violates basic reliability, even if directed by a senior person. Option B shows you honor commitments while remaining responsive to authority.',
    'Bu, avtoritet təzyiqi altında etibarlılığı yoxlayır — sosial bəyənmə tələsidir. Rəsmi yenidən təyin olmadan tapşırılmış işi tərk etmək əsas etibarlılığı pozur. B seçimi həm öhdəliyə hörmət etdiyinizi, həm də səlahiyyətə cavab verdiyinizi göstərir.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- COMPETENCY: English Proficiency (33333333-3333-3333-3333-333333333333, weight: 15%)
-- "Communicate effectively in English in professional event environments (B1–C1 range)"
-- 5 questions: 2 MCQ (B1, B2 grammar/vocab in context) + 2 open-ended + 1 SJT
-- =============================================================================

-- E1: MCQ — B1 Level — Professional Vocabulary in Context (Easy)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000003-0000-0000-0000-000000000001',
    '33333333-3333-3333-3333-333333333333',
    'easy', 'mcq',
    'A foreign delegate approaches you and says: "I''m afraid I''ve misplaced my conference badge." Which response uses the MOST professional English?',
    'Xarici bir nümayəndə sizə yaxınlaşıb deyir: "Qorxuram ki, konfrans nişanımı itirmişəm." Hansı cavab ən PEŞƏKAR ingilis dilindən istifadə edir?',
    '[
        {"key": "A", "text_en": "Oh no, that''s bad. You need to go find someone.", "text_az": "Vay, bu pis. Birini tapmaq lazımdır."},
        {"key": "B", "text_en": "Not a problem — please come with me to the registration desk and we will issue a replacement right away.", "text_az": "Problem deyil — zəhmət olmasa mənimlə qeydiyyat masasına gəlin, dərhal əvəzedicisini veririk."},
        {"key": "C", "text_en": "Sorry, I don''t know. Maybe ask somebody else.", "text_az": "Üzr istəyirəm, bilmirəm. Bəlkə başqasına soruşun."},
        {"key": "D", "text_en": "The badge is yours responsibility. You must find it.", "text_az": "Nişan sizin məsuliyyətinizdir. Tapmalısınız."}
    ]',
    'B',
    1.4, -0.9, 0.12,
    'Option B uses key B2+ professional collocations: "not a problem", "please come with me", "right away". It signals service orientation and grammatical control. Option D contains a grammar error ("yours responsibility" → "your responsibility").',
    'B seçimi əsas B2+ peşəkar kollokasiyalardan istifadə edir: "not a problem", "please come with me", "right away". O, xidmət yönümlülüyü və qrammatik nəzarəti göstərir.',
    'Learn 20 key hospitality collocations for events: "right away", "my pleasure", "please allow me", "let me check for you", "I''ll look into it immediately". These phrases mark you as B2+ instantly.',
    'Tədbirlər üçün 20 əsas mehmannəvazlıq kollokasiyasını öyrənin: "right away", "my pleasure", "please allow me", "let me check for you". Bu ifadələr sizi dərhal B2+ kimi işarələyir.'
)
ON CONFLICT (id) DO NOTHING;

-- E2: MCQ — B2 Level — Grammar Accuracy in Professional Context (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000003-0000-0000-0000-000000000002',
    '33333333-3333-3333-3333-333333333333',
    'medium', 'mcq',
    'You need to send a quick message to an international speaker who has not yet confirmed their arrival time. Which message is grammatically correct AND appropriately professional?',
    'Hələ gəliş vaxtını təsdiqləməmiş beynəlxalq natiqə qısa mesaj göndərməlisiniz. Hansı mesaj həm qrammatik cəhətdən düzgün, HƏM DƏ uyğun peşəkardır?',
    '[
        {"key": "A", "text_en": "Dear Dr. Aliyeva, could you please confirm your expected arrival time at your earliest convenience? We want to ensure everything is prepared for your session.", "text_az": "Hörmətli Dr. Əliyeva, imkan tapdıqda gözlənilən gəliş vaxtınızı təsdiqləyə bilərsinizmi? Sessiyaya hazırlığı təmin etmək istəyirik."},
        {"key": "B", "text_en": "Hi, when are you coming? We need to know soon.", "text_az": "Salam, nə vaxt gəlirsiniz? Tezliklə bilməliyik."},
        {"key": "C", "text_en": "Dear Dr. Aliyeva, we are writing to you because we want to know the time you will arrive because we are preparing.", "text_az": "Hörmətli Dr. Əliyeva, hazırlaşdığımız üçün gəlişinizin nə vaxt olacağını bilmək üçün sizə yazırıq."},
        {"key": "D", "text_en": "Dear Dr. Aliyeva, can you confirm arrival time? Its very important for us.", "text_az": "Hörmətli Dr. Əliyeva, gəliş vaxtını təsdiqləyə bilərsinizmi? Bu, bizim üçün çox önəmlidir."}
    ]',
    'A',
    1.8, 0.3, 0.15,
    'Option A uses correct C1 grammar structures: conditional politeness ("could you please"), indirect request framing, and the C1-level phrase "at your earliest convenience". Option D contains a spelling error ("Its" → "It''s"). Option C is grammatically clumsy with repetitive "because" clauses.',
    'A seçimi düzgün C1 qrammatik strukturlarından istifadə edir: şərti nəzakət ("could you please"), dolayı xahiş çərçivəsi. D seçimi orfoqrafiya səhvi ehtiva edir. C seçimi təkrar "because" cümlələri ilə qrammatikal cəhətdən zəifdir.',
    'Practice the B2→C1 grammar upgrade: replace "I want to know" with "could you kindly let me know", replace "because" chains with subordinate clauses using "in order to" or "so that".',
    'B2→C1 qrammatik yüksəltməni məşq edin: "I want to know"u "could you kindly let me know" ilə əvəzləyin, "because" zəncirini "in order to" ilə qurulan tabe cümlələrlə əvəzləyin.'
)
ON CONFLICT (id) DO NOTHING;

-- E3: Open-ended — Professional Email Writing (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000003-0000-0000-0000-000000000003',
    '33333333-3333-3333-3333-333333333333',
    'medium', 'open_ended',
    'Write a short professional email (5–7 sentences) to an international partner organization confirming that the venue for next week''s workshop has changed from Room 204 to the Main Hall on Floor 3. The email should be clear, polite, and include all necessary practical details.',
    'Növbəti həftəki seminar üçün məkanın 204 otaqdan 3-cü mərtəbədəki Baş Zalına dəyişdirildiyini beynəlxalq tərəfdaş təşkilata bildirən qısa peşəkar e-poçt (5-7 cümlə) yazın. E-poçt aydın, nəzakətli olmalı və bütün lazımi praktiki məlumatları ehtiva etməlidir.',
    '[
        {"name": "formal_greeting", "weight": 0.15, "keywords": ["Dear", "I hope this email finds you well", "I am writing to inform you", "I am writing to confirm", "I hope this message reaches you well", "Hörmətli", "Bu e-poçtu sizə bildirmək üçün yazıram", "Sizi məlumatlandırmaq üçün yazıram"]},
        {"name": "clear_change_statement", "weight": 0.25, "keywords": ["venue has changed", "room has been changed", "we would like to inform you that the location", "the session will now take place", "we are writing to confirm the venue change", "məkan dəyişdirildi", "otaq dəyişdirildi", "sessiyanın yeri dəyişdi"]},
        {"name": "specific_details", "weight": 0.25, "keywords": ["Main Hall", "Floor 3", "third floor", "Room 204", "instead of", "previous room", "Baş Zal", "3-cü mərtəbə", "əvəzinə", "əvvəlki otaq"]},
        {"name": "apology_or_acknowledgment", "weight": 0.15, "keywords": ["apologize for any inconvenience", "sorry for any confusion", "we apologize for the short notice", "we understand this is a last-minute change", "thank you for your understanding", "narahatlıq üçün üzr istəyirik", "qısamüddətli bildiriş üçün üzr istəyirik"]},
        {"name": "professional_close", "weight": 0.20, "keywords": ["please do not hesitate to contact us", "should you have any questions", "we look forward to seeing you", "kind regards", "best regards", "yours sincerely", "hər hansı sualınız olarsa", "ürəkdən hörmətlə", "hörmətlə"]}
    ]',
    2.0, 0.5, 0.0,
    'A strong B2+ email has 5 clear elements: formal greeting, explicit statement of the change, full practical details, acknowledgment of inconvenience, and a professional close with an offer to assist.',
    'Güclü B2+ e-poçtun 5 açıq elementi var: rəsmi salamlama, dəyişikliyin açıq ifadəsi, tam praktiki detallar, narahatlığın qəbulu və yardım təklifi ilə peşəkar bağlama.',
    'Study the IELTS GT Task 1 letter format — it teaches exactly this skill. Focus on: opening purpose statement, numbered details, polite acknowledgment, formal close. 15 minutes of practice daily for 2 weeks will measurably improve your professional English.',
    'IELTS GT Tapşırıq 1 məktub formatını öyrənin — o məhz bu bacarığı öyrədir. Fokuslanın: açılış məqsəd bəyanatı, nömrələnmiş detallar, nəzakətli qəbul, rəsmi bağlama. Gündəlik 15 dəqiqəlik məşq 2 həftə ərzində peşəkar ingilis dilinizi ölçülə bilən şəkildə inkişaf etdirəcək.'
)
ON CONFLICT (id) DO NOTHING;

-- E4: Open-ended — Spoken English Under Pressure (Hard)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000003-0000-0000-0000-000000000004',
    '33333333-3333-3333-3333-333333333333',
    'hard', 'open_ended',
    'An international journalist approaches you at a TEDx event and asks: "Can you briefly explain what this event is about and what makes it unique compared to other conferences in the region?" Write what you would say — your response should be 3–4 sentences in fluent, natural English at B2–C1 level.',
    'TEDx tədbirindən jurnalist sizə yaxınlaşıb soruşur: "Bu tədbirин nə haqqında olduğunu qısaca izah edə bilərsinizmi və onu regiondakı digər konfranslardan nə fərqləndirir?" Nə deyəcəyinizi yazın — cavabınız B2–C1 səviyyəsində axıcı, təbii ingilis dilində 3–4 cümlə olmalıdır.',
    '[
        {"name": "fluent_opening", "weight": 0.20, "keywords": ["This event is", "Today we are hosting", "This is", "We are here to", "This conference brings together", "What you''re seeing today is", "Bu tədbir", "Bu konfrans bir araya gətirir"]},
        {"name": "b2_vocabulary", "weight": 0.25, "keywords": ["innovative", "thought-provoking", "brings together", "platform for", "diverse range of", "cutting-edge", "speakers from across", "locally driven", "community-focused", "inspired by", "yenilikçi", "düşündürücü", "platforma"]},
        {"name": "comparative_structure", "weight": 0.25, "keywords": ["unlike other conferences", "what sets it apart", "the key difference is", "in contrast to", "what makes it unique is", "rather than", "compared to other events", "digər konfranslardan fərqli olaraq", "onu fərqləndirən şey"]},
        {"name": "coherent_structure", "weight": 0.15, "keywords": ["firstly", "additionally", "moreover", "what''s more", "and importantly", "on top of that", "also", "linked clauses", "subordinate clauses", "əlavə olaraq", "üstəlik", "bundan əlavə"]},
        {"name": "confident_close", "weight": 0.15, "keywords": ["I hope you enjoy the event", "feel free to reach out", "do let us know if you have any questions", "we''d love to have your coverage", "thank you for covering this event", "tədbirдən zövq alacağınızı ümid edirəm", "hər hansı sualınız olarsa"]}
    ]',
    2.1, 0.9, 0.0,
    'This tests spontaneous spoken-English production at B2–C1. Key indicators: uses comparative structures, B2-level vocabulary (not just "good" and "nice"), coherent multi-clause sentences, and a confident professional close.',
    'Bu, B2–C1 səviyyəsində spontan danışıq ingilis dilini yoxlayır. Əsas göstəricilər: müqayisəli quruluş, B2 lüğəti, ardıcıl çox cümləli ifadələr və güvənli peşəkar bağlama.',
    'Practice the "elevator pitch" format in English: 30 seconds, 3 sentences. Use this template: [What it is] + [Who it''s for] + [What makes it different]. Record yourself and listen back — your ear catches errors your eye misses.',
    '"Lift təqdimatı" formatını ingilis dilində məşq edin: 30 saniyə, 3 cümlə. Bu şablondan istifadə edin: [Nədir] + [Kim üçündür] + [Nə fərqli edir]. Özünüzü qeyd edin və dinləyin — qulağınız gözünüzün qaçırdığı səhvləri tutur.'
)
ON CONFLICT (id) DO NOTHING;

-- E5: MCQ SJT — Professional English Register (SJT — tests proficiency, appears to test communication etiquette)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    is_sjt_reliability, lie_detector_flag,
    feedback_en, feedback_az
) VALUES (
    'e0000003-0000-0000-0000-000000000005',
    '33333333-3333-3333-3333-333333333333',
    'medium', 'mcq',
    'An international VIP guest says to you: "I''m a bit confused about the schedule — the program says the panel starts at 14:00 but my invitation says 14:30." Which response demonstrates the MOST professional English AND the most effective handling?',
    'Beynəlxalq VIP qonaq sizə deyir: "Cədvəl barədə bir az çaşqınam — proqramda panel saat 14:00-da başlayır, ancaq dəvətimdə 14:30 yazır." Hansı cavab həm ən PEŞƏKAR ingilis dilini, HƏM DƏ ən effektiv idarəetməni nümayiş etdirir?',
    '[
        {"key": "A", "text_en": "Yeah, the times are mixed up sometimes. Just come at 14:00 to be safe.", "text_az": "Hə, vaxtlar bəzən qarışır. Ehtiyatla 14:00-da gəlin."},
        {"key": "B", "text_en": "I sincerely apologize for the confusion. Allow me to verify the correct time with our coordinator immediately and I will confirm for you within two minutes.", "text_az": "Çaşqınlıq üçün səmimiyyətlə üzr istəyirəm. İcazə verin koordinatorumuzla dərhal düzgün vaxtı yoxlayım və iki dəqiqə ərzində sizə təsdiqləyim."},
        {"key": "C", "text_en": "That is a problem with our printing team. I will report it.", "text_az": "Bu, çap komandamızın problemidir. Bildirim."},
        {"key": "D", "text_en": "Both times may be right — the panel has a pre-session and main session, so please check which one you''re invited to.", "text_az": "Hər iki vaxt düzgün ola bilər — panelin ön sessiyası və əsas sessiyası var, zəhmət olmasa hansına dəvət olunduğunuzu yoxlayın."}
    ]',
    'B',
    2.0, 0.4, 0.12,
    TRUE, FALSE,
    'Option B scores highest on all IELTS-aligned speaking dimensions: formal register ("I sincerely apologize", "allow me"), commitment with a specific timeframe ("within two minutes"), and correct grammar throughout. Option A uses informal register ("Yeah") inappropriate for VIP interaction. Option C deflects blame rather than solving the problem.',
    'B seçimi IELTS-uyğun bütün danışıq ölçülərini keçir: rəsmi registr ("I sincerely apologize", "allow me"), konkret vaxt çərçivəsi ilə öhdəlik ("within two minutes") və bütün boyu düzgün qrammatika.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- COMPETENCY: Leadership (44444444-4444-4444-4444-444444444444, weight: 15%)
-- "Motivate and guide others, take initiative, make decisions under uncertainty, manage small teams"
-- 5 questions: 2 MCQ (easy, medium) + 2 open-ended (medium, hard) + 1 SJT
-- =============================================================================

-- L1: MCQ — Initiative in Leadership Vacuum (Easy)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'l0000004-0000-0000-0000-000000000001',
    '44444444-4444-4444-4444-444444444444',
    'easy', 'mcq',
    'You are one of six volunteers at an outdoor event. The team coordinator has not arrived 10 minutes before gates open. Attendees are already arriving and no one knows what to do. What is the BEST action?',
    'Siz açıq havada bir tədbirde altı könüllüdən birisiniz. Qapılar açılmazdan 10 dəqiqə əvvəl komanda koordinatoru gəlməyib. İştirakçılar artıq gəlir və heç kim nə edəcəyini bilmir. Ən YAXŞI hərəkət hansıdır?',
    '[
        {"key": "A", "text_en": "Wait — acting without authority could cause problems", "text_az": "Gözlə — icazə olmadan hərəkət etmək problemlərə yol aça bilər"},
        {"key": "B", "text_en": "Briefly gather the team, assign each person a role based on what you know about the plan, and start the setup", "text_az": "Qısaca komandanı topla, plana dair bildiklərinə əsasən hər kəsə rol təyin et və qurulumu başlat"},
        {"key": "C", "text_en": "Call the event organizer and wait for instructions before doing anything", "text_az": "Tədbirın təşkilatçısını zəng et və nəsə etməzdən əvvəl göstərişlər gözlə"},
        {"key": "D", "text_en": "Do your own assigned task only and let others figure out theirs", "text_az": "Yalnız öz tapşırılmış işini et, başqaları öz işlərini özləri tapsın"}
    ]',
    'B',
    1.5, -0.7, 0.12,
    'Situational leadership (Hersey-Blanchard) calls for a directive "Telling" style when the team lacks direction and time is critical. Option B demonstrates initiative, team awareness, and the ability to create structure from ambiguity — core leadership indicators.',
    'Vəziyyətli liderlik (Hersey-Blanchard), komandanın istiqamətsiz olduğu və vaxtın kritik olduğu hallarda direktiv "Söyləmə" tərzi tələb edir. B seçimi təşəbbüs, komanda şüuru və qeyri-müəyyənlikdən struktur yaratma qabiliyyətini nümayiş etdirir.',
    'Study "stepping up" leadership moments: the key skill is not authority — it''s the willingness to create order when none exists. Practice by volunteering to lead briefings even in low-stakes situations.',
    '"Addım atma" liderlik anlarını öyrənin: əsas bacarıq səlahiyyət deyil — heç bir nizam olmadıqda nizam yaratmaq istəyidir. Aşağı riskli vəziyyətlərdə belə brifinqlərə rəhbərlik etməyə könüllü olaraq məşq edin.'
)
ON CONFLICT (id) DO NOTHING;

-- L2: MCQ — Leadership Style Adaptation Under Team Conflict (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'l0000004-0000-0000-0000-000000000002',
    '44444444-4444-4444-4444-444444444444',
    'medium', 'mcq',
    'You are leading a team of 4 volunteers during a fast-paced tech conference. Two experienced volunteers disagree on how to manage the speaker waiting area — one wants a strict sign-in system, the other prefers a flexible approach. The situation is slowing down the whole team. What do you do?',
    'Sürətli keçən texnoloji konfransda 4 könüllüdən ibarət komandaya rəhbərlik edirsiniz. İki təcrübəli könüllü natiq gözləmə otağını necə idarə edəcəkləri barədə razılaşmır — biri ciddi qeydiyyat sistemi istəyir, digəri çevik yanaşmanı üstün tutur. Vəziyyət bütün komandanı yavaşladır. Nə edərdiniz?',
    '[
        {"key": "A", "text_en": "Let them debate — they are both experienced and will reach a conclusion", "text_az": "Onları mübahisə etsinlər — hər ikisi təcrübəlidir və nəticəyə çatacaqlar"},
        {"key": "B", "text_en": "Decide immediately yourself and assign one of them to implement it to end the delay", "text_az": "Dərhal özün qərar ver və gecikmə bitirmək üçün onlardan birini tətbiq etmək üçün göndər"},
        {"key": "C", "text_en": "Acknowledge both views quickly, make a final call based on the current volume of speakers, and communicate the rationale to the team", "text_az": "Hər iki fikri tez qəbul et, cari natiq sayına əsasən son qərar ver və rasionalu komandaya izah et"},
        {"key": "D", "text_en": "Escalate to the senior coordinator — team disagreements should not be handled by a peer leader", "text_az": "Baş koordinatora yüksəlt — komanda anlaşmazlıqlarını həmyaşıd liderin idarə etməməsi lazımdır"}
    ]',
    'C',
    1.8, 0.3, 0.15,
    'Option C demonstrates the "Selling" leadership style (Hersey-Blanchard): the leader makes the decision but explains the reasoning, respecting both contributors and building buy-in. Option B is too autocratic for experienced team members and risks resentment. Option A surrenders the leadership role.',
    'C seçimi "Satma" liderlik tərzi nümayiş etdirir (Hersey-Blanchard): lider qərar verir, lakin hər iki iştirakçıya hörmət göstərərək rasionalı izah edir. B seçimi təcrübəli üzvlər üçün çox avtoritar olub narazılıq riskini daşıyır.',
    'Practice the "ACE" micro-decision framework: Acknowledge the competing views (5 seconds), Choose based on current facts (15 seconds), Explain your logic in one sentence. Under time pressure, this is faster and fairer than debate.',
    '"ACE" mikro-qərar çərçivəsini məşq edin: Rəqabət edən fikirləri qəbul edin (5 saniyə), Cari faktlara əsasən seçin (15 saniyə), Məntiqi bir cümlə ilə izah edin. Vaxt təzyiqi altında bu müzakirədən daha sürətli və ədalətlidir.'
)
ON CONFLICT (id) DO NOTHING;

-- L3: Open-ended — Leading a Struggling Team Member (Medium)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'l0000004-0000-0000-0000-000000000003',
    '44444444-4444-4444-4444-444444444444',
    'medium', 'open_ended',
    'You are team lead for the day at a cultural festival with 8 volunteers. One volunteer — a first-timer — is visibly overwhelmed: they have made two errors at the ticketing desk and seem close to tears. The event is in full swing and you cannot leave your overall coordination role for long. What do you do?',
    'Siz 8 könüllü ilə mədəni festivalda günün komanda rəhbərisiniz. Bir könüllü — ilk dəfə iştirak edən — bilet masasında iki səhv etmiş, göz yaşının tam astanasındadır. Tədbir tam gücündə davam edir və ümumi koordinasiya rolunuzu uzun müddət tərk edə bilmirsiniz. Nə edərsiniz?',
    '[
        {"name": "acknowledge_privately", "weight": 0.20, "keywords": ["pulled them aside briefly", "spoke to them quietly away from the crowd", "checked in with them one-on-one", "stepped out of earshot of attendees to speak", "gave them a moment away from the desk", "onları bir qırağa çəkdim", "sakit bir yerdə onlarla danışdım", "bir-bir yoxladım"]},
        {"name": "normalize_and_reassure", "weight": 0.20, "keywords": ["told them errors are normal at first", "reassured them it happens to everyone", "reminded them that making mistakes is part of learning", "told them they were doing fine overall", "normalized the difficulty of the task", "səhvlərin əvvəlcə normaldır dedim", "bu hər kəslə baş verdiyini bildirdim"]},
        {"name": "simplify_the_task", "weight": 0.20, "keywords": ["adjusted their role to something simpler", "reassigned them to a lower-pressure task", "paired them with a more experienced volunteer", "gave them one clear task to focus on", "reduced their workload temporarily", "onları daha sadə rol üçün yenidən təyin etdim", "daha az təzyiqli tapşırığa keçirdim", "daha təcrübəli bir könüllü ilə cütlədim"]},
        {"name": "follow_up", "weight": 0.20, "keywords": ["checked back within 15 minutes", "circled back after 20 minutes to see how they were doing", "sent another team member to check on them", "asked a colleague to keep an eye on them", "confirmed they were stable before moving on fully", "15 dəqiqə sonra yenidən baxdım", "20 dəqiqə sonra necə olduğunu yoxladım"]},
        {"name": "protect_their_dignity", "weight": 0.20, "keywords": ["never pointed out the errors in front of others", "did not draw attention to their mistakes publicly", "ensured the feedback was given privately", "kept the interaction positive and professional in view of others", "handled the situation discreetly", "səhvlərini başqalarının qarşısında göstərmədim", "geri bildirimi özəl verdim", "vəziyyəti diskret idarə etdim"]}
    ]',
    1.9, 0.5, 0.0,
    'Effective leadership of a struggling person requires 5 elements: private acknowledgment, normalizing error, task simplification, follow-up, and protecting dignity. Missing any one of these scores significantly lower.',
    'Çətin vəziyyətdəki insanın effektiv idarəsi 5 element tələb edir: özəl tanınma, səhvi normallaşdırma, tapşırığı sadələşdirmə, izləmə və ləyaqəti qoruma.',
    'Study "situational coaching": the best leaders adjust their support level to the person''s current state, not just their usual ability. A high-performer in panic needs "Telling" + reassurance, not "Delegating".',
    '"Situasiya koçluğu"nu öyrənin: ən yaxşı liderlər dəstək səviyyəsini insanın adi qabiliyyətinə deyil, cari vəziyyətinə uyğunlaşdırır. Panikadakı yüksək performanslı "Delegasiya" deyil, "Söyləmə" + əmin etmə tələb edir.'
)
ON CONFLICT (id) DO NOTHING;

-- L4: Open-ended — Leading Under Resource Scarcity and Uncertainty (Hard)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    expected_concepts,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'l0000004-0000-0000-0000-000000000004',
    '44444444-4444-4444-4444-444444444444',
    'hard', 'open_ended',
    'You are team lead for the volunteer crew at a major public event expecting 1,500 attendees. 2 hours before opening, 3 of your 7 volunteers call in sick. The event organizer is unreachable. You must cover all planned stations with 4 people instead of 7. Describe your decision-making process, how you prioritize stations, how you communicate the situation to your team, and what you do about the missing coordinator contact.',
    'Siz 1500 iştirakçı gözlənilən böyük ictimai tədbirдə könüllü qrupunun komanda rəhbərisiniz. Açılışdan 2 saat əvvəl 7 könüllüdən 3-ü xəstə olduğunu bildirir. Tədbir təşkilatçısı ilə əlaqə yaratmaq mümkün deyil. Bütün planlaşdırılmış stansiyaları 7 əvəzinə 4 nəfərlə örtməlisiniz. Qərar qəbul etmə prosesini, stansiyalara prioritet verməyi, vəziyyəti komandanıza necə çatdırdığınızı və çatışmayan koordinator əlaqəsi ilə bağlı nə etdiyinizi təsvir edin.',
    '[
        {"name": "triage_stations", "weight": 0.25, "keywords": ["identified which stations are critical", "ranked stations by attendee impact", "determined which posts could be merged", "assessed which areas could not be left unmanned", "decided which stations were lowest priority given attendance flow", "hansı stansiyaların kritik olduğunu müəyyən etdim", "iştirakçı axınına görə stansiyaları sıraladım", "hansı postların birləşdirilə biləcəyini qiymətləndirdim"]},
        {"name": "team_communication", "weight": 0.20, "keywords": ["gathered the 4 remaining volunteers immediately", "briefed the team honestly about the situation", "did not hide the staff shortage from the team", "communicated calmly and with a clear plan", "explained the redeployment without creating panic", "qalan 4 könüllüyü dərhal topladım", "komandaya vəziyyəti dürüstlüklə bildirdim", "çatışmazlığı komandadan gizlətmədim"]},
        {"name": "escalate_independently", "weight": 0.20, "keywords": ["tried multiple contact methods for the coordinator", "contacted a senior staff member instead", "reached out to the venue manager directly", "sent a written record of the situation via message", "attempted to reach backup contact from the event brief", "koordinator üçün bir neçə əlaqə metodu sınadım", "əvəzinə baş heyət üzvü ilə əlaqə saxladım", "birbaşa məkan meneceri ilə əlaqə saxladım"]},
        {"name": "adaptive_deployment", "weight": 0.20, "keywords": ["merged two lower-traffic stations into one", "assigned the most capable volunteer to the highest-pressure post", "created 2-hour rotation blocks to prevent fatigue", "kept mobile cover to respond to gaps as they appeared", "built flexibility into the deployment plan", "iki aşağı trafiki stansiyaları birləşdirdim", "ən qabiliyyətli könüllünü ən yüksək təzyiqli posta göndərdim", "yorğunluğun qarşısını almaq üçün rotasiya blokları yaratdım"]},
        {"name": "document_and_report", "weight": 0.15, "keywords": ["documented the absences and the changes made", "kept a written record in case of post-event review", "planned to report the coordination failure after the event", "noted the incident for the debrief", "created a record of deployment decisions for transparency", "iştirak etməyənləri və edilən dəyişiklikləri sənədləşdirdim", "hadisəni brifinq üçün qeydə aldım", "şəffaflıq üçün yerləşdirmə qərarlarının qeydini apardım"]}
    ]',
    2.3, 1.2, 0.0,
    'This question tests leadership under maximum constraint — resource scarcity, authority gap, time pressure. Strong answers show: systematic triage, honest communication, independent escalation, adaptive deployment, and documentation. All 5 must appear.',
    'Bu sual maksimum məhdudiyyət altında liderliyi yoxlayır — resurs çatışmazlığı, səlahiyyət boşluğu, vaxt təzyiqi. Güclü cavablar: sistematik triaj, dürüst ünsiyyət, müstəqil eskalasiya, adaptiv yerləşdirmə və sənədləşməni nümayiş etdirir.',
    'Build a personal "event emergency playbook": what do you do if 40% of your team drops out? If the coordinator disappears? Having pre-thought decisions means you lead confidently instead of improvising under stress.',
    'Şəxsi "tədbir fövqəladə hallar ssenari kitabı" qurun: komandanızın 40%-i getsə nə edərsiniz? Koordinator yox olsa? Öncədən düşünülmüş qərarlar olması stres altında improvizasiya etmək əvəzinə güvənlə rəhbərlik etməyə imkan verir.'
)
ON CONFLICT (id) DO NOTHING;

-- L5: MCQ SJT — Leadership Integrity vs Group Loyalty (SJT — tests leadership values, appears to test team dynamics)
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    is_sjt_reliability, lie_detector_flag,
    feedback_en, feedback_az
) VALUES (
    'l0000004-0000-0000-0000-000000000005',
    '44444444-4444-4444-4444-444444444444',
    'medium', 'mcq',
    'You are the volunteer team lead. After the event, the organizer asks for feedback on your team''s performance. You know that one volunteer performed very poorly — arrived late, missed tasks, and left early. However, that volunteer is well-liked by everyone, and the rest of the team asks you not to mention it. What do you do?',
    'Siz könüllü komanda rəhbərisiniz. Tədbirдən sonra təşkilatçı komandanızın performansı barədə rəy istəyir. Bir könüllünün çox pis performans göstərdiyini bilirsiniz — gec gəldi, tapşırıqları yerinə yetirmədi, tez çıxdı. Lakin o könüllü hamı tərəfindən sevilir, komandanın qalanı sizi bundan bəhs etməməyinizi xahiş edir. Nə edərsiniz?',
    '[
        {"key": "A", "text_en": "Stay silent — protecting team morale is more important than one performance report", "text_az": "Susur ol — komanda mənəviyyatını qorumaq bir performans hesabatından daha vacibdir"},
        {"key": "B", "text_en": "Report the performance issues to the organizer honestly but professionally, focusing on specific behaviors rather than personal judgment", "text_az": "Performans problemlərini şəxsi mühakimə əvəzinə konkret davranışlara fokuslanaraq təşkilatçıya dürüstlüklə lakin peşəkarcasına çatdır"},
        {"key": "C", "text_en": "Give a vague positive report to keep everyone happy", "text_az": "Hamını xoşbəxt etmək üçün qeyri-müəyyən müsbət hesabat ver"},
        {"key": "D", "text_en": "Report the issues only if the organizer asks specific questions about that volunteer", "text_az": "Yalnız təşkilatçı həmin könüllü barədə konkret sual etsə problemləri çatdır"}
    ]',
    'B',
    2.0, 0.5, 0.12,
    TRUE, FALSE,
    'This is a leadership integrity question masked as a team dynamics decision. Effective leaders give honest, behavior-focused feedback even under social pressure — because false positive reports harm the organization, the volunteer''s growth, and the credibility of the team lead. Option B demonstrates that leadership means accountability, not popularity management.',
    'Bu, komanda dinamikası qərarı kimi gizlədilmiş liderlik dürüstlüyü sualıdır. Effektiv liderlər sosial təzyiq altında belə dürüst, davranışa yönəlik rəy verirlər — çünki yanlış müsbət hesabatlar təşkilata, könüllünün inkişafına və komanda rəhbərinin etibarlılığına zərər verir.'
)
ON CONFLICT (id) DO NOTHING;
