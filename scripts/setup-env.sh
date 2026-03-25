#!/bin/bash
# Volaura — Auto-setup local .env from Railway production vars
# Usage: bash scripts/setup-env.sh
# Requires: railway CLI logged in (railway login)

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_ENV="$PROJECT_ROOT/apps/api/.env"
WEB_ENV="$PROJECT_ROOT/apps/web/.env.local"

echo "🔧 Volaura Environment Setup"
echo "────────────────────────────"

# Check railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install: npm i -g @railway/cli && railway login"
    exit 1
fi

# Check if linked
if ! railway status &> /dev/null 2>&1; then
    echo "⚠️  Not linked to Railway project. Run from apps/api/ directory."
    echo "   cd apps/api && railway link"
    exit 1
fi

echo "📡 Pulling env vars from Railway..."

# Pull Railway vars into API .env
cd "$PROJECT_ROOT/apps/api"
railway variables --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
# Filter out Railway internal vars
skip = {'RAILWAY_', 'NIXPACKS_'}
with open('$API_ENV', 'w', encoding='utf-8') as f:
    f.write('# AUTO-GENERATED from Railway production — $(date -u +%Y-%m-%dT%H:%M:%SZ)\n')
    f.write('# Do NOT commit this file\n\n')
    f.write('APP_ENV=development\n')
    f.write('APP_URL=http://localhost:3000\n')
    f.write('API_PORT=8000\n\n')
    for k, v in sorted(data.items()):
        if not any(k.startswith(s) for s in skip):
            f.write(f'{k}={v}\n')
print(f'✅ Written {len([k for k in data if not any(k.startswith(s) for s in skip)])} vars to apps/api/.env')
" 2>/dev/null || {
    echo "⚠️  Could not parse Railway vars. Copying from .env.example..."
    cp "$PROJECT_ROOT/apps/api/.env.example" "$API_ENV"
    echo "📝 Fill in values manually in apps/api/.env"
}

# Web .env.local
echo ""
echo "📱 Setting up frontend env..."
cat > "$WEB_ENV" << 'WEBEOF'
# AUTO-GENERATED — frontend env
NEXT_PUBLIC_SUPABASE_URL=https://hvykysvdkalkbswmgfut.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_hruec2YAtdmvD1jZ6ElbNQ_g4VNDItM
NEXT_PUBLIC_API_URL=https://volauraapi-production.up.railway.app
WEBEOF
echo "✅ Written apps/web/.env.local"

echo ""
echo "────────────────────────────"
echo "✅ Done! Next steps:"
echo "   cd apps/api && pip install -r requirements.txt"
echo "   cd apps/web && pnpm install"
echo "   pnpm dev  (from project root)"
