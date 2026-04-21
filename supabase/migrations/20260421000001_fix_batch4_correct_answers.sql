-- Fix batch4 MCQ questions missing correct_answer column.
-- Batch4 (20260415200000_seed_questions_batch4.sql) used score-based option format
-- but never set correct_answer — so every user answer scored 0.0 silently.
-- IRT 3PL uses binary 0/1 responses; we map score=1.0 option → correct_answer.
--
-- Affected competencies: empathy_safeguarding (4), reliability (5),
-- english_proficiency (5), leadership (5) — 19 questions total.

-- EMPATHY_SAFEGUARDING
UPDATE public.questions SET correct_answer = 'c' WHERE id = 'e5000012-0000-4000-a000-000000000001';
UPDATE public.questions SET correct_answer = 'b' WHERE id = 'e5000012-0000-4000-a000-000000000002';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000012-0000-4000-a000-000000000003';
UPDATE public.questions SET correct_answer = 'b' WHERE id = 'e5000012-0000-4000-a000-000000000004';

-- RELIABILITY
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000022-0000-4000-a000-000000000001';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000022-0000-4000-a000-000000000002';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000022-0000-4000-a000-000000000003';
UPDATE public.questions SET correct_answer = 'b' WHERE id = 'e5000022-0000-4000-a000-000000000004';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000022-0000-4000-a000-000000000005';

-- ENGLISH_PROFICIENCY
UPDATE public.questions SET correct_answer = 'c' WHERE id = 'e5000077-0000-4000-a000-000000000001';
UPDATE public.questions SET correct_answer = 'b' WHERE id = 'e5000077-0000-4000-a000-000000000002';
UPDATE public.questions SET correct_answer = 'b' WHERE id = 'e5000077-0000-4000-a000-000000000003';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000077-0000-4000-a000-000000000004';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000077-0000-4000-a000-000000000005';

-- LEADERSHIP
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000044-0000-4000-a000-000000000001';
UPDATE public.questions SET correct_answer = 'c' WHERE id = 'e5000044-0000-4000-a000-000000000002';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000044-0000-4000-a000-000000000003';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000044-0000-4000-a000-000000000004';
UPDATE public.questions SET correct_answer = 'a' WHERE id = 'e5000044-0000-4000-a000-000000000005';
