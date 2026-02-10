#!/bin/bash
#
# EHF Test Script
# Usage: ./test_ehf.sh <xml-file>
#
# Sends EHF XML to test endpoint and displays pretty result
#

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
ENDPOINT="${API_URL}/api/test/ehf/send"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No XML file specified${NC}"
    echo ""
    echo "Usage: $0 <xml-file>"
    echo ""
    echo "Examples:"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_1_simple.xml"
    echo "  $0 my-test-invoice.xml"
    echo ""
    echo "Or use sample files:"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_1_simple.xml       # Simple invoice (25% VAT)"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_2_multi_line.xml    # Multi-line (different VAT rates)"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_3_zero_vat.xml      # Export (0% VAT)"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_4_reverse_charge.xml # Reverse charge"
    echo "  $0 backend/tests/fixtures/ehf/ehf_sample_5_credit_note.xml   # Credit note"
    exit 1
fi

XML_FILE="$1"

# Check if file exists
if [ ! -f "$XML_FILE" ]; then
    echo -e "${RED}Error: File not found: $XML_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           EHF Test Endpoint - Invoice Tester              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📄 XML File:${NC} $XML_FILE"
echo -e "${YELLOW}🌐 Endpoint:${NC} $ENDPOINT"
echo ""
echo -e "${BLUE}Sending EHF invoice...${NC}"
echo ""

# Create temporary file for response
RESPONSE_FILE=$(mktemp)

# Send request
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
    -X POST "$ENDPOINT" \
    -H "Content-Type: application/xml" \
    --data-binary @"$XML_FILE")

# Parse response
RESPONSE=$(cat "$RESPONSE_FILE")
rm "$RESPONSE_FILE"

# Check HTTP status
if [ "$HTTP_CODE" -ne 200 ]; then
    echo -e "${RED}✗ HTTP Error: $HTTP_CODE${NC}"
    echo ""
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# Pretty print results
echo -e "${GREEN}✓ HTTP 200 OK${NC}"
echo ""

# Extract key information using jq
if command -v jq &> /dev/null; then
    # Check overall success
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    
    if [ "$SUCCESS" = "true" ]; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  SUCCESS - Invoice Processed Successfully                ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Processing steps
        echo -e "${BLUE}Processing Steps:${NC}"
        echo ""
        echo "$RESPONSE" | jq -r '.steps[] | "\(.step): \(.status)"' | while read -r line; do
            if [[ "$line" == *"✅"* ]]; then
                echo -e "  ${GREEN}$line${NC}"
            elif [[ "$line" == *"⚠️"* ]]; then
                echo -e "  ${YELLOW}$line${NC}"
            elif [[ "$line" == *"❌"* ]]; then
                echo -e "  ${RED}$line${NC}"
            else
                echo -e "  $line"
            fi
        done
        
        echo ""
        echo -e "${BLUE}Summary:${NC}"
        echo "$RESPONSE" | jq -r '.summary | to_entries[] | "  \(.key): \(.value)"'
        
        # Show warnings if any
        WARNINGS=$(echo "$RESPONSE" | jq -r '.steps[] | select(.warnings) | .warnings[]' 2>/dev/null)
        if [ -n "$WARNINGS" ]; then
            echo ""
            echo -e "${YELLOW}Warnings:${NC}"
            echo "$WARNINGS" | while read -r warning; do
                echo -e "  ${YELLOW}⚠️  $warning${NC}"
            done
        fi
        
        # Show review queue info
        REVIEW_QUEUE_ID=$(echo "$RESPONSE" | jq -r '.steps[] | select(.review_queue_id) | .review_queue_id' 2>/dev/null)
        if [ -n "$REVIEW_QUEUE_ID" ] && [ "$REVIEW_QUEUE_ID" != "null" ]; then
            echo ""
            echo -e "${YELLOW}📋 Added to Review Queue${NC}"
            echo -e "  Review Queue ID: $REVIEW_QUEUE_ID"
        else
            echo ""
            echo -e "${GREEN}✓ High confidence - Ready for auto-booking${NC}"
        fi
        
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  FAILED - Processing Error                               ${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Show errors
        ERRORS=$(echo "$RESPONSE" | jq -r '.steps[] | select(.errors) | .errors[]' 2>/dev/null)
        if [ -n "$ERRORS" ]; then
            echo -e "${RED}Errors:${NC}"
            echo "$ERRORS" | while read -r error; do
                echo -e "  ${RED}✗ $error${NC}"
            done
        fi
    fi
    
    echo ""
    echo -e "${BLUE}Full Response (JSON):${NC}"
    echo "$RESPONSE" | jq '.'
    
else
    # jq not available, show raw response
    echo "$RESPONSE"
fi

echo ""
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
