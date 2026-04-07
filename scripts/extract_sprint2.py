"""
This script extracts JSON files from temporary task directories produced by Claude Code background agents
and copies them into the question-evolution/sprint-2 directory.
"""
import json, re, sys

TASK_DIR = r"C:\Users\user\AppData\Local\Temp\claude\C--Projects-VOLAURA\a0e32fd4-9284-4cbc-89bb-56dd21b0bcf4\tasks"
OUT_DIR = r"C:\Projects\VOLAURA\scripts\question-evolution\sprint-2"

files = {
    'devops': ('aa29c28816e20c7c1.output', 'devops-cybersecurity'),
    'hr': ('afd412b3f68464490.output', 'hr-manager'),
    'marketing': ('a7094c2b31088969e.output', 'marketing-manager'),
    'product': ('a5b77b3c9022b8677.output', 'product-manager'),
}

for name, (fname, outname) in files.items():
    fpath = TASK_DIR + "\\" + fname
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()

    questions_json = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            msg = obj.get('message', {})
            content = msg.get('content', [])

            if not isinstance(content, list):
                continue

            for item in content:
                if not isinstance(item, dict) or item.get('type') != 'text':
                    continue
                text = item.get('text', '')

                # Extract from markdown code blocks  ```json ... ```
                pattern = re.compile(r'```(?:json)?\s*(\[.+?\])\s*```', re.DOTALL)
                code_blocks = pattern.findall(text)
                for block in code_blocks:
                    try:
                        qs = json.loads(block)
                        if isinstance(qs, list) and len(qs) >= 5:
                            if questions_json is None or len(qs) > len(questions_json):
                                questions_json = qs
                    except Exception as e:
                        pass

        except Exception as e:
            continue

    if questions_json:
        out_path = OUT_DIR + "\\" + outname + ".json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(questions_json, f, ensure_ascii=False, indent=2)
        print(f"{name}: {len(questions_json)} questions -> {outname}.json")
        ids = [q.get('id', '?') for q in questions_json[:3]]
        print(f"  IDs: {ids}")
    else:
        print(f"{name}: FAILED - no questions extracted")
