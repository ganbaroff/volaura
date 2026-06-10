-- =============================================================================
-- Repair question texts broken by 20260413010000_rename_volunteer_to_professional.sql
--
-- That migration ran a blind REPLACE over public.questions
--   (volunteer -> team member, könüllü -> komanda üzvü), producing compound-noun
-- garbage wherever "volunteer" modified another noun or was used as a verb:
--   "volunteer team lead"  -> "team member team lead"
--   "signed up to volunteer" -> "signed up to team member"
--   "volunteer coordination app" -> "team member coordination app"
--
-- GROUND TRUTH: the 13 affected rows below were identified by direct prod query
-- (2026-06-10, project dwdgzfusjsobnixgyzjk) — marker patterns over scenario_en/az.
-- Earlier draft matched on full text replayed from seeds; that missed prod drift
-- (2 of 4 probed keys missed) and included 4 rows that never existed in prod
-- (seed.sql rows with non-hex ids never inserted). Hence: match on PRIMARY KEY
-- with a mangle-marker guard — exact, idempotent (second run matches nothing).
--
-- Scope: scenario_en + scenario_az only. Options/expected_concepts verified
-- unaffected (0 mangled doubles in prod). Texts hand-rewritten to professional
-- register, not re-replaced.
-- =============================================================================

-- communication ---------------------------------------------------------------

UPDATE public.questions SET
    scenario_en = 'You are a team lead. During setup you discover the printed name badges have a typo — 30 names are misspelled. The event starts in 90 minutes and the organizer has not noticed yet. What do you do FIRST?',
    scenario_az = 'Siz komanda rəhbərisiniz. Qurulum zamanı çap edilmiş ad nişanlarında yazı xətası olduğunu kəşf edirsiniz — 30 ad səhv yazılmışdır. Tədbirə 90 dəqiqə qalıb və təşkilatçı hələ fərq etməyib. İlk olaraq nə edərdiniz?'
WHERE id = 'c0000001-0000-0000-0000-000000000006'
  AND scenario_en LIKE '%team member team lead%';

UPDATE public.questions SET
    scenario_en = 'You need to send a WhatsApp message to 45 staff members telling them that tomorrow''s 08:00 briefing has moved to 09:30 in Room C-7. Which version is BEST?',
    scenario_az = 'Sabah saat 08:00-dakı brifinqin saat 09:30-a C-7 otağına köçürüldüyünü 45 işçiyə WhatsApp mesajı ilə bildirməlisiniz. Hansı variant ən YAXŞIdır?'
WHERE id = 'c0000001-0000-0000-0000-000000000007'
  AND scenario_en LIKE '%team member staff%';

UPDATE public.questions SET
    scenario_en = 'You are explaining the staff check-in app to two different groups back to back: first, a group of university students (21-25 years old), then a group of senior community members (60+ years old). How should you adjust your communication?',
    scenario_az = 'İşçilərin qeydiyyat tətbiqini ardıcıl olaraq iki fərqli qrupa izah edirsiniz: əvvəlcə universitet tələbələri qrupu (21-25 yaş), sonra yaşlı icma üzvləri qrupu (60+ yaş). Kommunikasiyanızı necə uyğunlaşdırmalısınız?'
WHERE id = 'c0000001-0000-0000-0000-000000000008'
  AND scenario_en LIKE '%team member check-in app%';

UPDATE public.questions SET
    scenario_en = 'You propose a new coordination approach to your team. Three of your five teammates openly disagree, saying the old system works fine. You have no authority to force the change. What is the MOST effective communication strategy to gain buy-in?',
    scenario_az = 'Komandanıza yeni bir koordinasiya yanaşması təklif edirsiniz. Beş komanda üzvünüzdən üçü açıqca razı deyil, köhnə sistemin yaxşı işlədiyini deyir. Dəyişikliyi məcbur etmək üçün heç bir səlahiyyətiniz yoxdur. Dəstək qazanmaq üçün ən effektiv kommunikasiya strategiyası hansıdır?'
WHERE id = 'c0000001-0000-0000-0000-000000000010'
  AND scenario_en LIKE '%team member coordination approach%';

-- tech_literacy ---------------------------------------------------------------

UPDATE public.questions SET
    scenario_en = 'You are updating a shared Google Sheet with staff attendance. You accidentally delete a row with 12 names. What do you do IMMEDIATELY?',
    scenario_az = 'Siz ortaq Google Cədvəlində işçilərin davamiyyət məlumatlarını yeniləyirsiniz. Təsadüfən 12 adın olduğu sətri silirsiniz. DƏRHAL nə edirsiniz?'
WHERE id = '60000001-0000-0000-0000-000000000002'
  AND scenario_en LIKE '%team member attendance%';

UPDATE public.questions SET
    scenario_en = 'After the event you notice the staff attendance spreadsheet — containing full names, phone numbers, and IDs — has been shared with "Anyone with the link can edit." What should you do?',
    scenario_az = 'Tədbirdən sonra fərq edirsiniz ki, tam adlar, telefon nömrələri və şəxsiyyət vəsiqəsi məlumatlarını ehtiva edən işçilərin iştirak cədvəli "Keçid olan hər kəs redaktə edə bilər" kimi paylaşılıb. Nə etməlisiniz?'
WHERE id = '60000001-0000-0000-0000-000000000006'
  AND scenario_en LIKE '%team member attendance spreadsheet%';

UPDATE public.questions SET
    scenario_en = 'Mid-event the staff coordination app crashes and walkie-talkie channel 2 is full of static. You are managing 6 sub-teams spread across 3 floors. How do you maintain coordination?',
    scenario_az = 'Tədbirin ortasında işçi koordinasiya tətbiqi çökür və telsiz kanalı 2 statiklə doludur. Siz 3 mərtəbəyə yayılmış 6 alt komandanı idarə edirsiniz. Koordinasiyanı necə qoruyarsınız?'
WHERE id = '60000001-0000-0000-0000-000000000008'
  AND scenario_en LIKE '%team member coordination app%';

UPDATE public.questions SET
    scenario_en = 'You are maintaining a Google Sheet tracking 150 staff members. Column B has their names, Column C has "Present" or "Absent." Your coordinator asks for a quick count of how many are present. Describe exactly what you would type or do.',
    scenario_az = 'Siz 150 işçini izləyən Google Cədvəlini idarə edirsiniz. B sütununda işçilərin adları, C sütununda "Mövcud" və ya "Yoxdur" var. Koordinatorunuz neçə nəfərin mövcud olduğunu soruşur. Nə yazacağınızı və ya nə edəcəyinizi dəqiq izah edin.'
WHERE id = '60000001-0000-0000-0000-000000000009'
  AND scenario_en LIKE '%150 team members%';

-- adaptability ----------------------------------------------------------------

UPDATE public.questions SET
    scenario_en = 'During a 3-day international forum: Day 1 — the keynote room floods; Day 2 — 40% of your staff calls in sick; Day 3 — the event software crashes mid-session. You were team lead throughout. Describe how you adapted each day.',
    scenario_az = '3 günlük beynəlxalq forumda: 1-ci gün — əsas natiq otağını su basır; 2-ci gün — işçilərinizin 40%-i xəstəlik bildirir; 3-cü gün — tədbir proqramı sessiya zamanı çökür. Bütün bu müddət ərzində komanda rəhbəri idiniz. Hər gün necə uyğunlaşdığınızı izah edin.'
WHERE id = 'd0000001-0000-0000-0000-000000000007'
  AND scenario_en LIKE '%team member team calls%';

UPDATE public.questions SET
    scenario_en = 'Your shift officially ends at 18:00. At 17:45 a major incident occurs — a key team leader is injured and cannot continue. You have dinner plans at 19:00 that you cannot easily cancel. Describe how you navigate this situation.',
    scenario_az = 'Növbəniz rəsmi olaraq 18:00-da bitir. 17:45-də böyük bir hadisə baş verir — əsas komanda lideri yaralanır və davam edə bilmir. Saat 19:00-da asanlıqla ləğv edə bilmədiyiniz nahar planlarınız var. Bu vəziyyəti necə idarə edəcəyinizi izah edin.'
WHERE id = 'd0000001-0000-0000-0000-000000000010'
  AND scenario_en LIKE '%team member team leader%';

-- reliability -----------------------------------------------------------------

UPDATE public.questions SET
    scenario_en = 'You signed up to work the registration desk at a cultural festival from 8am to 2pm. On the morning of the event, you wake up feeling slightly tired but not ill. What do you do?',
    scenario_az = 'Siz bir mədəniyyət festivalının qeydiyyat masasında saat 08:00-dan 14:00-a kimi işləməyə yazılmısınız. Tədbir günü səhər bir az yorğun oyanırsınız, lakin xəstə deyilsiniz. Nə edirsiniz?'
WHERE id = '20000001-0000-0000-0000-000000000001'
  AND scenario_en LIKE '%signed up to team member%';

UPDATE public.questions SET
    scenario_en = 'Your team lead asked you to submit your availability form by Friday. It is Thursday evening and you have not filled it out yet. What is the most responsible action?',
    scenario_az = 'Komanda lideriniz sizdən cümə gününə qədər mövcudluq formanızı təqdim etməyinizi istədi. İndi cümə axşamı axşamıdır və formanı hələ doldurmamısınız. Ən məsuliyyətli hərəkət nədir?'
WHERE id = '20000001-0000-0000-0000-000000000002'
  AND scenario_en LIKE '%team member team lead asked%';

UPDATE public.questions SET
    scenario_en = 'You are the senior staff lead for an accreditation desk at a major summit. Two hours before opening, the badge-printing system is down and your technical contact is unreachable. 300 delegates expected. Describe your full response plan.',
    scenario_az = 'Siz sammitdə akkreditasiya masasının baş işçi rəhbərisiniz. Açılışdan iki saat əvvəl nişan çap sistemi işləmir və texniki əlaqə şəxsinizə çata bilmirsiniz. 300 nümayəndə gözlənilir. Tam cavab planınızı təsvir edin.'
WHERE id = '20000001-0000-0000-0000-000000000009'
  AND scenario_en LIKE '%lead team member%';

-- End: 13 rows repaired (4 communication, 4 tech_literacy, 2 adaptability, 3 reliability).
