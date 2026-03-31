-- =============================================================================
-- SEED: 5 MCQ questions for communication competency
-- Competency: communication (11111111-1111-1111-1111-111111111111, weight: 20%)
--
-- Gap identified: communication had only 3 MCQ questions (c0000001-...-001, -002, -005)
-- across all seed files. All other 7 competencies have 6+ MCQ questions each.
-- This migration brings communication to 8 MCQ questions total.
--
-- Research sources used for psychometric calibration:
--   • SHL Universal Competency Framework (UCF) — "Communicating Information" cluster:
--     oral communication, written communication, listening, influencing
--   • CCL (Center for Creative Leadership) Communication competency behavioral anchors
--   • Korn Ferry Competency Framework "Communicates Effectively" (Lominger FYI)
--   • Barrett-Lennard Relationship Inventory — active listening sub-scale
--   • Situational Judgement Test (SJT) design norms per Weekley & Ployhart (2006):
--     plausible distractors represent common low-proficiency behaviors
--
-- IRT parameter spread per question:
--   C6: easy    (b = -1.1)
--   C7: medium  (b = -0.2)
--   C8: medium  (b =  0.1)
--   C9: hard    (b =  0.8)
--   C10: hard   (b =  1.3)
--
-- UUID prefix: c0000001-0000-0000-0000-000000000006 through 000000000010
-- =============================================================================


-- =============================================================================
-- C6: MCQ — Upward Communication / Reporting Bad News (Easy)
-- Framework: CCL "Courage to Communicate" + SHL UCF oral communication anchor
-- IRT: a=1.3, b=-1.1, c=0.12
-- =============================================================================
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000006',
    '11111111-1111-1111-1111-111111111111',
    'easy', 'mcq',
    'You are a volunteer team lead. During setup you discover the printed name badges have a typo — 30 names are misspelled. The event starts in 90 minutes and the organizer has not noticed yet. What do you do FIRST?',
    'Siz könüllü komanda rəhbərsiniz. Qurulum zamanı çap edilmiş ad nişanlarında yazı xətası olduğunu kəşf edirsiniz — 30 ad səhv yazılmışdır. Tədbirə 90 dəqiqə qalıb və təşkilatçı hələ fərq etməyib. İlk olaraq nə edərdiniz?',
    '[
        {"key": "A", "text_en": "Wait to see if the organizer notices on their own", "text_az": "Təşkilatçının özünün fərq etməsini gözlə"},
        {"key": "B", "text_en": "Immediately inform the organizer with the exact problem and the time remaining to fix it", "text_az": "Dərhal təşkilatçıya dəqiq problemi və düzəltmək üçün qalan vaxtı bildirin"},
        {"key": "C", "text_en": "Try to fix the badges yourself without telling anyone", "text_az": "Heç kimə deməzdən nişanları özün düzəltməyə çalış"},
        {"key": "D", "text_en": "Tell your colleagues but not the organizer — it might embarrass them", "text_az": "Həmkarlarına söylə amma təşkilatçıya deyilmə — bu onları utandıra bilər"}
    ]',
    'B',
    1.3, -1.1, 0.12,
    'Effective upward communication means surfacing problems early with relevant facts (what, how many, how long). Waiting or bypassing the decision-maker removes their ability to act. Option B gives the organizer the information they need to solve the problem in time.',
    'Effektiv yuxarı kommunikasiya problemləri erkən, müvafiq faktlarla (nə, neçə, nə qədər vaxt) ortaya qoymaqdır. Gözləmək və ya qərar verəni aradan çıxarmaq onların hərəkət etmə qabiliyyətini ortadan qaldırır. B seçimi təşkilatçıya vaxtında problemin həlli üçün lazımi məlumatları verir.',
    'When reporting a problem upward, always lead with: what happened, scale of impact, and time available to fix it. Never bury the main issue in background details.',
    'Yuxarıya problem bildirərkən həmişə belə başlayın: nə baş verdi, təsirin miqyası və düzəltmək üçün mövcud vaxt. Əsas məsələni heç vaxt arxa fon detallarına gömməyin.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- C7: MCQ — Written Communication Clarity (Medium)
-- Framework: Korn Ferry "Written Communications" behavioral anchor (clear, concise, adapted to audience)
-- IRT: a=1.5, b=-0.2, c=0.14
-- =============================================================================
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000007',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'You need to send a WhatsApp message to 45 volunteer staff telling them that tomorrow''s 08:00 briefing has moved to 09:30 in Room C-7. Which version is BEST?',
    'Sabah saat 08:00-dakı brifinqin saat 09:30-a C-7 otağına köçürüldüyünü 45 könüllü işçiyə WhatsApp mesajı ilə bildirməlisiniz. Hansı variant ən YAXŞIdır?',
    '[
        {"key": "A", "text_en": "\"Hey team, just so you know, there has been a slight change to the morning briefing schedule, it is now going to be a little later than originally planned, so please be aware of that when you are getting ready tomorrow morning.\"", "text_az": "\"Salam komanda, sadəcə bildirirəm ki, səhər brifinq cədvəlində kiçik bir dəyişiklik var, indi ilkin planlaşdırılandan bir az gec olacaq, buna görə sabah səhər hazırlaşarkən bu barədə xəbərdar olun.\""},
        {"key": "B", "text_en": "\"UPDATE: Tomorrow''s briefing is NOW 09:30 in Room C-7 (was 08:00). Please confirm receipt with a thumbs-up.\"", "text_az": "\"YENİLƏMƏ: Sabahkı brifinq İNDİ saat 09:30-da C-7 otağında (əvvəlcə 08:00 idi). Zəhmət olmasa alındığını baş barmağı ilə təsdiqləyin.\""},
        {"key": "C", "text_en": "\"Changed. C7 930.\"", "text_az": "\"Dəyişdi. C7 930.\""},
        {"key": "D", "text_en": "\"Please note that due to some logistical considerations, the briefing originally scheduled for 08:00 has been rescheduled. The new time is 09:30. The location is also changing. We''ll be in Room C-7 tomorrow.\"", "text_az": "\"Nəzərinizə çatdırmaq istəyirəm ki, bəzi logistik mülahizələrə görə əvvəlcə 08:00-a planlaşdırılmış brifinq yenidən planlaşdırılıb. Yeni vaxt 09:30-dur. Yer də dəyişir. Sabah C-7 otağında olacağıq.\""}
    ]',
    'B',
    1.5, -0.2, 0.14,
    'Effective written communication for operational updates requires: the key change front-loaded, old vs. new values explicit, and a read-receipt mechanism. Option A is vague. Option C lacks critical details. Option D buries the information in justifications. Option B leads with the facts and closes the confirmation loop.',
    'Əməliyyat yeniləmələri üçün effektiv yazılı kommunikasiya tələb edir: əsas dəyişiklik önə çəkilsin, köhnə vs. yeni dəyərlər açıq göstərilsin, oxundu-təsdiq mexanizmi olsun. A seçimi qeyri-müəyyəndir. C seçimində kritik detallar yoxdur. D seçimi məlumatı əsaslandırmalara gömür. B seçimi faktlarla başlayır və təsdiq dövrəsini bağlayır.',
    'For operational messages: put the "what changed" in the first 5 words, use explicit before/after values, and always request a read-receipt for time-sensitive changes.',
    'Əməliyyat mesajları üçün: "nə dəyişdi"ni ilk 5 sözdə qoyun, açıq əvvəl/sonra dəyərləri istifadə edin və vaxt baxımından həssas dəyişikliklər üçün həmişə oxundu-təsdiq tələb edin.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- C8: MCQ — Audience Adaptation (Medium)
-- Framework: SHL UCF "Adapts communication style to audience" behavioral anchor
-- IRT: a=1.6, b=0.1, c=0.15
-- =============================================================================
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000008',
    '11111111-1111-1111-1111-111111111111',
    'medium', 'mcq',
    'You are explaining the volunteer check-in app to two different groups back to back: first, a group of university students (21-25 years old), then a group of senior community volunteers (60+ years old). How should you adjust your communication?',
    'Könüllü qeydiyyat tətbiqini ardalı iki qrupa izah edirsiniz: əvvəlcə universitet tələbə qrupu (21-25 yaş), sonra yaşlı icma könüllüləri qrupu (60+ yaş). Kommunikasiyanızı necə uyğunlaşdırmalısınız?',
    '[
        {"key": "A", "text_en": "Use exactly the same explanation for both — consistency ensures everyone gets the same information", "text_az": "Hər ikisi üçün eyni izahatı istifadə et — ardıcıllıq hər kəsin eyni məlumatı almasını təmin edir"},
        {"key": "B", "text_en": "Use technical app terminology with students; for seniors, slow your pace, use physical demos, and avoid jargon", "text_az": "Tələbələrlə texniki tətbiq terminlərindən istifadə et; yaşlılar üçün tempi azalt, fiziki nümayiş et, jarqondan çəkin"},
        {"key": "C", "text_en": "Skip the app explanation for seniors — they probably won''t use it anyway", "text_az": "Yaşlılar üçün tətbiq izahatını atla — çox güman ki, onlar bunu istifadə etməyəcəklər"},
        {"key": "D", "text_en": "Ask a younger volunteer to explain it to the seniors instead", "text_az": "Yaşlılara izah etmək üçün gənc könüllüdən kömək istə"}
    ]',
    'B',
    1.6, 0.1, 0.15,
    'Communication competence includes adapting style, pace, and vocabulary to the specific audience. Using identical communication for diverse groups is not consistency — it is indifference. Option B correctly identifies that seniors benefit from slower pace, hands-on demonstration, and plain language.',
    'Kommunikasiya səriştəsi üslubun, tempin və lüğətin konkret auditoriyaya uyğunlaşdırılmasını əhatə edir. Müxtəlif qruplara eyni kommunikasiyanı tətbiq etmək ardıcıllıq deyil — biganəlikdir. B seçimi yaşlıların daha yavaş temp, praktiki nümayiş və sadə dildən faydalandığını düzgün müəyyənləşdirir.',
    'Before any group briefing, spend 30 seconds asking: Who are they? What do they already know? What do they fear? These 3 questions define your communication style.',
    'İstənilən qrup brifinqindən əvvəl 30 saniyə ayırın: Onlar kimdir? Artıq nə bilirlər? Nədən qorxurlar? Bu 3 sual kommunikasiya üslubunuzu müəyyənləşdirir.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- C9: MCQ — Nonverbal Communication & Active Listening Under Stress (Hard)
-- Framework: Barrett-Lennard Relationship Inventory — empathic understanding sub-scale;
--            Egan's SOLER model (Squarely face, Open posture, Lean forward, Eye contact, Relax)
-- IRT: a=1.7, b=0.8, c=0.15
-- =============================================================================
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000009',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'mcq',
    'A distressed attendee approaches you mid-event, speaking rapidly and with tears in their eyes. They say: "Nobody is listening to me, I don''t know what to do." You have 3 minutes before your next assigned task. What is the MOST effective communication response?',
    'Tədbirın ortasında narahat bir iştirakçı sizə yaxınlaşır, sürətlə danışır və gözlərindən yaşlar süzülür. Deyirlər: "Heç kim məni dinləmir, nə edəcəyimi bilmirəm." Növbəti tapşırığınıza 3 dəqiqəniz var. Ən effektiv kommunikasiya cavabı hansıdır?',
    '[
        {"key": "A", "text_en": "Immediately redirect them to the help desk — you are not trained for this", "text_az": "Dərhal onları yardım masasına yönləndir — sən bunun üçün hazırlıqlı deyilsən"},
        {"key": "B", "text_en": "Stop, face them directly, make brief eye contact, say ''I hear you'' — then ask one focused question to understand the core issue before deciding next steps", "text_az": "Dur, onlara birbaşa bax, qısa göz əlaqəsi qur, ''Sizi eşidirəm'' de — sonra əsas problemi başa düşmək üçün növbəti addımları qərara almadan əvvəl bir hədəfli sual ver"},
        {"key": "C", "text_en": "Listen for 30 seconds while glancing at your watch so they know you have limited time", "text_az": "30 saniyə dinlə, ancaq saatına bax ki, vaxtının məhdud olduğunu bilsinlər"},
        {"key": "D", "text_en": "Summarize their situation back to them based on what you think they mean, then give them advice", "text_az": "Onların dediklərini özünüzün anladığınız şəkildə öz sözlərinizlə ümumiləşdirin, sonra məsləhət verin"}
    ]',
    'B',
    1.7, 0.8, 0.15,
    'When someone is emotionally distressed, effective communication begins with physical presence (stop, face them), minimal acknowledgment ("I hear you"), and a single clarifying question — not redirection, advice, or multi-tasking. Option C signals you are half-present. Option D assumes understanding before checking. Option A abandons the person. Option B demonstrates the listening foundation that all further support depends on.',
    'Kimsə emosional sıkıntı içindəykən effektiv kommunikasiya fiziki mövcudluqla (dur, üzünü çevir), minimal tanınmayla ("Sizi eşidirəm") və bir aydınlaşdırıcı sual ilə başlayır — yönləndirmə, məsləhət və ya çox işlə məşğul olmaqla deyil. C seçimi yarımçıq mövcud olduğunuzu göstərir. D seçimi yoxlamadan əvvəl anladığınızı fərz edir. A seçimi insanı tərk edir. B seçimi bütün növbəti dəstəyin bağlı olduğu dinləmə əsasını nümayiş etdirir.',
    'Practice Egan''s SOLER model: Squarely face the person, Open posture, Lean slightly forward, Eye contact (not staring), Relaxed body. These 5 cues signal genuine listening before you say a word.',
    'Egan''ın SOLER modelini məşq edin: insanla birbaşa qarşı durun, açıq bədən mövqeyi, azacıq irəliyə əyilin, göz kontaktı (baxışını dikməyin), rahat bədən. Bu 5 işarə siz bir söz deməzdən əvvəl həqiqi dinləməni bildirir.'
)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- C10: MCQ — Influencing Communication / Buy-in Under Disagreement (Hard)
-- Framework: Korn Ferry "Influences" competency + CCL peer influence behavioral anchors
-- IRT: a=1.8, b=1.3, c=0.20
-- =============================================================================
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az,
    options, correct_answer,
    irt_a, irt_b, irt_c,
    feedback_en, feedback_az,
    development_tip_en, development_tip_az
) VALUES (
    'c0000001-0000-0000-0000-000000000010',
    '11111111-1111-1111-1111-111111111111',
    'hard', 'mcq',
    'You propose a new volunteer coordination approach to your team. Three of your five teammates openly disagree, saying the old system works fine. You have no authority to force the change. What is the MOST effective communication strategy to gain buy-in?',
    'Komandanıza yeni bir könüllü koordinasiya yanaşması təklif edirsiniz. Beş komanda üzvünüzdən üçü açıqca razı deyil, köhnə sistemin yaxşı işlədiyini deyir. Dəyişikliyi məcbur etmək üçün heç bir səlahiyyətiniz yoxdur. Dəstək qazanmaq üçün ən effektiv kommunikasiya strategiyası hansıdır?',
    '[
        {"key": "A", "text_en": "Repeat your proposal more clearly and with more detail — they probably didn''t understand it the first time", "text_az": "Təklifinizi daha aydın və daha ətraflı təkrarlayın — yəqin ki, ilk dəfə başa düşmədilər"},
        {"key": "B", "text_en": "Ask each dissenter: ''What specific concern about the current proposal would need to change for you to support it?'' — then address those concerns directly", "text_az": "Hər razı olmayana soruşun: ''Mövcud təklifin hansı konkret narahatlığı dəyişdirilməlidir ki, siz onu dəstəkləyəsiniz?'' — sonra bu narahatlıqları birbaşa həll edin"},
        {"key": "C", "text_en": "Find the most influential teammate and convince them privately — the others will follow", "text_az": "Ən nüfuzlu komanda üzvünü tapın və onları xüsusi olaraq inandırın — qalanları ardınca gələcək"},
        {"key": "D", "text_en": "Agree to drop the proposal for now and bring it back when you have more authority", "text_az": "İndiliyin üçün təklifdən imtina etməyə razılaşın və daha çox səlahiyyətiniz olduqda geri qaytarın"}
    ]',
    'B',
    1.8, 1.3, 0.20,
    'Influencing without authority requires diagnosing resistance, not overcoming it by force or repetition. Option A (repeat louder) ignores that the resistance is not about clarity. Option C (lobby the leader) bypasses the dissenters and creates a brittle agreement. Option D (defer) surrenders the communication challenge. Option B directly surfaces the specific barrier each person holds, which is the precondition for any genuine persuasion.',
    'Səlahiyyətsiz təsir dirənişi diaqnostika etmək tələb edir, zorla və ya təkrarlama ilə deyil. A seçimi (daha güclü təkrarlayın) dirənişin aydınlıq haqqında olmadığını nəzərə almır. C seçimi (lideri lobbiləyin) razı olmayanları yan keçir və kövrək bir razılıq yaradır. D seçimi (təxirə salın) kommunikasiya problemindən imtina edir. B seçimi hər bir insanın saxladığı konkret maneəni birbaşa ortaya qoyur ki, bu da hər hansı həqiqi inandırmanın ön şərtidir.',
    'Before persuading anyone, diagnose their resistance: Is it about data? Trust? Process? Personal experience? Each type requires a different communication approach. Asking "what would need to change for you to support this?" is the fastest diagnostic tool.',
    'Kimisə inandırmadan əvvəl onların müqavimətini diaqnostika edin: məlumatla əlaqəlidirmi? Etibarla? Proseslə? Şəxsi təcrübəylə? Hər tip fərqli bir kommunikasiya yanaşması tələb edir. "Bunu dəstəkləmək üçün nəyin dəyişməsi lazımdır?" sualı ən sürətli diaqnostika vasitəsidir.'
)
ON CONFLICT (id) DO NOTHING;
