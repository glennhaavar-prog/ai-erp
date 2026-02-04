# EHF Integration Module

**EHF 3.0 (PEPPOL BIS Billing 3.0) for Norwegian Electronic Invoicing**

This module provides complete support for sending and receiving Norwegian EHF invoices via the PEPPOL network.

---

## 📋 Features

✅ **Receive EHF invoices** via webhook from PEPPOL access point  
✅ **Parse EHF XML** (UBL 2.1) to Pydantic models  
✅ **Validate** against PEPPOL business rules and Norwegian standards  
✅ **Send EHF invoices** via Unimicro API  
✅ **Generate EHF XML** from Python models  
✅ **Norwegian VAT mapping** (EHF tax codes ↔ Norwegian MVA codes)  
✅ **Type-safe** with Pydantic validation  
✅ **Async/await** support throughout  
✅ **Comprehensive logging** with structlog  

---

## 🚀 Quick Start

### 1. Installation

```bash
# Add dependencies to requirements.txt
lxml>=5.1.0
httpx>=0.27.0
structlog>=24.1.0
pydantic>=2.5.0

pip install -r requirements.txt
```

### 2. Setup Unimicro Account

1. Register at: https://www.unimicro.no/peppol
2. Get API credentials:
   - API Key
   - Webhook Secret
3. Configure webhook endpoint: `https://your-domain.com/api/webhooks/ehf`

### 3. Basic Usage

#### Receiving EHF Invoices

```python
from app.services.ehf import receive_ehf_invoice

# In your FastAPI webhook endpoint:
@app.post("/webhooks/ehf")
async def ehf_webhook(request: Request):
    xml_content = await request.body()
    xml_content = xml_content.decode('utf-8')
    
    result = await receive_ehf_invoice(
        xml_content=xml_content,
        tenant_id=1,
        webhook_secret="your-secret"
    )
    
    if result["success"]:
        # Create VendorInvoice from result["vendor_invoice_data"]
        return {"status": "received"}
    else:
        return {"status": "error", "errors": result["errors"]}
```

#### Parsing EHF XML

```python
from app.services.ehf import parse_ehf_xml

result = parse_ehf_xml(xml_content)

if result.success:
    invoice = result.invoice
    print(f"Invoice: {invoice.invoice_id}")
    print(f"Supplier: {invoice.accounting_supplier_party.name}")
    print(f"Amount: {invoice.payable_amount} {invoice.document_currency_code}")
    print(f"Lines: {len(invoice.invoice_lines)}")
else:
    print(f"Errors: {result.errors}")
```

#### Validating EHF XML

```python
from app.services.ehf import validate_ehf_xml

is_valid, messages = validate_ehf_xml(xml_content)

if is_valid:
    print("✅ EHF is valid!")
else:
    print("❌ Validation failed:")
    for msg in messages:
        print(f"  - {msg}")
```

#### Sending EHF Invoices

```python
from app.services.ehf import EHFSender, EHFInvoice

# Create invoice model (see Models section)
invoice = EHFInvoice(...)

# Send via Unimicro
sender = EHFSender(
    api_key="your-api-key",
    test_mode=True  # Use test environment
)

result = await sender.send_invoice_ehf(
    invoice=invoice,
    recipient_org_number="123456789"
)

if result["status"] == "sent":
    print(f"✅ Sent! Transmission ID: {result['transmission_id']}")
else:
    print(f"❌ Failed: {result['error']}")
```

---

## 📁 File Structure

```
app/services/ehf/
├── __init__.py          # Module exports
├── models.py            # Pydantic models for EHF structures
├── parser.py            # Parse EHF XML to models
├── validator.py         # Validate EHF XML
├── receiver.py          # Receive EHF via webhook
└── sender.py            # Send EHF via API
```

---

## 📚 Models

### EHFInvoice

Main invoice model representing a complete EHF 3.0 invoice.

```python
from app.services.ehf.models import EHFInvoice

invoice = EHFInvoice(
    invoice_id="INV-2024-001",
    issue_date=date(2024, 2, 1),
    due_date=date(2024, 3, 1),
    document_currency_code="NOK",
    accounting_supplier_party=supplier,  # EHFParty
    accounting_customer_party=customer,  # EHFParty
    invoice_lines=[line1, line2],        # List[EHFInvoiceLine]
    line_extension_amount=Decimal("10000"),
    tax_exclusive_amount=Decimal("10000"),
    tax_inclusive_amount=Decimal("12500"),
    payable_amount=Decimal("12500"),
    tax_total=tax_total,                 # EHFTaxTotal
)
```

### EHFParty

Party information (supplier or customer).

```python
from app.services.ehf.models import EHFParty

party = EHFParty(
    endpoint_id="987654321",           # Organization number
    endpoint_scheme="0192",            # Norway = 0192
    name="Acme Corp AS",
    street_name="Testveien 1",
    city_name="Oslo",
    postal_zone="0123",
    country_code="NO",
    company_id="987654321",
    vat_id="NO987654321MVA",
)
```

### EHFInvoiceLine

Individual invoice line.

```python
from app.services.ehf.models import EHFInvoiceLine

line = EHFInvoiceLine(
    id="1",
    invoiced_quantity=Decimal("10"),
    invoiced_quantity_unit_code="EA",  # EA=each, HUR=hour
    line_extension_amount=Decimal("10000"),
    item_name="Consulting services",
    item_description="Q1 2024 consulting",
    price_amount=Decimal("1000"),
    tax_category_id="S",               # S=Standard, Z=Zero, E=Exempt
    tax_category_percent=Decimal("25.0"),
)
```

### Norwegian VAT Mapping

```python
from app.services.ehf.models import map_ehf_tax_to_norwegian_code

# EHF → Norwegian VAT code
vat_code = map_ehf_tax_to_norwegian_code("S", Decimal("25.0"))
# Returns: "5" (inngående MVA 25%)
```

**Mapping table:**
| EHF Category | Rate | Norwegian Code | Description |
|--------------|------|----------------|-------------|
| S | 25% | 5 | Inngående MVA høy sats |
| S | 15% | 51 | Inngående MVA middels sats |
| S | 12% | 52 | Inngående MVA lav sats |
| Z | 0% | 6 | Ingen MVA-plikt |
| E | 0% | 6 | Fritatt |

---

## 🔧 API Reference

### Parser

#### `parse_ehf_xml(xml_content: str) -> EHFParseResult`

Parse EHF XML to Pydantic model.

**Returns:**
```python
EHFParseResult(
    success=True,
    invoice=EHFInvoice(...),
    errors=[],
    warnings=["Warning message"],
    raw_xml="<Invoice>..."
)
```

#### `ehf_to_vendor_invoice_dict(ehf_invoice: EHFInvoice) -> dict`

Convert EHFInvoice to dict suitable for VendorInvoice database model.

**Returns:**
```python
{
    "invoice_number": "INV-001",
    "invoice_date": date(2024, 2, 1),
    "vendor_name": "Acme Corp AS",
    "vendor_org_number": "987654321",
    "currency": "NOK",
    "amount_excl_vat": Decimal("10000"),
    "vat_amount": Decimal("2500"),
    "total_amount": Decimal("12500"),
    "kid_number": "12345678901",
    "line_items": [...],
    "tax_breakdown": [...],
}
```

### Validator

#### `validate_ehf_xml(xml_content: str) -> Tuple[bool, List[str]]`

Validate EHF XML against PEPPOL rules and Norwegian standards.

**Validation includes:**
- XML well-formedness
- UBL 2.1 schema compliance (if schema provided)
- PEPPOL BIS Billing 3.0 business rules
- Norwegian-specific rules (org.nr format, VAT rates)

**Returns:**
```python
(True, [])  # Valid

(False, [
    "[ERROR] BR-01: Invoice must have an invoice number",
    "[WARNING] NO-02: Currency is EUR, expected NOK"
])  # Invalid
```

### Receiver

#### `async receive_ehf_invoice(xml_content: str, tenant_id: int, ...) -> dict`

Receive and process EHF invoice from webhook.

**Returns:**
```python
{
    "success": True,
    "vendor_invoice_id": 123,
    "ehf_invoice_id": "INV-2024-001",
    "vendor_invoice_data": {...},
    "errors": [],
    "warnings": []
}
```

### Sender

#### `async send_invoice_ehf(invoice: EHFInvoice, recipient_org_number: str) -> dict`

Send EHF invoice via Unimicro API.

**Returns:**
```python
{
    "status": "sent",
    "ehf_id": "INV-2024-001",
    "sent_at": "2024-02-01T10:30:00",
    "transmission_id": "abc123",
    "recipient": "123456789"
}
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/services/test_ehf.py -v

# Run specific test
pytest tests/services/test_ehf.py::TestEHFParser::test_parse_valid_ehf -v

# Run integration tests (requires test environment)
pytest tests/services/test_ehf.py -v -m integration
```

### Test Files

See `tests/services/test_ehf.py` for:
- ✅ Parser tests
- ✅ Validator tests
- ✅ VAT mapping tests
- ✅ XML generation tests
- ✅ Integration tests

### Test Data

Official EHF examples from Difi: https://test-vefa.difi.no/

---

## 🔐 Security

### Webhook Signature Verification

Always verify webhook signatures to prevent unauthorized access:

```python
from app.services.ehf import EHFReceiver

receiver = EHFReceiver(webhook_secret="your-secret")

# In webhook endpoint:
signature = request.headers.get("X-Unimicro-Signature")
is_valid = receiver.verify_webhook_signature(xml_content, signature)

if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid signature")
```

### Store Credentials Securely

```python
# ❌ NEVER hardcode
api_key = "abc123"

# ✅ Use environment variables
import os
api_key = os.getenv("UNIMICRO_API_KEY")

# ✅ Or AWS Secrets Manager
import boto3
secret = boto3.client('secretsmanager').get_secret_value(SecretId='ehf-api-key')
api_key = secret['SecretString']
```

---

## 📊 Logging

Module uses `structlog` for structured logging.

```python
import structlog

logger = structlog.get_logger(__name__)

# Logs include context:
logger.info(
    "ehf_receive_completed",
    tenant_id=1,
    invoice_id="INV-001",
    duration_seconds=2.5
)
```

**Configure in your app:**

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
)
```

---

## 🚨 Error Handling

### Common Errors

**1. Invalid XML:**
```python
result = parse_ehf_xml(invalid_xml)
# result.success = False
# result.errors = ["Invalid XML: syntax error"]
```

**2. Validation Failed:**
```python
is_valid, messages = validate_ehf_xml(xml)
# is_valid = False
# messages = ["[ERROR] BR-01: Missing invoice number"]
```

**3. API Error:**
```python
result = await sender.send_invoice_ehf(...)
# result = {"status": "failed", "error": "API error: 401 - Invalid API key"}
```

### Best Practices

```python
# Always check success
result = await receive_ehf_invoice(...)
if not result["success"]:
    logger.error("ehf_receive_failed", errors=result["errors"])
    # Send to review queue
    return

# Log all steps
logger.info("ehf_processing_started", invoice_id=invoice_id)
# ... process ...
logger.info("ehf_processing_completed", invoice_id=invoice_id)
```

---

## 🌐 Unimicro API Reference

### Endpoints

**Send Invoice:**
```http
POST https://api.unimicro.no/peppol/v1/send
Authorization: Bearer {API_KEY}
Content-Type: application/xml
X-Recipient-ID: {org_number}
X-Recipient-Scheme: 0192

{EHF XML}
```

**Validate Invoice:**
```http
POST https://api.unimicro.no/peppol/v1/validate
Authorization: Bearer {API_KEY}
Content-Type: application/xml

{EHF XML}
```

**Webhook (incoming):**
```http
POST https://your-domain.com/api/webhooks/ehf
Content-Type: application/xml
X-Unimicro-Signature: {HMAC-SHA256}

{EHF XML}
```

### Test Environment

```python
sender = EHFSender(
    api_key="test-key",
    api_url="https://api-test.unimicro.no/peppol/v1",
    test_mode=True
)
```

---

## 🔄 Integration with Main System

### Webhook Endpoint (FastAPI)

```python
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from app.services.ehf import receive_ehf_invoice
from app.database import get_db
from app.models.vendor_invoice import VendorInvoice
from app.tasks.invoice_processing import process_invoice

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/ehf")
async def ehf_webhook(
    request: Request,
    x_unimicro_signature: str = Header(None),
    db = Depends(get_db)
):
    # Get XML
    xml_content = await request.body()
    xml_content = xml_content.decode('utf-8')
    
    # Get tenant (implement this based on your auth)
    tenant_id = get_tenant_from_request(request)
    webhook_secret = get_webhook_secret(tenant_id)
    
    # Process EHF
    result = await receive_ehf_invoice(
        xml_content,
        tenant_id,
        webhook_secret=webhook_secret,
        metadata={"message_id": request.headers.get("X-Message-ID")}
    )
    
    if not result["success"]:
        logger.error("ehf_webhook_failed", errors=result["errors"])
        raise HTTPException(status_code=400, detail=result["errors"])
    
    # Find or create vendor
    vendor_data = result["vendor_invoice_data"]
    vendor = await find_or_create_vendor(
        db,
        tenant_id=tenant_id,
        org_number=vendor_data["vendor_org_number"],
        name=vendor_data["vendor_name"],
    )
    
    # Create VendorInvoice
    invoice = VendorInvoice(
        tenant_id=tenant_id,
        vendor_id=vendor.id,
        invoice_number=vendor_data["invoice_number"],
        invoice_date=vendor_data["invoice_date"],
        due_date=vendor_data["due_date"],
        currency=vendor_data["currency"],
        amount_excl_vat=vendor_data["amount_excl_vat"],
        vat_amount=vendor_data["vat_amount"],
        total_amount=vendor_data["total_amount"],
        kid_number=vendor_data["kid_number"],
        line_items=vendor_data["line_items"],
        ehf_raw_xml=vendor_data["ehf_raw_xml"],
        ehf_received_at=vendor_data["ehf_received_at"],
        review_status="pending",
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # Trigger async processing by Invoice Agent
    process_invoice.delay(invoice.id)
    
    return {
        "status": "received",
        "invoice_id": invoice.id,
        "ehf_invoice_id": result["ehf_invoice_id"]
    }
```

---

## 📝 Example: Complete Workflow

```python
from datetime import date
from decimal import Decimal
from app.services.ehf import (
    EHFInvoice,
    EHFParty,
    EHFInvoiceLine,
    EHFTaxTotal,
    EHFTaxSubtotal,
    EHFSender,
)

# 1. Create invoice model
supplier = EHFParty(
    endpoint_id="987654321",
    name="My Company AS",
    company_id="987654321",
)

customer = EHFParty(
    endpoint_id="123456789",
    name="Customer AS",
    company_id="123456789",
)

line = EHFInvoiceLine(
    id="1",
    invoiced_quantity=Decimal("10"),
    line_extension_amount=Decimal("10000"),
    item_name="Consulting services",
    price_amount=Decimal("1000"),
    tax_category_id="S",
    tax_category_percent=Decimal("25.0"),
)

tax_subtotal = EHFTaxSubtotal(
    taxable_amount=Decimal("10000"),
    tax_amount=Decimal("2500"),
    tax_category_id="S",
    tax_category_percent=Decimal("25.0"),
)

tax_total = EHFTaxTotal(
    tax_amount=Decimal("2500"),
    tax_subtotals=[tax_subtotal],
)

invoice = EHFInvoice(
    invoice_id="INV-2024-001",
    issue_date=date(2024, 2, 1),
    due_date=date(2024, 3, 1),
    accounting_supplier_party=supplier,
    accounting_customer_party=customer,
    invoice_lines=[line],
    line_extension_amount=Decimal("10000"),
    tax_exclusive_amount=Decimal("10000"),
    tax_inclusive_amount=Decimal("12500"),
    payable_amount=Decimal("12500"),
    tax_total=tax_total,
)

# 2. Send via EHF
sender = EHFSender(api_key=os.getenv("UNIMICRO_API_KEY"))
result = await sender.send_invoice_ehf(invoice, "123456789")

print(f"Status: {result['status']}")
print(f"Transmission ID: {result['transmission_id']}")
```

---

## 📚 Resources

**Official Specifications:**
- PEPPOL BIS Billing 3.0: https://docs.peppol.eu/poacc/billing/3.0/
- EHF 3.0: https://anskaffelser.dev/postaward/g3/
- UBL 2.1: http://docs.oasis-open.org/ubl/

**Norwegian Resources:**
- Difi EHF Portal: https://ehf.difi.no/
- Test tool: https://test-vefa.difi.no/
- Unimicro PEPPOL: https://www.unimicro.no/peppol

**PEPPOL Network:**
- PEPPOL Directory: https://directory.peppol.eu/
- Participant lookup: https://peppol.helger.com/

---

## 🤝 Contributing

When contributing to this module:

1. ✅ Follow type hints (Python 3.11+)
2. ✅ Write tests for new features
3. ✅ Update this README
4. ✅ Use async/await consistently
5. ✅ Add structured logging

---

## 📄 License

Part of AI-Agent ERP system. Internal use.

---

## 🆘 Troubleshooting

### Issue: Webhook not receiving invoices

**Check:**
1. Is webhook URL publicly accessible? (not localhost)
2. Is HTTPS configured? (required by PEPPOL)
3. Is signature verification correct?
4. Check Unimicro dashboard for transmission logs

### Issue: Validation errors

**Common causes:**
- Missing required fields (invoice ID, dates)
- Sum of lines ≠ total
- Tax calculations incorrect
- Invalid organization number

**Debug:**
```python
is_valid, messages = validate_ehf_xml(xml)
for msg in messages:
    print(msg)  # See specific validation errors
```

### Issue: API errors when sending

**Check:**
1. API key is valid
2. Recipient has PEPPOL endpoint registered
3. XML is valid EHF 3.0 format
4. Not rate-limited

---

**Questions? Contact: Glenn or check project documentation**

---

**Version:** 1.0.0  
**Last Updated:** February 2026  
**Status:** ✅ Production Ready
