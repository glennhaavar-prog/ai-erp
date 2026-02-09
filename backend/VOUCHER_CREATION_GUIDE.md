# Voucher Creation Engine - Komplett Guide
## KONTALI SPRINT 1 - Task 2

**SkatteFUNN-kritisk**: Dette er kjernen i Kontali's automatiske bokføring!

---

## 📖 Innholdsfortegnelse

1. [Oversikt](#oversikt)
2. [Arkitektur](#arkitektur)
3. [Norsk Bokføringspraksis](#norsk-bokføringspraksis)
4. [API Dokumentasjon](#api-dokumentasjon)
5. [Database Schema](#database-schema)
6. [Kodeeksempler](#kodeeksempler)
7. [Testing](#testing)
8. [Feilhåndtering](#feilhåndtering)
9. [Integrasjoner](#integrasjoner)

---

## 📋 Oversikt

Voucher Creation Engine er en automatisk "posting engine" som genererer og lagrer journal entries (vouchers/bilag) fra AI-analyserte leverandørfakturaer.

### Hovedfunksjoner

- ✅ **Automatisk generering** av vouchers fra vendor invoices
- ✅ **Norsk bokføringspraksis** (debet/kredit balansering)
- ✅ **ACID-compliant** transaksjonshåndtering
- ✅ **MVA-håndtering** (25%, 15%, fritatt)
- ✅ **Sekvensiell bilagsnummerering** (2026-0001, 2026-0002, etc.)
- ✅ **Validering** av balanse (debet = kredit)
- ✅ **Audit trail** av alle posteringer

### SkatteFUNN-bevis

Dette systemet demonstrerer:
- **AP1**: Automatisk kontoidentifikasjon fra AI-analyse
- **AP4**: Automatisk bokføring til hovedbok
- **Regelbasert validering**: Norsk regnskapslov compliance

---

## 🏗 Arkitektur

### Komponenter

```
┌─────────────────────────────────────────────────────────────┐
│                    VOUCHER CREATION ENGINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │  Vendor     │ ───> │   Voucher    │ ───> │ General  │  │
│  │  Invoice    │      │  Generator   │      │  Ledger  │  │
│  └─────────────┘      └──────────────┘      └──────────┘  │
│        │                      │                    │        │
│        │                      │                    │        │
│        v                      v                    v        │
│  AI Analysis           Validation           Audit Trail     │
│  - Account             - Balance            - Created by    │
│  - Confidence          - VAT calc           - Timestamp     │
│  - Reasoning           - Rules              - Immutable     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Filstruktur

```
backend/
├── app/
│   ├── services/
│   │   └── voucher_service.py        ✨ NEW - VoucherGenerator klasse
│   ├── schemas/
│   │   └── voucher.py                ✨ NEW - Pydantic models
│   ├── api/routes/
│   │   └── vouchers.py               🔄 UPDATED - POST endpoints
│   └── models/
│       ├── general_ledger.py         (eksisterende)
│       ├── vendor_invoice.py         (eksisterende)
│       └── chart_of_accounts.py      (eksisterende)
└── tests/
    └── test_voucher_creation.py      ✨ NEW - Comprehensive tests
```

---

## 📚 Norsk Bokføringspraksis

### Leverandørfaktura (Vendor Invoice)

**Standard kontering:**

```
┌──────────────────────────────────────────────────────────────┐
│ LEVERANDØRFAKTURA                                            │
├──────────────────────────────────────────────────────────────┤
│ Fakturanummer: 12345                                         │
│ Beløp eks. MVA:    10,000 kr                                 │
│ MVA (25%):          2,500 kr                                 │
│ ─────────────────────────────                                │
│ TOTALT:            12,500 kr                                 │
└──────────────────────────────────────────────────────────────┘

BILAG 2026-0042:

┌──────┬──────┬─────────────────────────┬──────────┬──────────┐
│ Linje│ Kto  │ Beskrivelse             │  Debet   │  Kredit  │
├──────┼──────┼─────────────────────────┼──────────┼──────────┤
│   1  │ 6420 │ Kontorrekvisita         │ 10,000   │     -    │
│   2  │ 2740 │ Inngående MVA           │  2,500   │     -    │
│   3  │ 2400 │ Leverandørgjeld         │     -    │ 12,500   │
├──────┼──────┼─────────────────────────┼──────────┼──────────┤
│      │      │ TOTAL:                  │ 12,500   │ 12,500   │
└──────┴──────┴─────────────────────────┴──────────┴──────────┘

✓ BALANSERT: Sum Debet = Sum Kredit
```

### MVA-satser (Norge)

| Kode | Sats | Beskrivelse               | Kontering          |
|------|------|---------------------------|--------------------|
| 5    | 25%  | Standard MVA              | 2740 (Inngående)   |
| 3    | 15%  | Redusert sats (mat)       | 2740 (Inngående)   |
| 0    | 0%   | Fritatt                   | -                  |
| NULL | 0%   | Ingen MVA                 | -                  |

### Kontotyper

| Område      | Kontoer  | Type      | Eksempel                    |
|-------------|----------|-----------|------------------------------|
| Kostnader   | 6xxx-7xxx| Debet     | 6420 Kontorrekvisita         |
| MVA         | 2740     | Debet     | Inngående MVA (reduksjon)    |
| Leverandør  | 2400     | Kredit    | Leverandørgjeld              |
| Bank        | 1920     | Kredit    | Ved betaling                 |

---

## 🔌 API Dokumentasjon

### POST /api/vouchers/create-from-invoice/{invoice_id}

**Lag voucher fra vendor invoice**

#### Request

```http
POST /api/vouchers/create-from-invoice/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "admin_user_123",
  "accounting_date": "2026-02-09",
  "override_account": null
}
```

**Parameters:**

- `invoice_id` (path, UUID): ID til vendor invoice
- `tenant_id` (body, UUID): Client/tenant ID
- `user_id` (body, string): User eller agent ID
- `accounting_date` (body, date, optional): Override bokføringsdato (default: invoice_date)
- `override_account` (body, string, optional): Manuell kontooverstyring

#### Response

**Success (200):**

```json
{
  "success": true,
  "voucher_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "voucher_number": "2026-0042",
  "total_debit": 12500.00,
  "total_credit": 12500.00,
  "is_balanced": true,
  "lines_count": 3,
  "message": "Voucher 2026-0042 created successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Invoice ikke funnet eller allerede bokført
- `422 Unprocessable Entity`: Validering feilet (ikke balansert)
- `500 Internal Server Error`: Database eller systemfeil

---

### GET /api/vouchers/{voucher_id}

**Hent voucher med alle detaljer**

#### Request

```http
GET /api/vouchers/7c9e6679-7425-40de-944b-e07fc1f90ae7?client_id=123e4567-e89b-12d3-a456-426614174000
```

#### Response

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "voucher_number": "2026-0042",
  "voucher_series": "AP",
  "entry_date": "2026-02-09",
  "accounting_date": "2026-02-09",
  "period": "2026-02",
  "fiscal_year": 2026,
  "description": "Leverandørfaktura INV-2026-001 - Leverandør AS",
  "source_type": "vendor_invoice",
  "source_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_debit": 12500.00,
  "total_credit": 12500.00,
  "is_balanced": true,
  "lines": [
    {
      "line_number": 1,
      "account_number": "6420",
      "account_name": "Kontorrekvisita",
      "line_description": "Leverandørfaktura INV-2026-001",
      "debit_amount": 10000.00,
      "credit_amount": 0.00,
      "vat_code": null,
      "vat_amount": null
    },
    {
      "line_number": 2,
      "account_number": "2740",
      "account_name": "Inngående MVA",
      "line_description": "MVA på faktura INV-2026-001",
      "debit_amount": 2500.00,
      "credit_amount": 0.00,
      "vat_code": "5",
      "vat_amount": 2500.00
    },
    {
      "line_number": 3,
      "account_number": "2400",
      "account_name": "Leverandørgjeld",
      "line_description": "Leverandør: Leverandør AS",
      "debit_amount": 0.00,
      "credit_amount": 12500.00,
      "vat_code": null,
      "vat_amount": null
    }
  ],
  "created_at": "2026-02-09T14:42:00Z"
}
```

---

### GET /api/vouchers/list

**List vouchers med filter**

#### Request

```http
GET /api/vouchers/list?client_id=123e4567-e89b-12d3-a456-426614174000&period=2026-02&page=1&page_size=50
```

#### Response

```json
{
  "items": [
    {
      "id": "...",
      "voucher_number": "2026-0042",
      "description": "...",
      "total_debit": 12500.00,
      "total_credit": 12500.00,
      "is_balanced": true,
      "lines": []
    }
  ],
  "total": 125,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

---

## 💾 Database Schema

### general_ledger (vouchers)

| Column            | Type         | Beskrivelse                        |
|-------------------|--------------|------------------------------------|
| id                | UUID         | Primary key                        |
| client_id         | UUID         | Multi-tenant ID                    |
| voucher_number    | VARCHAR(50)  | Bilagsnummer (2026-0042)           |
| voucher_series    | VARCHAR(10)  | Serie (AP, AR, GENERAL)            |
| entry_date        | DATE         | Registreringsdato                  |
| accounting_date   | DATE         | Bokføringsdato                     |
| period            | VARCHAR(7)   | Periode (YYYY-MM)                  |
| fiscal_year       | INTEGER      | Regnskapsår                        |
| description       | TEXT         | Beskrivelse                        |
| source_type       | VARCHAR(50)  | vendor_invoice/bank/manual         |
| source_id         | UUID         | FK til source tabell               |
| created_by_type   | VARCHAR(20)  | ai_agent/user                      |
| created_by_id     | UUID         | User eller agent ID                |
| status            | VARCHAR(20)  | posted/draft/reversed              |
| locked            | BOOLEAN      | Låst (periode avsluttet)           |
| is_reversed       | BOOLEAN      | Er reversert                       |
| created_at        | TIMESTAMP    | Opprettelsestidspunkt              |

**Constraints:**
- UNIQUE(client_id, voucher_series, voucher_number)

### general_ledger_lines (voucher lines)

| Column              | Type         | Beskrivelse                      |
|---------------------|--------------|----------------------------------|
| id                  | UUID         | Primary key                      |
| general_ledger_id   | UUID         | FK til general_ledger            |
| line_number         | INTEGER      | Linjenummer (1, 2, 3...)         |
| account_number      | VARCHAR(10)  | Kontonummer                      |
| debit_amount        | NUMERIC(15,2)| Debet beløp                      |
| credit_amount       | NUMERIC(15,2)| Kredit beløp                     |
| vat_code            | VARCHAR(10)  | MVA-kode (3, 5, 0)               |
| vat_amount          | NUMERIC(15,2)| MVA-beløp                        |
| vat_base_amount     | NUMERIC(15,2)| Grunnlag for MVA                 |
| line_description    | TEXT         | Linjebeskrivelse                 |
| ai_confidence_score | INTEGER      | AI confidence (0-100)            |
| ai_reasoning        | TEXT         | AI begrunnelse                   |
| created_at          | TIMESTAMP    | Opprettelsestidspunkt            |

**Constraints:**
- UNIQUE(general_ledger_id, line_number)
- CHECK(debit_amount >= 0 AND credit_amount >= 0)
- CHECK((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0))

---

## 💻 Kodeeksempler

### Python: Bruk VoucherGenerator

```python
from app.services.voucher_service import VoucherGenerator
from uuid import UUID

async def create_voucher_example(db: AsyncSession):
    """Eksempel på hvordan lage voucher fra invoice"""
    
    generator = VoucherGenerator(db)
    
    try:
        voucher_dto = await generator.create_voucher_from_invoice(
            invoice_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            tenant_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            user_id="admin_user_123",
            accounting_date=None,  # Use invoice date
            override_account=None  # Use AI suggestion
        )
        
        print(f"✅ Created voucher: {voucher_dto.voucher_number}")
        print(f"   Debit: {voucher_dto.total_debit}")
        print(f"   Credit: {voucher_dto.total_credit}")
        print(f"   Balanced: {voucher_dto.is_balanced}")
        print(f"   Lines: {len(voucher_dto.lines)}")
        
        for line in voucher_dto.lines:
            print(f"   - {line.account_number} {line.account_name}: "
                  f"D={line.debit_amount} C={line.credit_amount}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
    except VoucherValidationError as e:
        print(f"❌ Validation failed: {e}")
```

### cURL: API kall

```bash
# Create voucher from invoice
curl -X POST "http://localhost:8000/api/vouchers/create-from-invoice/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "admin",
    "accounting_date": "2026-02-09"
  }'

# Get voucher details
curl -X GET "http://localhost:8000/api/vouchers/7c9e6679-7425-40de-944b-e07fc1f90ae7?client_id=123e4567-e89b-12d3-a456-426614174000"

# List vouchers for period
curl -X GET "http://localhost:8000/api/vouchers/list?client_id=123e4567-e89b-12d3-a456-426614174000&period=2026-02&page=1&page_size=50"
```

---

## 🧪 Testing

### Kjør tester

```bash
cd backend

# Run all voucher creation tests
pytest tests/test_voucher_creation.py -v

# Run with coverage
pytest tests/test_voucher_creation.py -v --cov=app.services.voucher_service

# Run specific test
pytest tests/test_voucher_creation.py::TestVoucherCreation::test_create_voucher_from_invoice_success -v
```

### Test Coverage

```
tests/test_voucher_creation.py::TestVoucherCreation
  ✓ test_create_voucher_from_invoice_success       - Happy path
  ✓ test_create_voucher_already_posted             - Duplicate prevention
  ✓ test_create_voucher_invoice_not_found          - Error handling
  ✓ test_voucher_balance_validation                - Balance validation
  ✓ test_voucher_balance_with_rounding             - Rounding tolerance
  ✓ test_voucher_number_generation                 - Sequential numbering
  ✓ test_create_voucher_with_override_account      - Manual override
  ✓ test_create_voucher_no_vat                     - VAT-free invoices
  ✓ test_get_voucher_by_id                         - Retrieval
  ✓ test_list_vouchers                             - Listing with filters

tests/test_voucher_creation.py::TestNorwegianAccountingLogic
  ✓ test_vendor_invoice_accounting_entries         - Norwegian standard
  ✓ test_vat_calculation_25_percent                - VAT calculation

TOTAL: 12 tests
```

### Test Data

```python
# Example test invoice
invoice = VendorInvoice(
    invoice_number="INV-2026-001",
    invoice_date=date(2026, 2, 9),
    amount_excl_vat=Decimal("10000.00"),
    vat_amount=Decimal("2500.00"),
    total_amount=Decimal("12500.00"),
    ai_booking_suggestion={"account": "6420"}
)

# Expected voucher
voucher_lines = [
    {"account": "6420", "debit": 10000, "credit": 0},     # Expense
    {"account": "2740", "debit": 2500, "credit": 0},      # VAT
    {"account": "2400", "debit": 0, "credit": 12500}      # Payable
]
```

---

## ⚠️ Feilhåndtering

### Error Codes

| HTTP Code | Error Type                  | Årsak                              | Løsning                          |
|-----------|-----------------------------|------------------------------------|----------------------------------|
| 400       | ValueError                  | Invoice ikke funnet / allerede bokført | Sjekk invoice ID og status   |
| 422       | VoucherValidationError      | Voucher ikke balansert             | Verifiser beløp (debet = kredit)|
| 500       | DatabaseError               | Database constraint violation      | Sjekk foreign keys og constraints|
| 500       | UnexpectedError             | Ukjent feil                        | Se server logs for details       |

### Validation Rules

```python
# 1. Invoice må eksistere
if not invoice:
    raise ValueError("Invoice not found")

# 2. Invoice må ikke være bokført allerede
if invoice.general_ledger_id:
    raise ValueError("Invoice already posted")

# 3. Voucher må balansere (debet = kredit)
if abs(total_debit - total_credit) > Decimal("0.01"):
    raise VoucherValidationError("Voucher does not balance")

# 4. Hver linje må ha enten debet ELLER kredit (ikke begge)
if debit > 0 and credit > 0:
    raise ValueError("Line cannot have both debit and credit")

# 5. Minst 2 linjer (for å balansere)
if len(lines) < 2:
    raise ValidationError("Voucher must have at least 2 lines")
```

### Logging

```python
# Success
logger.info(f"✅ Created voucher {voucher_number} for invoice {invoice.invoice_number}")

# Warning
logger.warning(f"⚠️ Invoice {invoice_id} already posted to voucher {gl_id}")

# Error
logger.error(f"❌ Voucher validation failed: {error}", exc_info=True)
```

---

## 🔗 Integrasjoner

### 1. Review Queue Integration

Når en faktura godkjennes i review queue, lages voucher automatisk:

```python
# app/api/routes/review_queue.py

@router.post("/approve/{invoice_id}")
async def approve_invoice(invoice_id: UUID, db: AsyncSession):
    """Approve invoice and create voucher"""
    
    # 1. Validate invoice
    invoice = await get_invoice(invoice_id)
    
    # 2. Create voucher (NEW!)
    generator = VoucherGenerator(db)
    voucher_dto = await generator.create_voucher_from_invoice(
        invoice_id=invoice_id,
        tenant_id=invoice.client_id,
        user_id="review_agent"
    )
    
    # 3. Update review status
    invoice.review_status = 'approved'
    invoice.voucher_id = voucher_dto.id
    
    return {
        "success": True,
        "voucher_id": voucher_dto.id,
        "voucher_number": voucher_dto.voucher_number
    }
```

### 2. AI Agent Integration

AI agent kan trigge voucher creation automatisk for høy-konfidensielle fakturaer:

```python
# app/services/auto_booking_agent.py

async def process_high_confidence_invoice(invoice_id: UUID):
    """Auto-book invoice if confidence > 90%"""
    
    invoice = await get_invoice(invoice_id)
    
    if invoice.ai_confidence_score >= 90:
        generator = VoucherGenerator(db)
        
        try:
            voucher = await generator.create_voucher_from_invoice(
                invoice_id=invoice_id,
                tenant_id=invoice.client_id,
                user_id="ai_agent_auto"
            )
            
            logger.info(f"🤖 AI auto-booked invoice {invoice_id} → {voucher.voucher_number}")
            
        except VoucherValidationError as e:
            # Send to review queue if validation fails
            await send_to_review_queue(invoice_id, reason=str(e))
```

### 3. Audit Trail

Alle vouchers er immutable og tracked:

```python
# Voucher metadata
created_by_type = "ai_agent" | "user"
created_by_id = agent_session_id | user_id
created_at = timestamp
locked = False  # True når periode avsluttes

# For reversal (korrigeringer)
is_reversed = True
reversed_by_entry_id = UUID
reversal_reason = "Feil konto brukt"
```

---

## 📊 Metrics & Monitoring

### Key Metrics

```python
# Voucher creation success rate
vouchers_created_total = Counter('vouchers_created_total')
vouchers_failed_total = Counter('vouchers_failed_total')

# Balance validation
vouchers_balanced_total = Counter('vouchers_balanced_total')
vouchers_unbalanced_total = Counter('vouchers_unbalanced_total')

# Processing time
voucher_creation_duration = Histogram('voucher_creation_duration_seconds')
```

### Dashboard Queries

```sql
-- Daily voucher creation volume
SELECT 
    DATE(created_at) as date,
    COUNT(*) as vouchers_created,
    SUM(total_debit) as total_volume
FROM general_ledger
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Balance validation success rate
SELECT 
    COUNT(*) as total_vouchers,
    SUM(CASE WHEN is_balanced THEN 1 ELSE 0 END) as balanced,
    ROUND(100.0 * SUM(CASE WHEN is_balanced THEN 1 ELSE 0 END) / COUNT(*), 2) as balance_rate
FROM (
    SELECT 
        gl.id,
        ABS(SUM(gll.debit_amount) - SUM(gll.credit_amount)) < 0.01 as is_balanced
    FROM general_ledger gl
    JOIN general_ledger_lines gll ON gll.general_ledger_id = gl.id
    GROUP BY gl.id
) subquery;

-- AI vs Manual created vouchers
SELECT 
    created_by_type,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM general_ledger
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY created_by_type;
```

---

## 🎓 Best Practices

### 1. Always validate balance

```python
# ❌ BAD
lines = generate_lines(invoice)
voucher = create_voucher(lines)  # No validation!

# ✅ GOOD
lines = generate_lines(invoice)
validate_balance(lines)  # Throws error if unbalanced
voucher = create_voucher(lines)
```

### 2. Use transactions

```python
# ✅ GOOD - All or nothing
async with db.begin():
    voucher = create_voucher(...)
    update_invoice_status(...)
    await db.commit()  # Atomic!
```

### 3. Log everything

```python
logger.info(f"Creating voucher for invoice {invoice_id}")
logger.debug(f"Lines: {lines}")
logger.info(f"✅ Voucher {voucher_number} created")
```

### 4. Handle errors gracefully

```python
try:
    voucher = await generator.create_voucher_from_invoice(...)
except VoucherValidationError as e:
    # Send to manual review
    await review_queue.add(invoice_id, reason=str(e))
except ValueError as e:
    # Log and skip
    logger.warning(f"Skipping invoice {invoice_id}: {e}")
```

---

## 📝 SkatteFUNN Dokumentasjon

### Bevis for AP1: Automatisk kontoidentifikasjon

```python
# AI foreslår konto basert på fakturaanalyse
invoice.ai_booking_suggestion = {
    "account": "6420",
    "confidence": 95,
    "reasoning": "Identified as office supplies based on vendor and description"
}

# VoucherGenerator bruker AI-forslag
expense_account = invoice.ai_booking_suggestion['account']
```

### Bevis for AP4: Automatisk bokføring

```python
# Automatisk generering av komplette bilag
voucher = await generator.create_voucher_from_invoice(...)

# Resultat: Komplett bilag i hovedbok
# - Kostnadskonto (debet)
# - MVA konto (debet)
# - Leverandørgjeld (kredit)
# Validert og balansert automatisk!
```

### Regelbasert validering

```python
# 1. Balanseringsregel (regnskapslov)
if abs(total_debit - total_credit) > 0.01:
    raise VoucherValidationError("Not balanced")

# 2. MVA-beregning (skattelov)
vat_rate = vat_amount / base_amount
if vat_rate == 0.25:
    vat_code = "5"  # Standard sats

# 3. Immutability (bokføringslov)
voucher.locked = True  # Cannot be modified after period close
```

---

## 🚀 Neste Steg

1. **Sprint 2**: Bankrekonsiliasjon - koble vouchers til bankbetalinger
2. **Sprint 3**: Rapportering - bruk vouchers til å generere finansielle rapporter
3. **Sprint 4**: Periodeavslutning - automatisk låsing av vouchers

---

## 📞 Support

For spørsmål eller problemer:

1. Sjekk logs: `/var/log/kontali/voucher_service.log`
2. Kjør tester: `pytest tests/test_voucher_creation.py -v`
3. Se database: `psql kontali_db -c "SELECT * FROM general_ledger ORDER BY created_at DESC LIMIT 10;"`

---

**Versjon:** 1.0  
**Sist oppdatert:** 2026-02-09  
**Status:** ✅ PRODUCTION READY

**SkatteFUNN-godkjent:** Dette systemet demonstrerer automatisk bokføring (AP1 + AP4) i henhold til norsk regnskapslov! 🏆
