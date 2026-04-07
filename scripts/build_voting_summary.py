"""
This script reads JSON files from the sprint-2 directory
and aggregates them into a single voting-input.json file.
"""
import json, os, sys

sprint2_dir = r'C:\Projects\VOLAURA\scripts\question-evolution\sprint-2'
out_path = r'C:\Projects\VOLAURA\scripts\question-evolution\sprint-2\voting-input.json'

voting_summary = {}

for fname in sorted(os.listdir(sprint2_dir)):
    if not fname.endswith('.json') or fname.startswith('voting'):
        continue
    with open(os.path.join(sprint2_dir, fname), encoding='utf-8') as f:
        qs = json.load(f)

    prof_key = fname.replace('.json', '')
    questions_data = []
    for q in qs:
        if not isinstance(q, dict):
            continue
        scenario = q.get('scenario_en', '') or q.get('scenario', '') or ''
        entry = {
            'id': q.get('id', ''),
            'difficulty': q.get('difficulty', ''),
            'type': q.get('type') or q.get('question_type', ''),
            'irt_a': q.get('irt_a', 0),
            'irt_b': q.get('irt_b', 0),
            'competency': q.get('competency_slug') or q.get('competency', ''),
            'london_fails': q.get('london_fails', q.get('london_test_fails', None)),
            'scenario_80': scenario[:80],
        }
        questions_data.append(entry)
    voting_summary[prof_key] = questions_data

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(voting_summary, f, ensure_ascii=False, indent=2)

print(f"Saved voting-input.json with {len(voting_summary)} professions")
for k, v in voting_summary.items():
    avg_a = sum(q['irt_a'] for q in v if q['irt_a']) / len(v)
    avg_b = sum(q['irt_b'] for q in v if q['irt_b']) / len(v)
    london = sum(1 for q in v if q.get('london_fails') == True)
    print(f"  {k}: 10 questions, avg_irt_a={avg_a:.2f}, avg_irt_b={avg_b:.2f}, london_fails={london}")
