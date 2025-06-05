#!/bin/bash
# Security testing script for TKR News Gatherer
# Tests authentication, rate limiting, input validation, and security headers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL=${API_URL:-"http://localhost:8000"}
API_KEY=${API_KEY:-"test_api_key"}
JWT_TOKEN=""

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "🔒 TKR News Gatherer Security Test Suite"
echo "========================================"
echo "API URL: $API_URL"
echo ""

# Test 1: Health Check (should be public)
print_test "Testing health check endpoint (public access)"
response=$(curl -s -w "%{http_code}" -o /dev/null "$API_URL/health")
if [ "$response" = "200" ]; then
    print_pass "Health check accessible without authentication"
else
    print_fail "Health check failed (HTTP $response)"
fi

# Test 2: Security Headers
print_test "Testing security headers"
headers=$(curl -s -I "$API_URL/health")

if echo "$headers" | grep -q "x-content-type-options: nosniff"; then
    print_pass "X-Content-Type-Options header present"
else
    print_fail "Missing X-Content-Type-Options header"
fi

if echo "$headers" | grep -q "x-frame-options: DENY"; then
    print_pass "X-Frame-Options header present"
else
    print_fail "Missing X-Frame-Options header"
fi

if echo "$headers" | grep -q "strict-transport-security"; then
    print_pass "HSTS header present"
else
    print_fail "Missing HSTS header"
fi

# Test 3: Authentication Required
print_test "Testing authentication requirement"
response=$(curl -s -w "%{http_code}" -o /dev/null "$API_URL/provinces")
if [ "$response" = "401" ]; then
    print_pass "Authentication required for protected endpoints"
else
    print_fail "Protected endpoint accessible without authentication (HTTP $response)"
fi

# Test 4: API Key Authentication
print_test "Testing API key authentication"
response=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "X-API-Key: $API_KEY" \
    "$API_URL/provinces")
if [ "$response" = "200" ]; then
    print_pass "API key authentication working"
elif [ "$response" = "401" ]; then
    print_warning "API key authentication failed - check API_KEY configuration"
else
    print_fail "Unexpected response for API key auth (HTTP $response)"
fi

# Test 5: JWT Authentication
print_test "Testing JWT authentication"
jwt_response=$(curl -s -X POST "$API_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=secure_password")

if echo "$jwt_response" | grep -q "access_token"; then
    JWT_TOKEN=$(echo "$jwt_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    pass
")
    print_pass "JWT token obtained successfully"
else
    print_fail "Failed to obtain JWT token"
fi

# Test 6: JWT Protected Endpoint
if [ -n "$JWT_TOKEN" ]; then
    print_test "Testing JWT protected endpoint"
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer $JWT_TOKEN" \
        "$API_URL/news/ontario?limit=1")
    if [ "$response" = "200" ]; then
        print_pass "JWT authentication working for protected endpoints"
    else
        print_fail "JWT protected endpoint failed (HTTP $response)"
    fi
fi

# Test 7: Input Validation
print_test "Testing input validation"

# Test invalid province
response=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "Authorization: Bearer $JWT_TOKEN" \
    "$API_URL/news/invalid_province?limit=1")
if [ "$response" = "400" ] || [ "$response" = "422" ]; then
    print_pass "Invalid province rejected"
else
    print_fail "Invalid province accepted (HTTP $response)"
fi

# Test invalid limit
response=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "Authorization: Bearer $JWT_TOKEN" \
    "$API_URL/news/ontario?limit=100")
if [ "$response" = "400" ] || [ "$response" = "422" ]; then
    print_pass "Invalid limit rejected"
else
    print_fail "Invalid limit accepted (HTTP $response)"
fi

# Test 8: SSRF Protection
print_test "Testing SSRF protection"
ssrf_response=$(curl -s -X POST "$API_URL/scrape" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"urls": ["http://localhost:22", "http://169.254.169.254/metadata"]}')

if echo "$ssrf_response" | grep -q "not allowed\|validation"; then
    print_pass "SSRF protection working"
else
    print_warning "SSRF protection may not be working properly"
fi

# Test 9: Rate Limiting
print_test "Testing rate limiting"
echo "Making rapid requests to test rate limiting..."

rate_limit_hit=false
for i in {1..20}; do
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "X-API-Key: $API_KEY" \
        "$API_URL/provinces")
    if [ "$response" = "429" ]; then
        rate_limit_hit=true
        break
    fi
    sleep 0.1
done

if [ "$rate_limit_hit" = true ]; then
    print_pass "Rate limiting working (got 429 Too Many Requests)"
else
    print_warning "Rate limiting may not be working (no 429 responses)"
fi

# Test 10: Error Information Disclosure
print_test "Testing error information disclosure"
error_response=$(curl -s "$API_URL/nonexistent-endpoint")

if echo "$error_response" | grep -qi "traceback\|stack\|debug\|exception"; then
    print_fail "Error response may expose sensitive information"
else
    print_pass "Error responses appear sanitized"
fi

# Test 11: CORS Configuration
print_test "Testing CORS configuration"
cors_response=$(curl -s -H "Origin: http://malicious.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: X-Requested-With" \
    -X OPTIONS "$API_URL/provinces")

if echo "$cors_response" | grep -q "Access-Control-Allow-Origin: \*"; then
    print_fail "CORS allows all origins (security risk)"
elif echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    print_pass "CORS properly configured"
else
    print_warning "CORS configuration unclear"
fi

# Test 12: SQL Injection Attempt (if applicable)
if [ -n "$JWT_TOKEN" ]; then
    print_test "Testing SQL injection protection"
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer $JWT_TOKEN" \
        "$API_URL/news/ontario'; DROP TABLE articles; --?limit=1")
    if [ "$response" = "400" ] || [ "$response" = "422" ]; then
        print_pass "SQL injection attempt blocked"
    else
        print_warning "SQL injection test inconclusive (HTTP $response)"
    fi
fi

echo ""
echo "🔒 Security Test Summary"
echo "======================"
echo "Review the test results above for any FAIL or WARN items."
echo "- PASS: Security control is working correctly"
echo "- FAIL: Security vulnerability found - immediate action required"
echo "- WARN: Potential security issue - review configuration"
echo ""
echo "Recommendations:"
echo "1. Ensure all FAIL items are addressed before production"
echo "2. Review WARN items and adjust configuration as needed"
echo "3. Run this test regularly as part of your security validation"
echo "4. Consider additional penetration testing for production deployment"