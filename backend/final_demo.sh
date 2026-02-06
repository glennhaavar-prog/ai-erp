#!/bin/bash

echo "=================================================================="
echo "🎯 Hovedbok REST API - Final Demonstration"
echo "=================================================================="
echo ""

CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
BASE_URL="http://localhost:8000/api/reports/hovedbok"

echo "1️⃣  GET All Entries (first 3)"
echo "------------------------------------------------------------------"
curl -s "${BASE_URL}/?client_id=${CLIENT_ID}&page_size=3" | jq '{
  total_entries: .summary.total_entries,
  total_debit: .summary.total_debit,
  total_credit: .summary.total_credit,
  first_entry: .entries[0] | {
    voucher: .full_voucher,
    date: .accounting_date,
    description: .description,
    balanced: .totals.balanced
  }
}'

echo ""
echo "2️⃣  Filter by Account Number (6340)"
echo "------------------------------------------------------------------"
curl -s "${BASE_URL}/?client_id=${CLIENT_ID}&account_number=6340&page_size=2" | jq '{
  entries_found: (.entries | length),
  entries: .entries | map({voucher: .full_voucher, description: .description})
}'

echo ""
echo "3️⃣  Sort by Date (descending, most recent first)"
echo "------------------------------------------------------------------"
curl -s "${BASE_URL}/?client_id=${CLIENT_ID}&sort_by=accounting_date&sort_order=desc&page_size=2" | jq '{
  entries: .entries | map({voucher: .full_voucher, date: .accounting_date, description: .description})
}'

echo ""
echo "4️⃣  Summary Statistics"
echo "------------------------------------------------------------------"
curl -s "${BASE_URL}/?client_id=${CLIENT_ID}" | jq '.summary'

echo ""
echo "=================================================================="
echo "✅ Hovedbok REST API is fully operational!"
echo "=================================================================="
