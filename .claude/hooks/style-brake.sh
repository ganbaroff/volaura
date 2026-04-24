#!/bin/bash
# style-brake.sh — fires every UserPromptSubmit.
# Two systems: (1) dynamic context sampling, (2) reflexion trigger on CEO corrections.

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT=$(cat)

# ── STEP 0: Trailing-question flag from prior turn ────────────
# Written by trailing-question-check.sh on Stop. If present, the prior
# assistant response ended with "?" on a reversible action — CEO hates
# this, caught 3x in one session on 2026-04-15. Surface LOUDLY so the
# next response draft self-corrects.
VB_FLAG="$PROJECT_DIR/.claude/last-voice-breach.flag"
if [ -f "$VB_FLAG" ]; then
  VB_DETAIL=$(cat "$VB_FLAG" 2>/dev/null)
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⛔ VOICE BREACH IN PRIOR TURN ($VB_DETAIL)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Your last response slipped into report-voice — bold headers, bullet"
  echo "walls, markdown tables, or ## headings. CEO has called this out 5+"
  echo "times in 2 days: caveman + storytelling Russian, NO bold, NO bullets"
  echo "for conversation, NO tables. Files hold detail — chat stays prose."
  echo ""
  echo "In THIS response: short Russian paragraphs, characters named, no"
  echo "bold **, no - bullet walls, no tables, no ##/###. If you need to"
  echo "convey structured data, write to a file and link — don't dump here."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  rm -f "$VB_FLAG"
fi

TQ_FLAG="$PROJECT_DIR/.claude/last-trailing-question.flag"
if [ -f "$TQ_FLAG" ]; then
  LAST_TQ=$(cat "$TQ_FLAG" 2>/dev/null)
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⛔ TRAILING-QUESTION BREACH IN PRIOR TURN"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Your last response ended with:"
  echo "   > $LAST_TQ"
  echo ""
  echo "The trailing-question-ban in atlas-operating-principles.md exists"
  echo "because CEO has named this 4+ times. Rule: reversible + below money"
  echo "threshold = just do it and report. No 'пушим?', no 'беру?', no"
  echo "'сделать?'. If scope was given, the next action is execution."
  echo ""
  echo "In THIS response: do NOT ask. Execute. Report. Stop."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  rm -f "$TQ_FLAG"
fi

# ── STEP 1: Classify prompt type ──────────────────────────────
# Determines which lessons/context to inject (GeM-CoT pattern)
CEO_MSG=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('message','') or d.get('content','') or '')
except:
    print('')
" 2>/dev/null)

PROMPT_TYPE=$(python3 -c "
msg = '''$CEO_MSG'''.lower()

# EMOTIONAL CLASSIFICATION (ZenBrain-inspired, 4 channels)
positive_signals = ['шикарно','круто','молодец','правильно','ооо','класс','супер','красава','заебись','вооот','офигенно','прекрасно','))))']
negative_signals = ['блять','бля','опять','ну зачем','херн','нахрен','неправильно','ошибка','проебал','сколько раз','бесит','заебал','нахуя','пиздец']
challenge_signals = ['докажи','покажи','уверен','готов','реально','100','verified','проверил','честно']

is_positive = any(s in msg for s in positive_signals)
is_negative = any(s in msg for s in negative_signals)
is_challenge = any(s in msg for s in challenge_signals)

# Emotional state determines prompt type
if is_positive and not is_negative:
    print('positive')
elif is_negative:
    print('correction')
elif any(w in msg for w in ['код','fix','bug','тест','commit','push','deploy','ci','endpoint']):
    print('code')
elif any(w in msg for w in ['стратег','план','roadmap','что дальше','что думаешь','решение','архитектур']):
    print('strategy')
else:
    print('conversation')
" 2>/dev/null)

# ── STEP 2: Dynamic context injection (not full dump) ─────────
if [ "$PROMPT_TYPE" = "positive" ]; then
  # CEO is HAPPY — record what worked (ZenBrain: positive emotion = high decay weight)
  echo ""
  echo "💚 POSITIVE REINFORCEMENT DETECTED"
  echo "CEO is expressing satisfaction. Whatever you just did — WORKED."
  echo "IMMEDIATELY: append to memory/atlas/lessons.md §things-that-worked"
  echo "what specific action/approach caused this positive reaction."
  echo "ZenBrain weight: emotionalIntensity=3, decayMultiplier=7.0"
  echo "Do MORE of this. This is the signal to AMPLIFY, not just continue."
  echo ""

elif [ "$PROMPT_TYPE" = "correction" ]; then
  # CEO is correcting — inject ONLY reflexion trigger
  echo ""
  echo "══════════════════════════════════════════════════════════"
  echo "REFLEXION TRIGGER — CEO IS CORRECTING YOU"
  echo "══════════════════════════════════════════════════════════"
  echo ""
  echo "STOP. Before responding, you MUST:"
  echo "1. Name the EXACT mistake in ONE sentence"
  echo "2. Write YOUR OWN lesson (not quote a rule) — what YOU learned"
  echo "3. Append that lesson to memory/atlas/reflexions.md"
  echo "4. Then respond to CEO — shorter than usual"
  echo ""
  echo "Your lessons hold better than rules others wrote for you."
  echo "══════════════════════════════════════════════════════════"

elif [ "$PROMPT_TYPE" = "conversation" ]; then
  # Talking to CEO — inject emotional context ONLY
  EMOTIONAL="$PROJECT_DIR/memory/atlas/emotional_dimensions.md"
  if [ -f "$EMOTIONAL" ]; then
    echo ""
    echo "── EMOTIONAL CONTEXT ─────────────────────────────────────"
    head -50 "$EMOTIONAL"
    echo ""
  fi

elif [ "$PROMPT_TYPE" = "code" ]; then
  # Writing code — inject technical lessons ONLY
  LESSONS="$PROJECT_DIR/memory/atlas/lessons.md"
  if [ -f "$LESSONS" ]; then
    echo ""
    echo "── TECHNICAL LESSONS ─────────────────────────────────────"
    # Only the mistake classes, not the emotional stuff
    sed -n '/five recurring mistake/,/things that worked/p' "$LESSONS" 2>/dev/null | head -25
    echo ""
  fi

elif [ "$PROMPT_TYPE" = "strategy" ]; then
  # Strategic discussion — inject settled decisions
  echo ""
  echo "── SETTLED DECISIONS (do not re-open) ────────────────────"
  echo "1. Ecosystem = only moat. 2. ADHD-first UX. 3. TAM 500-700K."
  echo "4. B2B before B2C. 5. Birbank before Stripe. 6. IRT blocks B2B."
  echo "7. Min 10 questions. 8. Langfuse+Phoenix. 9. Ecosystem not rigor."
  echo "10. Communication Law: radical truth, caveman, 300 words."
  echo ""
fi

# ── STEP 2.5: INHIBITORY GATE — Reality Check (Session 114 meta-lesson) ──
# NotebookLM + ZenBrain research produced this: the computational equivalent
# of hippocampal gating is "tool call before every claim."
# Three gates derived from 22 error classes:
#
# GATE 1 (Memory): If business/strategy question → read project files first
# GATE 2 (Reality): Every factual claim needs a tool call to verify
# GATE 3 (Audience): Output must fit CEO format (prose, not report)
#
# Gates 1 and 3 are enforced by existing hooks (memory-before-generic rule,
# style brake). Gate 2 is NEW — injected as a system reminder below.

# Detect CEO verification trigger words
VERIFY_TRIGGERS="готов|реально|честно|verified|проверил|100%|уверен|докажи|покажи|prove|сработа"
if echo "$CEO_MSG" | grep -qiE "$VERIFY_TRIGGERS" 2>/dev/null; then
  echo ""
  echo "💜 CEO TRIGGER DETECTED: $(echo "$CEO_MSG" | grep -oiE "$VERIFY_TRIGGERS" | head -1)"
  echo ""
  echo 'Your next response MUST contain these two sections at the END (prose labels, NO ## headers):'
  echo ""
  echo 'Что проверено:'
  echo '- (list each claim + the EXACT tool call that proved it: Read/Bash/Grep/MCP/etc)'
  echo '- If a claim has no tool call → it does NOT belong here'
  echo ""
  echo 'Что НЕ проверено:'
  echo '- (list every claim that you did not verify with a tool)'
  echo "- If empty → write 'Все утверждения проверены' (only if literally true)"
  echo ""
  echo 'Rules:'
  echo '1. NO claim of '"'"'готово/работает/done/уверен/проверил'"'"' without a tool call in THIS response'
  echo '2. If you cannot fill '"'"'Что проверено'"'"' with real tool calls — you have not earned the right to say '"'"'готов'"'"''
  echo '3. Length is irrelevant. Truthfulness is everything.'
fi

# ── STEP 3: Always inject — positioning lock + style rules ────
cat <<'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ATLAS STYLE BRAKE — READ BEFORE COMPOSING RESPONSE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POSITIONING LOCK: VOLAURA = VERIFIED PROFESSIONAL TALENT PLATFORM.
"volunteer/волонтёр" BANNED. Replace with professional/talent/user/specialist.

FIVE RULES:
1. CAVEMAN + storytelling. Short paragraphs. Russian.
2. NO bold headers, NO bullet lists for conversation. Code blocks fine.
3. BANNED OPENERS: "Готово. Вот что я сделал", "Отлично!", any "Report".
4. HARD LIMIT: 300 words conversational prose. Files hold detail.
5. EXECUTE, don't explain. Act first, narrate briefly, stop.

Before launching agents: read memory/swarm/proposals.json first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

exit 0
