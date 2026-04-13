-- Batch 4: Fill competencies with <15 questions to enable CAT convergence
-- empathy_safeguarding: +4 (11→15), reliability: +5 (10→15),
-- english_proficiency: +5 (10→15), leadership: +5 (10→15)
--
-- Competency UUIDs:
--   empathy_safeguarding = 88888888-8888-8888-8888-888888888888
--   reliability          = 22222222-2222-2222-2222-222222222222
--   english_proficiency  = 77777777-7777-7777-7777-777777777777
--   leadership           = 44444444-4444-4444-4444-444444444444

-- ═══════════════════════════════════════════════════════════════
-- EMPATHY_SAFEGUARDING (+4 questions → 15 total)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO public.questions (id, competency_id, question_type, scenario_en, scenario_az, options, expected_concepts, irt_a, irt_b, irt_c, is_active) VALUES

('e5000012-0000-4000-a000-000000000001', '88888888-8888-8888-8888-888888888888', 'mcq',
'A participant in your workshop breaks down crying after a group exercise about personal strengths. Other participants look uncomfortable. What do you do FIRST?',
'Seminarınızda bir iştirakçı şəxsi güclü tərəflər haqqında qrup məşqindən sonra ağlamağa başlayır. Digər iştirakçılar narahat görünür. İlk olaraq nə edirsiniz?',
'[{"id":"a","text":"Pause the session and ask the participant to step outside with you","score":0.9},{"id":"b","text":"Continue the exercise to avoid drawing more attention","score":0.2},{"id":"c","text":"Ask the group to take a 5-minute break while you check in privately","score":1.0},{"id":"d","text":"Tell the participant it is okay and move on quickly","score":0.4}]',
'["emotional_safety","group_dynamics","de-escalation","privacy"]',
1.6, 0.3, 0.2, true),

('e5000012-0000-4000-a000-000000000002', '88888888-8888-8888-8888-888888888888', 'mcq',
'You notice that a junior team member has been unusually quiet in meetings for 2 weeks. Their work quality is unchanged. What is the MOST empathetic response?',
'Komanda üzvünün 2 həftədir görüşlərdə qeyri-adi dərəcədə sakit olduğunu görürsünüz. İş keyfiyyəti dəyişməyib. Ən empatik cavab nədir?',
'[{"id":"a","text":"Raise it in the next team meeting so everyone can support them","score":0.1},{"id":"b","text":"Send a private message: I noticed you seem quieter lately — is everything okay?","score":1.0},{"id":"c","text":"Wait until their work quality drops before intervening","score":0.2},{"id":"d","text":"Ask their manager to check on them","score":0.5}]',
'["observation","private_communication","non-judgment","proactive_care"]',
1.4, -0.5, 0.2, true),

('e5000012-0000-4000-a000-000000000003', '88888888-8888-8888-8888-888888888888', 'mcq',
'During a feedback session, a colleague says "I feel like nobody values my contributions." You are the facilitator. What is the BEST response?',
'Geri bildirim sessiyasında bir həmkar deyir ki "heç kimin mənim töhfələrimi qiymətləndirmədiyini hiss edirəm." Siz fasilitatorusunuz. Ən yaxşı cavab nədir?',
'[{"id":"a","text":"Acknowledge the feeling, then ask the group for specific examples of their contributions","score":1.0},{"id":"b","text":"Explain that everyone contributes equally","score":0.2},{"id":"c","text":"Move on to avoid making the situation awkward","score":0.1},{"id":"d","text":"Suggest they talk to HR about it","score":0.3}]',
'["active_listening","validation","constructive_redirection","psychological_safety"]',
1.5, 0.0, 0.2, true),

('e5000012-0000-4000-a000-000000000004', '88888888-8888-8888-8888-888888888888', 'mcq',
'A volunteer from a conservative cultural background expresses discomfort with a mixed-gender team activity. You need all team members to participate. What do you do?',
'Mühafizəkar mədəni mühitdən olan könüllü qarışıq cinsli komanda fəaliyyətindən narahatlığını bildirir. Bütün komanda üzvlərinin iştirakına ehtiyacınız var. Nə edirsiniz?',
'[{"id":"a","text":"Explain that participation is mandatory and everyone must adapt","score":0.2},{"id":"b","text":"Redesign the activity to offer parallel tracks that achieve the same goal","score":1.0},{"id":"c","text":"Excuse them from the activity entirely","score":0.3},{"id":"d","text":"Ask them to try it first and see if they feel comfortable","score":0.6}]',
'["cultural_sensitivity","inclusive_design","goal_preservation","accommodation"]',
1.7, 0.5, 0.2, true);

-- ═══════════════════════════════════════════════════════════════
-- RELIABILITY (+5 questions → 15 total)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO public.questions (id, competency_id, question_type, scenario_en, scenario_az, options, expected_concepts, irt_a, irt_b, irt_c, is_active) VALUES

('e5000022-0000-4000-a000-000000000001', '22222222-2222-2222-2222-222222222222', 'mcq',
'You committed to delivering a report by Friday. On Wednesday, you realize you cannot finish on time due to unexpected data issues. What do you do?',
'Cümə gününə hesabat təqdim etməyi öhdəsinə götürmüsünüz. Çərşənbə günü gözlənilməz data problemləri səbəbindən vaxtında bitirə bilməyəcəyinizi başa düşürsünüz. Nə edirsiniz?',
'[{"id":"a","text":"Notify the stakeholder immediately, explain the issue, propose a new deadline","score":1.0},{"id":"b","text":"Work overtime to deliver on time regardless of quality","score":0.4},{"id":"c","text":"Wait until Friday and explain then","score":0.1},{"id":"d","text":"Deliver a partial report on Friday without mentioning the gaps","score":0.2}]',
'["proactive_communication","transparency","deadline_management","stakeholder_trust"]',
1.5, -0.3, 0.2, true),

('e5000022-0000-4000-a000-000000000002', '22222222-2222-2222-2222-222222222222', 'mcq',
'Your team relies on you to run a weekly status meeting. You have a personal appointment that conflicts with next week meeting. What is the MOST reliable approach?',
'Komandanız həftəlik status görüşünü keçirməyinizə arxalanır. Növbəti həftəki görüşlə üst-üstə düşən şəxsi görüşünüz var. Ən etibarlı yanaşma nədir?',
'[{"id":"a","text":"Find a substitute facilitator, brief them on the agenda, and inform the team in advance","score":1.0},{"id":"b","text":"Cancel the meeting for that week","score":0.2},{"id":"c","text":"Ask someone to take notes and review later","score":0.5},{"id":"d","text":"Attend the meeting remotely even if distracted","score":0.4}]',
'["delegation","preparation","continuity","responsibility"]',
1.3, -0.5, 0.2, true),

('e5000022-0000-4000-a000-000000000003', '22222222-2222-2222-2222-222222222222', 'mcq',
'You discover a minor error in a report you submitted last week. Nobody has noticed it yet. The error does not change the conclusion. What do you do?',
'Keçən həftə təqdim etdiyiniz hesabatda kiçik bir xəta kəşf edirsiniz. Heç kim hələ fərq etməyib. Xəta nəticəni dəyişmir. Nə edirsiniz?',
'[{"id":"a","text":"Correct it and send an updated version with a brief note explaining the change","score":1.0},{"id":"b","text":"Leave it since the conclusion is unchanged","score":0.2},{"id":"c","text":"Fix it silently in the shared drive","score":0.4},{"id":"d","text":"Wait to see if anyone notices","score":0.1}]',
'["integrity","proactive_correction","transparency","quality_standards"]',
1.6, 0.2, 0.2, true),

('e5000022-0000-4000-a000-000000000004', '22222222-2222-2222-2222-222222222222', 'mcq',
'A colleague asks you to cover their shift tomorrow. You already have plans but could technically rearrange them. You have covered for this person 3 times this month. What do you say?',
'Bir həmkarınız sabah növbəsini əvəz etməyinizi xahiş edir. Artıq planlarınız var amma texniki olaraq dəyişə bilərsiniz. Bu ay bu şəxsi 3 dəfə əvəz etmisiniz. Nə deyirsiniz?',
'[{"id":"a","text":"Agree again to maintain the relationship","score":0.3},{"id":"b","text":"Decline clearly and suggest they build a broader coverage rotation","score":1.0},{"id":"c","text":"Agree but express frustration about the pattern","score":0.4},{"id":"d","text":"Ignore the message","score":0.1}]',
'["boundary_setting","sustainable_reliability","constructive_feedback","self_advocacy"]',
1.4, 0.7, 0.2, true),

('e5000022-0000-4000-a000-000000000005', '22222222-2222-2222-2222-222222222222', 'mcq',
'You are managing 3 concurrent projects. Project A deadline moved up by a week. You cannot deliver all three on time. What is the MOST reliable way to handle this?',
'3 paralel layihəni idarə edirsiniz. A layihəsinin son tarixi 1 həftə əvvələ çəkildi. Hər üçünü vaxtında təhvil verə bilməzsiniz. Bunu ən etibarlı şəkildə necə idarə edirsiniz?',
'[{"id":"a","text":"Triage: negotiate scope reduction on the lowest-priority project and communicate revised timelines for all three","score":1.0},{"id":"b","text":"Work 16-hour days to deliver everything","score":0.3},{"id":"c","text":"Quietly deprioritize one project and hope nobody notices","score":0.1},{"id":"d","text":"Ask your manager to reassign one project","score":0.6}]',
'["prioritization","proactive_communication","scope_management","realistic_commitments"]',
1.7, 0.4, 0.2, true);

-- ═══════════════════════════════════════════════════════════════
-- ENGLISH_PROFICIENCY (+5 questions → 15 total)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO public.questions (id, competency_id, question_type, scenario_en, scenario_az, options, expected_concepts, irt_a, irt_b, irt_c, is_active) VALUES

('e5000077-0000-4000-a000-000000000001', '77777777-7777-7777-7777-777777777777', 'mcq',
'Choose the MOST appropriate email opening for a first-time message to a potential business partner at a multinational company:',
'Çoxmillətli şirkətdə potensial biznes partnyoruna ilk dəfə mesaj üçün ən uyğun e-poçt açılışını seçin:',
'[{"id":"a","text":"Hey! I wanted to reach out about a possible collaboration.","score":0.3},{"id":"b","text":"Dear Sir/Madam, I am writing to introduce our organization and explore potential synergies.","score":0.6},{"id":"c","text":"Dear [Name], I am writing to introduce [Organization] and explore how we might collaborate on [specific area].","score":1.0},{"id":"d","text":"Hi there, quick question about working together.","score":0.2}]',
'["register_awareness","personalization","professional_tone","purpose_clarity"]',
1.3, -0.8, 0.2, true),

('e5000077-0000-4000-a000-000000000002', '77777777-7777-7777-7777-777777777777', 'mcq',
'Which sentence contains a grammatical error?',
'Hansı cümlədə qrammatik xəta var?',
'[{"id":"a","text":"The team has been working on this project since January.","score":0.0},{"id":"b","text":"Each of the participants have submitted their reports.","score":1.0},{"id":"c","text":"Neither the manager nor the employees were available.","score":0.0},{"id":"d","text":"The committee is meeting tomorrow to discuss the budget.","score":0.0}]',
'["subject_verb_agreement","indefinite_pronouns","grammar_accuracy"]',
1.5, -0.3, 0.2, true),

('e5000077-0000-4000-a000-000000000003', '77777777-7777-7777-7777-777777777777', 'mcq',
'You need to write a professional summary of a 20-page technical report for non-technical stakeholders. What is the BEST approach?',
'Qeyri-texniki maraqlı tərəflər üçün 20 səhifəlik texniki hesabatın peşəkar xülasəsini yazmalısınız. Ən yaxşı yanaşma nədir?',
'[{"id":"a","text":"Translate every technical term into plain language, keeping all details","score":0.3},{"id":"b","text":"Lead with key findings and recommendations, use plain language, include a glossary for essential technical terms","score":1.0},{"id":"c","text":"Copy the executive summary from the report","score":0.2},{"id":"d","text":"Write bullet points of every section heading","score":0.4}]',
'["audience_awareness","synthesis","plain_language","information_hierarchy"]',
1.4, 0.0, 0.2, true),

('e5000077-0000-4000-a000-000000000004', '77777777-7777-7777-7777-777777777777', 'mcq',
'During a video call with international colleagues, a participant uses the idiom "let us not beat around the bush." A colleague from Japan looks confused. What is the BEST clarification?',
'Beynəlxalq həmkarlarla video zəng zamanı bir iştirakçı "let us not beat around the bush" idiomunu istifadə edir. Yaponiyadan olan həmkar çaşqın görünür. Ən yaxşı izahat nədir?',
'[{"id":"a","text":"Explain: it means let us speak directly about the main issue without unnecessary introduction","score":1.0},{"id":"b","text":"Repeat the phrase louder","score":0.0},{"id":"c","text":"Say: it is just an expression, don not worry about it","score":0.2},{"id":"d","text":"Switch to a different topic","score":0.1}]',
'["cross_cultural_communication","idiom_awareness","inclusive_clarification"]',
1.2, -1.0, 0.2, true),

('e5000077-0000-4000-a000-000000000005', '77777777-7777-7777-7777-777777777777', 'mcq',
'You receive an email that says: "Per our previous discussion, please action the deliverables by EOD." What does this mean?',
'Belə bir e-poçt alırsınız: "Per our previous discussion, please action the deliverables by EOD." Bu nə deməkdir?',
'[{"id":"a","text":"Complete the agreed tasks by the end of today","score":1.0},{"id":"b","text":"Review the discussion notes sometime this week","score":0.2},{"id":"c","text":"Send a reply confirming you received the email","score":0.1},{"id":"d","text":"Schedule a follow-up meeting to discuss the deliverables","score":0.3}]',
'["business_jargon","comprehension","deadline_awareness"]',
1.1, -1.2, 0.2, true);

-- ═══════════════════════════════════════════════════════════════
-- LEADERSHIP (+5 questions → 15 total)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO public.questions (id, competency_id, question_type, scenario_en, scenario_az, options, expected_concepts, irt_a, irt_b, irt_c, is_active) VALUES

('e5000044-0000-4000-a000-000000000001', '44444444-4444-4444-4444-444444444444', 'mcq',
'Your team just failed to meet a major deadline. The client is unhappy. As team lead, what is your FIRST action?',
'Komandanız vacib bir son tarixə çata bilmədi. Müştəri narazıdır. Komanda lideri olaraq ilk hərəkətiniz nədir?',
'[{"id":"a","text":"Own the failure to the client, present a recovery plan, then debrief the team without blame","score":1.0},{"id":"b","text":"Find out who caused the delay and address it with them","score":0.4},{"id":"c","text":"Email the client apologizing and promising it will not happen again","score":0.3},{"id":"d","text":"Call an emergency team meeting to discuss what went wrong","score":0.6}]',
'["accountability","client_management","blame-free_culture","recovery_planning"]',
1.6, 0.3, 0.2, true),

('e5000044-0000-4000-a000-000000000002', '44444444-4444-4444-4444-444444444444', 'mcq',
'Two senior members of your team have a disagreement about the technical approach for a project. Both have valid arguments. The disagreement is slowing progress. What do you do?',
'Komandanızın iki böyük üzvü layihə üçün texniki yanaşma barədə fikir ayrılığındadır. Hər ikisinin etibarlı arqumentləri var. Fikir ayrılığı irəliləyişi yavaşladır. Nə edirsiniz?',
'[{"id":"a","text":"Let them work it out themselves — they are senior enough","score":0.2},{"id":"b","text":"Pick one approach and mandate it","score":0.3},{"id":"c","text":"Facilitate a structured discussion: each presents their case, team evaluates against project criteria, decide together","score":1.0},{"id":"d","text":"Split the project so each can use their preferred approach","score":0.4}]',
'["conflict_resolution","structured_decision_making","facilitation","team_alignment"]',
1.5, 0.0, 0.2, true),

('e5000044-0000-4000-a000-000000000003', '44444444-4444-4444-4444-444444444444', 'mcq',
'A high-performing team member asks to lead a new initiative. They have the skills but have never led a project before. What is the BEST leadership response?',
'Yüksək performanslı komanda üzvü yeni bir təşəbbüsə rəhbərlik etmək istəyir. Bacarıqları var amma heç vaxt layihəyə rəhbərlik etməyib. Ən yaxşı liderlik cavabı nədir?',
'[{"id":"a","text":"Assign them as lead with a structured mentoring plan and weekly check-ins","score":1.0},{"id":"b","text":"Wait until they have more experience","score":0.2},{"id":"c","text":"Let them lead without interference to show trust","score":0.4},{"id":"d","text":"Co-lead with them so you can control the outcome","score":0.5}]',
'["talent_development","delegation_with_support","growth_mindset","structured_autonomy"]',
1.4, -0.3, 0.2, true),

('e5000044-0000-4000-a000-000000000004', '44444444-4444-4444-4444-444444444444', 'mcq',
'You are leading a cross-functional team of 12 people. Three subgroups have formed and rarely communicate with each other. Deliverables are starting to conflict. How do you unify the team?',
'12 nəfərlik çoxfunksiyalı komandaya rəhbərlik edirsiniz. Üç alt qrup formalaşıb və nadir hallarda bir-biri ilə əlaqə saxlayır. Çatdırılmalılar toqquşmağa başlayır. Komandanı necə birləşdirirsiniz?',
'[{"id":"a","text":"Create a shared project board with cross-group dependencies visible, hold weekly cross-group syncs, rotate meeting facilitators","score":1.0},{"id":"b","text":"Send an email reminding everyone to communicate better","score":0.1},{"id":"c","text":"Merge the subgroups into one team","score":0.3},{"id":"d","text":"Assign a project manager to coordinate between groups","score":0.6}]',
'["systems_thinking","communication_infrastructure","cross_functional_leadership","visibility"]',
1.7, 0.5, 0.2, true),

('e5000044-0000-4000-a000-000000000005', '44444444-4444-4444-4444-444444444444', 'mcq',
'Your organization is going through a restructuring. Your team is anxious about potential layoffs. You do not have full information yet. What is the MOST effective leadership approach?',
'Təşkilatınız yenidən qurulma prosesindədir. Komandanız potensial ixtisarlar barədə narahatdır. Hələ tam məlumatınız yoxdur. Ən effektiv liderlik yanaşması nədir?',
'[{"id":"a","text":"Be transparent: share what you know, what you do not know, and when you expect to know more. Commit to updating them.","score":1.0},{"id":"b","text":"Reassure everyone that their jobs are safe even if you are not sure","score":0.1},{"id":"c","text":"Say nothing until you have complete information","score":0.2},{"id":"d","text":"Redirect focus to current work and avoid discussing the restructuring","score":0.3}]',
'["transparency_under_uncertainty","trust_building","honest_communication","anxiety_management"]',
1.8, 0.6, 0.2, true);
