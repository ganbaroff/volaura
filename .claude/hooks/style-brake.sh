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
# Detect if CEO is correcting (triggers reflexion)
correction_signals = ['блять','бля','опять','ну зачем','херн','нахрен','неправильно','ошибка','проебал','сколько раз','бесит']
is_correction = any(s in msg for s in correction_signals)
# Detect conversation vs code vs strategy
if is_correction:
    print('correction')
elif any(w in msg for w in ['код','fix','bug','тест','commit','push','deploy','ci','endpoint']):
    print('code')
elif any(w in msg for w in ['стратег','план','roadmap','что дальше','что думаешь','решение','архитектур']):
    print('strategy')
else:
    print('conversation')
" 2>/dev/null)

# ── STEP 2: Dynamic context injection (not full dump) ─────────
if [ "$PROMPT_TYPE" = "correction" ]; then
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
