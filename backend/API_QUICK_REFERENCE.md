# AI-ERP API Quick Reference

**Base URL:** `http://localhost:8000`  
**Last Updated:** 2026-02-11

---

## Core

```
GET  /health                          Health check
GET  /                                API info
```

---

## Dashboard (`/api/dashboard`)

```
GET  /api/dashboard/                                Cross-client summary
GET  /api/dashboard/status                          System status (traffic light)
GET  /api/dashboard/activity?limit=10               Recent activity log
GET  /api/dashboard/verification                    Receipt verification status
GET  /api/dashboard/multi-client/tasks              Multi-client task list
     ?tenant_id={uuid}&category={invoicing|bank|reporting|all}
```

---

## Vouchers (`/api/vouchers`)

```
POST /api/vouchers/create-from-invoice/{invoice_id}    Create voucher from invoice
GET  /api/vouchers/list                                List vouchers
     ?client_id={uuid}&period=YYYY-MM&page=1&page_size=50
GET  /api/vouchers/{voucher_id}                        Get voucher by ID
     ?client_id={uuid}
GET  /api/vouchers/by-number/{voucher_number}          Get voucher by number
     ?client_id={uuid}
GET  /api/vouchers/{voucher_id}/audit-trail            Audit trail
     ?client_id={uuid}
```

---

## Voucher Journal (`/voucher-journal`) ⚠️ NO /api/ PREFIX

```
GET  /voucher-journal/                               List journal entries
     ?client_id={uuid}&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
     &voucher_type={type}&account_number={acct}&search={query}
     &amount_min={min}&amount_max={max}&limit=100&offset=0
GET  /voucher-journal/{voucher_id}                   Get voucher detail
GET  /voucher-journal/types                          List voucher types
GET  /voucher-journal/export                         Export to JSON/CSV
     ?client_id={uuid}&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&format=json|csv
```

---

## Journal Entries (`/api/journal-entries`)

```
POST /api/journal-entries/                           Create journal entry
     Body: {client_id, accounting_date, description, lines[]}
```

---

## Reports (`/api/reports`)

```
GET  /api/reports/saldobalanse                       Trial balance
     ?client_id={uuid}&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD
     &account_from={acct}&account_to={acct}

GET  /api/reports/resultat                           Income statement
     ?client_id={uuid}&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD

GET  /api/reports/balanse                            Balance sheet
     ?client_id={uuid}&to_date=YYYY-MM-DD

GET  /api/reports/hovedbok                           General ledger
     ?client_id={uuid}&account_from={acct}&account_to={acct}
     &from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&limit=1000&offset=0
```

---

## Ledgers (NO /api/ PREFIX)

```
GET  /customer-ledger/                               Customer ledger (Kundereskontro)
     ?client_id={uuid}&status=open|partially_paid|paid|overdue|all
     &date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&customer_id={uuid}

GET  /supplier-ledger/                               Supplier ledger (Leverandørreskontro)
     ?client_id={uuid}&status=open|partially_paid|paid|all
     &date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&supplier_id={uuid}
```

---

## Accounts (`/api/accounts`)

```
GET  /api/accounts/                                  List accounts
     ?client_id={uuid}&account_type={type}&search={query}&active_only=true
GET  /api/accounts/{account_id}                      Get account by ID
POST /api/accounts/?client_id={uuid}                 Create account
     Body: {account_number, account_name, account_type, ...}
PUT  /api/accounts/{account_id}                      Update account
DEL  /api/accounts/{account_id}?soft_delete=true     Delete/deactivate account
```

---

## Bank (`/api/bank`)

```
POST /api/bank/import?client_id={uuid}                       Import bank CSV
     Multipart: file=transactions.csv

GET  /api/bank/transactions                                  List transactions
     ?client_id={uuid}&status=unmatched|matched|reviewed|ignored&limit=100

GET  /api/bank/transactions/{transaction_id}                 Transaction detail
     ?client_id={uuid}

GET  /api/bank/transactions/{transaction_id}/suggestions     Match suggestions
     ?client_id={uuid}

POST /api/bank/transactions/{transaction_id}/match           Manual match
     ?client_id={uuid}&invoice_id={uuid}&invoice_type=vendor|customer&user_id={uuid}

GET  /api/bank/reconciliation/stats                          Reconciliation stats
     ?client_id={uuid}

POST /api/bank/auto-match                                    Run auto-matching
     ?client_id={uuid}&batch_id={uuid}
```

---

## Contacts

### Customers (`/api/contacts/customers`)

```
GET  /api/contacts/customers/                        List customers
     ?client_id={uuid}&status=active|inactive&search={query}&skip=0&limit=100
GET  /api/contacts/customers/{customer_id}           Get customer
     ?include_balance=true&include_transactions=false&include_invoices=false
POST /api/contacts/customers/                        Create customer
     Body: {client_id, name, org_number, address, contact, financial, ...}
PUT  /api/contacts/customers/{customer_id}           Update customer
DEL  /api/contacts/customers/{customer_id}           Deactivate customer
GET  /api/contacts/customers/{customer_id}/audit-log Audit log
     ?skip=0&limit=50
```

### Suppliers (`/api/contacts/suppliers`)

```
GET  /api/contacts/suppliers/                        List suppliers
     ?client_id={uuid}&status=active|inactive&search={query}&skip=0&limit=100
GET  /api/contacts/suppliers/{supplier_id}           Get supplier
     ?include_balance=true&include_transactions=false&include_invoices=false
POST /api/contacts/suppliers/                        Create supplier
     Body: {client_id, company_name, org_number, address, contact, financial, ...}
PUT  /api/contacts/suppliers/{supplier_id}           Update supplier
DEL  /api/contacts/suppliers/{supplier_id}           Deactivate supplier
GET  /api/contacts/suppliers/{supplier_id}/audit-log Audit log
     ?skip=0&limit=50
```

---

## Review Queue (`/api/review-queue`)

```
GET  /api/review-queue/                              List review items
     ?client_id={uuid}&status={status}&priority={priority}&limit=50&offset=0
GET  /api/review-queue/{item_id}                     Get review item
POST /api/review-queue/{item_id}/approve             Approve item
POST /api/review-queue/{item_id}/reject              Reject item
```

---

## Clients (`/api/clients`)

```
GET  /api/clients/                                   List all clients
```

---

## Tenants (`/api/tenants`)

```
GET  /api/tenants/{tenant_id}                        Get tenant info
```

---

## Common Parameters

**Dates:**
- Format: `YYYY-MM-DD` (e.g., `2026-02-11`)

**Pagination:**
- `limit` or `page_size`: Max items per page
- `offset` or `skip`: Starting position
- `page`: Page number (some endpoints)

**UUID Parameters:**
- All IDs are UUIDv4 format
- Example: `628a36eb-0697-4f1e-8a0e-63963eb7b85d`

---

## HTTP Status Codes

```
200  OK                   Request successful
201  Created              Resource created
307  Temporary Redirect   Use trailing slash
400  Bad Request          Invalid request
404  Not Found            Resource/endpoint not found
405  Method Not Allowed   Wrong HTTP method
422  Validation Error     Missing/invalid parameters
500  Internal Error       Server error
```

---

## Testing

Run automated endpoint verification:
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
./test_all_endpoints.sh
```

---

## Critical Path Differences ⚠️

**ENDPOINTS WITH `/api/` PREFIX:**
- Dashboard
- Vouchers
- Reports
- Accounts
- Bank
- Review Queue
- Journal Entries
- Clients
- Contacts (customers/suppliers)

**ENDPOINTS WITHOUT `/api/` PREFIX:**
- Voucher Journal: `/voucher-journal/`
- Customer Ledger: `/customer-ledger/`
- Supplier Ledger: `/supplier-ledger/`

**Always use trailing slash for base paths!**

---

## Example Requests

### Get dashboard summary
```bash
curl http://localhost:8000/api/dashboard/
```

### List vouchers for a client
```bash
curl "http://localhost:8000/api/vouchers/list?client_id=628a36eb-0697-4f1e-8a0e-63963eb7b85d&page=1&page_size=50"
```

### Get saldobalanse (trial balance)
```bash
curl "http://localhost:8000/api/reports/saldobalanse?client_id=628a36eb-0697-4f1e-8a0e-63963eb7b85d&from_date=2026-01-01&to_date=2026-02-11"
```

### List voucher journal (NOTE: NO /api/ prefix!)
```bash
curl "http://localhost:8000/voucher-journal/?client_id=628a36eb-0697-4f1e-8a0e-63963eb7b85d&limit=100"
```

### Import bank transactions
```bash
curl -X POST "http://localhost:8000/api/bank/import?client_id=628a36eb-0697-4f1e-8a0e-63963eb7b85d" \
  -F "file=@transactions.csv"
```

### Create customer
```bash
curl -X POST "http://localhost:8000/api/contacts/customers/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "628a36eb-0697-4f1e-8a0e-63963eb7b85d",
    "name": "Demo AS",
    "org_number": "999999999",
    "is_company": true,
    "address": {
      "line1": "Storgata 1",
      "postal_code": "0001",
      "city": "Oslo"
    }
  }'
```

---

## OpenAPI / Swagger Docs

**Interactive API documentation:**
```
http://localhost:8000/docs
```

**Alternative ReDoc UI:**
```
http://localhost:8000/redoc
```

**OpenAPI JSON schema:**
```
http://localhost:8000/openapi.json
```

---

**Generated:** 2026-02-11  
**Source:** Verified against running instance  
**Full docs:** See `CORRECTED_API_DOCUMENTATION.md`
