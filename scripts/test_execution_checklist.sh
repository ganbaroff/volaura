#!/bin/bash
# test_execution_checklist.sh
# Pre-audit checklist: verify environment is ready before running tests

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== VOLAURA Functional Test Execution Checklist ===${NC}\n"

# ====== PHASE 0: Environment Setup ======

echo -e "${YELLOW}[PHASE 0] Environment Verification${NC}"

# Check API is reachable
echo -n "1. API health check... "
if curl -s https://volaura.app/health | jq . > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} (/health responding)"
else
    echo -e "${RED}FAIL${NC} (API not responding at volaura.app)"
    echo "   Hint: Check Railway deployment status"
    exit 1
fi

# Check frontend is reachable
echo -n "2. Frontend availability... "
if curl -s https://volaura.app | grep -q "<!DOCTYPE" 2>/dev/null; then
    echo -e "${GREEN}PASS${NC} (Vercel deployment live)"
else
    echo -e "${RED}FAIL${NC} (Frontend not responding)"
    echo "   Hint: Check Vercel deployment status"
    exit 1
fi

# Check test results directory exists
echo -n "3. Test results directory... "
mkdir -p test_results
echo -e "${GREEN}CREATED${NC} (test_results/)"

# Check for required tools
echo -n "4. Required tools (curl, jq, python3)... "
if command -v curl &> /dev/null && command -v jq &> /dev/null && command -v python3 &> /dev/null; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (missing curl, jq, or python3)"
    exit 1
fi

# ====== PHASE 1a: Auth Setup ======

echo -e "\n${YELLOW}[PHASE 1a] Auth Prerequisites${NC}"

echo -n "1. Test account creation... "
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!Auth"
TEST_USERNAME="testuser_$(date +%s)"

SIGNUP_RESPONSE=$(curl -s -X POST https://volaura.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"username\": \"$TEST_USERNAME\"
  }" 2>/dev/null || echo '{}')

if echo "$SIGNUP_RESPONSE" | jq -e '.data.user' > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} ($TEST_EMAIL)"
    USER_ID=$(echo "$SIGNUP_RESPONSE" | jq -r '.data.user.id')
    echo "   Saved: test_user.json"
    echo "$SIGNUP_RESPONSE" | jq . > test_results/test_user.json
else
    echo -e "${YELLOW}WARN${NC} (Signup may already exist or API issue)"
    # Try login instead
    echo "   Attempting login..."
fi

# ====== PHASE 1b: Session Verification ======

echo -e "\n${YELLOW}[PHASE 1b] Session & Token Verification${NC}"

echo -n "1. Login and get session... "
LOGIN_RESPONSE=$(curl -s -X POST https://volaura.app/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Content-Type: application/json" \
  -c test_results/cookies.txt \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }" 2>/dev/null || echo '{}')

if echo "$LOGIN_RESPONSE" | jq -e '.data.session' > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} (session obtained)"
    SESSION_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.session.access_token')
    echo "   Token: ${SESSION_TOKEN:0:20}..."
    echo "export SESSION_TOKEN='$SESSION_TOKEN'" > test_results/env.sh
else
    echo -e "${YELLOW}WARN${NC} (may already be logged in, continuing...)"
fi

# ====== PHASE 2: Critical Path Checks ======

echo -e "\n${YELLOW}[PHASE 2] Critical Path Verification${NC}"

# Test /api/profiles/me (blocked by CORS?)
echo -n "1. Protected route access (/api/profiles/me)... "
PROFILE_RESPONSE=$(curl -s -b test_results/cookies.txt \
  https://volaura.app/api/profiles/me 2>/dev/null || echo '{}')

if echo "$PROFILE_RESPONSE" | jq -e '.data' > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} (profile data returned)"
elif echo "$PROFILE_RESPONSE" | grep -q "Access-Control-Allow-Origin" 2>/dev/null; then
    echo -e "${RED}FAIL${NC} (CORS error)"
    echo "   Hint: Railway CORS config not deployed yet"
elif echo "$PROFILE_RESPONSE" | grep -q "401\|Unauthorized" 2>/dev/null; then
    echo -e "${RED}FAIL${NC} (401 Unauthorized)"
    echo "   Hint: Token not being injected by apiFetch"
else
    echo -e "${YELLOW}WARN${NC} (unexpected response)"
fi

# Test /api/assessment/sessions (check state)
echo -n "2. Assessment endpoint (/api/assessment/sessions)... "
ASSESSMENT_RESPONSE=$(curl -s -X POST \
  -b test_results/cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"competency_slug": "communication"}' \
  https://volaura.app/api/assessment/sessions 2>/dev/null || echo '{}')

if echo "$ASSESSMENT_RESPONSE" | jq -e '.data' > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} (session created)"
elif echo "$ASSESSMENT_RESPONSE" | grep -q "Access-Control-Allow-Origin" 2>/dev/null; then
    echo -e "${RED}FAIL${NC} (CORS error)"
else
    echo -e "${YELLOW}WARN${NC} (unexpected response)"
fi

# Test notification endpoint
echo -n "3. Notifications endpoint (/api/notifications/unread-count)... "
NOTIF_RESPONSE=$(curl -s -i -b test_results/cookies.txt \
  https://volaura.app/api/notifications/unread-count 2>/dev/null)

if echo "$NOTIF_RESPONSE" | grep -q "200"; then
    echo -e "${GREEN}PASS${NC} (200 OK)"
elif echo "$NOTIF_RESPONSE" | grep -q "Access-Control"; then
    echo -e "${RED}FAIL${NC} (CORS error)"
else
    echo -e "${YELLOW}WARN${NC} (check response headers)"
fi

# ====== PHASE 3: Frontend Checks ======

echo -e "\n${YELLOW}[PHASE 3] Frontend Checks${NC}"

echo -n "1. Landing page load... "
LANDING=$(curl -s -o /dev/null -w "%{http_code}" https://volaura.app)
if [ "$LANDING" == "200" ]; then
    echo -e "${GREEN}PASS${NC} (HTTP 200)"
else
    echo -e "${RED}FAIL${NC} (HTTP $LANDING)"
fi

echo -n "2. Dashboard page load (logged in)... "
DASHBOARD=$(curl -s -o /dev/null -w "%{http_code}" -b test_results/cookies.txt https://volaura.app/en/dashboard)
if [ "$DASHBOARD" == "200" ]; then
    echo -e "${GREEN}PASS${NC} (HTTP 200)"
else
    echo -e "${YELLOW}WARN${NC} (HTTP $DASHBOARD, may require auth redirect)"
fi

# ====== Summary ======

echo -e "\n${YELLOW}=== Checklist Complete ===${NC}"
echo -e "\n${GREEN}Ready to start parallel test execution?${NC}"
echo ""
echo "Next steps:"
echo "1. Review test_results/ directory (populated with test data)"
echo "2. Distribute FUNCTIONAL-TEST-STRATEGY.md to team leads"
echo "3. Assign Phase owners (see strategy document, Part 2)"
echo "4. Each team submits results to test_results/{team-name}.json"
echo "5. Run: python3 scripts/aggregate_test_results.py"
echo ""
echo "Expected timeline: ~45 min (parallel execution, 8-10 people)"
echo ""
