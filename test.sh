#!/bin/bash

echo "=== Testing Honeybadger Server ==="
echo ""

# Test 1: Lynis report
echo "Test 1: Sending Lynis report..."
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: testserver01" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: lynis" \
  -d @test-lynis-report.json
echo -e "\n"

# Test 2: Trivy report
echo "Test 2: Sending Trivy report..."
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: testserver01" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: trivy" \
  -d @test-trivy-report.json
echo -e "\n"

# Test 3: Different server
echo "Test 3: Sending report from different server..."
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: webserver02" \
  -H "X-Username: admin" \
  -H "X-Report-Type: lynis" \
  -d @test-lynis-report.json
echo -e "\n"

# Test 4: Health check
echo "Test 4: Health check..."
curl http://localhost:7123/health
echo -e "\n\n"

# Show results
echo "=== Checking saved reports ==="
ls -lR reports/
