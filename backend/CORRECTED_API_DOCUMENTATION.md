# AI-ERP Backend API - Corrected Documentation

**Last verified:** 2026-02-11  
**Base URL:** `http://localhost:8000`  
**Status:** ✅ All endpoints verified by automated testing

---

## Table of Contents

1. [Core Endpoints](#core-endpoints)
2. [Dashboard](#dashboard)
3. [Vouchers & Journal Entries](#vouchers--journal-entries)
4. [Reports & Ledgers](#reports--ledgers)
5. [Accounts & Chart of Accounts](#accounts--chart-of-accounts)
6. [Bank & Reconciliation](#bank--reconciliation)
7. [Contacts (Customers & Suppliers)](#contacts-customers--suppliers)
8. [Review Queue](#review-queue)
9. [Clients & Tenants](#clients--tenants)
10. [Advanced Features](#advanced-features)

---

## Core Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "app": "AI-Agent ERP",
  "version": "1.0.0"
}
```

### Root / API Info
```http
GET /
```

**Response:**
```json
{
  "message": "AI-Agent ERP API",
  "version": "1.0.0",
  "endpoints": {
    "graphql": "/graphql",
    "health": "/health",
    "chat": "/api/chat"
  }
}
```

---

## Dashboard

**Base Path:** `/api/dashboard`

### Get Dashboard Summary
```http
GET /api/dashboard/
```

**Description:** Cross-client dashboard summary for accountants.

**Response:**
```json
{
  "total_clients": 98,
  "total_pending_items": 92,
  "summary_by_category": {
    "vouchers_pending": 91,
    "bank_items_open": 169,
    "reconciliation_pending": 0,
    "vat_pending": 0
  },
  "clients": [...]
}
```

### Get Dashboard Status
```http
GET /api/dashboard/status
```

**Description:** Traffic light status with system health indicators.

**Response:**
```json
{
  "status": "green|yellow|red",
  "message": "All systems operational",
  "timestamp": "2026-02-11T13:52:50.651359",
  "counters": {
    "review_queue": {...},
    "invoices": {...},
    "ehf": {...},
    "bank": {...}
  }
}
```

### Get Recent Activity
```http
GET /api/dashboard/activity
```

**Query Parameters:**
- `limit` (int, optional): Max activities to return (default: 10)

**Response:**
```json
{
  "activities": [
    {
      "id": "uuid",
      "type": "review_created",
      "timestamp": "2026-02-11T12:00:00Z",
      "description": "Item added to review queue",
      "confidence": 75
    }
  ]
}
```

### Get Verification Status
```http
GET /api/dashboard/verification
```

**Description:** Receipt verification dashboard - proves nothing is forgotten.

**Response:**
```json
{
  "overall_status": "green|yellow|red",
  "status_message": "✅ ALL RECEIPTS TRACKED",
  "ehf_invoices": {
    "received": 100,
    "processed": 95,
    "booked": 90,
    "pending": 5
  },
  "bank_transactions": {...},
  "review_queue": {...}
}
```

### Get Multi-Client Tasks
```http
GET /api/dashboard/multi-client/tasks
```

**Query Parameters:**
- `tenant_id` (UUID, required): Tenant/regnskapsbyrå ID
- `category` (string, optional): Filter by category (`invoicing`, `bank`, `reporting`, `all`)

**Description:** 🚀 **KONTALI PARADIGM SHIFT** - See ALL unsure cases across ALL clients at once.

**Response:**
```json
{
  "tenant_id": "uuid",
  "total_clients": 5,
  "clients": [...],
  "tasks": [
    {
      "id": "uuid",
      "type": "vendor_invoice_review",
      "category": "invoicing",
      "client_id": "uuid",
      "client_name": "Demo AS",
      "description": "Review vendor invoice",
      "confidence": 75,
      "priority": "high",
      "data": {...}
    }
  ],
  "summary": {
    "total_tasks": 42,
    "by_category": {...}
  }
}
```

---

## Vouchers & Journal Entries

### Vouchers API

**Base Path:** `/api/vouchers`

#### Create Voucher from Invoice
```http
POST /api/vouchers/create-from-invoice/{invoice_id}
```

**Request Body:**
```json
{
  "tenant_id": "uuid",
  "user_id": "string",
  "accounting_date": "2026-02-09",
  "override_account": null
}
```

**Response:**
```json
{
  "success": true,
  "voucher_id": "uuid",
  "voucher_number": "2026-0042",
  "total_debit": 12500.00,
  "total_credit": 12500.00,
  "is_balanced": true,
  "lines_count": 3,
  "message": "Voucher created successfully"
}
```

#### List Vouchers
```http
GET /api/vouchers/list
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `period` (string, optional): Filter by period (YYYY-MM)
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 50, max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

#### Get Voucher by ID
```http
GET /api/vouchers/{voucher_id}
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID for security

**Response:**
```json
{
  "id": "uuid",
  "voucher_number": "2026-0042",
  "accounting_date": "2026-02-09",
  "description": "Supplier invoice",
  "lines": [
    {
      "line_number": 1,
      "account_number": "6000",
      "account_name": "Kontorrekvisita",
      "debit_amount": 10000.00,
      "credit_amount": 0,
      "description": "Office supplies"
    }
  ],
  "total_debit": 12500.00,
  "total_credit": 12500.00,
  "is_balanced": true
}
```

#### Get Voucher by Number
```http
GET /api/vouchers/by-number/{voucher_number}
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Example:**
```http
GET /api/vouchers/by-number/2026-0042?client_id=uuid
```

#### Get Voucher Audit Trail
```http
GET /api/vouchers/{voucher_id}/audit-trail
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Response:**
```json
{
  "voucher_id": "uuid",
  "voucher_number": "2026-0042",
  "entries": [
    {
      "id": "uuid",
      "action": "create",
      "changed_by_type": "ai_agent",
      "changed_by_name": "AI Bokfører",
      "timestamp": "2026-02-09T20:15:00Z",
      "reason": "Automatic booking from vendor invoice"
    }
  ]
}
```

### Voucher Journal (Bilagsjournal)

**Base Path:** `/voucher-journal` ⚠️ **NO /api PREFIX!**

#### List Voucher Journal
```http
GET /voucher-journal/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `date_from` (date, optional): From date (YYYY-MM-DD)
- `date_to` (date, optional): To date (YYYY-MM-DD)
- `voucher_type` (string, optional): Filter by type
- `account_number` (string, optional): Filter by account
- `amount_min` (float, optional): Minimum amount
- `amount_max` (float, optional): Maximum amount
- `search` (string, optional): Search in description/voucher number
- `limit` (int, optional): Max results (default: 100, max: 1000)
- `offset` (int, optional): Pagination offset

**Response:**
```json
{
  "entries": [
    {
      "id": "uuid",
      "voucher_number": "2026-0042",
      "accounting_date": "2026-02-09",
      "description": "Supplier invoice",
      "total_debit": 12500.00,
      "total_credit": 12500.00,
      "balanced": true,
      "line_count": 3
    }
  ],
  "total_count": 500,
  "returned_count": 100,
  "limit": 100,
  "offset": 0
}
```

#### Get Voucher Detail
```http
GET /voucher-journal/{voucher_id}
```

**Response:**
```json
{
  "id": "uuid",
  "voucher_number": "2026-0042",
  "lines": [...],
  "total_debit": 12500.00,
  "total_credit": 12500.00,
  "balanced": true
}
```

#### Get Voucher Types
```http
GET /voucher-journal/types
```

**Response:**
```json
{
  "types": [
    {
      "value": "supplier_invoice",
      "label": "Leverandørfaktura",
      "description": "Incoming supplier invoice"
    },
    ...
  ]
}
```

#### Export Voucher Journal
```http
GET /voucher-journal/export
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `date_from` (date, optional): From date
- `date_to` (date, optional): To date
- `format` (string, optional): Export format (`json` or `csv`)

### Journal Entries

**Base Path:** `/api/journal-entries`

#### Create Journal Entry
```http
POST /api/journal-entries/
```

**Request Body:**
```json
{
  "client_id": "uuid",
  "accounting_date": "2026-02-09",
  "description": "Manual entry",
  "lines": [
    {
      "account_number": "6000",
      "debit_amount": 1000.00,
      "credit_amount": 0,
      "description": "Office supplies"
    },
    {
      "account_number": "2400",
      "debit_amount": 0,
      "credit_amount": 1000.00,
      "description": "Supplier credit"
    }
  ]
}
```

**Response:**
```json
{
  "id": "uuid",
  "voucher_number": "2026-0043",
  "status": "posted",
  "is_balanced": true,
  "created_at": "2026-02-09T14:00:00Z"
}
```

---

## Reports & Ledgers

**Base Path:** `/api/reports`

### Saldobalanse (Trial Balance)
```http
GET /api/reports/saldobalanse
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `from_date` (date, optional): From date
- `to_date` (date, optional): To date
- `account_from` (string, optional): Account range start (e.g., "3000")
- `account_to` (string, optional): Account range end (e.g., "8999")

**Response:**
```json
{
  "client_id": "uuid",
  "from_date": "2026-01-01",
  "to_date": "2026-02-11",
  "balances": [
    {
      "account_number": "1920",
      "account_name": "Driftskonto",
      "total_debit": 100000.00,
      "total_credit": 50000.00,
      "balance": 50000.00
    }
  ],
  "total_debit": 500000.00,
  "total_credit": 500000.00,
  "is_balanced": true
}
```

### Resultatregnskap (Income Statement)
```http
GET /api/reports/resultat
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `from_date` (date, optional): From date
- `to_date` (date, optional): To date

**Response:**
```json
{
  "client_id": "uuid",
  "inntekter": [...],
  "sum_inntekter": 500000.00,
  "kostnader": {
    "varekjop": {...},
    "lonnkostnader": {...},
    "andre_driftskostnader": {...}
  },
  "sum_kostnader": 300000.00,
  "resultat": 200000.00
}
```

### Balanse (Balance Sheet)
```http
GET /api/reports/balanse
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `to_date` (date, optional): Balance date (default: today)

**Response:**
```json
{
  "client_id": "uuid",
  "balance_date": "2026-02-11",
  "eiendeler": [...],
  "sum_eiendeler": 1000000.00,
  "gjeld_egenkapital": [...],
  "sum_gjeld_egenkapital": 1000000.00,
  "udisponert_overskudd": 200000.00,
  "is_balanced": true
}
```

### Hovedbok (General Ledger)
```http
GET /api/reports/hovedbok
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `account_number` (string, optional): Single account filter *(deprecated, use ranges)*
- `account_from` (string, optional): Account range start
- `account_to` (string, optional): Account range end
- `from_date` (date, optional): From date
- `to_date` (date, optional): To date
- `limit` (int, optional): Max entries (default: 1000)
- `offset` (int, optional): Pagination offset

**Response:**
```json
{
  "client_id": "uuid",
  "account_from": "6000",
  "account_to": "6999",
  "opening_balance": 10000.00,
  "closing_balance": 15000.00,
  "entries": [
    {
      "entry_id": "uuid",
      "voucher_number": "2026-0042",
      "accounting_date": "2026-02-09",
      "entry_description": "Supplier invoice",
      "account_number": "6000",
      "line_description": "Office supplies",
      "debit_amount": 5000.00,
      "credit_amount": 0,
      "vat_code": "3",
      "vat_amount": 1250.00
    }
  ],
  "count": 50,
  "limit": 1000,
  "offset": 0
}
```

### Customer Ledger (Kundereskontro)

**Base Path:** `/customer-ledger` ⚠️ **NO /api PREFIX!**

```http
GET /customer-ledger/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `status` (string, optional): Filter by status (`open`, `partially_paid`, `paid`, `overdue`, `all`)
- `date_from` (date, optional): From date
- `date_to` (date, optional): To date
- `customer_id` (UUID, optional): Filter by customer

**Response:**
```json
{
  "entries": [
    {
      "id": "uuid",
      "customer_id": "uuid",
      "customer_name": "Demo AS",
      "invoice_number": "2026-001",
      "invoice_date": "2026-02-01",
      "due_date": "2026-02-15",
      "amount": 10000.00,
      "remaining_amount": 5000.00,
      "status": "partially_paid"
    }
  ]
}
```

### Supplier Ledger (Leverandørreskontro)

**Base Path:** `/supplier-ledger` ⚠️ **NO /api PREFIX!**

```http
GET /supplier-ledger/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `status` (string, optional): Filter by status (`open`, `partially_paid`, `paid`, `all`)
- `date_from` (date, optional): From date
- `date_to` (date, optional): To date
- `supplier_id` (UUID, optional): Filter by supplier

**Response:** Similar structure to Customer Ledger.

---

## Accounts & Chart of Accounts

**Base Path:** `/api/accounts`

### List Accounts
```http
GET /api/accounts/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `account_type` (string, optional): Filter by type (`asset`, `liability`, `equity`, `revenue`, `expense`)
- `search` (string, optional): Search by number or name
- `active_only` (bool, optional): Show only active accounts (default: true)

**Response:**
```json
{
  "accounts": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "account_number": "1920",
      "account_name": "Driftskonto",
      "account_type": "asset",
      "default_vat_code": "0",
      "vat_deductible": true,
      "is_active": true
    }
  ],
  "total_count": 150
}
```

### Get Account by ID
```http
GET /api/accounts/{account_id}
```

### Create Account
```http
POST /api/accounts/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Request Body:**
```json
{
  "account_number": "6100",
  "account_name": "Kontorrekvisita",
  "account_type": "expense",
  "default_vat_code": "3",
  "vat_deductible": true
}
```

### Update Account
```http
PUT /api/accounts/{account_id}
```

### Delete Account (Soft Delete)
```http
DELETE /api/accounts/{account_id}
```

**Query Parameters:**
- `soft_delete` (bool, optional): Soft delete (deactivate) vs hard delete (default: true)

---

## Bank & Reconciliation

**Base Path:** `/api/bank`

### Import Bank Transactions
```http
POST /api/bank/import
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Request:**
- Multipart form data with CSV file

**Response:**
```json
{
  "success": true,
  "batch_id": "uuid",
  "transactions_imported": 50,
  "auto_matched": 35,
  "match_rate": 70.0,
  "filename": "transactions.csv",
  "client_id": "uuid"
}
```

### List Bank Transactions
```http
GET /api/bank/transactions
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `status` (string, optional): Filter by status (`unmatched`, `matched`, `reviewed`, `ignored`)
- `limit` (int, optional): Max results (default: 100, max: 500)

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "transaction_date": "2026-02-09",
      "amount": -5000.00,
      "description": "Payment to supplier",
      "status": "matched"
    }
  ],
  "total": 50
}
```

### Get Transaction Details
```http
GET /api/bank/transactions/{transaction_id}
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

### Get Match Suggestions
```http
GET /api/bank/transactions/{transaction_id}/suggestions
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Response:**
```json
{
  "transaction": {...},
  "suggestions": [
    {
      "invoice_id": "uuid",
      "invoice_number": "2026-001",
      "amount": 5000.00,
      "confidence_score": 95,
      "match_reasons": ["exact_amount", "date_proximity"]
    }
  ],
  "count": 3
}
```

### Manual Match Transaction
```http
POST /api/bank/transactions/{transaction_id}/match
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `invoice_id` (UUID, required): Invoice ID to match
- `invoice_type` (string, required): `vendor` or `customer`
- `user_id` (UUID, required): User performing the match

**Response:**
```json
{
  "success": true,
  "reconciliation": {...},
  "message": "Transaction successfully matched"
}
```

### Get Reconciliation Statistics
```http
GET /api/bank/reconciliation/stats
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID

**Response:**
```json
{
  "total_transactions": 100,
  "matched": 70,
  "unmatched": 30,
  "reviewed": 0,
  "auto_match_rate": 50.0,
  "manual_match_count": 20
}
```

### Run Auto-Matching
```http
POST /api/bank/auto-match
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `batch_id` (UUID, optional): Process specific upload batch

**Response:**
```json
{
  "success": true,
  "message": "Auto-matched 35 of 50 transactions",
  "summary": {
    "total": 50,
    "matched": 35,
    "low_confidence": 15,
    "match_rate": 70.0
  }
}
```

---

## Contacts (Customers & Suppliers)

### Customers

**Base Path:** `/api/contacts/customers` ⚠️ **SPECIAL MOUNTING**

#### List Customers
```http
GET /api/contacts/customers/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `status` (string, optional): Filter by status (`active`, `inactive`)
- `search` (string, optional): Search by name, org_number, birth_number
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Max results (default: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "client_id": "uuid",
    "customer_number": "00001",
    "name": "Demo AS",
    "org_number": "999999999",
    "address": {...},
    "contact": {...},
    "financial": {...},
    "status": "active"
  }
]
```

#### Get Customer
```http
GET /api/contacts/customers/{customer_id}
```

**Query Parameters:**
- `include_balance` (bool, optional): Include current balance (default: true)
- `include_transactions` (bool, optional): Include recent transactions (default: false)
- `include_invoices` (bool, optional): Include open invoices (default: false)

#### Create Customer
```http
POST /api/contacts/customers/
```

**Request Body:**
```json
{
  "client_id": "uuid",
  "is_company": true,
  "name": "Demo AS",
  "org_number": "999999999",
  "address": {
    "line1": "Storgata 1",
    "postal_code": "0001",
    "city": "Oslo",
    "country": "Norge"
  },
  "contact": {
    "person": "John Doe",
    "phone": "+47 12345678",
    "email": "john@demo.no"
  },
  "financial": {
    "payment_terms_days": 14,
    "currency": "NOK",
    "use_kid": true
  }
}
```

#### Update Customer
```http
PUT /api/contacts/customers/{customer_id}
```

#### Deactivate Customer
```http
DELETE /api/contacts/customers/{customer_id}
```

**Note:** Deletion not allowed, only deactivation.

#### Get Customer Audit Log
```http
GET /api/contacts/customers/{customer_id}/audit-log
```

### Suppliers

**Base Path:** `/api/contacts/suppliers` ⚠️ **SPECIAL MOUNTING**

All supplier endpoints follow the same pattern as customers, replacing `/customers/` with `/suppliers/`.

---

## Review Queue

**Base Path:** `/api/review-queue`

### List Review Queue Items
```http
GET /api/review-queue/
```

**Query Parameters:**
- `client_id` (UUID, required): Client ID
- `status` (string, optional): Filter by status
- `priority` (string, optional): Filter by priority
- `limit` (int, optional): Max results
- `offset` (int, optional): Pagination offset

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "category": "manual_review_required",
      "client_id": "uuid",
      "source_type": "vendor_invoice",
      "source_id": "uuid",
      "issue_description": "Low confidence on account classification",
      "ai_confidence": 65,
      "status": "pending",
      "created_at": "2026-02-11T10:00:00Z"
    }
  ],
  "total": 92,
  "page": 1
}
```

### Get Review Queue Item
```http
GET /api/review-queue/{item_id}
```

### Approve Review Item
```http
POST /api/review-queue/{item_id}/approve
```

### Reject Review Item
```http
POST /api/review-queue/{item_id}/reject
```

---

## Clients & Tenants

### Clients

**Base Path:** `/api/clients`

#### List Clients
```http
GET /api/clients/
```

**Note:** This endpoint may return 307 redirect. Use the trailing slash!

**Response:**
```json
{
  "clients": [
    {
      "id": "uuid",
      "name": "Demo AS",
      "org_number": "999999999",
      "status_summary": {
        "vouchers_pending": 5,
        "bank_items_open": 10,
        "reconciliation_status": "in_progress",
        "vat_status": "current"
      }
    }
  ]
}
```

### Tenants

**Base Path:** `/api/tenants`

#### Get Tenant Info
```http
GET /api/tenants/{tenant_id}
```

---

## Advanced Features

### AI Features

**Base Path:** `/api/ai-features`

- Smart categorization
- Anomaly detection
- Predictive reconciliation
- *(Check source code for detailed endpoints)*

### Opening Balance

**Base Path:** `/api/opening-balance`

- Import opening balances for new clients
- *(Check source code for detailed endpoints)*

### Currencies

**Base Path:** `/api/currencies`

- Multi-currency support
- Auto-updating exchange rates
- *(Check source code for detailed endpoints)*

### Period Close

**Base Path:** `/api/period-close`

- Automated monthly/quarterly closing
- *(Check source code for detailed endpoints)*

### Accruals

**Base Path:** `/api/accruals`

- Time-based expense allocation
- *(Check source code for detailed endpoints)*

---

## Common Patterns

### Pagination
Most list endpoints support pagination with:
- `limit`: Max items per page
- `offset` or `skip`: Starting position
- `page`: Page number (some endpoints)

### Date Formats
All dates use ISO 8601 format:
- Date: `YYYY-MM-DD`
- DateTime: `YYYY-MM-DDTHH:MM:SS.ffffffZ` (UTC)

### UUIDs
All IDs are UUIDv4 strings.

### Error Responses
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common status codes:
- `200` OK
- `201` Created
- `400` Bad Request
- `404` Not Found
- `422` Validation Error
- `500` Internal Server Error

---

## Testing

Run the automated test suite:
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
./test_all_endpoints.sh
```

---

## API Design Notes

### Path Inconsistencies (Known Issues)

⚠️ **Warning:** The API has inconsistent path prefixes:

- **WITH `/api/` prefix:**
  - Dashboard: `/api/dashboard/`
  - Vouchers: `/api/vouchers/`
  - Reports: `/api/reports/`
  - Accounts: `/api/accounts/`
  - Bank: `/api/bank/`
  - Review Queue: `/api/review-queue/`
  - Journal Entries: `/api/journal-entries/`
  - Clients: `/api/clients/`
  - Contacts: `/api/contacts/customers/`, `/api/contacts/suppliers/`

- **WITHOUT `/api/` prefix:**
  - Voucher Journal: `/voucher-journal/`
  - Customer Ledger: `/customer-ledger/`
  - Supplier Ledger: `/supplier-ledger/`

**Recommendation:** Standardize all endpoints to use `/api/` prefix in future versions.

### Authentication
Currently, the API does not enforce authentication. This is suitable for:
- Local development
- Demo environment
- Internal network deployments

For production, implement:
- JWT bearer tokens
- API key authentication
- Role-based access control (RBAC)

### Rate Limiting
No rate limiting is currently implemented. Consider adding for production.

---

## Changelog

**2026-02-11:**
- Initial corrected documentation
- All endpoints verified via automated testing
- Path discrepancies documented
- Response examples added

---

**For Developers:**

This documentation was generated by scanning actual route files and testing against a running instance.

**Source files verified:**
- `app/api/routes/*.py`
- `app/main.py` (router mounting)
- Automated test: `test_all_endpoints.sh`

**Last test run:** 2026-02-11 at 13:52 UTC
