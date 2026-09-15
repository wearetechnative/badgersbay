#!/usr/bin/env bash
# Manual test script for OS type extraction and tar filename changes
# Usage: ./test-manual.sh

set -e

SERVER="http://localhost:7123"
TOKEN="${HONEYBADGER_TOKEN:-test-token}"

echo "=== Testing OS Type Extraction ==="

echo "Test 1: Upload fastfetch without X-OS-Type header..."
curl -X POST "$SERVER/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: fastfetch" \
  -d @test-fastfetch-report.json \
  -v

echo ""
echo "Test 2: Check server logs for OS type extraction message"
echo "Expected: 'Extracted OS type from fastfetch data: NixOS 24.05'"
echo ""

echo "Test 3: Access dashboard and check OS Type column"
echo "Open: $SERVER/ (requires authentication)"
echo ""

echo "=== Testing Tar Filename ==="
echo "Upload a tar archive and verify filename has 'honeybadger-' prefix"
echo ""

echo "All tests described. Run manually and verify outputs."
