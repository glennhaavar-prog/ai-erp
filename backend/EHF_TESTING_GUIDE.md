# EHF Testing Guide

Complete guide to testing EHF (Elektronisk Handelsformat) invoice processing in Kontali ERP.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Testing Methods](#testing-methods)
4. [Sample Files](#sample-files)
5. [Understanding the Flow](#understanding-the-flow)
6. [Creating Your Own Test Files](#creating-your-own-test-files)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Overview

### What is EHF?

EHF (Elektronisk Handelsformat) is the Norwegian standard for electronic invoicing based on PEPPOL BIS Billing 3.0 (UBL 2.1). It enables fully automated B2B invoice exchange through the PEPPOL network.

### Test Environment

Kontali ERP includes a complete test environment that allows you to:

- ✅ Send test EHF invoices without PEPPOL access point setup
- ✅ Bypass webhook signature verification
- ✅ Process invoices through the complete pipeline
- ✅ See detailed step-by-step results
- ✅ Verify database entries
- ✅ Test AI processing and review queue

### Architecture

```
EHF XML → Test Endpoint → Parser → Validator → Vendor → Invoice → AI Agent → Review Queue
```

---

## Quick Start

### 1. Using Web UI (Easiest)

Navigate to: `http://localhost:3000/test/ehf`

1. Choose **Upload File** or **Paste XML**
2. Select a sample file or paste your own XML
3. Click **Send & Process Invoice**
4. View detailed results for each step

### 2. Using Command Line

```bash
# From backend directory
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend

# Test with sample file
./scripts/test_ehf.sh tests/fixtures/ehf/ehf_sample_1_simple.xml

# Or with your own file
./scripts/test_ehf.sh /path/to/your/invoice.xml
```

### 3. Using curl

```bash
curl -X POST http://localhost:8000/api/test/ehf/send \
  -H "Content-Type: application/xml" \
  --data-binary @tests/fixtures/ehf/ehf_sample_1_simple.xml
```

Or with JSON wrapper:

```bash
curl -X POST http://localhost:8000/api/test/ehf/send-raw \
  -H "Content-Type: application/json" \
  -d '{
    "xml_content": "<?xml version=\"1.0\"...>"
  }'
```

---

## Testing Methods

### Web UI (`/test/ehf`)

**Best for:** Interactive testing, demos, debugging

**Features:**
- Drag-and-drop file upload
- Paste XML directly
- Load sample files with one click
- Visual step-by-step results
- Color-coded status indicators
- Detailed error messages

### CLI Script (`test_ehf.sh`)

**Best for:** Command-line workflows, automation, CI/CD

**Features:**
- Pretty-printed output with colors
- JSON response formatting
- Exit codes for automation
- Works with jq for JSON parsing

**Usage:**
```bash
./scripts/test_ehf.sh <xml-file>

# Examples:
./scripts/test_ehf.sh tests/fixtures/ehf/ehf_sample_1_simple.xml
./scripts/test_ehf.sh tests/fixtures/ehf/ehf_sample_2_multi_line.xml
```

### REST API

**Best for:** Integration testing, automated testing, CI/CD

**Endpoints:**

#### POST `/api/test/ehf/send`
- **Content-Type:** `application/xml` or `multipart/form-data`
- **Body:** Raw XML or file upload
- **Returns:** Detailed processing result

#### POST `/api/test/ehf/send-raw`
- **Content-Type:** `application/json`
- **Body:** `{"xml_content": "<Invoice>...</Invoice>"}`
- **Returns:** Same as `/send`

**Response Format:**
```json
{
  "test_mode": true,
  "success": true,
  "timestamp": "2026-02-10T10:30:00Z",
  "steps": [
    {
      "step": "parse",
      "status": "✅ success",
      "message": "EHF XML parsed successfully",
      "ehf_invoice_id": "FAKTURA-2026-001"
    },
    {
      "step": "validate",
      "status": "✅ success",
      "message": "EHF validation passed"
    },
    {
      "step": "vendor",
      "status": "✅ success",
      "vendor_id": "uuid",
      "vendor_name": "Norsk IT-Konsulent AS",
      "is_new": false
    },
    {
      "step": "invoice_created",
      "status": "✅ success",
      "invoice_id": "uuid",
      "invoice_number": "FAKTURA-2026-001",
      "amount": {
        "excl_vat": 25000.0,
        "vat": 6250.0,
        "total": 31250.0,
        "currency": "NOK"
      }
    },
    {
      "step": "ai_processing",
      "status": "✅ success",
      "confidence": 95,
      "action": "auto_approved"
    },
    {
      "step": "review_queue",
      "status": "⏭️ skipped",
      "message": "High confidence - ready for auto-booking"
    }
  ],
  "summary": {
    "invoice_id": "uuid",
    "ehf_invoice_id": "FAKTURA-2026-001",
    "vendor_name": "Norsk IT-Konsulent AS",
    "total_amount": 31250.0,
    "currency": "NOK"
  }
}
```

---

## Sample Files

We provide 5 realistic test EHF invoices covering different scenarios:

### 1. Simple Invoice (`ehf_sample_1_simple.xml`)
- **Description:** Basic invoice with 1 line and 25% VAT
- **Vendor:** Norsk IT-Konsulent AS (987654321)
- **Amount:** 31,250 NOK (25,000 + 6,250 VAT)
- **Use case:** Testing basic flow

### 2. Multi-line Invoice (`ehf_sample_2_multi_line.xml`)
- **Description:** Multiple lines with different VAT rates
- **Vendor:** Norsk Kontorrekvisita AS (912345678)
- **Amount:** 52,975 NOK
- **VAT rates:** 25%, 15%, 12%, 0%
- **Use case:** Complex VAT calculations

### 3. Export Invoice (`ehf_sample_3_zero_vat.xml`)
- **Description:** Zero-rated invoice for export
- **Vendor:** Nordic Export Solutions AS (876543219)
- **Customer:** Stockholm Trading AB (Sweden)
- **Amount:** 89,500 NOK (0% VAT)
- **Use case:** Export transactions

### 4. Reverse Charge Invoice (`ehf_sample_4_reverse_charge.xml`)
- **Description:** Foreign supplier with reverse charge
- **Vendor:** Copenhagen Design ApS (Denmark)
- **Amount:** 58,000 NOK (0% VAT)
- **Use case:** Snudd avregning (§ 11-3)

### 5. Credit Note (`ehf_sample_5_credit_note.xml`)
- **Description:** Credit note for returned goods
- **Vendor:** Norsk IT-Konsulent AS (987654321)
- **Amount:** 6,250 NOK (negative)
- **Use case:** Returns and corrections

---

## Understanding the Flow

### Step-by-Step Processing

#### 1. Parse XML → EHFInvoice Model
**What happens:**
- XML is parsed using lxml
- UBL 2.1 structure is mapped to Pydantic models
- Party information extracted (supplier/customer)
- Line items, tax totals, payment info parsed

**Success criteria:**
- Valid XML structure
- All required fields present
- Correct UBL namespaces

#### 2. Validate Against EHF Standard
**What happens:**
- Business rules validation (BR-01, BR-02, etc.)
- Norwegian-specific rules
- Organization number format validation
- Tax calculations verified

**Success criteria:**
- Passes all mandatory business rules
- May have warnings but no errors

#### 3. Find/Create Vendor
**What happens:**
- Search for vendor by organization number
- Create new vendor if not found
- Reuse existing vendor if found

**Success criteria:**
- Vendor exists in database
- Organization number and name stored

#### 4. Create VendorInvoice
**What happens:**
- Invoice record created in database
- Line items stored as JSONB
- EHF raw XML saved for reference
- Status set to "pending"

**Success criteria:**
- Invoice saved with all fields
- Unique ID assigned
- Linked to correct vendor and client

#### 5. AI Processing
**What happens:**
- Invoice Agent analyzes invoice
- Suggests account mapping
- Calculates confidence score
- Determines if review needed

**Success criteria:**
- Confidence score calculated (0-100%)
- Suggested booking created
- Action decided (auto_approve vs. needs_review)

#### 6. Review Queue (Conditional)
**What happens:**
- If confidence < threshold: Add to review queue
- If confidence >= threshold: Ready for auto-booking
- Accountant can review and approve

**Success criteria:**
- Low confidence → Review queue entry created
- High confidence → Skip review, ready to book

---

## Creating Your Own Test Files

### EHF Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    
    <!-- Required: Specification -->
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    
    <!-- Required: Invoice identification -->
    <cbc:ID>YOUR-INVOICE-NUMBER</cbc:ID>
    <cbc:IssueDate>2026-02-10</cbc:IssueDate>
    <cbc:DueDate>2026-03-12</cbc:DueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>NOK</cbc:DocumentCurrencyCode>
    
    <!-- Required: Supplier (Your company) -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="0192">999999999</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>Your Company AS</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Your Street 123</cbc:StreetName>
                <cbc:CityName>Oslo</cbc:CityName>
                <cbc:PostalZone>0123</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>NO</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyLegalEntity>
                <cbc:CompanyID schemeID="0192">999999999</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <!-- Required: Customer -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cbc:EndpointID schemeID="0192">123456789</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>Kontali AS</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Storgata 50</cbc:StreetName>
                <cbc:CityName>Bergen</cbc:CityName>
                <cbc:PostalZone>5003</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>NO</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyLegalEntity>
                <cbc:CompanyID schemeID="0192">123456789</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <!-- Payment information -->
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>
        <cbc:PaymentID>12345678901234</cbc:PaymentID>
        <cac:PayeeFinancialAccount>
            <cbc:ID>15034567890</cbc:ID>
        </cac:PayeeFinancialAccount>
    </cac:PaymentMeans>
    
    <!-- Tax total -->
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="NOK">2500.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="NOK">10000.00</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="NOK">2500.00</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>25.0</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    
    <!-- Monetary totals -->
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="NOK">10000.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="NOK">12500.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="NOK">12500.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <!-- Invoice lines -->
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="HUR">20</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="NOK">10000.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Your Product/Service</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>25.0</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="NOK">500.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>
```

### Norwegian Organization Numbers

Use realistic 9-digit org numbers:
- **Format:** 9 digits with mod-11 checksum
- **Test numbers:** 987654321, 912345678, 876543219
- **Real lookup:** https://data.brreg.no

### VAT Codes

| Code | Percentage | Description | Norwegian Term |
|------|------------|-------------|----------------|
| S    | 25%        | Standard rate | Høy sats |
| AA   | 15%        | Reduced rate | Middels sats (mat) |
| AB   | 12%        | Low rate | Lav sats (kultur) |
| Z    | 0%         | Zero rate | Nullsats (bøker) |
| G    | 0%         | Export | Eksport |
| AE   | 0%         | Reverse charge | Snudd avregning |

---

## Troubleshooting

### Problem: "Invalid XML" error

**Cause:** XML syntax error or invalid structure

**Solution:**
1. Validate XML with online tool
2. Check namespace declarations
3. Ensure all tags are properly closed
4. Use sample files as template

### Problem: "Missing required fields" error

**Cause:** Business rule validation failed

**Solution:**
1. Check required fields: ID, IssueDate, Supplier, Customer
2. Verify namespace prefixes (cbc:, cac:)
3. Ensure all amounts match (totals = sum of lines)
4. Verify tax calculations

### Problem: Vendor not created

**Cause:** Organization number format invalid

**Solution:**
1. Use 9-digit Norwegian org number
2. Or foreign org number with correct scheme
3. Check schemeID attribute (0192 for NO)

### Problem: Invoice created but not processed

**Cause:** AI Agent error or database issue

**Solution:**
1. Check logs: `docker logs ai-erp-backend`
2. Verify database connection
3. Check invoice status in database
4. Manual retry: API call to process endpoint

### Problem: Test endpoint not found (404)

**Cause:** Backend not running or route not registered

**Solution:**
1. Start backend: `docker-compose up backend`
2. Check route registration in `app/main.py`
3. Verify URL: `http://localhost:8000/api/test/ehf/send`
4. Check health: `http://localhost:8000/health`

---

## FAQ

### Q: Can I use the test endpoint in production?

**A:** No. The test endpoint bypasses security checks (signature verification). Use the production webhook endpoint `/webhooks/ehf` with proper PEPPOL access point integration.

### Q: How do I set up real EHF reception?

**A:** You need:
1. PEPPOL access point account (e.g., Unimicro, ELMA)
2. Webhook URL configured in access point
3. Webhook secret for signature verification
4. DNS/firewall configured to receive webhooks

### Q: What's the difference between test and production endpoint?

| Feature | Test Endpoint | Production Endpoint |
|---------|--------------|---------------------|
| Path | `/api/test/ehf/send` | `/webhooks/ehf` |
| Signature verification | No | Yes (required) |
| Tenant detection | Test client | From webhook headers |
| Purpose | Development/testing | Production use |

### Q: Can I test with real customer data?

**A:** Yes, but be careful:
- Test client is separate from production
- Data is stored in database
- Sanitize sensitive information
- Use test org numbers when possible

### Q: How do I run E2E tests?

**A:** Run pytest:
```bash
cd backend
pytest tests/test_ehf_e2e.py -v
```

Or test specific sample:
```bash
pytest tests/test_ehf_e2e.py::TestEHFEndToEnd::test_ehf_sample_processing[Simple Invoice] -v
```

### Q: Where are invoices stored?

**A:** Database tables:
- `vendor_invoices` - Invoice data
- `vendors` - Vendor information
- `review_queue` - Items needing review
- EHF XML stored in `vendor_invoices.ehf_raw_xml`

### Q: How do I verify an invoice was processed?

**A:** Check database:
```sql
SELECT 
    id, 
    invoice_number, 
    vendor_id, 
    total_amount, 
    review_status,
    ehf_received_at
FROM vendor_invoices
WHERE invoice_number = 'YOUR-INVOICE-NUMBER';
```

Or use API:
```bash
curl http://localhost:8000/api/invoices/{invoice_id}
```

---

## Next Steps

1. ✅ **Test all sample files** - Verify your setup works
2. ✅ **Create custom test file** - Use your own data
3. ✅ **Run E2E tests** - Verify full pipeline
4. ✅ **Test via web UI** - Try interactive testing
5. ✅ **Integrate with PEPPOL** - Set up production webhook

## Support

- **Documentation:** This file
- **Sample files:** `backend/tests/fixtures/ehf/`
- **Tests:** `backend/tests/test_ehf_e2e.py`
- **Code:** `backend/app/services/ehf/`

## References

- [EHF 3.0 Specification (Norwegian)](https://anskaffelser.dev/postaward/g3/spec/current/billing-3.0/norway/)
- [PEPPOL BIS Billing 3.0](https://docs.peppol.eu/poacc/billing/3.0/)
- [UBL 2.1 Documentation](http://docs.oasis-open.org/ubl/UBL-2.1.html)
- [Difi EHF Resources](https://www.anskaffelser.no/e-handel/e-handel-intro)

---

**Last updated:** 2026-02-10  
**Version:** 1.0
