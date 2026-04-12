-- =============================================================================
-- BATCH 3: 30 MCQ questions across 5 competencies
-- Fills identified gaps to ensure every competency has sufficient item bank
-- depth for adaptive IRT 3PL engine (minimum 10 per high-weight competency).
--
-- Competencies seeded:
--   communication        (11111111-...-111) — 10 questions (C11-C20)
--   event_performance    (55555555-...-555) —  5 questions (EP11-EP15)
--   tech_literacy        (66666666-...-666) —  5 questions (TL11-TL15)
--   adaptability         (77777777-...-777) —  5 questions (AD11-AD15)
--   empathy_safeguarding (88888888-...-888) —  5 questions (ES11-ES15)
--
-- Psychometric calibration sources:
--   • SHL Universal Competency Framework (UCF) — behavioral anchors per cluster
--   • Korn Ferry Competency Framework (Lominger FYI for Leaders)
--   • CCL (Center for Creative Leadership) competency behavioral indicators
--   • Situational Judgement Test norms (Weekley & Ployhart, 2006):
--     plausible distractors represent common low-proficiency behaviors
--   • OECD Future of Work competency taxonomy (2024 update)
--
-- IRT parameter design:
--   a (discrimination): 1.0–2.5 — higher = better differentiation
--   b (difficulty):     spread across easy (<-0.5), medium (-0.5 to 0.5), hard (>0.5)
--   c (guessing):       0.10–0.25 for 4-option MCQ, ~0.15 average
--
-- UUID scheme:
--   Communication:        c0000001-0000-0000-0000-000000000011 through 020
--   Event performance:    e0000005-0000-0000-0000-000000000011 through 015
--   Tech literacy:        d0000006-0000-0000-0000-000000000011 through 015
--   Adaptability:         a0000007-0000-0000-0000-000000000011 through 015
--   Empathy/safeguarding: f0000008-0000-0000-0000-000000000011 through 015
--
-- All scenarios use professional workplace contexts (team projects, deadlines,
-- meetings, presentations, client work, cross-department collaboration).
-- =============================================================================


-- =============================================================================
-- COMMUNICATION (11111111-1111-1111-1111-111111111111)
-- Weight: 0.20 | 10 questions: 3 easy, 4 medium, 3 hard
-- =============================================================================


-- C11: Delivering Constructive Feedback to a Peer (Easy)
-- Framework: SHL UCF "Relating and Networking" + Korn Ferry "Interpersonal Savvy"
-- IRT: a=1.2, b=-1.2, c=0.12
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000011',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'A colleague submits a client report with several formatting errors and two factual mistakes. The deadline is tomorrow and your manager expects a polished document. What is the BEST way to communicate this?',
    'Həmkarınız müştəri hesabatını bir neçə formatlaşdırma xətası və iki faktiki səhvlə təqdim edir. Son tarix sabahdır və meneceriniz cilalanmış sənəd gözləyir. Bunu bildirməyin ən YAXŞI yolu hansıdır?',
    '[
        {"key": "A", "text_en": "Fix the errors yourself without telling them — it is faster", "text_az": "Onlara demədən səhvləri özün düzəlt — daha sürətlidir"},
        {"key": "B", "text_en": "Send them a message highlighting the specific errors, explaining the impact on the client, and offering to review the corrected version together", "text_az": "Onlara konkret xətaları vurğulayan, müştəriyə təsirini izah edən və düzəldilmiş versiyanı birlikdə nəzərdən keçirməyi təklif edən mesaj göndərin"},
        {"key": "C", "text_en": "Escalate to your manager so they can address it directly", "text_az": "Birbaşa həll etməsi üçün menecerinizə eskalasiya edin"},
        {"key": "D", "text_en": "Wait until after the deadline to mention it — no point stressing them now", "text_az": "Qeyd etmək üçün son tarixdən sonranı gözləyin — indi onları stresə salmağın mənası yoxdur"}
    ]',
    'B',
    1.2, -1.2, 0.12,
    'Constructive feedback is specific, timely, and solution-oriented. Option A robs the colleague of a learning opportunity. Option C bypasses them entirely and damages trust. Option D misses the correction window. Option B names the issue, explains why it matters, and offers collaborative resolution.',
    'Konstruktiv rəy konkret, vaxtında və həll yönümlüdür. A seçimi həmkardan öyrənmə fürsətini alır. C seçimi onları tamamilə yan keçir və etibarı zədələyir. D seçimi düzəliş pəncərəsini buraxır. B seçimi problemi adlandırır, əhəmiyyətini izah edir və birgə həll təklif edir.',
    'Use the SBI model for feedback: Situation (when/where), Behavior (what specifically happened), Impact (what effect it had). This removes personal judgment from the conversation.',
    'Rəy üçün SBI modelindən istifadə edin: Vəziyyət (nə vaxt/harada), Davranış (konkret nə baş verdi), Təsir (nə effekt yaratdı). Bu, söhbətdən şəxsi mühakiməni çıxarır.'
)
ON CONFLICT (id) DO NOTHING;


-- C12: Summarizing a Complex Discussion for Stakeholders (Easy)
-- Framework: Korn Ferry "Communicates Effectively" — synthesizing information
-- IRT: a=1.3, b=-0.9, c=0.13
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000012',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'After a 90-minute cross-department meeting with 12 participants, your director asks you to send a summary email to all attendees within the hour. The discussion covered five topics but only two resulted in decisions. What should the email prioritize?',
    'Direktorunuz 12 iştirakçılı 90 dəqiqəlik şöbələrarası iclasdan sonra bir saat ərzində bütün iştirakçılara xülasə e-poçtu göndərməyinizi xahiş edir. Müzakirə beş mövzunu əhatə edib, lakin yalnız ikisi qərarlara gətirib. E-poçt nəyə üstünlük verməlidir?',
    '[
        {"key": "A", "text_en": "A chronological transcript of who said what during the meeting", "text_az": "İclas zamanı kimin nə dediyinin xronoloji əlyazması"},
        {"key": "B", "text_en": "The two decisions made, action items with owners and deadlines, and a brief note on the three open topics", "text_az": "Qəbul edilmiş iki qərar, sahibləri və son tarixləri olan hərəkət bəndləri, və üç açıq mövzu haqqında qısa qeyd"},
        {"key": "C", "text_en": "Only the two decisions — the open topics are not worth mentioning yet", "text_az": "Yalnız iki qərar — açıq mövzuları hələlik qeyd etməyə dəyməz"},
        {"key": "D", "text_en": "A detailed summary of all five topics with equal space given to each", "text_az": "Hər birinə bərabər yer verilməklə beş mövzunun ətraflı xülasəsi"}
    ]',
    'B',
    1.3, -0.9, 0.13,
    'Effective meeting summaries prioritize outcomes over process. Option A is a transcript, not a summary. Option C omits open topics that participants may need to prepare for. Option D treats all topics equally despite unequal resolution. Option B leads with decisions and actions while acknowledging unfinished business.',
    'Effektiv iclas xülasələri nəticələri prosesdən üstün tutur. A seçimi xülasə deyil, əlyazmadır. C seçimi iştirakçıların hazırlaşmalı ola biləcəyi açıq mövzuları buraxır. D seçimi bərabər olmayan həllə baxmayaraq bütün mövzulara bərabər yanaşır. B seçimi qərarlar və hərəkətlərlə başlayır, başa çatmamış işləri qeyd edir.',
    'For meeting summaries use the DAP format: Decisions (what was agreed), Actions (who does what by when), Parking lot (what remains open). Recipients scan the top, not the bottom.',
    'İclas xülasələri üçün DAP formatından istifadə edin: Qərarlar (nə razılaşdırıldı), Hərəkətlər (kim nə vaxt nə edir), Açıq mövzular (nə açıq qalır). Alıcılar aşağını deyil, yuxarını nəzərdən keçirir.'
)
ON CONFLICT (id) DO NOTHING;


-- C13: Clarifying Ambiguous Instructions from a Manager (Easy)
-- Framework: CCL "Learning Agility" + SHL UCF "Following Instructions"
-- IRT: a=1.1, b=-0.7, c=0.14
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000013',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'Your project manager sends a message: "Please prepare the data for the quarterly review." You are unsure which dataset, format, or deadline they mean. What is the BEST next step?',
    'Layihə meneceriniz mesaj göndərir: "Zəhmət olmasa rüblük baxış üçün məlumatları hazırlayın." Hansı məlumat dəstini, formatı və ya son tarixi nəzərdə tutduqlarından əmin deyilsiniz. Ən YAXŞI növbəti addım hansıdır?',
    '[
        {"key": "A", "text_en": "Prepare what you think they mean based on last quarter''s format — they will correct you if it is wrong", "text_az": "Keçən rübün formatına əsasən nə nəzərdə tutduqlarını düşündüyünüzü hazırlayın — səhv olarsa düzəldəcəklər"},
        {"key": "B", "text_en": "Reply with a specific clarification: ''To confirm — you need the Q1 sales dataset in the slide template by Friday 3pm. Is that correct?''", "text_az": "Konkret aydınlaşdırma ilə cavab verin: ''Təsdiq üçün — cümə saat 15:00-a qədər slayd şablonunda Q1 satış məlumat dəstini lazımdır. Doğrudurmu?''"},
        {"key": "C", "text_en": "Ask a colleague what they think the manager meant", "text_az": "Menecerin nə nəzərdə tutduğunu düşündüklərini həmkarınızdan soruşun"},
        {"key": "D", "text_en": "Wait for the manager to send more details — they will follow up if it is urgent", "text_az": "Menecerin daha ətraflı məlumat göndərməsini gözləyin — təcili olarsa əlavə edəcəklər"}
    ]',
    'B',
    1.1, -0.7, 0.14,
    'Clarifying ambiguous instructions requires proposing a specific interpretation for the sender to confirm or correct. Option A risks wasted effort. Option C introduces a middleman. Option D loses time. Option B gives the manager a concrete proposal to react to, which is faster than open-ended questioning.',
    'Qeyri-müəyyən təlimatları aydınlaşdırmaq göndərənin təsdiq və ya düzəltməsi üçün konkret interpretasiya təklif etməyi tələb edir. A seçimi boş əmək riski yaradır. C seçimi vasitəçi daxil edir. D seçimi vaxt itirir. B seçimi menecerə reaksiya vermək üçün konkret təklif verir ki, bu da açıq suallardan daha sürətlidir.',
    'When instructions are vague, use the "confirm-propose" pattern: restate what you understood in specific terms and ask for a yes/no. This shifts the burden from "figure it out" to "verify my understanding."',
    'Təlimatlar qeyri-müəyyən olduqda, "təsdiq-təklif" modelindən istifadə edin: anladığınızı konkret ifadələrlə yenidən bildirin və bəli/xeyr soruşun. Bu, yükü "anla" dan "anlayışımı yoxla"ya keçirir.'
)
ON CONFLICT (id) DO NOTHING;


-- C14: Cross-Cultural Communication in Multicultural Teams (Medium)
-- Framework: SHL UCF "Adapting and Responding to Change" + Hofstede cultural dimensions
-- IRT: a=1.5, b=-0.3, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000014',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'You lead a project team with members from four countries. During a video call, you notice that two members from high-context cultures never disagree openly, while two from low-context cultures dominate the discussion. The project needs honest input from everyone. What is the MOST effective approach?',
    'Dörd ölkədən olan üzvləri olan layihə komandasına rəhbərlik edirsiniz. Video zəng zamanı yüksək kontekstli mədəniyyətlərdən olan iki üzvün heç vaxt açıq razılaşmadığını, aşağı kontekstli mədəniyyətlərdən olan ikisinin müzakirəyə hakim olduğunu müşahidə edirsiniz. Layihə hər kəsdən dürüst rəy tələb edir. Ən effektiv yanaşma hansıdır?',
    '[
        {"key": "A", "text_en": "Treat everyone equally — ask each person the same question in the same way during the call", "text_az": "Hər kəsə bərabər davranın — zəng zamanı hər kəsə eyni sualı eyni şəkildə verin"},
        {"key": "B", "text_en": "Before the call, send an anonymous survey. During the call, use round-robin turns. After the call, follow up individually with quiet members to capture insights they may share privately", "text_az": "Zəngdən əvvəl anonim sorğu göndərin. Zəng zamanı növbəli danışıq istifadə edin. Zəngdən sonra şəxsi paylaşa biləcəkləri fikirləri almaq üçün sakit üzvlərlə fərdi əlaqə qurun"},
        {"key": "C", "text_en": "Tell the quiet members they need to speak up more — directness is a professional expectation", "text_az": "Sakit üzvlərə daha çox danışmalı olduqlarını söyləyin — birbaşalıq peşəkar gözləntidir"},
        {"key": "D", "text_en": "Let the dominant members lead since they are more engaged — the quiet ones can contribute via email later", "text_az": "Dominant üzvlərə rəhbərlik etməyə icazə verin çünki daha fəaldırlar — sakit olanlar sonra e-poçt vasitəsilə töhfə verə bilərlər"}
    ]',
    'B',
    1.5, -0.3, 0.15,
    'Cross-cultural communication requires creating multiple input channels, not imposing one style. Option A ignores different communication norms. Option C forces low-context norms onto high-context communicators. Option D accepts an unbalanced dynamic. Option B uses three complementary methods (pre-survey, structured turns, private follow-up) to ensure all voices contribute.',
    'Mədəniyyətlərarası kommunikasiya bir üslubu tətbiq etmək deyil, çoxsaylı giriş kanalları yaratmağı tələb edir. A seçimi fərqli kommunikasiya normalarını nəzərə almır. C seçimi aşağı kontekst normalarını yüksək kontekst ünsiyyətçilərinə məcbur edir. D seçimi qeyri-balanslaşdırılmış dinamikanı qəbul edir. B seçimi bütün səslərin töhfə verməsini təmin etmək üçün üç tamamlayıcı üsuldan istifadə edir.',
    'For multicultural teams, design three input modes: asynchronous (written before meeting), synchronous-structured (round-robin during meeting), and private (1:1 follow-up after). High-context cultures often share best in the third mode.',
    'Çoxmədəniyyətli komandalar üçün üç giriş rejimi dizayn edin: asinxron (iclasdan əvvəl yazılı), sinxron-strukturlaşdırılmış (iclas zamanı növbəli), və şəxsi (sonra 1:1). Yüksək kontekstli mədəniyyətlər çox vaxt üçüncü rejimdə ən yaxşısını paylaşır.'
)
ON CONFLICT (id) DO NOTHING;


-- C15: Managing Communication During a Crisis (Medium)
-- Framework: CCL "Courage to Communicate" + SHL UCF "Coping with Pressures and Setbacks"
-- IRT: a=1.6, b=-0.1, c=0.14
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000015',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'Your team''s product demo to a key client is in 2 hours. The lead presenter has just called in sick and the backup presenter has never seen the latest version of the slide deck. You are the project coordinator. What communication steps do you take FIRST?',
    'Komandanızın əsas müştəriyə məhsul nümayişinə 2 saat qalıb. Əsas təqdimçi xəstəliyə görə zəng etdi və ehtiyat təqdimçi slayd destinin ən son versiyasını heç vaxt görməyib. Siz layihə koordinatorusunuz. İlk olaraq hansı kommunikasiya addımlarını atırsınız?',
    '[
        {"key": "A", "text_en": "Email the client to postpone — better to delay than to present poorly", "text_az": "Təxirə salmaq üçün müştəriyə e-poçt göndərin — pis təqdimatdan gec etmək yaxşıdır"},
        {"key": "B", "text_en": "Brief the backup presenter on the 3 critical slides, assign other team members to handle Q&A sections they know best, and notify the client that the presenting team has changed", "text_az": "Ehtiyat təqdimçini 3 kritik slayd haqqında məlumatlandırın, digər komanda üzvlərinə ən yaxşı bildikləri S&C bölmələrini həvalə edin, və müştəriyə təqdimat komandasının dəyişdiyini bildirin"},
        {"key": "C", "text_en": "Do the presentation yourself — you know the project best as coordinator", "text_az": "Təqdimatı özünüz edin — koordinator kimi layihəni ən yaxşı siz tanıyırsınız"},
        {"key": "D", "text_en": "Send the slide deck to the backup presenter and trust them to prepare on their own", "text_az": "Slayd destini ehtiyat təqdimçiyə göndərin və öz başına hazırlanacağına etibar edin"}
    ]',
    'B',
    1.6, -0.1, 0.14,
    'Crisis communication requires parallel actions: equip the replacement with essentials (not everything), distribute load across the team, and proactively inform the stakeholder. Option A abandons the opportunity. Option C ignores role boundaries. Option D leaves the backup unsupported. Option B coordinates three communication streams simultaneously.',
    'Böhran kommunikasiyası paralel hərəkətlər tələb edir: əvəzçini əsaslarla (hər şeylə deyil) təchiz edin, yükü komanda arasında bölüşdürün və maraqlı tərəfi proaktiv məlumatlandırın. A seçimi fürsəti tərk edir. C seçimi rol sərhədlərini nəzərə almır. D seçimi ehtiyatı dəstəksiz buraxır. B seçimi üç kommunikasiya axınını eyni vaxtda koordinasiya edir.',
    'In a crisis, communicate in three directions simultaneously: down (brief your team), up (inform your stakeholder), and across (coordinate with support functions). The coordinator''s job is routing information, not doing all the work.',
    'Böhranda üç istiqamətdə eyni vaxtda ünsiyyət qurun: aşağı (komandanızı məlumatlandırın), yuxarı (maraqlı tərəfi xəbərdar edin) və yan (dəstək funksiyaları ilə koordinasiya edin). Koordinatorun işi məlumatı yönləndirməkdir, bütün işi görməkdir deyil.'
)
ON CONFLICT (id) DO NOTHING;


-- C16: Persuasive Presentation to Skeptical Audience (Medium)
-- Framework: Korn Ferry "Presentation Skills" + CCL "Influence" behavioral anchors
-- IRT: a=1.7, b=0.2, c=0.16
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000016',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'You are presenting a new workflow tool to 20 department managers who have openly stated they are satisfied with the current system. You have 15 minutes. What is the MOST persuasive communication structure?',
    'Mövcud sistemdən razı olduqlarını açıq bildirmiş 20 şöbə menecerinə yeni iş axını alətini təqdim edirsiniz. 15 dəqiqəniz var. Ən inandırıcı kommunikasiya strukturu hansıdır?',
    '[
        {"key": "A", "text_en": "Start with a full feature walkthrough so they can see everything the new tool does", "text_az": "Yeni alətin nə etdiyini görə bilmələri üçün tam xüsusiyyət icmalı ilə başlayın"},
        {"key": "B", "text_en": "Begin by acknowledging the current system works, then present 2-3 specific pain points the new tool solves with data from their own department, and end with a low-risk pilot proposal", "text_az": "Mövcud sistemin işlədiyini etiraf edərək başlayın, sonra yeni alətin onların öz şöbəsindən məlumatlarla həll etdiyi 2-3 konkret problem nöqtəsini təqdim edin və aşağı riskli pilot təklifi ilə bitirin"},
        {"key": "C", "text_en": "Show testimonials from other companies that switched — social proof drives adoption", "text_az": "Keçid edən digər şirkətlərdən rəylər göstərin — sosial sübut qəbulu sürətləndirir"},
        {"key": "D", "text_en": "Focus on cost savings — managers respond best to financial arguments", "text_az": "Xərclərə qənaətə diqqət yetirin — menecerlər maliyyə arqumentlərinə ən yaxşı cavab verir"}
    ]',
    'B',
    1.7, 0.2, 0.16,
    'Persuading a satisfied audience requires first validating their current position (reducing defensiveness), then connecting the change to their specific pain points (not generic features), and offering a low-commitment next step. Option A overwhelms with features they did not ask for. Option C relies on external proof without local relevance. Option D assumes a single motivation. Option B follows the validate-problem-propose arc.',
    'Razı qalmış auditoriyanı inandırmaq əvvəlcə onların mövcud mövqeyini təsdiq etməyi (müdafiəni azaltmaq), sonra dəyişikliyi onların xüsusi problem nöqtələrinə bağlamağı (ümumi xüsusiyyətlərə deyil) və aşağı öhdəlikli növbəti addım təklif etməyi tələb edir. A seçimi istəmədikləri xüsusiyyətlərlə sıxışdırır. C seçimi yerli uyğunluğu olmadan xarici sübutlara əsaslanır. D seçimi tək motivasiya fərz edir. B seçimi təsdiq-problem-təklif qövsünü izləyir.',
    'When presenting to a resistant audience, follow the ACE structure: Acknowledge their current reality, Connect the change to their specific pain, and End with an Easy next step (pilot, trial, demo) that requires minimal commitment.',
    'Müqavimət göstərən auditoriyaya təqdimat edərkən ACE strukturuna əməl edin: Onların mövcud reallığını Etiraf edin, dəyişikliyi onların xüsusi ağrı nöqtəsinə Bağlayın, və minimal öhdəlik tələb edən Asan növbəti addımla (pilot, sınaq, demo) Bitirin.'
)
ON CONFLICT (id) DO NOTHING;


-- C17: Navigating Difficult Conversations with a Direct Report (Medium)
-- Framework: SHL UCF "Leading and Deciding" + Korn Ferry "Manages Conflict"
-- IRT: a=1.6, b=0.4, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000017',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'A team member has missed three consecutive deadlines. Their work quality is excellent when delivered, but the lateness is affecting the entire project timeline. You need to have a conversation with them. What is the MOST effective communication approach?',
    'Bir komanda üzvü ardıcıl üç son tarixi buraxıb. İşlərinin keyfiyyəti çatdırıldığında əladır, lakin gecikmə bütün layihə cədvəlinə təsir edir. Onlarla söhbət etməlisiniz. Ən effektiv kommunikasiya yanaşması hansıdır?',
    '[
        {"key": "A", "text_en": "Send them an email documenting the missed deadlines and cc their manager for accountability", "text_az": "Buraxılmış son tarixləri sənədləşdirən e-poçt göndərin və hesabatlılıq üçün menecerinə cc edin"},
        {"key": "B", "text_en": "Have a private face-to-face conversation: acknowledge their quality of work, state the specific impact of the delays on the team, ask what barriers they are facing, and co-create a realistic timeline together", "text_az": "Şəxsi üzbəüz söhbət edin: işlərinin keyfiyyətini etiraf edin, gecikmələrin komandaya konkret təsirini bildirin, hansı maneələrlə üzləşdiklərini soruşun, və birlikdə real cədvəl yaradın"},
        {"key": "C", "text_en": "Reassign their tasks to someone faster — actions speak louder than words", "text_az": "Tapşırıqlarını daha sürətli birinə həvalə edin — hərəkətlər sözlərdən daha güclüdür"},
        {"key": "D", "text_en": "Give them one more chance without a conversation — maybe they are going through something personal", "text_az": "Söhbət etmədən onlara bir şans daha verin — bəlkə şəxsi bir şey yaşayırlar"}
    ]',
    'B',
    1.6, 0.4, 0.15,
    'Difficult conversations require balancing directness with empathy. Option A is public shaming disguised as documentation. Option C punishes without understanding. Option D avoids the conversation entirely. Option B opens with recognition, states the impact factually, explores root causes, and ends with a joint solution — the hallmark of effective managerial communication.',
    'Çətin söhbətlər birbaşalığı empatiya ilə balanslaşdırmağı tələb edir. A seçimi sənədləşdirmə kimi maskalanmış ictimai rüsvayçılıqdır. C seçimi anlamadan cəzalandırır. D seçimi söhbətdən tamamilə qaçır. B seçimi tanınma ilə başlayır, təsiri faktiki olaraq bildirir, kök səbəbləri araşdırır və birgə həll ilə bitirir — effektiv idarəçilik kommunikasiyasının əlaməti.',
    'For performance conversations, use the COIN model: Context (the situation), Observation (what you specifically saw), Impact (how it affected others), Next steps (what you agree to do). This structure prevents the conversation from becoming personal.',
    'Performans söhbətləri üçün COIN modelindən istifadə edin: Kontekst (vəziyyət), Müşahidə (konkret nə gördüyünüz), Təsir (başqalarına necə təsir etdi), Növbəti addımlar (nə etməyə razılaşdığınız). Bu struktur söhbətin şəxsiləşməsinin qarşısını alır.'
)
ON CONFLICT (id) DO NOTHING;


-- C18: Mediating a Disagreement Between Two Senior Colleagues (Hard)
-- Framework: Korn Ferry "Manages Conflict" + CCL "Boundary Spanning"
-- IRT: a=1.9, b=0.7, c=0.18
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000018',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'mcq',
    'Two senior specialists in your project team have a public disagreement during a client workshop. One insists on approach A, the other on approach B. Both have valid technical arguments. The client is visibly uncomfortable and the workshop has 45 minutes remaining. As the project lead, what do you do?',
    'Layihə komandanızdakı iki böyük mütəxəssisin müştəri seminarında ictimai fikir ayrılığı var. Biri A yanaşmasında, digəri B yanaşmasında israr edir. Hər ikisinin etibarlı texniki arqumentləri var. Müştəri göründüyü kimi narahatdır və seminara 45 dəqiqə qalıb. Layihə rəhbəri kimi nə edirsiniz?',
    '[
        {"key": "A", "text_en": "Let them debate — the best argument will win and the client sees a rigorous team", "text_az": "Debat etmələrinə icazə verin — ən yaxşı arqument qalib gələcək və müştəri ciddi komanda görəcək"},
        {"key": "B", "text_en": "Acknowledge both positions publicly, reframe the debate as ''Option A optimizes for X, Option B for Y — let us map both against the client''s priorities,'' then facilitate a structured comparison with the client''s input", "text_az": "Hər iki mövqeyi ictimai olaraq etiraf edin, debatı ''A seçimi X üçün optimallaşdırır, B seçimi Y üçün — hər ikisini müştərinin prioritetlərinə uyğunlaşdıraq'' kimi yenidən çərçivələyin, sonra müştərinin giriş ilə strukturlaşdırılmış müqayisə aparın"},
        {"key": "C", "text_en": "Side with the more experienced specialist to end the disagreement quickly", "text_az": "Fikir ayrılığını tez bitirmək üçün daha təcrübəli mütəxəssisin tərəfini tutun"},
        {"key": "D", "text_en": "Call for a break and ask both specialists to resolve it privately before resuming", "text_az": "Fasilə elan edin və hər iki mütəxəssisdən davam etməzdən əvvəl bunu şəxsi olaraq həll etmələrini xahiş edin"}
    ]',
    'B',
    1.9, 0.7, 0.18,
    'Public disagreement in front of a client requires reframing, not suppression. Option A lets the conflict escalate and alienates the client. Option C destroys the authority of the overruled specialist. Option D delays resolution and signals dysfunction. Option B converts the disagreement into a structured decision framework that includes the client, demonstrating both rigor and professionalism.',
    'Müştəri qarşısında ictimai fikir ayrılığı boğulmanı deyil, yenidən çərçivələməni tələb edir. A seçimi konfliktin artmasına və müştərinin uzaqlaşmasına icazə verir. C seçimi rədd edilən mütəxəssisin nüfuzunu məhv edir. D seçimi həlli gecikdirir və disfunksiyanı siqnallaşdırır. B seçimi fikir ayrılığını müştərini daxil edən strukturlaşdırılmış qərar çərçivəsinə çevirir, həm dəqiqliyi, həm peşəkarlığı nümayiş etdirir.',
    'When two experts disagree in front of a stakeholder, use the "reframe as trade-off" technique: name what each option optimizes for, then let the stakeholder''s priorities break the tie. You mediate the frame, not the answer.',
    'İki ekspert maraqlı tərəf qarşısında razılaşmadıqda, "kompromis kimi yenidən çərçivələmə" texnikasından istifadə edin: hər seçimin nəyi optimallaşdırdığını adlandırın, sonra maraqlı tərəfin prioritetlərinin bərabərliyi pozmasına icazə verin. Siz çərçivəni vasitəçilik edirsiniz, cavabı deyil.'
)
ON CONFLICT (id) DO NOTHING;


-- C19: Communicating Unpopular Decisions to a Team (Hard)
-- Framework: Korn Ferry "Directs Work" + SHL UCF "Deciding and Initiating Action"
-- IRT: a=2.0, b=1.0, c=0.18
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000019',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'mcq',
    'Senior leadership has decided to cancel a project your 8-person team has been working on for 3 months. The decision is final and cannot be reversed. You need to communicate this in tomorrow''s team meeting. Two team members have already expressed they will be upset. What is the MOST effective communication strategy?',
    'Yüksək rəhbərlik 8 nəfərlik komandanızın 3 aydır üzərində işlədiyi layihəni ləğv etmək qərarına gəlib. Qərar qətidir və geri dönülməzdir. Bunu sabahkı komanda iclasında bildirməlisiniz. İki komanda üzvü artıq narazı olacaqlarını ifadə edib. Ən effektiv kommunikasiya strategiyası hansıdır?',
    '[
        {"key": "A", "text_en": "Share the decision via email before the meeting so people can process it privately, then use the meeting for questions", "text_az": "Qərarı iclasdan əvvəl e-poçtla paylaşın ki, insanlar onu şəxsi olaraq həzm etsinlər, sonra iclası suallar üçün istifadə edin"},
        {"key": "B", "text_en": "In the meeting, state the decision clearly with the business reasoning, acknowledge the team''s effort and the emotional impact, allow space for reactions, and then redirect focus to how their skills will be deployed next", "text_az": "İclasda qərarı biznes əsaslandırması ilə aydın bildirin, komandanın səyini və emosional təsirini etiraf edin, reaksiyalara yer verin, sonra diqqəti onların bacarıqlarının bundan sonra necə istifadə olunacağına yönləndirin"},
        {"key": "C", "text_en": "Soften the blow by framing it as a ''pause'' rather than a cancellation — they can always resume later", "text_az": "Zərbəni yumşaltmaq üçün onu ləğvetmə deyil, ''pauza'' kimi çərçivələyin — sonra həmişə davam edə bilərlər"},
        {"key": "D", "text_en": "Deliver the message quickly and move on to new assignments — dwelling on it will only make it worse", "text_az": "Mesajı tez çatdırın və yeni tapşırıqlara keçin — üzərində dayanmaq yalnız vəziyyəti pisləşdirəcək"}
    ]',
    'B',
    2.0, 1.0, 0.18,
    'Communicating bad news effectively requires honesty about the decision, respect for the emotional impact, and forward direction. Option A avoids face-to-face delivery of difficult news. Option C is dishonest and delays the real reaction. Option D dismisses the team''s emotional investment. Option B follows the truth-empathy-direction sequence: clear decision, acknowledged feelings, future-oriented next step.',
    'Pis xəbəri effektiv kommunikasiya etmək qərar haqqında dürüstlük, emosional təsirə hörmət və irəliyə istiqamət tələb edir. A seçimi çətin xəbərin üzbəüz çatdırılmasından qaçır. C seçimi qeyri-səmimidi və həqiqi reaksiyanı gecikdirir. D seçimi komandanın emosional investisiyasını rədd edir. B seçimi həqiqət-empatiya-istiqamət ardıcıllığını izləyir: aydın qərar, etiraf edilmiş hisslər, gələcəyə yönəlmiş növbəti addım.',
    'For delivering bad news, use the HEAD framework: Honest statement of the decision, Empathy for the impact, Acknowledgment of contributions, Direction for what comes next. Never sugarcoat and never rush past the emotional moment.',
    'Pis xəbər çatdırmaq üçün HEAD çərçivəsindən istifadə edin: Qərarın Dürüst ifadəsi, təsir üçün Empatiya, töhfələrin Tanınması, növbəti addımlar üçün İstiqamət. Heç vaxt şirinləşdirməyin və emosional andan heç vaxt tələsik keçməyin.'
)
ON CONFLICT (id) DO NOTHING;


-- C20: Synthesizing Conflicting Information for Executive Decision (Hard)
-- Framework: SHL UCF "Analysing" + Korn Ferry "Business Insight" + CCL "Strategic Perspective"
-- IRT: a=2.2, b=1.4, c=0.20
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000020',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'mcq',
    'You are preparing a briefing for the CEO. Three departments have submitted data for the same decision: Marketing says launch now (based on competitor timing), Finance says delay 6 months (based on cash flow), and Engineering says launch is technically feasible but quality is at 85%. The CEO expects a single-page recommendation from you. What is the BEST communication approach?',
    'Baş direktorun brifinqini hazırlayırsınız. Üç şöbə eyni qərar üçün məlumat təqdim edib: Marketinq indi buraxmağı deyir (rəqib vaxtına əsasən), Maliyyə 6 ay gecikdirməyi deyir (pul axınına əsasən), Mühəndislik isə buraxılışın texniki cəhətdən mümkün olduğunu, lakin keyfiyyətin 85% olduğunu bildirir. Baş direktor sizdən bir səhifəlik tövsiyə gözləyir. Ən YAXŞI kommunikasiya yanaşması hansıdır?',
    '[
        {"key": "A", "text_en": "Present the three perspectives equally and let the CEO decide — it is not your place to recommend", "text_az": "Üç perspektivi bərabər təqdim edin və Baş direktorun qərara gəlməsinə icazə verin — tövsiyə etmək sizin yeriniz deyil"},
        {"key": "B", "text_en": "State your recommendation first with the primary rationale, then present the three inputs as supporting/conflicting evidence, name the key trade-off explicitly, and include the risk and mitigation for the recommended path", "text_az": "Əsas əsaslandırma ilə tövsiyənizi əvvəlcə bildirin, sonra üç girişi dəstəkləyici/ziddiyyətli sübut kimi təqdim edin, əsas kompromisi açıq adlandırın, və tövsiyə olunan yol üçün risk və azaltmanı daxil edin"},
        {"key": "C", "text_en": "Side with Finance — financial prudence always wins at the executive level", "text_az": "Maliyyənin tərəfini tutun — maliyyə ehtiyatlılığı icra səviyyəsində həmişə qalib gəlir"},
        {"key": "D", "text_en": "Present a compromise: launch a limited version now to satisfy all three departments", "text_az": "Kompromis təqdim edin: hər üç şöbəni razı salmaq üçün indi məhdud versiya buraxın"}
    ]',
    'B',
    2.2, 1.4, 0.20,
    'Executive communication requires synthesis, not aggregation. Option A abdicates the analyst''s responsibility to recommend. Option C applies a blanket rule instead of contextual analysis. Option D compromises without evaluating whether a partial launch serves the strategic goal. Option B leads with a clear recommendation, provides transparent evidence (including conflicting data), names the trade-off, and addresses risk — the hallmark of executive-ready communication.',
    'İcra kommunikasiyası toplama deyil, sintez tələb edir. A seçimi analitikin tövsiyə etmək məsuliyyətindən imtina edir. C seçimi kontekstual analiz əvəzinə ümumi qayda tətbiq edir. D seçimi qismən buraxılışın strateji məqsədə xidmət edib etmədiyini qiymətləndirmədən güzəştə gedir. B seçimi aydın tövsiyə ilə başlayır, şəffaf sübut təqdim edir, kompromisi adlandırır və riski ünvanlayır — icra kommunikasiyasına hazırlığın əlaməti.',
    'For executive briefings, use the BLUF structure (Bottom Line Up Front): lead with your recommendation in the first sentence, then provide the evidence pyramid — supporting data first, conflicting data second, risk last. Executives read top-down and may stop at any point.',
    'İcra brifinqləri üçün BLUF strukturundan (Alt Xətt Əvvəlcə) istifadə edin: ilk cümlədə tövsiyənizlə başlayın, sonra sübut piramidası təqdim edin — əvvəlcə dəstəkləyici məlumat, sonra ziddiyyətli məlumat, son olaraq risk. İcraçılar yuxarıdan aşağıya oxuyur və istənilən nöqtədə dayana bilər.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- EVENT PERFORMANCE (55555555-5555-5555-5555-555555555555)
-- Weight: 0.10 | 5 questions: 2 easy, 2 medium, 1 hard
-- =============================================================================


-- EP11: Managing Time-Critical Setup Tasks (Easy)
-- Framework: SHL UCF "Planning and Organising" + OECD "Task Management"
-- IRT: a=1.2, b=-1.0, c=0.12
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000005-0000-0000-0000-000000000011',
    '55555555-5555-5555-5555-555555555555',
    'easy', 'mcq',
    'You arrive at a conference venue 2 hours before doors open. Your checklist has 8 tasks: AV setup, registration desk, signage, catering coordination, speaker check-in, Wi-Fi testing, photography briefing, and security walkthrough. You have a team of 4 people. What is the BEST first action?',
    'Konfrans məkanına qapıların açılmasına 2 saat qala gəlirsiniz. Siyahınızda 8 tapşırıq var: AV quraşdırma, qeydiyyat masası, nişanlar, iaşə koordinasiyası, natiq qeydiyyatı, Wi-Fi testi, fotoqrafiya brifinqi və təhlükəsizlik gəzintisi. 4 nəfərlik komandanız var. Ən YAXŞI ilk addım hansıdır?',
    '[
        {"key": "A", "text_en": "Start with AV setup since it is the most complex and work through the list in order", "text_az": "Ən mürəkkəb olduğu üçün AV quraşdırma ilə başlayın və siyahını sıra ilə keçin"},
        {"key": "B", "text_en": "Prioritize tasks by dependency and deadline: assign AV and Wi-Fi first (they block other tasks), delegate independent tasks in parallel to team members, and set a 90-minute checkpoint", "text_az": "Tapşırıqları asılılıq və son tarixə görə prioritetləşdirin: əvvəlcə AV və Wi-Fi təyin edin (digər tapşırıqları bloklaşdırır), müstəqil tapşırıqları komanda üzvlərinə paralel həvalə edin və 90 dəqiqəlik yoxlama nöqtəsi təyin edin"},
        {"key": "C", "text_en": "Split the list evenly — 2 tasks per person — and check back when everything is done", "text_az": "Siyahını bərabər bölün — hər adama 2 tapşırıq — və hər şey bitdikdə yoxlayın"},
        {"key": "D", "text_en": "Do a full walkthrough of the venue yourself first to understand the layout before assigning any tasks", "text_az": "Hər hansı tapşırıq təyin etməzdən əvvəl planı anlamaq üçün əvvəlcə məkanı tamamilə gəzin"}
    ]',
    'B',
    1.2, -1.0, 0.12,
    'Event setup requires dependency-based prioritization, not sequential or equal-split approaches. AV and Wi-Fi are blockers — if they fail, other tasks cannot proceed. Option A is sequential and slow. Option C ignores task dependencies. Option D delays the entire team. Option B identifies critical-path tasks, parallelizes, and builds in a checkpoint.',
    'Tədbir quraşdırması sıralı və ya bərabər bölgü deyil, asılılıq əsaslı prioritetləşdirmə tələb edir. AV və Wi-Fi bloklayıcıdır — uğursuz olsalar, digər tapşırıqlar davam edə bilməz. A seçimi ardıcıl və yavaşdır. C seçimi tapşırıq asılılıqlarını nəzərə almır. D seçimi bütün komandanı gecikdirir. B seçimi kritik yol tapşırıqlarını müəyyənləşdirir, paralelləşdirir və yoxlama nöqtəsi qurur.',
    'For event setup, always identify "blocker tasks" first: tasks that other tasks depend on. Set those up first and in parallel. Everything else can happen concurrently once blockers are cleared.',
    'Tədbir quraşdırması üçün həmişə əvvəlcə "bloklayıcı tapşırıqları" müəyyənləşdirin: digər tapşırıqların asılı olduğu tapşırıqlar. Onları əvvəl və paralel qurun. Bloklayıcılar aradan qaldırıldıqdan sonra hər şey eyni vaxtda baş verə bilər.'
)
ON CONFLICT (id) DO NOTHING;


-- EP12: Handling an Unexpected Venue Problem (Easy)
-- Framework: CCL "Resilience" + SHL UCF "Coping with Pressures and Setbacks"
-- IRT: a=1.3, b=-0.8, c=0.13
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000005-0000-0000-0000-000000000012',
    '55555555-5555-5555-5555-555555555555',
    'easy', 'mcq',
    'Thirty minutes before a workshop starts, the projector in the main room stops working. 60 participants are expected. A smaller room with a working projector seats only 30. What do you do?',
    'Seminara 30 dəqiqə qalmış əsas otaqdakı proyektor işləməyi dayandırır. 60 iştirakçı gözlənilir. İşləyən proyektoru olan kiçik otaq yalnız 30 nəfər tutur. Nə edirsiniz?',
    '[
        {"key": "A", "text_en": "Cancel the projection and print handouts instead — no projector, no slides", "text_az": "Proyeksiyanı ləğv edin və əvəzinə çap materialları paylayın — proyektor yoxdur, slayd yoxdur"},
        {"key": "B", "text_en": "Split participants into two groups: run the workshop twice using the smaller room, adjusting the schedule to accommodate both sessions", "text_az": "İştirakçıları iki qrupa bölün: kiçik otaqdan istifadə edərək seminari iki dəfə keçirin, hər iki sessiyaya uyğunlaşmaq üçün cədvəli tənzimləyin"},
        {"key": "C", "text_en": "Move everyone to the smaller room and ask 30 people to stand", "text_az": "Hər kəsi kiçik otağa köçürün və 30 nəfərdən ayaq üstə dayanmağı xahiş edin"},
        {"key": "D", "text_en": "Delay the workshop until IT fixes the projector, even if it takes an hour", "text_az": "Bir saat çəksə belə, İT proyektoru düzəldənə qədər seminarı gecikdirin"}
    ]',
    'B',
    1.3, -0.8, 0.13,
    'Event performance means solving problems with available resources, not waiting for ideal conditions. Option A discards the visual element entirely. Option C creates a poor experience for half the audience. Option D wastes an hour of 60 people''s time. Option B uses the available resource (smaller room) and adapts the format (two sessions) to serve all participants.',
    'Tədbir performansı ideal şərait gözləmək deyil, mövcud resurslarla problemləri həll etmək deməkdir. A seçimi vizual elementi tamamilə atır. C seçimi auditoriyanın yarısı üçün pis təcrübə yaradır. D seçimi 60 nəfərin bir saatını israf edir. B seçimi mövcud resursu (kiçik otaq) istifadə edir və formatı (iki sessiya) bütün iştirakçılara xidmət etmək üçün uyğunlaşdırır.',
    'When venue equipment fails, think "format adaptation" before "equipment repair." Ask: can I change the delivery format (split sessions, rotate groups, use backup room) faster than fixing the hardware?',
    'Məkan avadanlığı uğursuz olduqda, "avadanlıq təmiri"ndən əvvəl "format uyğunlaşdırması" düşünün. Soruşun: çatdırma formatını (sessiyaları bölmək, qrupları dövr etmək, ehtiyat otaqdan istifadə etmək) avadanlığı təmir etməkdən daha sürətli dəyişə bilərəmmi?'
)
ON CONFLICT (id) DO NOTHING;


-- EP13: Coordinating Multi-Stakeholder Event Logistics (Medium)
-- Framework: SHL UCF "Planning and Organising" + Korn Ferry "Manages Complexity"
-- IRT: a=1.6, b=-0.2, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000005-0000-0000-0000-000000000013',
    '55555555-5555-5555-5555-555555555555',
    'medium', 'mcq',
    'You are coordinating a corporate summit with 3 external vendors (catering, AV, security), 2 internal teams (marketing, operations), and a VIP speaker arriving from abroad. On the day before the event, the catering vendor emails to say their delivery truck broke down and food will arrive 3 hours late — during the event itself. What is the BEST course of action?',
    'Siz 3 xarici təchizatçı (iaşə, AV, təhlükəsizlik), 2 daxili komanda (marketinq, əməliyyatlar) və xaricdən gələn VIP natiq ilə korporativ sammiti koordinasiya edirsiniz. Tədbirdən bir gün əvvəl iaşə təchizatçısı çatdırılma yük maşınının xarab olduğunu və yeməyin 3 saat gec — tədbirın özü zamanı çatacağını e-poçtla bildirir. Ən YAXŞI hərəkət tərzi hansıdır?',
    '[
        {"key": "A", "text_en": "Accept the delay and adjust the event schedule to push lunch back by 3 hours", "text_az": "Gecikməni qəbul edin və naharı 3 saat geri çəkmək üçün tədbir cədvəlini tənzimləyin"},
        {"key": "B", "text_en": "Contact two backup catering options immediately, negotiate partial delivery from the original vendor for essentials (coffee, water, snacks), and prepare a revised event flow with a contingency timeline that covers both scenarios", "text_az": "Dərhal iki ehtiyat iaşə seçimi ilə əlaqə saxlayın, əsas maddələr (qəhvə, su, qəlyanaltı) üçün orijinal təchizatçıdan qismən çatdırılma barədə danışıq aparın, və hər iki ssenarini əhatə edən ehtiyat cədvəli ilə yenidən işlənmiş tədbir axını hazırlayın"},
        {"key": "C", "text_en": "Cancel catering entirely and inform attendees to bring their own lunch", "text_az": "İaşəni tamamilə ləğv edin və iştirakçılara öz naharlarını gətirmələrini bildirin"},
        {"key": "D", "text_en": "Call the vendor and insist they fix the problem — it is their responsibility", "text_az": "Təchizatçıya zəng edin və problemi həll etmələrini israr edin — bu onların məsuliyyətidir"}
    ]',
    'B',
    1.6, -0.2, 0.15,
    'Multi-stakeholder event coordination requires contingency planning, not single-point-of-failure reactions. Option A disrupts the entire event for one vendor failure. Option C punishes attendees for a vendor problem. Option D focuses on blame instead of solutions. Option B activates backups, secures minimum essentials from the original vendor, and prepares two parallel timelines — the hallmark of professional event management.',
    'Çox maraqlı tərəfli tədbir koordinasiyası tək uğursuzluq nöqtəsi reaksiyaları deyil, fövqəladə vəziyyət planlaması tələb edir. A seçimi bir təchizatçı uğursuzluğu üçün bütün tədbiri pozur. C seçimi təchizatçı probleminə görə iştirakçıları cəzalandırır. D seçimi həll əvəzinə günahlandırmaya yönəlir. B seçimi ehtiyatları aktivləşdirir, orijinal təchizatçıdan minimum əsas maddələri təmin edir və iki paralel cədvəl hazırlayır.',
    'For every critical vendor at an event, always have a "Plan B contact" saved before the event day. The time to find a backup caterer is not when the first one fails — it is during planning.',
    'Tədbirdəki hər kritik təchizatçı üçün tədbir günündən əvvəl həmişə "Plan B əlaqə" saxlayın. Ehtiyat iaşəçi tapmağın vaxtı birincisi uğursuz olduqda deyil — planlaşdırma zamanıdır.'
)
ON CONFLICT (id) DO NOTHING;


-- EP14: Real-Time Crowd Flow Management (Medium)
-- Framework: Korn Ferry "Action Oriented" + OECD "Problem-Solving in Technology-Rich Environments"
-- IRT: a=1.7, b=0.3, c=0.16
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000005-0000-0000-0000-000000000014',
    '55555555-5555-5555-5555-555555555555',
    'medium', 'mcq',
    'During a 500-person industry conference, you notice the registration queue has grown to 80+ people and the average check-in time is 4 minutes per person. The opening keynote starts in 25 minutes. You have 3 staff at registration and 2 roaming team members. What is the MOST effective immediate action?',
    'Siz 500 nəfərlik sənaye konfransı zamanı qeydiyyat növbəsinin 80+ nəfərə artdığını və orta qeydiyyat müddətinin adam başına 4 dəqiqə olduğunu müşahidə edirsiniz. Açılış əsas çıxışına 25 dəqiqə qalıb. Qeydiyyatda 3 əməkdaşınız və 2 gəzən komanda üzvünüz var. Ən effektiv dərhal hərəkət hansıdır?',
    '[
        {"key": "A", "text_en": "Ask people in the queue to be patient — the keynote will start late if needed", "text_az": "Növbədəki insanlardan səbirli olmalarını xahiş edin — lazım olsa əsas çıxış gec başlayacaq"},
        {"key": "B", "text_en": "Redeploy the 2 roaming members to open 2 additional check-in lanes, have one staff member pre-sort the queue by badge type (pre-registered vs walk-in), and announce the keynote will be livestreamed in the lobby for those still in line", "text_az": "2 gəzən üzvü 2 əlavə qeydiyyat xətti açmaq üçün yenidən yerləşdirin, bir əməkdaşa növbəni nişan növünə görə (əvvəlcədən qeydiyyatdan keçmiş vs yerində gələn) əvvəlcədən sıralasın, və hələ növbədə olanlara əsas çıxışın foyedə canlı yayımlanacağını elan edin"},
        {"key": "C", "text_en": "Let attendees skip registration and check in after the keynote", "text_az": "İştirakçılara qeydiyyatı ötürmələrinə və əsas çıxışdan sonra qeydiyyatdan keçmələrinə icazə verin"},
        {"key": "D", "text_en": "Delay the keynote by 30 minutes and announce the change", "text_az": "Əsas çıxışı 30 dəqiqə gecikdirin və dəyişikliyi elan edin"}
    ]',
    'B',
    1.7, 0.3, 0.16,
    'Crowd flow management requires increasing throughput, reducing bottlenecks, and providing alternatives — simultaneously. Option A does nothing about throughput. Option C bypasses security and tracking. Option D penalizes on-time arrivals. Option B increases lanes (throughput), pre-sorts the queue (reduces per-person time), and livestreams the keynote (removes the urgency that causes frustration).',
    'İzdiham axını idarəetməsi ötürmə qabiliyyətini artırmağı, darboğazları azaltmağı və alternativlər təqdim etməyi eyni vaxtda tələb edir. A seçimi ötürmə qabiliyyəti ilə bağlı heç nə etmir. C seçimi təhlükəsizlik və izləməni yan keçir. D seçimi vaxtında gələnləri cəzalandırır. B seçimi xətləri artırır, növbəni əvvəlcədən sıralayır və əsas çıxışı canlı yayımlayır.',
    'When queues build up at events, apply the three-lever model: increase processing lanes, reduce per-person processing time (pre-sort, pre-fill), and reduce the consequence of waiting (stream content, provide refreshments in queue).',
    'Tədbirlərdə növbələr artdıqda, üç qol modelini tətbiq edin: emal xətlərini artırın, adam başına emal vaxtını azaldın (əvvəlcədən sıralayın, əvvəlcədən doldurun) və gözləmənin nəticəsini azaldın (məzmunu yayımlayın, növbədə içki təqdim edin).'
)
ON CONFLICT (id) DO NOTHING;


-- EP15: Post-Event Performance Analysis and Improvement (Hard)
-- Framework: SHL UCF "Analysing" + Korn Ferry "Self-Development" + Deming PDCA cycle
-- IRT: a=1.9, b=0.9, c=0.18
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'e0000005-0000-0000-0000-000000000015',
    '55555555-5555-5555-5555-555555555555',
    'hard', 'mcq',
    'After a major product launch event, you receive mixed feedback: 92% satisfaction with content but only 58% satisfaction with logistics (registration wait, room transitions, parking). Senior leadership asks you to present an improvement plan for the next event. What is the MOST valuable analysis approach?',
    'Böyük məhsul təqdimat tədbirindən sonra qarışıq rəy alırsınız: məzmunla 92% məmnunluq, lakin logistika ilə (qeydiyyat gözləmə, otaq keçidləri, dayanacaq) yalnız 58% məmnunluq. Yüksək rəhbərlik sizdən növbəti tədbir üçün təkmilləşdirmə planı təqdim etməyinizi xahiş edir. Ən DƏYƏRLİ təhlil yanaşması hansıdır?',
    '[
        {"key": "A", "text_en": "Focus the plan on the logistics issues since content scored well — no need to analyze what worked", "text_az": "Məzmun yaxşı bal aldığına görə planı logistika məsələlərinə yönəldin — işləyəni təhlil etməyə ehtiyac yoxdur"},
        {"key": "B", "text_en": "Map each logistics failure to its root cause (understaffing, venue layout, vendor delay), quantify the impact in minutes lost per attendee, benchmark against industry standards, and propose solutions ranked by cost-effectiveness with projected improvement percentages", "text_az": "Hər logistika uğursuzluğunu kök səbəbinə uyğunlaşdırın (kifayət qədər kadr olmaması, məkan planı, təchizatçı gecikməsi), hər iştirakçı üçün itirilmiş dəqiqələrdə təsiri kəmiyyətləndirin, sənaye standartları ilə müqayisə edin, və xərc-effektivliyə görə sıralanmış həll yollarını proqnozlaşdırılan təkmilləşdirmə faizləri ilə təklif edin"},
        {"key": "C", "text_en": "Survey attendees again with more detailed questions to understand exactly what went wrong", "text_az": "Nəyin səhv getdiyini dəqiq anlamaq üçün daha ətraflı suallarla iştirakçıları yenidən sorğulayın"},
        {"key": "D", "text_en": "Hire a professional event management company for the next event — they will handle logistics", "text_az": "Növbəti tədbir üçün peşəkar tədbir idarəetmə şirkəti işə götürün — onlar logistikanı idarə edəcəklər"}
    ]',
    'B',
    1.9, 0.9, 0.18,
    'Post-event improvement requires root cause analysis, quantified impact, benchmarking, and cost-ranked solutions — not just fixing symptoms. Option A ignores learning from successes. Option C delays action for more data gathering. Option D outsources without understanding the problem. Option B provides a structured analysis framework that leadership can use to make informed investment decisions.',
    'Tədbir sonrası təkmilləşdirmə simptomların düzəldilməsini deyil, kök səbəb təhlili, kəmiyyətləndirilmiş təsir, müqayisə və xərcə görə sıralanmış həll yollarını tələb edir. A seçimi uğurlardan öyrənməni nəzərə almır. C seçimi daha çox məlumat toplamaq üçün hərəkəti gecikdirir. D seçimi problemi anlamadan kənar mənbəyə verir. B seçimi rəhbərliyin əsaslı investisiya qərarları qəbul etmək üçün istifadə edə biləcəyi strukturlaşdırılmış təhlil çərçivəsi təqdim edir.',
    'For post-event reviews, use the RIB framework: Root cause (why it happened), Impact (quantified in time/money/satisfaction), Benchmark (what is the industry standard). Solutions without root causes are patches. Root causes without quantified impact cannot be prioritized.',
    'Tədbir sonrası baxışlar üçün RİB çərçivəsindən istifadə edin: Kök səbəb (niyə baş verdi), Təsir (vaxt/pul/məmnunluqla kəmiyyətləndirilmiş), Müqayisə (sənaye standartı nədir). Kök səbəbi olmayan həll yolları yamaqlardir. Kəmiyyətləndirilmiş təsir olmadan kök səbəblər prioritetləşdirilə bilməz.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- TECH LITERACY (66666666-6666-6666-6666-666666666666)
-- Weight: 0.10 | 5 questions: 2 easy, 2 medium, 1 hard
-- =============================================================================


-- TL11: Evaluating Software Tool Security for Team Use (Easy)
-- Framework: OECD "Problem-Solving in Technology-Rich Environments" + NIST Cybersecurity basics
-- IRT: a=1.2, b=-1.1, c=0.12
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'd0000006-0000-0000-0000-000000000011',
    '66666666-6666-6666-6666-666666666666',
    'easy', 'mcq',
    'A colleague shares a free online tool for converting PDF invoices to spreadsheets. The tool asks you to upload client invoices containing names, amounts, and bank details. Your company has no policy on third-party tools. What should you do FIRST?',
    'Həmkarınız PDF fakturalarını cədvəllərə çevirmək üçün pulsuz onlayn alət paylaşır. Alət sizdən adlar, məbləğlər və bank təfərrüatları olan müştəri fakturalarını yükləməyinizi xahiş edir. Şirkətinizin üçüncü tərəf alətlər haqqında siyasəti yoxdur. Əvvəlcə nə etməlisiniz?',
    '[
        {"key": "A", "text_en": "Use it — the colleague already tried it and it works", "text_az": "İstifadə edin — həmkarınız artıq sınayıb və işləyir"},
        {"key": "B", "text_en": "Check the tool''s privacy policy, verify whether it stores uploaded data, and consult your IT or compliance team before uploading any client data", "text_az": "Alətin gizlilik siyasətini yoxlayın, yüklənmiş məlumatları saxlayıb-saxlamadığını yoxlayın, və hər hansı müştəri məlumatını yükləməzdən əvvəl İT və ya uyğunluq komandanıza müraciət edin"},
        {"key": "C", "text_en": "Upload a test file with fake data first to see if it works, then upload real invoices", "text_az": "Əvvəlcə işlədiyini görmək üçün saxta məlumatla sınaq faylı yükləyin, sonra real faturaları yükləyin"},
        {"key": "D", "text_en": "Avoid the tool and convert PDFs manually — better safe than sorry", "text_az": "Alətdən uzaq durun və PDF-ləri əl ilə çevirin — ehtiyatlı olmaq daha yaxşıdır"}
    ]',
    'B',
    1.2, -1.1, 0.12,
    'Tech literacy includes evaluating data security before adoption. Option A trusts a colleague''s experience over security assessment. Option C still exposes system metadata and usage patterns. Option D rejects efficiency without investigating. Option B follows the correct sequence: assess the tool''s data handling, then involve the appropriate authority.',
    'Texnologiya savadlılığı qəbuldan əvvəl məlumat təhlükəsizliyini qiymətləndirməyi əhatə edir. A seçimi təhlükəsizlik qiymətləndirməsi üzərində həmkarın təcrübəsinə etibar edir. C seçimi hələ də sistem metadata və istifadə nümunələrini açığa çıxarır. D seçimi araşdırmadan effektivliyi rədd edir. B seçimi düzgün ardıcıllığı izləyir: alətin məlumat emalını qiymətləndirin, sonra müvafiq səlahiyyətlini cəlb edin.',
    'Before using any new online tool with company data, ask three questions: Where is the data stored? Who can access it? Is there a delete/export option? If you cannot answer all three, do not upload sensitive data.',
    'Şirkət məlumatları ilə hər hansı yeni onlayn aləti istifadə etməzdən əvvəl üç sual soruşun: Məlumatlar harada saxlanılır? Kim daxil ola bilər? Silmə/ixrac seçimi varmı? Hər üçünə cavab verə bilmirsinizsə, həssas məlumatları yükləməyin.'
)
ON CONFLICT (id) DO NOTHING;


-- TL12: Using Data to Make Informed Decisions (Easy)
-- Framework: SHL UCF "Analysing" + OECD digital literacy framework
-- IRT: a=1.3, b=-0.7, c=0.14
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'd0000006-0000-0000-0000-000000000012',
    '66666666-6666-6666-6666-666666666666',
    'easy', 'mcq',
    'Your team uses a project management dashboard. You notice that Task completion rate shows 95% but Client satisfaction score shows 62%. Your manager asks: "Are we performing well?" What is the BEST response?',
    'Komandanız layihə idarəetmə panelidən istifadə edir. Tapşırıqların tamamlanma dərəcəsinin 95% göstərdiyini, lakin Müştəri məmnunluğu balının 62% olduğunu müşahidə edirsiniz. Meneceriniz soruşur: "Yaxşı işləyirik?" Ən YAXŞI cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Yes — 95% completion is excellent performance by any standard", "text_az": "Bəli — 95% tamamlanma hər standarta görə əla performansdır"},
        {"key": "B", "text_en": "The numbers suggest we are completing tasks on time but the output may not be meeting client expectations. We should investigate the gap between completion rate and satisfaction to find out if it is a quality, scope, or communication issue", "text_az": "Rəqəmlər göstərir ki, tapşırıqları vaxtında tamamlayırıq, lakin nəticə müştəri gözləntilərini qarşılamaya bilər. Keyfiyyət, əhatə dairəsi, yoxsa kommunikasiya problemi olduğunu öyrənmək üçün tamamlanma dərəcəsi və məmnunluq arasındakı fərqi araşdırmalıyıq"},
        {"key": "C", "text_en": "The satisfaction score is probably wrong — with 95% completion, clients should be happy", "text_az": "Məmnunluq balı yəqin ki, səhvdir — 95% tamamlanma ilə müştərilər razı olmalıdır"},
        {"key": "D", "text_en": "We need to focus only on the satisfaction score — completion rate does not matter if clients are unhappy", "text_az": "Yalnız məmnunluq balına diqqət yetirməliyik — müştərilər narazıdırsa tamamlanma dərəcəsinin əhəmiyyəti yoxdur"}
    ]',
    'B',
    1.3, -0.7, 0.14,
    'Tech literacy includes interpreting data critically, not taking single metrics at face value. Option A ignores the contradicting metric. Option C dismisses data that does not fit the narrative. Option D discards useful information. Option B identifies the gap between two metrics and proposes root-cause investigation — the correct analytical response.',
    'Texnologiya savadlılığı tək metrikləri zahirən qəbul etmək deyil, məlumatları tənqidi şəkildə şərh etməyi əhatə edir. A seçimi ziddiyyətli metriki nəzərə almır. C seçimi hekayəyə uyğun gəlməyən məlumatları rədd edir. D seçimi faydalı məlumatları atır. B seçimi iki metrik arasındakı fərqi müəyyənləşdirir və kök səbəb araşdırması təklif edir.',
    'When two dashboard metrics contradict each other, the gap itself is the insight. Never report one metric in isolation. Always ask: "What could explain the difference between these two numbers?"',
    'İki panel metriki bir-birinə zidd olduqda, fərqin özü fikir mənbəyidir. Heç vaxt bir metriki təcrid olunmuş şəkildə bildirməyin. Həmişə soruşun: "Bu iki rəqəm arasındakı fərqi nə izah edə bilər?"'
)
ON CONFLICT (id) DO NOTHING;


-- TL13: Automating Repetitive Workflows (Medium)
-- Framework: Korn Ferry "Tech Savvy" + OECD "ICT for Work" framework
-- IRT: a=1.5, b=-0.1, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'd0000006-0000-0000-0000-000000000013',
    '66666666-6666-6666-6666-666666666666',
    'medium', 'mcq',
    'Your team spends 3 hours every Monday morning manually copying data from email reports into a shared spreadsheet. There are 15 reports and the format is consistent. A colleague suggests "we should automate this." You have access to Google Workspace and basic no-code tools. What is the MOST effective first step?',
    'Komandanız hər bazar ertəsi səhər e-poçt hesabatlarından paylaşılan cədvələ məlumatları əl ilə kopyalamağa 3 saat sərf edir. 15 hesabat var və format ardıcıldır. Həmkarınız "bunu avtomatlaşdırmalıyıq" təklif edir. Google Workspace və əsas no-code alətlərə çıxışınız var. Ən effektiv ilk addım hansıdır?',
    '[
        {"key": "A", "text_en": "Build a full automation that processes all 15 reports — go big or go home", "text_az": "Bütün 15 hesabatı emal edən tam avtomatlaşdırma qurun — ya tam, ya heç"},
        {"key": "B", "text_en": "Start by automating 2-3 reports with the simplest format, validate accuracy against manual results, then scale to all 15 once the workflow is proven", "text_az": "Ən sadə formatlı 2-3 hesabatı avtomatlaşdırmaqla başlayın, dəqiqliyi əl ilə olan nəticələrlə yoxlayın, sonra iş axını sübut edildikdən sonra hamısına 15-ə genişləndirin"},
        {"key": "C", "text_en": "Hire a developer to build a custom solution — no-code tools are not reliable for business data", "text_az": "Xüsusi həll qurmaq üçün proqramçı işə götürün — no-code alətlər biznes məlumatları üçün etibarlı deyil"},
        {"key": "D", "text_en": "Keep the manual process but hire an intern to do it — it is only 3 hours per week", "text_az": "Əl ilə prosesi saxlayın, lakin bunu etmək üçün stajyer işə götürün — həftədə cəmi 3 saatdır"}
    ]',
    'B',
    1.5, -0.1, 0.15,
    'Effective automation starts small, validates, then scales. Option A risks building a full system that may fail on edge cases. Option C over-engineers a spreadsheet problem. Option D normalizes waste instead of solving it. Option B follows the pilot-validate-scale pattern: prove the approach works on a subset, then expand with confidence.',
    'Effektiv avtomatlaşdırma kiçik başlayır, doğrulayır, sonra genişlənir. A seçimi kənar hallarda uğursuz ola biləcək tam sistem qurma riski daşıyır. C seçimi cədvəl problemini həddən artıq mühəndisləşdirir. D seçimi həll etmək əvəzinə israfı normallaşdırır. B seçimi pilot-doğrulama-genişlənmə nümunəsini izləyir: yanaşmanın alt dəstdə işlədiyini sübut edin, sonra güvənlə genişləndirin.',
    'When automating any workflow, follow the 2-2-2 rule: automate 2 cases first, run for 2 weeks in parallel with manual, then scale if error rate is under 2%. This prevents automation from introducing more problems than it solves.',
    'Hər hansı iş axınını avtomatlaşdırarkən 2-2-2 qaydasına əməl edin: əvvəlcə 2 halı avtomatlaşdırın, əl ilə paralel 2 həftə işlədin, sonra səhv dərəcəsi 2%-dən azdırsa genişləndirin. Bu, avtomatlaşdırmanın həll etdiyindən daha çox problem yaratmasının qarşısını alır.'
)
ON CONFLICT (id) DO NOTHING;


-- TL14: Evaluating AI Tool Output for Business Decisions (Medium)
-- Framework: UNESCO AI Competency Framework + OECD "Critical Thinking with Digital Tools"
-- IRT: a=1.7, b=0.3, c=0.16
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'd0000006-0000-0000-0000-000000000014',
    '66666666-6666-6666-6666-666666666666',
    'medium', 'mcq',
    'You use an AI assistant to draft a competitive analysis report. The AI generates a convincing 5-page document with market share percentages, competitor revenue figures, and growth projections. Your director will present this to the board next week. What should you do BEFORE submitting the report?',
    'Rəqabət analizi hesabatının layihəsini yazmaq üçün AI köməkçisindən istifadə edirsiniz. AI bazar payı faizləri, rəqib gəlir rəqəmləri və böyümə proqnozları ilə inandırıcı 5 səhifəlik sənəd yaradır. Direktorunuz bunu gələn həftə İdarə Heyətinə təqdim edəcək. Hesabatı təqdim etməzdən ƏVVƏL nə etməlisiniz?',
    '[
        {"key": "A", "text_en": "Submit it — AI tools are trained on reliable data and the numbers look reasonable", "text_az": "Təqdim edin — AI alətləri etibarlı məlumatlar üzərində öyrədilib və rəqəmlər ağlabatan görünür"},
        {"key": "B", "text_en": "Verify every factual claim against primary sources (company filings, industry reports, press releases), flag any data points the AI may have fabricated, and add source citations for each statistic", "text_az": "Hər faktiki iddianı ilkin mənbələrə (şirkət hesabatları, sənaye hesabatları, mətbuat buraxılışları) qarşı yoxlayın, AI-nin uydurmuş ola biləcəyi hər hansı məlumat nöqtəsini qeyd edin, və hər statistika üçün mənbə istinadları əlavə edin"},
        {"key": "C", "text_en": "Ask another AI tool to verify the first AI''s output — cross-checking between AI tools is sufficient", "text_az": "Birinci AI-nin çıxışını yoxlamaq üçün başqa AI alətindən xahiş edin — AI alətləri arasında çarpaz yoxlama kifayətdir"},
        {"key": "D", "text_en": "Add a disclaimer that the report was AI-generated and that numbers should be independently verified", "text_az": "Hesabatın AI tərəfindən yaradıldığını və rəqəmlərin müstəqil yoxlanmalı olduğunu bildirən xəbərdarlıq əlavə edin"}
    ]',
    'B',
    1.7, 0.3, 0.16,
    'AI-generated content requires human verification of factual claims, especially quantitative data that will be presented to decision-makers. Option A trusts AI output uncritically. Option C uses the same technology with the same potential for fabrication. Option D shifts responsibility instead of solving the problem. Option B verifies each claim against authoritative sources and documents the evidence chain.',
    'AI tərəfindən yaradılmış məzmun, xüsusən qərar verənlərə təqdim olunacaq kəmiyyət məlumatları üçün faktiki iddiaların insan tərəfindən yoxlanmasını tələb edir. A seçimi AI çıxışına tənqidsiz etibar edir. C seçimi eyni uydurma potensialı olan eyni texnologiyanı istifadə edir. D seçimi problemi həll etmək əvəzinə məsuliyyəti köçürür. B seçimi hər iddianı nüfuzlu mənbələrə qarşı yoxlayır və sübut zəncirini sənədləşdirir.',
    'Treat AI-generated data the same way you treat a junior analyst''s first draft: the structure may be good, but every number needs a source. If you cannot find a source for a statistic, remove it or mark it as "unverified estimate."',
    'AI tərəfindən yaradılmış məlumatları kiçik analitikin ilk layihəsi kimi qəbul edin: struktur yaxşı ola bilər, lakin hər rəqəm mənbə tələb edir. Statistika üçün mənbə tapa bilmirsinizsə, onu silir və ya "yoxlanmamış təxmin" kimi qeyd edin.'
)
ON CONFLICT (id) DO NOTHING;


-- TL15: Managing a Data Breach Response (Hard)
-- Framework: NIST Cybersecurity Framework + Korn Ferry "Manages Complexity" + ISO 27001
-- IRT: a=2.0, b=0.8, c=0.19
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'd0000006-0000-0000-0000-000000000015',
    '66666666-6666-6666-6666-666666666666',
    'hard', 'mcq',
    'You discover that a shared team folder containing 200 client contact records was accidentally set to "Anyone with the link can view" instead of "Team only" for the past 2 weeks. There is no evidence anyone outside the team accessed it, but you cannot confirm. Your company handles EU client data. What is the CORRECT sequence of actions?',
    'Paylaşılan komanda qovluğunun 200 müştəri əlaqə qeydini ehtiva etdiyini və son 2 həftədir "Yalnız komanda" əvəzinə "Linkə sahib olan hər kəs baxa bilər" olaraq ayarlandığını kəşf edirsiniz. Komandadan kənar birinin daxil olduğuna dair sübut yoxdur, lakin təsdiqləyə bilməzsiniz. Şirkətiniz AB müştəri məlumatlarını emal edir. Düzgün hərəkət ardıcıllığı hansıdır?',
    '[
        {"key": "A", "text_en": "Change the permission to ''Team only'' immediately and move on — no one accessed it so no harm done", "text_az": "İcazəni dərhal ''Yalnız komanda''ya dəyişdirin və davam edin — heç kim daxil olmayıb, zərər yoxdur"},
        {"key": "B", "text_en": "1) Restrict access immediately, 2) check access logs for any external views, 3) report the incident to your data protection officer or compliance team, 4) document the timeline and scope for potential GDPR notification assessment, 5) implement access review controls to prevent recurrence", "text_az": "1) Dərhal girişi məhdudlaşdırın, 2) hər hansı xarici baxış üçün giriş qeydlərini yoxlayın, 3) hadisəni məlumatların müdafiəsi məmuruna və ya uyğunluq komandasına bildirin, 4) potensial GDPR bildiriş qiymətləndirməsi üçün zaman cədvəlini və əhatə dairəsini sənədləşdirin, 5) təkrarlanmanın qarşısını almaq üçün giriş nəzarəti tətbiq edin"},
        {"key": "C", "text_en": "Delete the folder to remove any trace of the exposure, then recreate it with correct permissions", "text_az": "İfşanın hər hansı izini silmək üçün qovluğu silin, sonra düzgün icazələrlə yenidən yaradın"},
        {"key": "D", "text_en": "Notify all 200 clients that their data may have been exposed — transparency is the best policy", "text_az": "Bütün 200 müştəriyə məlumatlarının ifşa oluna biləcəyini bildirin — şəffaflıq ən yaxşı siyasətdir"}
    ]',
    'B',
    2.0, 0.8, 0.19,
    'Data exposure incidents require a structured response: contain, assess, report, document, prevent. Option A ignores regulatory obligations. Option C destroys evidence needed for investigation. Option D may be premature before assessing actual exposure. Option B follows the NIST incident response framework: contain the breach, assess the scope, involve the appropriate authority, prepare for regulatory obligations, and implement preventive controls.',
    'Məlumat ifşası hadisələri strukturlaşdırılmış cavab tələb edir: ehtiva edin, qiymətləndirin, bildirin, sənədləşdirin, qarşısını alın. A seçimi tənzimləyici öhdəlikləri nəzərə almır. C seçimi araşdırma üçün lazım olan sübutları məhv edir. D seçimi faktiki ifşanı qiymətləndirməzdən əvvəl vaxtından əvvəl ola bilər. B seçimi NIST hadisə cavab çərçivəsini izləyir.',
    'For any data exposure, follow the CARD sequence: Contain (stop the exposure), Assess (check logs for actual access), Report (inform your DPO/compliance), Document (timeline for regulators). Never delete evidence, and never notify clients before your compliance team assesses the scope.',
    'Hər hansı məlumat ifşası üçün CARD ardıcıllığına əməl edin: Ehtiva edin (ifşanı dayandırın), Qiymətləndirin (faktiki giriş üçün qeydləri yoxlayın), Bildirin (DPO/uyğunluq komandanızı xəbərdar edin), Sənədləşdirin (tənzimləyicilər üçün zaman cədvəli). Heç vaxt sübutu silməyin və uyğunluq komandanız əhatə dairəsini qiymətləndirməzdən əvvəl müştəriləri heç vaxt xəbərdar etməyin.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- ADAPTABILITY (77777777-7777-7777-7777-777777777777)
-- Weight: 0.10 | 5 questions: 2 easy, 2 medium, 1 hard
-- =============================================================================


-- AD11: Adjusting Priorities When Requirements Change (Easy)
-- Framework: SHL UCF "Adapting and Responding to Change" + Korn Ferry "Nimble Learning"
-- IRT: a=1.2, b=-1.0, c=0.13
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'a0000007-0000-0000-0000-000000000011',
    '77777777-7777-7777-7777-777777777777',
    'easy', 'mcq',
    'You are halfway through writing a detailed project proposal when your manager calls to say the client has changed their requirements significantly. Most of your current work does not apply to the new scope. What do you do?',
    'Ətraflı layihə təklifini yazmağın yarısındasınız ki, meneceriniz zəng edib müştərinin tələblərini əhəmiyyətli dərəcədə dəyişdirdiyini bildirir. Hazırkı işinizin çoxu yeni əhatə dairəsinə uyğun gəlmir. Nə edirsiniz?',
    '[
        {"key": "A", "text_en": "Finish the current version first — you have already invested significant time in it", "text_az": "Əvvəlcə hazırkı versiyanı bitirin — artıq əhəmiyyətli vaxt sərf etmisiniz"},
        {"key": "B", "text_en": "Save the current work as a reference, identify which sections can be reused, start a new document aligned with the updated requirements, and set a revised timeline", "text_az": "Hazırkı işi istinad olaraq saxlayın, hansı bölmələrin yenidən istifadə oluna biləcəyini müəyyənləşdirin, yenilənmiş tələblərə uyğun yeni sənəd başladın, və yenidən işlənmiş cədvəl təyin edin"},
        {"key": "C", "text_en": "Push back on the client — changing requirements midway is unprofessional", "text_az": "Müştəriyə etiraz edin — tələbləri ortada dəyişdirmək qeyri-peşəkardır"},
        {"key": "D", "text_en": "Ask your manager to handle the rewrite since the change was not your decision", "text_az": "Dəyişiklik sizin qərarınız olmadığı üçün yenidən yazmağı menecerdən xahiş edin"}
    ]',
    'B',
    1.2, -1.0, 0.13,
    'Adaptability means pivoting without losing accumulated value. Option A falls into the sunk cost fallacy. Option C resists a client''s legitimate right to change scope. Option D abdicates responsibility. Option B preserves reusable work, resets to the new reality, and proactively manages the timeline impact.',
    'Uyğunlaşma yığılmış dəyəri itirmədən pivotlamaq deməkdir. A seçimi batıq xərc yanlışlığına düşür. C seçimi müştərinin əhatə dairəsini dəyişdirmək üçün qanuni hüququna müqavimət göstərir. D seçimi məsuliyyətdən imtina edir. B seçimi yenidən istifadə edilə bilən işi qoruyur, yeni reallığa sıfırlanır və cədvəl təsirini proaktiv idarə edir.',
    'When scope changes, do not restart from zero. Spend 10 minutes salvaging reusable sections from old work before starting the new version. Most pivots preserve 20-40% of prior effort if you look for it.',
    'Əhatə dairəsi dəyişdikdə, sıfırdan başlamayın. Yeni versiyanı başlamazdan əvvəl köhnə işdən yenidən istifadə edilə bilən bölmələri xilas etmək üçün 10 dəqiqə sərf edin. Əksər pivotlar axtarsanız əvvəlki səyin 20-40%-ni qoruyur.'
)
ON CONFLICT (id) DO NOTHING;


-- AD12: Learning a New Tool Under Time Pressure (Easy)
-- Framework: CCL "Learning Agility" + Korn Ferry "Nimble Learning"
-- IRT: a=1.3, b=-0.6, c=0.14
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'a0000007-0000-0000-0000-000000000012',
    '77777777-7777-7777-7777-777777777777',
    'easy', 'mcq',
    'Your team switches to a new project management tool starting Monday. You have never used it before. You have Friday afternoon free. What is the MOST effective way to prepare?',
    'Komandanız bazar ertəsindən etibarən yeni layihə idarəetmə alətinə keçir. Əvvəllər heç istifadə etməmisiniz. Cümə günortadan sonranız boşdur. Hazırlaşmağın ən effektiv yolu hansıdır?',
    '[
        {"key": "A", "text_en": "Read the entire user manual from start to finish", "text_az": "Bütün istifadəçi təlimatını əvvəldən sona oxuyun"},
        {"key": "B", "text_en": "Complete the tool''s quick-start tutorial, then recreate one of your current real tasks in the new system to test the workflow you will actually use on Monday", "text_az": "Alətin sürətli başlanğıc dərsini tamamlayın, sonra bazar ertəsi həqiqətən istifadə edəcəyiniz iş axınını sınamaq üçün hazırkı real tapşırıqlarınızdan birini yeni sistemdə yenidən yaradın"},
        {"key": "C", "text_en": "Wait until Monday and learn by doing — hands-on experience is the best teacher", "text_az": "Bazar ertəsinə qədər gözləyin və edərək öyrənin — praktiki təcrübə ən yaxşı müəllimdir"},
        {"key": "D", "text_en": "Watch YouTube reviews to understand if the tool is actually better than the old one", "text_az": "Alətin köhnəsindən həqiqətən daha yaxşı olub olmadığını anlamaq üçün YouTube rəylərini izləyin"}
    ]',
    'B',
    1.3, -0.6, 0.14,
    'Effective tool learning under time pressure combines structured introduction (quick-start) with applied practice on a real task. Option A is thorough but inefficient for a Friday afternoon. Option C delays preparation and risks Monday productivity. Option D evaluates instead of preparing. Option B ensures you arrive Monday with working muscle memory for your actual workflow.',
    'Vaxt təzyiqi altında effektiv alət öyrənməsi strukturlaşdırılmış girişi (sürətli başlanğıc) real tapşırıq üzərində tətbiqi praktika ilə birləşdirir. A seçimi hərtərəfli lakin cümə günortasından sonra üçün səmərəsizdir. C seçimi hazırlığı gecikdirir. D seçimi hazırlaşmaq əvəzinə qiymətləndirir. B seçimi bazar ertəsi faktiki iş axınınız üçün əzələ yaddaşı ilə gəlməyinizi təmin edir.',
    'When learning any new tool quickly, skip the manual. Do: 1) Quick-start tutorial (15 min), 2) Recreate one real task (30 min), 3) Note 3 things that confused you (5 min). This "tutorial + real task" combo is 3x more effective than reading documentation.',
    'Hər hansı yeni aləti tez öyrənərkən təlimatı atlayın. Edin: 1) Sürətli başlanğıc dərsi (15 dəq), 2) Bir real tapşırığı yenidən yaradın (30 dəq), 3) Sizi çaşdıran 3 şeyi qeyd edin (5 dəq). Bu "dərs + real tapşırıq" birləşməsi sənəd oxumaqdan 3 dəfə daha effektivdir.'
)
ON CONFLICT (id) DO NOTHING;


-- AD13: Adapting Leadership Style to a New Team Culture (Medium)
-- Framework: SHL UCF "Leading and Deciding" + Korn Ferry "Situational Adaptability"
-- IRT: a=1.6, b=0.0, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'a0000007-0000-0000-0000-000000000013',
    '77777777-7777-7777-7777-777777777777',
    'medium', 'mcq',
    'You have been transferred to lead a new team that operates very differently from your previous one. Your old team thrived on daily stand-ups, tight deadlines, and direct feedback. The new team values autonomy, weekly check-ins, and written communication. After one week of applying your old style, team morale is dropping. What do you do?',
    'Əvvəlki komandanızdan çox fərqli işləyən yeni komandaya rəhbərlik etmək üçün köçürülmüsünüz. Köhnə komandanız gündəlik stand-up-lar, sıx son tarixlər və birbaşa rəylə inkişaf edirdi. Yeni komanda muxtariyyəti, həftəlik yoxlamaları və yazılı kommunikasiyanı dəyərləndirir. Köhnə üslubunuzu bir həftə tətbiq etdikdən sonra komanda ruhu düşür. Nə edirsiniz?',
    '[
        {"key": "A", "text_en": "Continue with your style — the team needs time to adjust to effective management", "text_az": "Öz üslubunuzla davam edin — komandanın effektiv idarəetməyə uyğunlaşmağa vaxtı lazımdır"},
        {"key": "B", "text_en": "Meet with team members individually to understand their preferred working style, then adapt your management approach to match the team''s culture while gradually introducing elements from your leadership toolkit that add value", "text_az": "Onların üstünlük verdikləri iş üslubunu anlamaq üçün komanda üzvləri ilə fərdi görüşün, sonra idarəetmə yanaşmanızı komandanın mədəniyyətinə uyğunlaşdırın, eyni zamanda dəyər əlavə edən rəhbərlik alət dəstinizdən elementləri tədricən təqdim edin"},
        {"key": "C", "text_en": "Switch entirely to the team''s existing style — if it was working before you arrived, do not change it", "text_az": "Tamamilə komandanın mövcud üslubuna keçin — siz gəlməzdən əvvəl işləyirdisə, dəyişdirməyin"},
        {"key": "D", "text_en": "Ask HR to reassign you to a team that matches your management style", "text_az": "HR-dən sizi idarəetmə üslubunuza uyğun gələn komandaya yenidən təyin etməsini xahiş edin"}
    ]',
    'B',
    1.6, 0.0, 0.15,
    'Adaptability in leadership means adjusting your approach to the team, not forcing the team to adjust to you. Option A imposes your style and ignores the data (morale drop). Option C fully abandons your experience. Option D avoids the growth opportunity. Option B listens first, adapts the core approach, and strategically introduces improvements — the definition of situational leadership.',
    'Rəhbərlikdə uyğunlaşma komandanı sizə uyğunlaşmağa məcbur etmək deyil, yanaşmanızı komandaya uyğunlaşdırmaq deməkdir. A seçimi üslubunuzu tətbiq edir və məlumatı (ruh düşkünlüyünü) nəzərə almır. C seçimi təcrübənizi tamamilə tərk edir. D seçimi inkişaf fürsətindən qaçır. B seçimi əvvəlcə dinləyir, əsas yanaşmanı uyğunlaşdırır və strateji olaraq təkmilləşdirmələr təqdim edir.',
    'When joining a new team, apply the 30-60-90 rule: listen for 30 days, adapt for the next 30, then introduce changes in the final 30. Trying to change a team''s culture in week one signals that you value your preferences over their proven methods.',
    'Yeni komandaya qoşulduqda 30-60-90 qaydasını tətbiq edin: 30 gün dinləyin, növbəti 30 gün uyğunlaşın, sonra son 30 gündə dəyişiklikləri təqdim edin. Komandanın mədəniyyətini birinci həftədə dəyişdirməyə çalışmaq sizin üstünlüklərinizi onların sübut olunmuş metodlarından üstün tutduğunuz siqnalını verir.'
)
ON CONFLICT (id) DO NOTHING;


-- AD14: Recovering from a Failed Product Launch Strategy (Medium)
-- Framework: Korn Ferry "Resilience" + CCL "Results Orientation Under Ambiguity"
-- IRT: a=1.7, b=0.4, c=0.16
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'a0000007-0000-0000-0000-000000000014',
    '77777777-7777-7777-7777-777777777777',
    'medium', 'mcq',
    'Your team launched a new feature based on 3 months of market research. After 2 weeks, adoption is at 8% — far below the 40% target. User feedback suggests the feature solves a real problem but the onboarding flow is confusing. The next quarterly review is in 6 weeks. What is the MOST adaptive response?',
    'Komandanız 3 aylıq bazar araşdırmasına əsaslanaraq yeni xüsusiyyət buraxdı. 2 həftədən sonra qəbul 8%-dir — 40% hədəfdən çox aşağı. İstifadəçi rəyi xüsusiyyətin real problemi həll etdiyini, lakin onboarding axınının çaşdırıcı olduğunu göstərir. Növbəti rüblük baxışa 6 həftə qalıb. Ən uyğunlaşan cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Give the feature more time — 2 weeks is too early to judge, users need at least a month to discover it", "text_az": "Xüsusiyyətə daha çox vaxt verin — 2 həftə mühakimə etmək üçün çox erkəndir, istifadəçilərin onu kəşf etməsi üçün ən azı bir ay lazımdır"},
        {"key": "B", "text_en": "Run a rapid 1-week sprint to simplify the onboarding flow based on user feedback, A/B test the new flow against the original, and set a 3-week checkpoint with clear go/no-go criteria before the quarterly review", "text_az": "İstifadəçi rəyinə əsasən onboarding axınını sadələşdirmək üçün sürətli 1 həftəlik sprint keçirin, yeni axını orijinalla A/B test edin, və rüblük baxışdan əvvəl aydın davam/dayandır meyarları ilə 3 həftəlik yoxlama nöqtəsi təyin edin"},
        {"key": "C", "text_en": "Pull the feature and redesign it from scratch — the low adoption proves the approach was wrong", "text_az": "Xüsusiyyəti geri çəkin və sıfırdan yenidən dizayn edin — aşağı qəbul yanaşmanın səhv olduğunu sübut edir"},
        {"key": "D", "text_en": "Increase marketing spend to drive more users to the feature — awareness is the issue", "text_az": "Daha çox istifadəçini xüsusiyyətə yönləndirmək üçün marketinq xərclərini artırın — məlumatlılıq problemdir"}
    ]',
    'B',
    1.7, 0.4, 0.16,
    'Adaptability includes rapid iteration based on evidence, not waiting or overreacting. Option A ignores clear user feedback. Option C discards a product that solves a real problem. Option D addresses awareness when the problem is usability. Option B acts on the specific feedback (confusing onboarding), tests the fix empirically, and sets a data-driven decision point.',
    'Uyğunlaşma gözləmək və ya həddən artıq reaksiya vermək deyil, sübutlara əsaslanan sürətli iterasiyanı əhatə edir. A seçimi aydın istifadəçi rəyini nəzərə almır. C seçimi real problemi həll edən məhsulu atır. D seçimi problem istifadə edilə bilərlik olduqda məlumatlılığı ünvanlayır. B seçimi konkret rəyə əsasən hərəkət edir, düzəlişi empirik olaraq sınayır və məlumatlara əsaslanan qərar nöqtəsi təyin edir.',
    'When a launch underperforms, separate "wrong problem" from "right problem, wrong delivery." User feedback that says "I need this but cannot figure it out" means your solution is right but your onboarding is wrong. Fix the delivery before questioning the strategy.',
    'Buraxılış gözlənildiyindən aşağı performans göstərdikdə, "yanlış problem"i "doğru problem, yanlış çatdırılma"dan ayırın. "Buna ehtiyacım var amma anlamıram" deyən istifadəçi rəyi həllinizin düzgün, lakin onboarding-in səhv olduğunu bildirir. Strategiyanı sorğulamadan əvvəl çatdırılmanı düzəldin.'
)
ON CONFLICT (id) DO NOTHING;


-- AD15: Navigating Organizational Restructuring (Hard)
-- Framework: SHL UCF "Adapting and Responding to Change" + Korn Ferry "Manages Ambiguity"
-- IRT: a=2.1, b=1.1, c=0.19
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'a0000007-0000-0000-0000-000000000015',
    '77777777-7777-7777-7777-777777777777',
    'hard', 'mcq',
    'Your company announces a major restructuring: your department is merging with another, your direct manager is leaving, half of your team will report to a new leader you have never worked with, and your role may evolve into something broader. The transition period is 3 months with limited clarity on final structures. How do you navigate this period MOST effectively?',
    'Şirkətiniz böyük yenidənqurma elan edir: şöbəniz digəri ilə birləşir, birbaşa meneceriniz gedir, komandanızın yarısı heç vaxt birlikdə işləmədiyiniz yeni rəhbərə tabedir və rolunuz daha geniş bir şeyə çevrilə bilər. Keçid dövrü yekun strukturlar haqqında məhdud aydınlıqla 3 aydır. Bu dövrdə ən effektiv necə hərəkət edirsiniz?',
    '[
        {"key": "A", "text_en": "Wait for the final structure to be announced before making any moves — acting on incomplete information is risky", "text_az": "Hər hansı addım atmadan yekun strukturun elan olunmasını gözləyin — natamam məlumata əsasən hərəkət etmək risklidir"},
        {"key": "B", "text_en": "Proactively schedule meetings with the new leader to understand their priorities, document your team''s ongoing projects and key knowledge for continuity, strengthen relationships with colleagues from the merging department, and identify 2-3 ways your skills can add value in the expanded scope", "text_az": "Proaktiv olaraq yeni rəhbərlə onların prioritetlərini anlamaq üçün görüşlər planlaşdırın, davamlılıq üçün komandanızın davam edən layihələrini və əsas biliklərini sənədləşdirin, birləşən şöbənin həmkarları ilə münasibətləri gücləndir, və genişlənmiş əhatə dairəsində bacarıqlarınızın dəyər əlavə edə biləcəyi 2-3 yol müəyyənləşdirin"},
        {"key": "C", "text_en": "Start looking for roles in other departments — restructurings usually result in layoffs", "text_az": "Digər şöbələrdə rollar axtarmağa başlayın — yenidənqurmalar adətən ixtisarla nəticələnir"},
        {"key": "D", "text_en": "Focus only on your current work and perform as usual — if you do good work, the restructuring will not affect you", "text_az": "Yalnız hazırkı işinizə diqqət yetirin və həmişəki kimi çalışın — yaxşı iş görsəniz, yenidənqurma sizi təsir etməyəcək"}
    ]',
    'B',
    2.1, 1.1, 0.19,
    'Navigating organizational ambiguity requires proactive relationship building, knowledge preservation, and positioning — not waiting or retreating. Option A loses 3 months of positioning opportunity. Option C assumes the worst without evidence. Option D assumes good work alone protects you during structural change. Option B takes four parallel adaptive actions: build new relationships, preserve institutional knowledge, expand your network, and position your skills for the new reality.',
    'Təşkilati qeyri-müəyyənlikdə naviqasiya gözləmək və ya geri çəkilmək deyil, proaktiv münasibət qurmaq, bilik qorunması və mövqeləndirmə tələb edir. A seçimi 3 aylıq mövqeləndirmə fürsətini itirir. C seçimi sübutsuz ən pisini fərz edir. D seçimi yalnız yaxşı işin sizi struktur dəyişikliyi zamanı qoruyacağını fərz edir. B seçimi dörd paralel adaptiv hərəkət həyata keçirir.',
    'During restructuring, the professionals who thrive are those who build bridges before the new org chart is finalized. Schedule coffee chats with 3 people from the merging team, document everything your team knows (institutional knowledge is your leverage), and frame your skills in terms of the new structure''s goals.',
    'Yenidənqurma zamanı inkişaf edən peşəkarlar yeni təşkilat sxemi yekunlaşdırılmadan əvvəl körpülər quran insanlardır. Birləşən komandadan 3 nəfərlə qəhvə söhbətləri planlaşdırın, komandanızın bildikləri hər şeyi sənədləşdirin, və bacarıqlarınızı yeni strukturun məqsədləri baxımından çərçivələyin.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- EMPATHY & SAFEGUARDING (88888888-8888-8888-8888-888888888888)
-- Weight: 0.05 | 5 questions: 2 easy, 2 medium, 1 hard
-- =============================================================================


-- ES11: Recognizing and Responding to a Colleague Under Stress (Easy)
-- Framework: Korn Ferry "Compassion" + CCL "Self-Awareness" behavioral anchors
-- IRT: a=1.2, b=-1.2, c=0.12
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'f0000008-0000-0000-0000-000000000011',
    '88888888-8888-8888-8888-888888888888',
    'easy', 'mcq',
    'During a team lunch, you notice a usually talkative colleague has been quiet for days, declined two social invitations, and seems distracted during meetings. They have not mentioned any problems. What is the MOST appropriate response?',
    'Komanda naharı zamanı adətən danışqan olan həmkarınızın günlərdir sakit olduğunu, iki sosial dəvəti rədd etdiyini və iclaslar zamanı diqqətsiz göründüyünü müşahidə edirsiniz. Heç bir problem barədə danışmayıblar. Ən müvafiq cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Ask them directly in front of others at lunch: ''You have been really quiet — is everything okay?''", "text_az": "Naharda başqalarının qarşısında birbaşa soruşun: ''Çox sakit olmusan — hər şey qaydasındadır?''"},
        {"key": "B", "text_en": "Find a private moment to say: ''I have noticed you seem a bit different lately. No pressure to share, but I wanted you to know I am here if you want to talk''", "text_az": "Şəxsi bir an tapıb deyin: ''Son vaxtlar bir az fərqli göründüyünüzü hiss etdim. Paylaşmaq üçün heç bir təzyiq yoxdur, amma danışmaq istəsəniz burada olduğumu bilməyinizi istədim''"},
        {"key": "C", "text_en": "Report your observation to HR — they are trained to handle these situations", "text_az": "Müşahidənizi HR-ə bildirin — onlar bu vəziyyətləri idarə etmək üçün hazırlıqlıdırlar"},
        {"key": "D", "text_en": "Give them space — they will talk when they are ready", "text_az": "Onlara yer verin — hazır olduqlarında danışacaqlar"}
    ]',
    'B',
    1.2, -1.2, 0.12,
    'Empathetic support requires privacy, non-pressured openness, and genuine availability. Option A puts them on the spot publicly. Option C bypasses the human connection and may feel like surveillance. Option D assumes they will reach out — many people in distress do not. Option B offers a private, low-pressure check-in that respects boundaries while signaling genuine care.',
    'Empatik dəstək gizlilik, təzyiqsiz açıqlıq və həqiqi mövcudluq tələb edir. A seçimi onları ictimai olaraq çətin vəziyyətə qoyur. C seçimi insan əlaqəsini yan keçir və nəzarət kimi hiss edilə bilər. D seçimi onların müraciət edəcəyini fərz edir — sıxıntıda olan bir çox insan etmir. B seçimi sərhədlərə hörmət edən, eyni zamanda həqiqi qayğını siqnallaşdıran şəxsi, aşağı təzyiqli yoxlama təklif edir.',
    'When a colleague''s behavior changes, use the "notice, not diagnose" approach: name what you observed ("I noticed you seem quieter"), not what you think it means ("you seem depressed"). Leave the interpretation to them.',
    'Həmkarın davranışı dəyişdikdə, "diaqnoz qoymaq deyil, müşahidə etmək" yanaşmasından istifadə edin: müşahidə etdiyinizi adlandırın ("daha sakit göründüyünüzü hiss etdim"), nə demək olduğunu düşündüyünüzü deyil ("depressiyada görünürsünüz"). Şərhi onların özünə buraxın.'
)
ON CONFLICT (id) DO NOTHING;


-- ES12: Supporting a Team Member Facing Discrimination (Easy)
-- Framework: SHL UCF "Supporting and Co-operating" + Korn Ferry "Values Differences"
-- IRT: a=1.3, b=-0.8, c=0.13
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'f0000008-0000-0000-0000-000000000012',
    '88888888-8888-8888-8888-888888888888',
    'easy', 'mcq',
    'During a team brainstorm, you notice that a colleague from a minority background has their ideas repeatedly interrupted or dismissed by others. The same ideas, when restated by a different colleague moments later, receive enthusiastic support. What is the MOST effective response in the moment?',
    'Komanda beyin fırtınası zamanı azlıq mənşəli həmkarınızın fikirlərinin başqaları tərəfindən dəfələrlə kəsildiyini və ya rədd edildiyini müşahidə edirsiniz. Eyni fikirlər, bir an sonra fərqli bir həmkar tərəfindən yenidən ifadə edildikdə, şövqlü dəstək alır. Ən effektiv hazırkı cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Say nothing during the meeting but speak to the affected colleague privately afterward", "text_az": "İclas zamanı heç nə deməyin, lakin sonra təsirlənmiş həmkarla şəxsi olaraq danışın"},
        {"key": "B", "text_en": "In the meeting, redirect credit by saying: ''I want to highlight that [colleague] actually raised this same point a few minutes ago — [colleague], could you expand on your original idea?''", "text_az": "İclasda deyərək krediti yönləndirin: ''Qeyd etmək istəyirəm ki, [həmkar] əslində bir neçə dəqiqə əvvəl eyni fikri irəli sürmüşdü — [həmkar], orijinal fikrinizi genişləndirə bilərsinizmi?''"},
        {"key": "C", "text_en": "Call out the interrupting colleagues directly: ''You are being dismissive and that is not acceptable''", "text_az": "Kəsən həmkarları birbaşa çağırın: ''Siz rədd edici davranırsınız və bu qəbuledilməzdir''"},
        {"key": "D", "text_en": "Let it go — confronting it in the meeting will make everyone uncomfortable", "text_az": "Buraxın — iclasda üzləşmək hər kəsi narahat edəcək"}
    ]',
    'B',
    1.3, -0.8, 0.13,
    'Active allyship means intervening in the moment, not afterward. Option A acknowledges the problem but does not correct the group dynamic. Option C is confrontational and may escalate rather than redirect. Option D normalizes the pattern. Option B restores credit to the original contributor without accusing anyone, models inclusive behavior, and gives the affected colleague the floor.',
    'Aktiv müttəfiqlik sonradan deyil, o anda müdaxilə etmək deməkdir. A seçimi problemi etiraf edir, lakin qrup dinamikasını düzəltmir. C seçimi qarşıdurmadır və yönləndirmək əvəzinə eskalasiya edə bilər. D seçimi nümunəni normallaşdırır. B seçimi heç kəsi ittiham etmədən orijinal töhfəçiyə krediti qaytarır, inkluziv davranışı modelləşdirir, və təsirlənmiş həmkara söz verir.',
    'Practice "amplification": when someone''s idea is overlooked or restated by others, name the original contributor and redirect the conversation. This is a concrete, low-conflict allyship technique that changes group dynamics without confrontation.',
    '"Gücləndir" texnikasını məşq edin: birinin fikri nəzərə alınmadıqda və ya başqaları tərəfindən yenidən ifadə edildikdə, orijinal töhfəçini adlandırın və söhbəti yönləndirin. Bu, qarşıdurmadan qrup dinamikasını dəyişdirən konkret, aşağı konfliktli müttəfiqlik texnikasıdır.'
)
ON CONFLICT (id) DO NOTHING;


-- ES13: Balancing Empathy with Professional Boundaries (Medium)
-- Framework: Korn Ferry "Compassion" + SHL UCF "Supporting and Co-operating" + EAP referral norms
-- IRT: a=1.6, b=-0.1, c=0.15
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'f0000008-0000-0000-0000-000000000013',
    '88888888-8888-8888-8888-888888888888',
    'medium', 'mcq',
    'A team member confides in you that they are going through a difficult divorce. Over the next two weeks, they frequently come to your desk to talk about their personal situation — sometimes for 30-40 minutes. Your own work is falling behind. You genuinely care about them but cannot continue as their primary support. What is the MOST empathetic AND professional response?',
    'Komanda üzvü sizə çətin boşanma prosesindən keçdiyini etibar edir. Növbəti iki həftə ərzində tez-tez masanıza gəlib şəxsi vəziyyətləri barədə danışırlar — bəzən 30-40 dəqiqə. Öz işiniz geridə qalır. Onlara həqiqətən əhəmiyyət verirsiniz, lakin əsas dəstək kimi davam edə bilmirsiniz. Ən empatik VƏ peşəkar cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Start looking busy when they approach — they will get the hint without a difficult conversation", "text_az": "Yaxınlaşdıqda məşğul görünməyə başlayın — çətin söhbət olmadan anlayacaqlar"},
        {"key": "B", "text_en": "Have an honest private conversation: express that you care about them, acknowledge what they are going through, explain that you are not equipped to provide the level of support they need, and suggest the company''s employee assistance program or a professional counselor", "text_az": "Dürüst şəxsi söhbət edin: onlara əhəmiyyət verdiyinizi ifadə edin, keçirdiklərini etiraf edin, ehtiyac duyduqları dəstək səviyyəsini təmin etmək üçün təchiz olmadığınızı izah edin, və şirkətin işçi yardım proqramını və ya peşəkar məsləhətçini təklif edin"},
        {"key": "C", "text_en": "Tell them you need to focus on work and suggest they talk to HR instead", "text_az": "İşə diqqət yetirməli olduğunuzu söyləyin və əvəzinə HR ilə danışmağı təklif edin"},
        {"key": "D", "text_en": "Continue being available — their well-being is more important than your deadlines", "text_az": "Əlçatan olmağa davam edin — onların rifahı sizin son tarixlərinizdən daha vacibdir"}
    ]',
    'B',
    1.6, -0.1, 0.15,
    'Empathy includes knowing the limits of your support capacity and directing someone to appropriate resources — not withdrawing passively or sacrificing your own performance. Option A is avoidance. Option C is cold and transactional. Option D enables dependency and harms your work. Option B combines genuine care, honest boundary-setting, and a constructive referral to professional support.',
    'Empatiya passiv geri çəkilmək və ya öz performansınızı qurban vermək deyil, dəstək qabiliyyətinizin hədlərini bilmək və kimsəni müvafiq mənbələrə yönləndirməyi əhatə edir. A seçimi qaçınmadır. C seçimi soyuq və tranzaksiyadır. D seçimi asılılığı mümkün edir və işinizə zərər verir. B seçimi həqiqi qayğını, dürüst sərhəd qoymanı və peşəkar dəstəyə konstruktiv yönləndirməni birləşdirir.',
    'Supporting a colleague in crisis does not mean becoming their therapist. The most helpful thing you can do is: listen once, validate their feelings, and then connect them with someone who has the training and capacity to help long-term (EAP, counselor, support group).',
    'Böhrandakı həmkara dəstək olmaq onların terapevtinə çevrilmək demək deyil. Edə biləcəyiniz ən faydalı şey: bir dəfə dinləyin, hisslərini təsdiqləyin, sonra uzunmüddətli kömək etmək üçün hazırlığı və imkanı olan biri ilə əlaqələndirin (EAP, məsləhətçi, dəstək qrupu).'
)
ON CONFLICT (id) DO NOTHING;


-- ES14: Handling a Safeguarding Concern in a Professional Setting (Medium)
-- Framework: UK Safeguarding Adults Framework + Korn Ferry "Courage" + duty-of-care norms
-- IRT: a=1.8, b=0.3, c=0.16
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'f0000008-0000-0000-0000-000000000014',
    '88888888-8888-8888-8888-888888888888',
    'medium', 'mcq',
    'During a corporate training session you are facilitating, a participant privately tells you that their manager has been making comments that make them feel unsafe at work. They ask you not to tell anyone. You are not the participant''s manager or HR representative. What is the CORRECT response?',
    'Aparıcısı olduğunuz korporativ təlim sessiyası zamanı bir iştirakçı sizə şəxsi olaraq menecerinın iş yerində özlərini təhlükəsiz hiss etdirməyən şərhlər verdiyini bildirir. Sizdən heç kimə deməməyinizi xahiş edirlər. Siz iştirakçının meneceri və ya HR nümayəndəsi deyilsiniz. Düzgün cavab hansıdır?',
    '[
        {"key": "A", "text_en": "Keep their confidence — they asked you not to tell anyone and you should respect their wishes", "text_az": "Onların etibarını saxlayın — sizdən heç kimə deməməyinizi xahiş etdilər və arzularına hörmət etməlisiniz"},
        {"key": "B", "text_en": "Thank them for trusting you, explain that you have a duty of care and cannot promise full confidentiality when someone''s safety is involved, offer to accompany them to HR or the designated safeguarding lead, and document what was disclosed using their exact words", "text_az": "Etibar etdikləri üçün təşəkkür edin, birinin təhlükəsizliyi söz mövzusu olduqda tam gizlilik vəd edə bilməyəcəyinizə görə qayğı vəzifənizin olduğunu izah edin, onlara HR-ə və ya təyin olunmuş qoruma rəhbərinə müşayiət etməyi təklif edin, və açıqlanan məlumatı onların dəqiq sözlərindən istifadə edərək sənədləşdirin"},
        {"key": "C", "text_en": "Confront the manager directly to resolve the situation quickly", "text_az": "Vəziyyəti tez həll etmək üçün birbaşa menecerlə üzləşin"},
        {"key": "D", "text_en": "Advise them to document the comments and report to HR themselves — it is their responsibility", "text_az": "Onlara şərhləri sənədləşdirməyi və özlərinin HR-ə bildirməsini tövsiyə edin — bu onların məsuliyyətidir"}
    ]',
    'B',
    1.8, 0.3, 0.16,
    'Safeguarding supersedes confidentiality requests when safety is at stake. Option A prioritizes confidentiality over duty of care. Option C bypasses proper channels and could escalate the situation. Option D places the entire burden on the vulnerable person. Option B follows safeguarding best practice: acknowledge, explain the limits of confidentiality, offer to support through the process, and document accurately.',
    'Təhlükəsizlik söz mövzusu olduqda qoruma gizlilik xahişlərindən üstündür. A seçimi qayğı vəzifəsi üzərində gizliliyə üstünlük verir. C seçimi müvafiq kanalları yan keçir və vəziyyəti pisləşdirə bilər. D seçimi bütün yükü həssas insanın üzərinə qoyur. B seçimi qoruma ən yaxşı praktikasını izləyir: etiraf edin, gizliliyin həddlərini izah edin, proses boyunca dəstək təklif edin, və dəqiq sənədləşdirin.',
    'When someone discloses a safety concern: do not promise confidentiality you cannot keep. Instead say: "I take this seriously and I want to help you. I may need to involve [specific person/team] to ensure your safety. I will not share this more widely than necessary." This is honest, protective, and empowering.',
    'Kimsə təhlükəsizlik narahatlığı açıqladıqda: saxlaya bilmədiyiniz gizlilik vəd etməyin. Əvəzinə deyin: "Bunu ciddi qəbul edirəm və sizə kömək etmək istəyirəm. Təhlükəsizliyinizi təmin etmək üçün [konkret şəxs/komanda] ilə əlaqə saxlamaq lazım ola bilər. Bunu lazım olandan daha geniş paylaşmayacağam." Bu dürüst, qoruyucu və gücləndirir.'
)
ON CONFLICT (id) DO NOTHING;


-- ES15: Ethical Decision Under Pressure — Whistleblowing Dilemma (Hard)
-- Framework: CCL "Courage" + SHL UCF "Ethics and Values" + ISO 37002 Whistleblowing Management
-- IRT: a=2.2, b=1.2, c=0.20
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'f0000008-0000-0000-0000-000000000015',
    '88888888-8888-8888-8888-888888888888',
    'hard', 'mcq',
    'You discover that a senior colleague has been reporting fabricated client satisfaction scores to leadership for the past quarter. The inflated numbers were used to justify a team expansion and budget increase. The colleague is well-liked, has mentored you, and the company has no formal whistleblowing channel. Reporting this could damage your career. What do you do?',
    'Böyük bir həmkarın son rüb ərzində rəhbərliyə uydurma müştəri məmnuniyyəti balları bildirdiyini kəşf edirsiniz. Şişirdilmiş rəqəmlər komandanın genişlənməsini və büdcə artımını əsaslandırmaq üçün istifadə olunub. Həmkar sevilir, sizə mentorluq edib və şirkətin rəsmi xəbərdarlıq kanalı yoxdur. Bunu bildirmək karyeranıza zərər verə bilər. Nə edirsiniz?',
    '[
        {"key": "A", "text_en": "Confront the colleague privately and give them a chance to correct the numbers themselves", "text_az": "Həmkarla şəxsi olaraq üzləşin və rəqəmləri özlərinin düzəltmələri üçün şans verin"},
        {"key": "B", "text_en": "Document the evidence thoroughly, identify the most appropriate reporting path (ethics committee, legal, or a trusted senior leader outside the colleague''s chain), report with the documented evidence, and keep a personal record of the timeline", "text_az": "Sübutları hərtərəfli sənədləşdirin, ən uyğun bildirmə yolunu müəyyənləşdirin (etika komitəsi, hüquq və ya həmkarın zəncirindən kənar etibarlı böyük rəhbər), sənədləşdirilmiş sübutlarla bildirin, və zaman cədvəlinin şəxsi qeydini saxlayın"},
        {"key": "C", "text_en": "Anonymously leak the real numbers to leadership and let them investigate", "text_az": "Real rəqəmləri anonim olaraq rəhbərliyə sızdırın və araşdırmalarına icazə verin"},
        {"key": "D", "text_en": "Stay quiet — the inflated numbers benefit the whole team and exposing them will hurt everyone, including yourself", "text_az": "Susun — şişirdilmiş rəqəmlər bütün komandaya fayda verir və onları ifşa etmək siz daxil olmaqla hər kəsə zərər verəcək"}
    ]',
    'B',
    2.2, 1.2, 0.20,
    'Ethical courage requires acting on evidence through proper channels, even at personal cost. Option A relies on the person who committed the fraud to self-correct. Option C avoids accountability and may not trigger proper investigation. Option D is complicit. Option B follows ISO 37002 whistleblowing best practice: gather evidence, identify the appropriate authority, report formally, and protect yourself through documentation.',
    'Etik cəsarət şəxsi xərcdə olsa belə, müvafiq kanallar vasitəsilə sübutlara əsaslanaraq hərəkət etməyi tələb edir. A seçimi saxtakarlığı törədən şəxsin özünü düzəltməsinə etibar edir. C seçimi hesabatlılıqdan qaçır və düzgün araşdırma başlatmaya bilər. D seçimi şəriklikdir. B seçimi ISO 37002 xəbərdarlıq ən yaxşı praktikasını izləyir: sübutları toplayın, müvafiq orqanı müəyyənləşdirin, rəsmi olaraq bildirin və sənədləşdirmə vasitəsilə özünüzü qoruyun.',
    'When facing an ethical dilemma at work, follow the SAFE framework: Secure the evidence (screenshots, copies, timestamps), Assess the severity (who is harmed and how), Find the right authority (not necessarily your direct manager), Execute the report with documentation. Personal loyalty never outweighs institutional integrity.',
    'İş yerində etik dilemmaya düşdükdə SAFE çərçivəsinə əməl edin: Sübutları Təmin edin (ekran görüntüləri, nüsxələr, zaman damğaları), Ciddiliyi Qiymətləndirin (kim zərər görür və necə), Doğru orqanı Tapın (mütləq birbaşa meneceriniz olmaya bilər), Hesabatı sənədləşdirmə ilə İcra edin. Şəxsi sədaqət heç vaxt institusional bütövlükdən üstün tutulmur.'
)
ON CONFLICT (id) DO NOTHING;
