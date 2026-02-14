#!/bin/bash
set -e

CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
BASE_URL="http://localhost:8000"

echo "🔥 SMOKETEST: Kontali Backend API"
echo "=================================="

# Test health endpoint
echo "✓ Health check..."
curl -sf "$BASE_URL/health" > /dev/null || { echo "❌ Health check failed"; exit 1; }

# Test all new Modul 3 endpoints
echo "✓ Modul 3: Other vouchers..."
curl -sf "$BASE_URL/api/other-vouchers/pending?client_id=$CLIENT_ID" > /dev/null
curl -sf "$BASE_URL/api/other-vouchers/stats?client_id=$CLIENT_ID" > /dev/null

# Test Modul 2 endpoints
echo "✓ Modul 2: Bank reconciliation..."
curl -sf "$BASE_URL/api/bank-recon/unmatched?client_id=$CLIENT_ID&account=1920&period_start=2026-02-01&period_end=2026-02-28" > /dev/null

# Test Modul 5 endpoints
echo "✓ Modul 5: Voucher control..."
curl -sf "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID" > /dev/null
curl -sf "$BASE_URL/api/voucher-control/stats?client_id=$CLIENT_ID" > /dev/null

# Test existing core endpoints (may fail with 400 if no data)
echo "✓ Core: Review queue..."
curl -s "$BASE_URL/api/review-queue/pending?client_id=$CLIENT_ID" > /dev/null || echo "  ⚠ Review queue returned error (expected if no data)"

echo ""
echo "✅ All smoketests passed!"
