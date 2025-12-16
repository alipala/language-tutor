#!/bin/bash
# Test Script for Phase 3.1 using curl
# Tests flexible language/level selection with a user who has NO learning plan

BASE_URL="http://localhost:8000"
EMAIL="d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz"
PASSWORD="040050803"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}================================================================================"
echo -e "  PHASE 3.1 TEST SUITE - Flexible Language/Level Selection (curl)"
echo -e "  Testing with: User WITHOUT learning plan"
echo -e "================================================================================${NC}\n"

# Step 1: Login and get token
echo -e "${BOLD}${BLUE}1. AUTHENTICATION TEST${NC}\n"
echo -e "${BLUE}ℹ️  Logging in with: ${EMAIL}${NC}"

LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed!${NC}"
    echo -e "${RED}Response: ${LOGIN_RESPONSE}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Login successful!${NC}"
echo -e "${BLUE}ℹ️  Token: ${TOKEN:0:20}...${NC}\n"

# Step 2: Test /api/challenges/counts with different parameters
echo -e "${BOLD}${BLUE}================================================================================"
echo -e "2. CHALLENGE COUNTS ENDPOINT TESTS"
echo -e "================================================================================${NC}\n"

# Test 2.1: Spanish A1
echo -e "${BOLD}Test 2.1: Spanish A1 (explicit params)${NC}"
echo -e "${BLUE}ℹ️  Should show counts for Spanish A1${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/counts?language=spanish&level=A1" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool
echo -e ""

# Test 2.2: German B2
echo -e "${BOLD}Test 2.2: German B2 (explicit params)${NC}"
echo -e "${BLUE}ℹ️  Should show counts for German B2${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/counts?language=german&level=B2" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool
echo -e ""

# Test 2.3: No params (fallback)
echo -e "${BOLD}Test 2.3: No params (fallback test)${NC}"
echo -e "${BLUE}ℹ️  Should fallback to default (english/B1)${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/counts" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool
echo -e ""

# Step 3: Test /api/challenges/daily
echo -e "${BOLD}${BLUE}================================================================================"
echo -e "3. DAILY CHALLENGES ENDPOINT TESTS"
echo -e "================================================================================${NC}\n"

# Test 3.1: Spanish A1
echo -e "${BOLD}Test 3.1: Spanish A1 daily challenges${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/daily?language=spanish&level=A1" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c 'import sys, json; data=json.load(sys.stdin); print(json.dumps({"challenges_count": len(data.get("challenges", [])), "completed_today": data.get("total_completed_today", 0), "streak": data.get("streak", 0)}, indent=2))'
echo -e ""

# Test 3.2: Dutch B1
echo -e "${BOLD}Test 3.2: Dutch B1 daily challenges${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/daily?language=dutch&level=B1" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c 'import sys, json; data=json.load(sys.stdin); print(json.dumps({"challenges_count": len(data.get("challenges", [])), "completed_today": data.get("total_completed_today", 0), "streak": data.get("streak", 0)}, indent=2))'
echo -e ""

# Step 4: Test /api/challenges/by-type/{type}
echo -e "${BOLD}${BLUE}================================================================================"
echo -e "4. BY-TYPE ENDPOINT TESTS"
echo -e "================================================================================${NC}\n"

# Test 4.1: Spanish A1 error_spotting
echo -e "${BOLD}Test 4.1: Spanish A1 error_spotting${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/by-type/error_spotting?language=spanish&level=A1&limit=3" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c 'import sys, json; data=json.load(sys.stdin); print(json.dumps({"type": data.get("type"), "total": data.get("total"), "challenges_returned": len(data.get("challenges", []))}, indent=2))'
echo -e ""

# Test 4.2: German A2 swipe_fix
echo -e "${BOLD}Test 4.2: German A2 swipe_fix${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/by-type/swipe_fix?language=german&level=A2&limit=3" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c 'import sys, json; data=json.load(sys.stdin); print(json.dumps({"type": data.get("type"), "total": data.get("total"), "challenges_returned": len(data.get("challenges", []))}, indent=2))'
echo -e ""

# Step 5: Test /api/challenges/languages
echo -e "${BOLD}${BLUE}================================================================================"
echo -e "5. LANGUAGES ENDPOINT TEST"
echo -e "================================================================================${NC}\n"

# Test 5.1: All languages for A1
echo -e "${BOLD}Test 5.1: All languages for A1${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/languages?level=A1" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool
echo -e ""

# Test 5.2: No params (user's level)
echo -e "${BOLD}Test 5.2: No params (user's default level)${NC}"
curl -s -X GET "${BASE_URL}/api/challenges/languages" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool
echo -e ""

# Summary
echo -e "${BOLD}${BLUE}================================================================================"
echo -e "TEST SUMMARY"
echo -e "================================================================================${NC}\n"
echo -e "${GREEN}✅ All endpoint tests completed!${NC}"
echo -e "${BLUE}ℹ️  Expected behavior for user without learning plan:${NC}"
echo -e "${BLUE}   - Should see 0 challenges initially${NC}"
echo -e "${BLUE}   - Backend auto-copies from reference challenges${NC}"
echo -e "${BLUE}   - Challenges become available for requested language/level${NC}"
echo -e "${BLUE}   - Can freely switch between languages${NC}\n"
echo -e "${BOLD}${GREEN}✅ Phase 3.1 testing complete!${NC}\n"
