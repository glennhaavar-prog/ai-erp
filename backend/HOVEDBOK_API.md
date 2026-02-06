# Hovedbok REST API Documentation

## Overview

The Hovedbok (General Ledger) REST API provides comprehensive access to accounting journal entries with advanced filtering, sorting, and pagination capabilities. This API joins data from multiple tables to provide complete bookkeeping information.

**Base URL:** `/api/reports/hovedbok/`

**API Documentation:** http://localhost:8000/docs#/Reports

---

## Endpoints

### 1. GET /api/reports/hovedbok/

Get a list of Hovedbok entries with filtering, sorting, and pagination.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `client_id` | UUID | **Yes** | - | Client ID to filter entries |
| `start_date` | date | No | - | Start date (accounting_date >= start_date) |
| `end_date` | date | No | - | End date (accounting_date <= end_date) |
| `account_number` | string | No | - | Filter by account number |
| `vendor_id` | UUID | No | - | Filter by vendor ID |
| `status` | string | No | - | Filter by status (posted/reversed) |
| `voucher_series` | string | No | - | Filter by voucher series (A/B/C) |
| `sort_by` | string | No | `accounting_date` | Sort field (accounting_date, voucher_number, created_at, entry_date) |
| `sort_order` | string | No | `asc` | Sort order (asc/desc) |
| `page` | integer | No | `1` | Page number (starts at 1) |
| `page_size` | integer | No | `50` | Number of entries per page (1-500) |
| `include_lines` | boolean | No | `true` | Include general ledger lines in response |
| `include_invoice` | boolean | No | `true` | Include vendor invoice details in response |

#### Example Requests

```bash
# Get all entries for a client
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"

# Get entries within date range
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&start_date=2024-01-01&end_date=2024-12-31"

# Filter by account number
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&account_number=6300"

# Filter by vendor
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&vendor_id=550e8400-e29b-41d4-a716-446655440000"

# Sort by date descending with pagination
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&sort_by=accounting_date&sort_order=desc&page=1&page_size=20"

# Get entries without detailed lines (faster)
curl "http://localhost:8000/api/reports/hovedbok/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&include_lines=false&include_invoice=false"
```

#### Response Format

```json
{
  "entries": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "client_id": "09409ccf-d23e-45e5-93b9-68add0b96277",
      "voucher_number": "1001",
      "voucher_series": "A",
      "full_voucher": "A-1001",
      "accounting_date": "2024-02-06",
      "entry_date": "2024-02-06",
      "period": "2024-02",
      "fiscal_year": 2024,
      "description": "Invoice INV-2024-001 - Test Leverandør AS",
      "source_type": "ehf_invoice",
      "source_id": "456e7890-e89b-12d3-a456-426614174001",
      "created_by_type": "ai_agent",
      "created_by_id": null,
      "status": "posted",
      "is_reversed": false,
      "reversed_by_entry_id": null,
      "reversal_reason": null,
      "locked": false,
      "created_at": "2024-02-06T13:42:06.947309",
      "lines": [
        {
          "id": "789e0123-e89b-12d3-a456-426614174002",
          "line_number": 1,
          "account_number": "6300",
          "debit_amount": 10000.00,
          "credit_amount": 0.00,
          "vat_code": "3",
          "vat_amount": 2500.00,
          "vat_base_amount": 10000.00,
          "line_description": "Marketing expenses",
          "department_id": null,
          "project_id": null,
          "cost_center_id": null,
          "ai_confidence_score": 95,
          "ai_reasoning": "Categorized as marketing based on vendor pattern"
        },
        {
          "id": "890e1234-e89b-12d3-a456-426614174003",
          "line_number": 2,
          "account_number": "2700",
          "debit_amount": 2500.00,
          "credit_amount": 0.00,
          "vat_code": null,
          "vat_amount": 0.0,
          "vat_base_amount": null,
          "line_description": "Input VAT 25%",
          "department_id": null,
          "project_id": null,
          "cost_center_id": null,
          "ai_confidence_score": null,
          "ai_reasoning": null
        },
        {
          "id": "901e2345-e89b-12d3-a456-426614174004",
          "line_number": 3,
          "account_number": "2400",
          "debit_amount": 0.00,
          "credit_amount": 12500.00,
          "vat_code": null,
          "vat_amount": 0.0,
          "vat_base_amount": null,
          "line_description": "Accounts payable - Test Leverandør AS",
          "department_id": null,
          "project_id": null,
          "cost_center_id": null,
          "ai_confidence_score": null,
          "ai_reasoning": null
        }
      ],
      "totals": {
        "debit": 12500.00,
        "credit": 12500.00,
        "balanced": true
      },
      "invoice": {
        "id": "456e7890-e89b-12d3-a456-426614174001",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-02-06",
        "due_date": "2024-03-07",
        "amount_excl_vat": 10000.00,
        "vat_amount": 2500.00,
        "total_amount": 12500.00,
        "currency": "NOK",
        "payment_status": "unpaid",
        "vendor": {
          "id": "012e3456-e89b-12d3-a456-426614174005",
          "name": "Test Leverandør AS",
          "org_number": "888888888",
          "vendor_number": "V001"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_entries": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "summary": {
    "total_debit": 12500.00,
    "total_credit": 12500.00,
    "total_entries": 1,
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "filters_applied": {
      "account_number": null,
      "vendor_id": null,
      "status": null,
      "voucher_series": null
    }
  },
  "timestamp": "2024-02-06T13:42:07.123456"
}
```

---

### 2. GET /api/reports/hovedbok/{entry_id}

Get a single Hovedbok entry by ID with complete details.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entry_id` | UUID | **Yes** | The ID of the general ledger entry |

#### Example Request

```bash
curl "http://localhost:8000/api/reports/hovedbok/123e4567-e89b-12d3-a456-426614174000"
```

#### Response Format

Same structure as individual entries in the list endpoint, but returns a single entry object (not wrapped in an array).

#### Error Responses

- **404 Not Found** - Entry with the given ID does not exist

```json
{
  "detail": "General ledger entry not found"
}
```

---

## Data Models

### GeneralLedger Entry

The main journal entry (Bilag) containing metadata about the transaction.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `client_id` | UUID | Client owning this entry |
| `voucher_number` | string | Voucher number (Bilagsnummer) |
| `voucher_series` | string | Voucher series (A/B/C) |
| `full_voucher` | string | Combined series-number (e.g., "A-1001") |
| `accounting_date` | date | Accounting period date |
| `entry_date` | date | When entry was created |
| `period` | string | Accounting period (YYYY-MM) |
| `fiscal_year` | integer | Fiscal year |
| `description` | text | Entry description |
| `source_type` | string | Source type (ehf_invoice, manual, bank_transaction) |
| `source_id` | UUID | Reference to source document |
| `created_by_type` | string | Creator type (ai_agent, user) |
| `created_by_id` | UUID | Creator ID |
| `status` | string | Status (draft, posted, reversed) |
| `is_reversed` | boolean | Whether this entry has been reversed |
| `reversed_by_entry_id` | UUID | ID of reversing entry |
| `reversal_reason` | text | Reason for reversal |
| `locked` | boolean | Whether entry is locked (after period close) |
| `created_at` | datetime | Creation timestamp |

### GeneralLedgerLine

Individual debit/credit line within an entry.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `line_number` | integer | Sequence within voucher |
| `account_number` | string | Chart of accounts number |
| `debit_amount` | decimal | Debit amount |
| `credit_amount` | decimal | Credit amount |
| `vat_code` | string | VAT code |
| `vat_amount` | decimal | VAT amount |
| `vat_base_amount` | decimal | Base amount for VAT calculation |
| `line_description` | text | Line description |
| `department_id` | UUID | Department (dimension) |
| `project_id` | UUID | Project (dimension) |
| `cost_center_id` | UUID | Cost center (dimension) |
| `ai_confidence_score` | integer | AI confidence (0-100) |
| `ai_reasoning` | text | AI's reasoning for this line |

### VendorInvoice

Related vendor invoice information (when source_type is "ehf_invoice").

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Invoice ID |
| `invoice_number` | string | Invoice number |
| `invoice_date` | date | Invoice date |
| `due_date` | date | Payment due date |
| `amount_excl_vat` | decimal | Amount excluding VAT |
| `vat_amount` | decimal | VAT amount |
| `total_amount` | decimal | Total amount |
| `currency` | string | Currency code |
| `payment_status` | string | Payment status |
| `vendor` | object | Vendor details |

---

## Features

### 1. **Advanced Filtering**
- Filter by client, date range, account, vendor, status, and voucher series
- Combine multiple filters for precise queries
- Efficient database queries with proper indexing

### 2. **Flexible Sorting**
- Sort by accounting_date, voucher_number, created_at, or entry_date
- Ascending or descending order
- Secondary sort by voucher_number for consistency

### 3. **Pagination**
- Configurable page size (1-500 entries)
- Page metadata (total pages, has next/prev)
- Efficient offset-based pagination

### 4. **Performance Optimization**
- Optional inclusion of lines and invoice details
- Eager loading with `selectinload` to prevent N+1 queries
- Aggregated summaries calculated efficiently

### 5. **Data Integrity**
- Totals verification (debit = credit)
- Balance check on each entry
- Immutable entries (posted entries cannot be modified)

### 6. **AI Integration**
- AI confidence scores for bookkeeping lines
- AI reasoning and categorization
- Learning patterns from historical data

---

## Use Cases

### 1. **Accounting Reports**
```bash
# Get all posted entries for a fiscal year
curl "http://localhost:8000/api/reports/hovedbok/?client_id=CLIENT_ID&start_date=2024-01-01&end_date=2024-12-31&status=posted"
```

### 2. **Audit Trail**
```bash
# Get all entries for a specific account
curl "http://localhost:8000/api/reports/hovedbok/?client_id=CLIENT_ID&account_number=6300&sort_by=accounting_date&sort_order=asc"
```

### 3. **Vendor Analysis**
```bash
# Get all entries related to a vendor
curl "http://localhost:8000/api/reports/hovedbok/?client_id=CLIENT_ID&vendor_id=VENDOR_ID&include_invoice=true"
```

### 4. **Period Reconciliation**
```bash
# Get entries for a specific month
curl "http://localhost:8000/api/reports/hovedbok/?client_id=CLIENT_ID&start_date=2024-02-01&end_date=2024-02-29"
```

### 5. **Lightweight Listing**
```bash
# Get entry headers only (fast)
curl "http://localhost:8000/api/reports/hovedbok/?client_id=CLIENT_ID&include_lines=false&include_invoice=false&page_size=100"
```

---

## Performance Considerations

### Query Optimization
- Use `include_lines=false` and `include_invoice=false` for faster queries when details aren't needed
- Limit page_size to reasonable values (50-100) for better response times
- Apply specific filters (dates, account, vendor) to reduce dataset size

### Database Indexes
The following indexes are automatically created:
- `client_id` (multi-tenant filtering)
- `accounting_date` (date range queries)
- `period` and `fiscal_year` (period queries)
- `voucher_number` (voucher lookups)
- `account_number` on lines (account filtering)

### Caching Recommendations
Consider caching:
- Aggregate summaries for completed periods
- Popular filter combinations
- Frequently accessed entries

---

## Error Handling

### 422 Unprocessable Entity
Invalid query parameters (e.g., invalid UUID, date format, or page_size out of range)

### 404 Not Found
Requested entry_id does not exist

### 500 Internal Server Error
Database connection issues or unexpected errors

---

## Integration Examples

### Python
```python
import httpx

async def get_hovedbok(client_id: str, start_date: str, end_date: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/reports/hovedbok/",
            params={
                "client_id": client_id,
                "start_date": start_date,
                "end_date": end_date,
                "sort_by": "accounting_date",
                "sort_order": "desc"
            }
        )
        return response.json()
```

### JavaScript
```javascript
async function getHovedbok(clientId, startDate, endDate) {
    const params = new URLSearchParams({
        client_id: clientId,
        start_date: startDate,
        end_date: endDate,
        sort_by: 'accounting_date',
        sort_order: 'desc'
    });
    
    const response = await fetch(`http://localhost:8000/api/reports/hovedbok/?${params}`);
    return await response.json();
}
```

### cURL
```bash
#!/bin/bash
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
START_DATE="2024-01-01"
END_DATE="2024-12-31"

curl -X GET "http://localhost:8000/api/reports/hovedbok/" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "start_date=$START_DATE" \
  --data-urlencode "end_date=$END_DATE" \
  --data-urlencode "sort_by=accounting_date" \
  --data-urlencode "sort_order=desc" \
  | jq .
```

---

## Future Enhancements

### Planned Features
- [ ] Export to CSV/Excel
- [ ] PDF report generation
- [ ] Real-time subscriptions (WebSocket)
- [ ] Advanced search (full-text on descriptions)
- [ ] Batch operations
- [ ] Reversal API endpoint
- [ ] Period closing API
- [ ] VAT reports integration

### Performance Improvements
- [ ] GraphQL endpoint for flexible field selection
- [ ] Cursor-based pagination for large datasets
- [ ] Redis caching layer
- [ ] Database read replicas

---

## Support

For questions or issues:
- **API Documentation:** http://localhost:8000/docs
- **GraphQL Playground:** http://localhost:8000/graphql
- **Health Check:** http://localhost:8000/health

---

## Version History

### v1.0.0 (2024-02-06)
- Initial release
- GET /api/reports/hovedbok/ (list with filters)
- GET /api/reports/hovedbok/{entry_id} (single entry)
- Full filtering, sorting, and pagination support
- Join GeneralLedger + GeneralLedgerLine + VendorInvoice
- Summary statistics and balance verification
