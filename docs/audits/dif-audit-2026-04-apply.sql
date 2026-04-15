-- DIF audit 2026-04 — ready-to-apply SQL for the 3 worst-case replacements.
--
-- WHY NOT YET APPLIED:
-- Updating a live question bank affects IRT calibration (irt_a/b/c are trained
-- on the OLD scenario text). CEO review recommended before running. Running
-- these will:
--   1. Soft-delete the 3 original items (is_active=FALSE, kept for audit).
--   2. Insert 3 replacement items with fresh UUIDs, needs_review=TRUE,
--      zeroed counters, NULL irt_a/b/c. Calibration restarts after ~30
--      completions on each new item.
--
-- Per Constitution law 3 + Epic E4 DIF audit doc in this folder.
--
-- HOW TO RUN (when approved):
--   psql "$SUPABASE_DIRECT_URL" -f docs/audits/dif-audit-2026-04-apply.sql
--
-- Or via Supabase MCP:
--   mcp execute_sql with this file's contents.

BEGIN;

-- ── E1. Soft-delete corporate-jargon English item ─────────────────────────
UPDATE public.questions
SET is_active = FALSE, needs_review = TRUE, updated_at = now()
WHERE id = 'e5000077-0000-4000-a000-000000000005';

-- ── E2. Soft-delete mixed-gender group-coded empathy item ─────────────────
UPDATE public.questions
SET is_active = FALSE, needs_review = TRUE, updated_at = now()
WHERE id = 'e5000012-0000-4000-a000-000000000004';

-- ── E3. Soft-delete Ctrl+Z keyboard-dependent item ────────────────────────
UPDATE public.questions
SET is_active = FALSE, needs_review = TRUE, updated_at = now()
WHERE id = '60000001-0000-0000-0000-000000000002';

-- ── E1-new. CEFR-B1 polite email request ──────────────────────────────────
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az, scenario_ru,
    options, correct_answer, cefr_level,
    irt_a, irt_b, irt_c, discrimination_index,
    times_shown, times_correct,
    is_sjt_reliability, lie_detector_flag, is_ai_generated,
    needs_review, is_active,
    feedback_en, feedback_az, development_tip_en, development_tip_az,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    '33333333-3333-3333-3333-333333333333',  -- english_proficiency
    'easy', 'mcq',
    $sen$A colleague sends you this message at 16:30 on Friday: "Hi, one quick thing — could you send me the meeting notes from Tuesday before you leave today? Thanks!" What should you do?$sen$,
    $saz$Bir həmkar size cümə günü saat 16:30-da belə bir mesaj göndərir: "Salam, kiçik bir şey — çərşənbə axşamı iclasın qeydlərini bu gün getməzdən əvvəl mənə göndərə bilərsiniz? Təşəkkürlər!" Nə edərdiniz?$saz$,
    NULL,
    '[{"key":"A","text_en":"Send the meeting notes before leaving today","text_az":"Bu gün getməzdən əvvəl iclasın qeydlərini göndərin","score":1.0},{"key":"B","text_en":"Reply that you will send them Monday","text_az":"Bazar ertəsi göndərəcəyinizi cavab verin","score":0.2},{"key":"C","text_en":"Ignore the message since it is not urgent","text_az":"Təcili olmadığı üçün mesajı nəzərə almayın","score":0.0},{"key":"D","text_en":"Ask what meeting they mean","text_az":"Hansı iclası nəzərdə tutduqlarını soruşun","score":0.5}]'::jsonb,
    'A', 'B1',
    NULL, NULL, NULL, NULL, 0, 0,
    FALSE, FALSE, FALSE,
    TRUE, TRUE,
    'Polite, reasonable request — respond and send before leaving.',
    'Nəzakətli, məntiqli xahiş — cavab ver və getməzdən əvvəl göndər.',
    'Watch for politeness markers ("Hi", "quick thing", "Thanks") — these signal low-stakes but time-bounded requests.',
    'Nəzakət markerlərinə diqqət yetirin — bunlar aşağı riskli, lakin vaxt məhdud istəkləri bildirir.',
    now(), now()
);

-- ── E2-new. Inclusive design under pressure, group-coding stripped ────────
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az, scenario_ru,
    options, correct_answer, cefr_level,
    irt_a, irt_b, irt_c, discrimination_index,
    times_shown, times_correct,
    is_sjt_reliability, lie_detector_flag, is_ai_generated,
    needs_review, is_active,
    feedback_en, feedback_az, development_tip_en, development_tip_az,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    '88888888-8888-8888-8888-888888888888',  -- empathy_safeguarding
    'medium', 'mcq',
    $sen$You are running a team-building workshop and one participant tells you privately that the planned physical-contact icebreaker makes them uncomfortable. They do not explain why. You need the full team aligned by the end of the session. What do you do?$sen$,
    $saz$Komanda qurma emalatxanası keçirirsiniz və bir iştirakçı şəxsən deyir ki, planlaşdırılan fiziki-təmaslı "buz sındırma" oyunu onu narahat edir. Səbəbini izah etmir. Sessiyanın sonuna qədər komandanın tam əhatəli olması lazımdır. Nə edərdiniz?$saz$,
    NULL,
    '[{"key":"A","text_en":"Tell them participation is mandatory — discomfort is part of growth","text_az":"İştirakın məcburi olduğunu söyləyin — narahatlıq inkişafın bir hissəsidir","score":0.1},{"key":"B","text_en":"Redesign the icebreaker so everyone can participate without physical contact","text_az":"Buz sındırma oyununu elə yenidən tərtib edin ki, hamı fiziki təmas olmadan iştirak edə bilsin","score":1.0},{"key":"C","text_en":"Excuse them from the icebreaker and run it for the rest of the group","text_az":"Onu buz sındırmadan azad edin və qalan qrup üçün keçirin","score":0.5},{"key":"D","text_en":"Ask what specifically would make them more comfortable, then adjust","text_az":"Onu daha rahat hansı şeyin edəcəyini soruşun, sonra uyğunlaşdırın","score":0.9}]'::jsonb,
    'B', NULL,
    NULL, NULL, NULL, NULL, 0, 0,
    FALSE, FALSE, FALSE,
    TRUE, TRUE,
    'Best answer: redesign for universal participation — protects the individual without excluding them.',
    'Ən yaxşı cavab: universal iştirak üçün yenidən tərtib — fərdi qorumaqla onu kənarlaşdırmır.',
    'Inclusive design beats accommodation-after-the-fact. Option D is close and agency-first — also strong.',
    'Əvvəlcədən əhatəli dizayn, sonradan uyğunlaşdırmadan yaxşıdır. D variantı yaxındır və təşəbbüs birincidir.',
    now(), now()
);

-- ── E3-new. Input-modality-neutral undo ───────────────────────────────────
INSERT INTO public.questions (
    id, competency_id, difficulty, type,
    scenario_en, scenario_az, scenario_ru,
    options, correct_answer, cefr_level,
    irt_a, irt_b, irt_c, discrimination_index,
    times_shown, times_correct,
    is_sjt_reliability, lie_detector_flag, is_ai_generated,
    needs_review, is_active,
    feedback_en, feedback_az, development_tip_en, development_tip_az,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    '66666666-6666-6666-6666-666666666666',  -- tech_literacy
    'easy', 'mcq',
    $sen$You accidentally delete a row containing 12 names from a shared Google Sheet. What do you do IMMEDIATELY?$sen$,
    $saz$Paylaşılan Google Sheet-də təsadüfən 12 adı olan bir sətri silirsiniz. DƏRHAL nə edirsiniz?$saz$,
    NULL,
    '[{"key":"A","text_en":"Close the browser tab and reopen the file","text_az":"Brauzer sekmesini bağlayıb faylı yenidən açın","score":0.2},{"key":"B","text_en":"Undo the deletion before doing anything else — via keyboard shortcut, the Edit menu, or mobile undo gesture","text_az":"Başqa bir şey etməzdən əvvəl silinməni geri alın — klavyatura qısa yolu, Redaktə menyusu və ya mobil geri alma jesti ilə","score":1.0},{"key":"C","text_en":"Notify the team and wait for someone more experienced to fix it","text_az":"Komandaya xəbər verin və daha təcrübəli birinin düzəltməsini gözləyin","score":0.5},{"key":"D","text_en":"Re-enter the 12 names manually from memory","text_az":"12 adı hafizədən əl ilə yenidən daxil edin","score":0.1}]'::jsonb,
    'B', NULL,
    NULL, NULL, NULL, NULL, 0, 0,
    FALSE, FALSE, FALSE,
    TRUE, TRUE,
    'Undo is the correct first action regardless of how you invoke it.',
    'Necə çağırdığınızdan asılı olmayaraq, geri alma düzgün ilk addımdır.',
    'Think "what is the right action" before "what buttons do I press".',
    '"Hansı düymələri basmalıyam" deyil, "düzgün addım nədir" deyə düşünün.',
    now(), now()
);

-- ── Audit breadcrumb ──────────────────────────────────────────────────────
INSERT INTO public.assessment_sessions_audit_log (occurred_at, actor, action, details)
SELECT now(), 'dif-audit-2026-04', 'item_replacement',
       jsonb_build_object(
         'replaced',
         ARRAY[
           'e5000077-0000-4000-a000-000000000005',
           'e5000012-0000-4000-a000-000000000004',
           '60000001-0000-0000-0000-000000000002'
         ],
         'doc', 'docs/audits/dif-audit-2026-04.md'
       )
WHERE EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema='public' AND table_name='assessment_sessions_audit_log'
);

COMMIT;
