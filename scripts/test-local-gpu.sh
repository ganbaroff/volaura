#!/bin/bash
# Test local Ollama GPU inference for swarm

echo "=== LOCAL GPU TEST ==="
echo "Testing Qwen3 8B on RTX 5060..."

RESPONSE=$(curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:8b",
    "messages": [{"role": "user", "content": "You are a code reviewer. Review this: function add(a,b){return a+b}. One sentence. Russian."}],
    "max_tokens": 100,
    "temperature": 0.7
  }')

echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'choices' in d:
    msg = d['choices'][0]['message']['content']
    usage = d.get('usage', {})
    print(f'Response: {msg}')
    print(f'Tokens: {usage.get(\"total_tokens\", \"?\")}')
    print(f'Model: {d.get(\"model\", \"?\")}')
    print('STATUS: LOCAL GPU WORKING')
else:
    print(f'Error: {d}')
"
