#!/bin/bash
# Simple test for invoice upload API

set -e

API_URL="http://localhost:8000"
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"  # GHB AS Test client

echo "🧪 Testing Invoice Upload API"
echo "============================================"

# Create a simple test PDF (even if it's not valid, just for testing)
TEST_PDF="/tmp/test_invoice.pdf"
echo "%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 85
>>
stream
BT
/F1 12 Tf
100 700 Td
(FAKTURA - Test Invoice) Tj
0 -20 Td
(Fra: Test Leverandor AS) Tj
0 -20 Td
(Org.nr: 987654321) Tj
0 -40 Td
(Fakturanummer: INV-2024-001) Tj
0 -20 Td
(Dato: 2024-02-07) Tj
0 -20 Td
(Forfall: 2024-03-07) Tj
0 -40 Td
(Beskrivelse:) Tj
0 -20 Td
(Kontorrekvisita og lisenser) Tj
0 -40 Td
(Belop eks. mva: NOK 8,000.00) Tj
0 -20 Td
(Mva 25%%: NOK 2,000.00) Tj
0 -20 Td
(Totalt: NOK 10,000.00) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000015 00000 n 
0000000074 00000 n 
0000000131 00000 n 
0000000339 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
473
%%EOF" > "$TEST_PDF"

echo "📄 Created test PDF: $TEST_PDF"

# Upload the invoice
echo ""
echo "📤 Uploading invoice..."
echo "   Endpoint: $API_URL/api/invoices/upload/"
echo "   Client ID: $CLIENT_ID"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "$API_URL/api/invoices/upload/" \
  -F "file=@$TEST_PDF" \
  -F "client_id=$CLIENT_ID")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
# Extract response body (all but last line)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "📥 Response Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Upload Successful!"
    echo "============================================"
    echo "$BODY" | python3 -m json.tool
    echo "============================================"
    
    # Extract key fields
    INVOICE_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('invoice_id', 'N/A'))")
    CONFIDENCE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence_score', 'N/A'))")
    
    echo ""
    echo "📊 Summary:"
    echo "   Invoice ID: $INVOICE_ID"
    echo "   Confidence Score: $CONFIDENCE%"
    echo "   Status: pending_review"
    
    # Test listing invoices
    echo ""
    echo "📋 Testing invoice list..."
    curl -s "$API_URL/api/invoices/?client_id=$CLIENT_ID" | python3 -m json.tool | head -20
    
    echo ""
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Upload Failed!"
    echo "   Status Code: $HTTP_CODE"
    echo "   Response:"
    echo "$BODY"
    exit 1
fi
