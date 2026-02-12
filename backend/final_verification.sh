#!/bin/bash

echo "=========================================="
echo "FINAL VERIFICATION - Report Export System"
echo "=========================================="
echo ""

# Test client
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"

# Counter
SUCCESS=0
TOTAL=12

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local output=$3
    
    echo -n "Testing ${name}... "
    http_code=$(curl -s -o ${output} -w "%{http_code}" "${url}")
    
    if [ "$http_code" -eq "200" ]; then
        size=$(stat -f%z ${output} 2>/dev/null || stat -c%s ${output} 2>/dev/null)
        if [ $size -gt 1000 ]; then
            echo "✅ OK (${http_code}, ${size} bytes)"
            ((SUCCESS++))
            return 0
        else
            echo "❌ FAIL (file too small: ${size} bytes)"
            return 1
        fi
    else
        echo "❌ FAIL (HTTP ${http_code})"
        return 1
    fi
}

# Run tests
test_endpoint "Saldobalanse PDF" \
    "http://localhost:8000/api/reports/saldobalanse/pdf?client_id=${CLIENT_ID}&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_saldobalanse.pdf"

test_endpoint "Saldobalanse Excel" \
    "http://localhost:8000/api/reports/saldobalanse/excel?client_id=${CLIENT_ID}&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_saldobalanse.xlsx"

test_endpoint "Resultat PDF" \
    "http://localhost:8000/api/reports/resultat/pdf?client_id=${CLIENT_ID}&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_resultat.pdf"

test_endpoint "Resultat Excel" \
    "http://localhost:8000/api/reports/resultat/excel?client_id=${CLIENT_ID}&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_resultat.xlsx"

test_endpoint "Balanse PDF" \
    "http://localhost:8000/api/reports/balanse/pdf?client_id=${CLIENT_ID}&to_date=2026-02-11" \
    "/tmp/verify_balanse.pdf"

test_endpoint "Balanse Excel" \
    "http://localhost:8000/api/reports/balanse/excel?client_id=${CLIENT_ID}&to_date=2026-02-11" \
    "/tmp/verify_balanse.xlsx"

test_endpoint "Hovedbok PDF" \
    "http://localhost:8000/api/reports/hovedbok/pdf?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_hovedbok.pdf"

test_endpoint "Hovedbok Excel" \
    "http://localhost:8000/api/reports/hovedbok/excel?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=2026-01-01&to_date=2026-02-11" \
    "/tmp/verify_hovedbok.xlsx"

test_endpoint "Leverandørreskontro PDF" \
    "http://localhost:8000/supplier-ledger/pdf?client_id=${CLIENT_ID}&status=all" \
    "/tmp/verify_supplier.pdf"

test_endpoint "Leverandørreskontro Excel" \
    "http://localhost:8000/supplier-ledger/excel?client_id=${CLIENT_ID}&status=all" \
    "/tmp/verify_supplier.xlsx"

test_endpoint "Kundereskontro PDF" \
    "http://localhost:8000/customer-ledger/pdf?client_id=${CLIENT_ID}&status=all" \
    "/tmp/verify_customer.pdf"

test_endpoint "Kundereskontro Excel" \
    "http://localhost:8000/customer-ledger/excel?client_id=${CLIENT_ID}&status=all" \
    "/tmp/verify_customer.xlsx"

echo ""
echo "=========================================="
echo "RESULTS: ${SUCCESS}/${TOTAL} tests passed"
echo "=========================================="

if [ $SUCCESS -eq $TOTAL ]; then
    echo "✅ ALL TESTS PASSED - System ready for production!"
    exit 0
else
    echo "❌ Some tests failed - check logs"
    exit 1
fi
