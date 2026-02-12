#!/bin/bash

CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
FROM_DATE="2026-01-01"
TO_DATE="2026-02-11"
BASE_URL="http://localhost:8000"

echo "Testing all 12 export endpoints..."
echo ""

# 1. Saldobalanse PDF
echo "1. Testing Saldobalanse PDF..."
curl -s "${BASE_URL}/api/reports/saldobalanse/pdf?client_id=${CLIENT_ID}&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/saldobalanse.pdf
[ -f /tmp/saldobalanse.pdf ] && echo "   ✓ Saldobalanse PDF created" || echo "   ✗ FAILED"

# 2. Saldobalanse Excel
echo "2. Testing Saldobalanse Excel..."
curl -s "${BASE_URL}/api/reports/saldobalanse/excel?client_id=${CLIENT_ID}&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/saldobalanse.xlsx
[ -f /tmp/saldobalanse.xlsx ] && echo "   ✓ Saldobalanse Excel created" || echo "   ✗ FAILED"

# 3. Resultat PDF
echo "3. Testing Resultat PDF..."
curl -s "${BASE_URL}/api/reports/resultat/pdf?client_id=${CLIENT_ID}&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/resultat.pdf
[ -f /tmp/resultat.pdf ] && echo "   ✓ Resultat PDF created" || echo "   ✗ FAILED"

# 4. Resultat Excel
echo "4. Testing Resultat Excel..."
curl -s "${BASE_URL}/api/reports/resultat/excel?client_id=${CLIENT_ID}&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/resultat.xlsx
[ -f /tmp/resultat.xlsx ] && echo "   ✓ Resultat Excel created" || echo "   ✗ FAILED"

# 5. Balanse PDF
echo "5. Testing Balanse PDF..."
curl -s "${BASE_URL}/api/reports/balanse/pdf?client_id=${CLIENT_ID}&to_date=${TO_DATE}" -o /tmp/balanse.pdf
[ -f /tmp/balanse.pdf ] && echo "   ✓ Balanse PDF created" || echo "   ✗ FAILED"

# 6. Balanse Excel
echo "6. Testing Balanse Excel..."
curl -s "${BASE_URL}/api/reports/balanse/excel?client_id=${CLIENT_ID}&to_date=${TO_DATE}" -o /tmp/balanse.xlsx
[ -f /tmp/balanse.xlsx ] && echo "   ✓ Balanse Excel created" || echo "   ✗ FAILED"

# 7. Hovedbok PDF
echo "7. Testing Hovedbok PDF..."
curl -s "${BASE_URL}/api/reports/hovedbok/pdf?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/hovedbok.pdf
[ -f /tmp/hovedbok.pdf ] && echo "   ✓ Hovedbok PDF created" || echo "   ✗ FAILED"

# 8. Hovedbok Excel
echo "8. Testing Hovedbok Excel..."
curl -s "${BASE_URL}/api/reports/hovedbok/excel?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=${FROM_DATE}&to_date=${TO_DATE}" -o /tmp/hovedbok.xlsx
[ -f /tmp/hovedbok.xlsx ] && echo "   ✓ Hovedbok Excel created" || echo "   ✗ FAILED"

# 9. Leverandørreskontro PDF
echo "9. Testing Leverandørreskontro PDF..."
curl -s "${BASE_URL}/supplier-ledger/pdf?client_id=${CLIENT_ID}&status=all" -o /tmp/leverandor.pdf
[ -f /tmp/leverandor.pdf ] && echo "   ✓ Leverandørreskontro PDF created" || echo "   ✗ FAILED"

# 10. Leverandørreskontro Excel
echo "10. Testing Leverandørreskontro Excel..."
curl -s "${BASE_URL}/supplier-ledger/excel?client_id=${CLIENT_ID}&status=all" -o /tmp/leverandor.xlsx
[ -f /tmp/leverandor.xlsx ] && echo "   ✓ Leverandørreskontro Excel created" || echo "   ✗ FAILED"

# 11. Kundereskontro PDF
echo "11. Testing Kundereskontro PDF..."
curl -s "${BASE_URL}/customer-ledger/pdf?client_id=${CLIENT_ID}&status=all" -o /tmp/kunde.pdf
[ -f /tmp/kunde.pdf ] && echo "   ✓ Kundereskontro PDF created" || echo "   ✗ FAILED"

# 12. Kundereskontro Excel
echo "12. Testing Kundereskontro Excel..."
curl -s "${BASE_URL}/customer-ledger/excel?client_id=${CLIENT_ID}&status=all" -o /tmp/kunde.xlsx
[ -f /tmp/kunde.xlsx ] && echo "   ✓ Kundereskontro Excel created" || echo "   ✗ FAILED"

echo ""
echo "Testing complete! Checking file types..."
echo ""
file /tmp/saldobalanse.pdf
file /tmp/saldobalanse.xlsx
file /tmp/resultat.pdf
file /tmp/resultat.xlsx
file /tmp/balanse.pdf
file /tmp/balanse.xlsx
file /tmp/hovedbok.pdf
file /tmp/hovedbok.xlsx
file /tmp/leverandor.pdf
file /tmp/leverandor.xlsx
file /tmp/kunde.pdf
file /tmp/kunde.xlsx

echo ""
echo "All exports saved to /tmp/"
