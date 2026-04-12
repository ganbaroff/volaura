-- Rename volunteer → professional/team member in badges and questions (prod data)
-- Positioning lock: VOLAURA is a verified professional talent platform

UPDATE public.badges SET
    name_en = REPLACE(name_en, 'Volunteer', 'Professional'),
    name_az = REPLACE(REPLACE(name_az, 'Könüllü', 'Peşəkar'), 'könüllü', 'peşəkar'),
    description_en = REPLACE(description_en, 'volunteer', 'professional'),
    description_az = REPLACE(REPLACE(description_az, 'könüllü', 'peşəkar'), 'Könüllü', 'Peşəkar')
WHERE name_en ILIKE '%volunteer%' OR name_az ILIKE '%könüllü%';

UPDATE public.questions SET
    scenario_en = REPLACE(REPLACE(scenario_en, 'volunteer', 'team member'), 'Volunteer', 'Team member'),
    scenario_az = REPLACE(REPLACE(scenario_az, 'könüllü', 'komanda üzvü'), 'Könüllü', 'Komanda üzvü')
WHERE scenario_en ILIKE '%volunteer%' OR scenario_az ILIKE '%könüllü%';

UPDATE public.questions SET
    options = REPLACE(REPLACE(options::text, 'volunteer', 'team member'), 'könüllü', 'komanda üzvü')::jsonb
WHERE options::text ILIKE '%volunteer%' OR options::text ILIKE '%könüllü%';

UPDATE public.questions SET
    expected_concepts = REPLACE(REPLACE(expected_concepts::text, 'volunteer', 'team member'), 'könüllü', 'komanda üzvü')::jsonb
WHERE expected_concepts IS NOT NULL
  AND (expected_concepts::text ILIKE '%volunteer%' OR expected_concepts::text ILIKE '%könüllü%');
