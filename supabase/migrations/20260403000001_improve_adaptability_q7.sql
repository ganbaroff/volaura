-- =============================================================================
-- IMPROVEMENT: Adaptability Q7 (Hard, open_ended)
-- ID: d0000001-0000-0000-0000-000000000007
--
-- Previous version had 3 separate crises across 3 days — overly compound,
-- hard to score consistently (assessor must evaluate 3 independent responses
-- in one answer blob). IRT parameter 2.4 discrimination is also unrealistic
-- for an ambiguous 3-part question.
--
-- New version: single real-time crisis with multiple cascading dimensions.
-- Tests adaptability across resource, communication, and calm-tone axes
-- in a single coherent scenario. AZ-market fit improved (no "3-day
-- international forum" assumption — single event day works at any size).
-- =============================================================================

UPDATE public.questions
SET
    scenario_en = 'You are team lead at a 200-person event. 90 minutes before the opening ceremony: your registration desk app crashes, 2 of your 6 volunteers call in sick, and the backup paper list is in the coordinator''s car (currently stuck in traffic). Describe how you manage the next 90 minutes.',
    scenario_az = 'Siz 200 nəfərlik bir tədbirə rəhbərlik edirsiniz. Açılış mərasimindən 90 dəqiqə əvvəl: qeydiyyat masasının tətbiqi çöküb, 6 könüllünizdən 2-si xəstə olduğunu bildirdi, ehtiyat kağız siyahısı isə koordinatorun maşınındadır (hal-hazırda trafik sıxlığındadır). Növbəti 90 dəqiqəni necə idarə edəcəyinizi izah edin.',
    feedback_en = 'Strong adaptability under compounding pressure requires: immediate manual fallback (don''t wait for the app), rapid resource rebalancing (cover sick volunteers by redistributing tasks), clear upward communication to coordinator, and calm tone that reassures your remaining team. The 90-minute window is recoverable — panicking is the only real failure.',
    feedback_az = 'Çoxlu gərginlik altında güclü uyğunlaşma tələb edir: dərhal əl ilə ehtiyat (tətbiqi gözləmə), sürətli resurs yenidən balanslaşdırması (xəstə könüllüləri tapşırıqları yenidən bölüşdürərək örtmək), koordinatora aydın yuxarı ünsiyyət, qalan komandanı arxayınlaşdıran sakit ton. 90 dəqiqəlik pəncərə bərpa oluna bilər — çaxnaşmaq yeganə real uğursuzluqdur.',
    development_tip_en = 'Build a personal "Day 0 checklist": offline backup always in your pocket, team contact list downloaded, escalation contact confirmed before every shift. Preparation is what adaptability runs on.',
    development_tip_az = '"Gün 0 yoxlama siyahısı" hazırlayın: oflayn ehtiyat həmişə cibinizdə, komanda əlaqə siyahısı endirilmiş, hər növbədən əvvəl eskalasiya əlaqəsi təsdiqlənmiş. Hazırlıq uyğunlaşmanın əsasıdır.',
    irt_a = 2.0,
    irt_b = 0.8
WHERE id = 'd0000001-0000-0000-0000-000000000007';
