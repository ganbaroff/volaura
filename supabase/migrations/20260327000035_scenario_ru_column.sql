-- Migration 000035: scenario_ru
-- Adds Russian locale for questions (nullable — fallback to scenario_en if NULL)
-- Required for CIS expansion (7K contacts in activation wave)

ALTER TABLE public.questions
ADD COLUMN IF NOT EXISTS scenario_ru TEXT;

-- Index to quickly find untranslated questions (for batch translation script)
CREATE INDEX IF NOT EXISTS idx_questions_no_ru
ON public.questions(id)
WHERE scenario_ru IS NULL;

COMMENT ON COLUMN public.questions.scenario_ru IS
  'Russian scenario text. NULL = use scenario_en as fallback. '
  'Fill via scripts/translate_ru.py before activation wave.';
