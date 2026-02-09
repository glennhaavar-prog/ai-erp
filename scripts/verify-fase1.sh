#!/bin/bash

# Kontali ERP - Fase 1 Verifikasjonsskript
# Kjører alle 5 tester for å bekrefte at regnskapskjernen fungerer

set -e

API="http://localhost:8000"
CLIENT_ID="8f6d593d-cb4e-42eb-a51c-a7b1dab660dc"

echo "============================================"
echo "KONTALI FASE 1 - VERIFIKASJONSTEST"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

function test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((pass_count++))
}

function test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((fail_count++))
}

function test_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Bokfør bilag → sjekk gjennomslag"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Bokfør testbilag
test_info "Bokfører testbilag..."
ENTRY_RESPONSE=$(curl -s -X POST "$API/api/journal-entries/" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"accounting_date\": \"2026-02-08\",
    \"voucher_series\": \"TEST\",
    \"description\": \"Verifikasjonstest - Kontorrekvisita\",
    \"source_type\": \"manual\",
    \"lines\": [
      {
        \"account_number\": \"6100\",
        \"debit_amount\": 500.00,
        \"credit_amount\": 0.00,
        \"vat_code\": \"5\",
        \"vat_amount\": 125.00,
        \"line_description\": \"Kontorrekvisita\"
      },
      {
        \"account_number\": \"2710\",
        \"debit_amount\": 125.00,
        \"credit_amount\": 0.00,
        \"vat_code\": null,
        \"vat_amount\": 0.00,
        \"line_description\": \"Inngående MVA 25%\"
      },
      {
        \"account_number\": \"2400\",
        \"debit_amount\": 0.00,
        \"credit_amount\": 625.00,
        \"vat_code\": null,
        \"vat_amount\": 0.00,
        \"line_description\": \"Leverandørgjeld\"
      }
    ]
  }")

ENTRY_ID=$(echo "$ENTRY_RESPONSE" | jq -r '.id // empty')

if [ -z "$ENTRY_ID" ]; then
    test_fail "Kunne ikke opprette testbilag"
    echo "Response: $ENTRY_RESPONSE"
else
    test_pass "Testbilag opprettet: $ENTRY_ID"
    
    # Sjekk i hovedbok
    test_info "Sjekker hovedbok for konto 6100..."
    HOVEDBOK=$(curl -s "$API/api/reports/hovedbok?client_id=$CLIENT_ID&account_number=6100")
    ENTRY_COUNT=$(echo "$HOVEDBOK" | jq '.entries | length')
    
    if [ "$ENTRY_COUNT" -gt 0 ]; then
        test_pass "Bilag synlig i hovedbok ($ENTRY_COUNT posteringer)"
    else
        test_fail "Bilag IKKE synlig i hovedbok"
    fi
    
    # Sjekk i saldobalanse
    test_info "Sjekker saldobalanse..."
    SALDOBALANSE=$(curl -s "$API/api/reports/saldobalanse?client_id=$CLIENT_ID")
    ACCOUNT_6100=$(echo "$SALDOBALANSE" | jq '.balances[] | select(.account_number=="6100")')
    
    if [ -n "$ACCOUNT_6100" ]; then
        test_pass "Konto 6100 synlig i saldobalanse"
    else
        test_fail "Konto 6100 IKKE synlig i saldobalanse"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Saldobalanse balanserer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SALDOBALANSE=$(curl -s "$API/api/reports/saldobalanse?client_id=$CLIENT_ID")
TOTAL_DEBIT=$(echo "$SALDOBALANSE" | jq '.total_debit')
TOTAL_CREDIT=$(echo "$SALDOBALANSE" | jq '.total_credit')
IS_BALANCED=$(echo "$SALDOBALANSE" | jq '.is_balanced')

test_info "Total debet: $TOTAL_DEBIT"
test_info "Total kredit: $TOTAL_CREDIT"

if [ "$IS_BALANCED" = "true" ]; then
    test_pass "Saldobalanse balanserer (debet = kredit)"
else
    test_fail "Saldobalanse balanserer IKKE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Drilldown fungerer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_info "Tester Saldobalanse → Hovedbok → Bilag..."

# 1. Hent konto fra saldobalanse
ACCOUNT=$(echo "$SALDOBALANSE" | jq -r '.balances[0].account_number')
test_info "Valgt konto: $ACCOUNT"

# 2. Hent hovedbok for kontoen
HOVEDBOK=$(curl -s "$API/api/reports/hovedbok?client_id=$CLIENT_ID&account_number=$ACCOUNT&limit=1")
VOUCHER_ID=$(echo "$HOVEDBOK" | jq -r '.entries[0].entry_id // empty')

if [ -z "$VOUCHER_ID" ]; then
    test_fail "Kunne ikke hente posteringer fra hovedbok"
else
    test_pass "Hovedbok returnerte posteringer for konto $ACCOUNT"
    
    # 3. Hent bilag
    VOUCHER=$(curl -s "$API/api/vouchers/$VOUCHER_ID")
    VOUCHER_NUMBER=$(echo "$VOUCHER" | jq -r '.voucher_number // empty')
    
    if [ -n "$VOUCHER_NUMBER" ]; then
        test_pass "Bilag hentet: $VOUCHER_NUMBER"
    else
        test_fail "Kunne ikke hente bilag $VOUCHER_ID"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Tallkonsistens (3 kontoer)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_info "Verifiserer tallkonsistens mellom saldobalanse og hovedbok..."

for ACCOUNT in "1920" "3000" "6000"; do
    # Hent saldo fra saldobalanse
    SALDO_BALANCE=$(echo "$SALDOBALANSE" | jq ".balances[] | select(.account_number==\"$ACCOUNT\") | .balance")
    
    # Hent posteringer fra hovedbok og beregn manuell sum
    HOVEDBOK=$(curl -s "$API/api/reports/hovedbok?client_id=$CLIENT_ID&account_number=$ACCOUNT")
    MANUAL_SUM=$(echo "$HOVEDBOK" | jq '[.entries[] | (.debit_amount - .credit_amount)] | add')
    
    if [ -z "$SALDO_BALANCE" ] || [ "$SALDO_BALANCE" = "null" ]; then
        test_info "Konto $ACCOUNT: Ikke funnet"
    else
        DIFF=$(echo "$SALDO_BALANCE - $MANUAL_SUM" | bc)
        ABS_DIFF=$(echo "$DIFF" | tr -d '-')
        
        test_info "Konto $ACCOUNT: Saldobalanse=$SALDO_BALANCE, Hovedbok sum=$MANUAL_SUM, Diff=$DIFF"
        
        # Accept small differences (< 0.01) due to floating point
        if (( $(echo "$ABS_DIFF < 0.01" | bc -l) )); then
            test_pass "Konto $ACCOUNT: Tallene stemmer"
        else
            test_fail "Konto $ACCOUNT: Avvik på $DIFF"
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Kryssnavigering"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_info "Sjekker at API-endepunkter støtter kryssnavigering..."

# Sjekk at bilag-API returnerer account_number (for link til hovedbok)
if [ -n "$VOUCHER_ID" ]; then
    VOUCHER=$(curl -s "$API/api/vouchers/$VOUCHER_ID")
    FIRST_ACCOUNT=$(echo "$VOUCHER" | jq -r '.lines[0].account_number // empty')
    
    if [ -n "$FIRST_ACCOUNT" ]; then
        test_pass "Bilag returnerer kontonummer (kan linke til hovedbok)"
    else
        test_fail "Bilag mangler kontonummer"
    fi
fi

# Sjekk at hovedbok returnerer entry_id (for link til bilag)
HOVEDBOK=$(curl -s "$API/api/reports/hovedbok?client_id=$CLIENT_ID&limit=1")
ENTRY_ID_CHECK=$(echo "$HOVEDBOK" | jq -r '.entries[0].entry_id // empty')

if [ -n "$ENTRY_ID_CHECK" ]; then
    test_pass "Hovedbok returnerer entry_id (kan linke til bilag)"
else
    test_fail "Hovedbok mangler entry_id"
fi

echo ""
echo "============================================"
echo "RESULTATER"
echo "============================================"
echo ""
echo -e "${GREEN}✓ PASS${NC}: $pass_count"
echo -e "${RED}✗ FAIL${NC}: $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}🎉 ALLE TESTER BESTÅTT!${NC}"
    exit 0
else
    echo -e "${RED}❌ $fail_count TESTER FEILET${NC}"
    exit 1
fi
