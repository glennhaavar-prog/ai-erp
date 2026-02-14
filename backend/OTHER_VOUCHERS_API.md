# OTHER VOUCHERS API DOCUMENTATION

## Overview

The Other Vouchers API provides endpoints for managing review queue items for non-supplier-invoice voucher types:

- **Employee Expenses** (ansatteutlegg)
- **Inventory Adjustments** (lagerjusteringer)
- **Manual Corrections** (manuelle korreksjoner)
- **Other** (uncategorized vouchers)

This API complements the existing Review Queue API (`/api/review-queue`) which handles supplier invoices.

## Base URL

```
http://localhost:8000/api/other-vouchers
```

## Authentication

Currently no authentication is required (TODO: will be added when auth is implemented).

## Endpoints

### 1. GET /pending - List Pending Other Vouchers

Retrieve a paginated list of pending review queue items for voucher types other than supplier invoices.

**URL**: `/api/other-vouchers/pending`

**Method**: `GET`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | UUID | **Yes** | Client UUID to filter by |
| `type` | String | No | Filter by specific voucher type (`employee_expense`, `inventory_adjustment`, `manual_correction`, `other`) |
| `priority` | String | No | Filter by priority (`low`, `medium`, `high`, `urgent`) |
| `page` | Integer | No | Page number (default: 1) |
| `page_size` | Integer | No | Items per page (default: 50) |

**Example Request**:

```bash
curl "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

**Example Response**:

```json
{
  "items": [
    {
      "id": "a0900caf-d3e0-4c51-9a52-8326b4570b81",
      "type": "inventory_adjustment",
      "client_id": "09409ccf-d23e-45e5-93b9-68add0b96277",
      "source_type": "inventory_adjustment",
      "source_id": "8ae480d4-adda-4fa2-b4e1-cd68bb2e0730",
      "title": "Inventory Adjustment - unclear description",
      "description": "Lagerjustering - uklar årsak til differanse",
      "priority": "urgent",
      "status": "pending",
      "issue_category": "unclear_description",
      "ai_confidence": 0.35,
      "ai_reasoning": "Inventory count differs by 15% from system. Requires manual verification of cause.",
      "ai_suggestion": {
        "account_number": "1400",
        "account_name": "Varebeholdning",
        "vat_code": "0",
        "amount": -4500.0,
        "debit_account": "6100",
        "credit_account": "1400"
      },
      "created_at": "2026-02-14T16:24:39.452987",
      "assigned_to_user_id": null
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

**Response Fields**:

- `items`: Array of review queue items
  - `id`: Unique identifier for the review queue item
  - `type`: Voucher type (employee_expense, inventory_adjustment, etc.)
  - `client_id`: Client UUID
  - `source_type`: Source entity type
  - `source_id`: UUID of the source entity
  - `title`: Human-readable title
  - `description`: Detailed description of the issue
  - `priority`: Priority level (low/medium/high/urgent)
  - `status`: Current status (pending/approved/corrected/rejected)
  - `issue_category`: Category of the issue (low_confidence, unusual_amount, etc.)
  - `ai_confidence`: AI confidence score (0.0 - 1.0)
  - `ai_reasoning`: Explanation of why AI flagged this for review
  - `ai_suggestion`: AI's suggested booking
  - `created_at`: Timestamp when item was created
  - `assigned_to_user_id`: User assigned to review (null if unassigned)
- `total`: Total number of items matching the filters
- `page`: Current page number
- `page_size`: Number of items per page

---

### 2. GET /stats - Get Other Vouchers Statistics

Retrieve statistics about other vouchers for a specific client.

**URL**: `/api/other-vouchers/stats`

**Method**: `GET`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | UUID | **Yes** | Client UUID to get statistics for |

**Example Request**:

```bash
curl "http://localhost:8000/api/other-vouchers/stats?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

**Example Response**:

```json
{
  "pending_by_type": {
    "employee_expense": 3,
    "inventory_adjustment": 1,
    "manual_correction": 0,
    "other": 0
  },
  "avg_confidence_by_type": {
    "employee_expense": 0.51,
    "inventory_adjustment": 0.47,
    "manual_correction": 0.35,
    "other": 0.0
  },
  "approved": {
    "today": 3,
    "this_week": 5,
    "this_month": 12
  },
  "corrected": {
    "today": 1,
    "this_week": 3,
    "this_month": 8
  },
  "rejected": {
    "today": 0,
    "this_week": 1,
    "this_month": 2
  }
}
```

**Response Fields**:

- `pending_by_type`: Object with count of pending items by voucher type
  - `employee_expense`: Number of pending employee expense vouchers
  - `inventory_adjustment`: Number of pending inventory adjustment vouchers
  - `manual_correction`: Number of pending manual correction vouchers
  - `other`: Number of pending uncategorized vouchers
- `avg_confidence_by_type`: Object with average AI confidence (0.0 - 1.0) per voucher type
- `approved`: Object with counts of approved items
  - `today`: Approved today
  - `this_week`: Approved this week (Mon-Sun)
  - `this_month`: Approved this month
- `corrected`: Object with counts of corrected items (by time period)
- `rejected`: Object with counts of rejected items (by time period)

**Note**: All counts exclude supplier invoices (which are tracked separately via `/api/review-queue`).

---

### 3. GET /{voucher_id} - Get Single Other Voucher

Retrieve detailed information about a specific other voucher review queue item.

**URL**: `/api/other-vouchers/{voucher_id}`

**Method**: `GET`

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `voucher_id` | UUID | **Yes** | Review queue item UUID |

**Example Request**:

```bash
curl "http://localhost:8000/api/other-vouchers/a0900caf-d3e0-4c51-9a52-8326b4570b81"
```

**Example Response**:

```json
{
  "id": "a0900caf-d3e0-4c51-9a52-8326b4570b81",
  "type": "inventory_adjustment",
  "client_id": "09409ccf-d23e-45e5-93b9-68add0b96277",
  "source_type": "inventory_adjustment",
  "source_id": "8ae480d4-adda-4fa2-b4e1-cd68bb2e0730",
  "title": "Inventory Adjustment - unclear description",
  "description": "Lagerjustering - uklar årsak til differanse",
  "priority": "urgent",
  "status": "pending",
  "issue_category": "unclear_description",
  "ai_confidence": 0.35,
  "ai_reasoning": "Inventory count differs by 15% from system. Requires manual verification of cause.",
  "ai_suggestion": {
    "account_number": "1400",
    "account_name": "Varebeholdning",
    "vat_code": "0",
    "amount": -4500.0,
    "debit_account": "6100",
    "credit_account": "1400"
  },
  "assigned_to_user_id": null,
  "assigned_at": null,
  "resolved_by_user_id": null,
  "resolved_at": null,
  "resolution_notes": null,
  "created_at": "2026-02-14T16:24:39.452987",
  "updated_at": "2026-02-14T16:24:39.452987"
}
```

**Response Fields**:

All fields from the list endpoint, plus:

- `assigned_at`: Timestamp when item was assigned (null if unassigned)
- `resolved_by_user_id`: User who resolved the item (null if pending)
- `resolved_at`: Timestamp when item was resolved (null if pending)
- `resolution_notes`: Notes from resolution (null if pending)
- `updated_at`: Timestamp of last update

**Error Responses**:

- `400 Bad Request`: Invalid UUID format or item is a supplier invoice
- `404 Not Found`: Review item not found

---

### 4. POST /{id}/approve - Approve an Other Voucher

Approve a review queue item and mark it as resolved.

**URL**: `/api/other-vouchers/{id}/approve`

**Method**: `POST`

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | **Yes** | Review queue item ID |

**Request Body**:

```json
{
  "notes": "Approved after verification with manager"
}
```

**Body Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notes` | String | No | Optional approval notes |

**Example Request**:

```bash
curl -X POST 'http://localhost:8000/api/other-vouchers/76474862-1688-4a98-8e5b-08131effbf09/approve' \
  -H 'Content-Type: application/json' \
  -d '{"notes": "Approved after manager review"}'
```

**Example Response**:

```json
{
  "id": "76474862-1688-4a98-8e5b-08131effbf09",
  "type": "employee_expense",
  "status": "approved",
  "updated_at": "2026-02-14T16:27:04.350256",
  "message": "Employee Expense approved successfully",
  "feedback_recorded": false
}
```

**Response Fields**:

- `id`: Review queue item ID
- `type`: Voucher type
- `status`: New status (approved)
- `updated_at`: Timestamp when item was updated
- `message`: Success message
- `feedback_recorded`: Whether AI feedback was recorded (currently always false for other vouchers)

**Error Responses**:

- `400 Bad Request`: Invalid UUID format or item already processed
- `404 Not Found`: Review item not found

---

### 5. POST /{id}/reject - Reject and Correct an Other Voucher

Reject the AI's suggestion and provide a corrected booking.

**URL**: `/api/other-vouchers/{id}/reject`

**Method**: `POST`

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | **Yes** | Review queue item ID |

**Request Body**:

```json
{
  "bookingEntries": [
    {
      "account_number": "7650",
      "vat_code": "0",
      "amount": 845
    }
  ],
  "notes": "Changed to marketing expense instead of representation"
}
```

**Body Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bookingEntries` | Array | **Yes** | Corrected booking entries |
| `notes` | String | No | Reason for correction |

**Example Request**:

```bash
curl -X POST 'http://localhost:8000/api/other-vouchers/d8656f49-871e-49c8-8069-1c5a5f344d2d/reject' \
  -H 'Content-Type: application/json' \
  -d '{
    "bookingEntries": [
      {"account_number": "7650", "vat_code": "0", "amount": 845}
    ],
    "notes": "Changed to marketing expense"
  }'
```

**Example Response**:

```json
{
  "id": "d8656f49-871e-49c8-8069-1c5a5f344d2d",
  "type": "employee_expense",
  "status": "corrected",
  "updated_at": "2026-02-14T16:27:09.331223",
  "message": "Employee Expense corrected successfully",
  "feedback_recorded": false,
  "correction": {
    "account_number": "7650",
    "vat_code": "0",
    "notes": "Changed to marketing expense"
  },
  "accuracy": {
    "account_correct": false,
    "vat_correct": true,
    "fully_correct": false
  }
}
```

**Response Fields**:

- `id`: Review queue item ID
- `type`: Voucher type
- `status`: New status (corrected)
- `updated_at`: Timestamp when item was updated
- `message`: Success message
- `feedback_recorded`: Whether AI feedback was recorded
- `correction`: Details of the correction
  - `account_number`: Corrected account number
  - `vat_code`: Corrected VAT code
  - `notes`: Correction notes
- `accuracy`: AI accuracy metrics
  - `account_correct`: Whether AI got the account right
  - `vat_correct`: Whether AI got the VAT right
  - `fully_correct`: Whether AI was fully correct

**Error Responses**:

- `400 Bad Request`: Invalid UUID format, item already processed, or missing booking entries
- `404 Not Found`: Review item not found

---

## Voucher Types

The following voucher types are supported:

| Type | Value | Description |
|------|-------|-------------|
| Employee Expense | `employee_expense` | Employee expense claims (reimbursements) |
| Inventory Adjustment | `inventory_adjustment` | Stock adjustments and corrections |
| Manual Correction | `manual_correction` | Manual accounting corrections |
| Other | `other` | Uncategorized vouchers |

**Note**: Supplier invoices (`supplier_invoice`) are handled by the `/api/review-queue` endpoints and are excluded from this API.

---

## Issue Categories

Common issue categories that trigger manual review:

| Category | Description |
|----------|-------------|
| `low_confidence` | AI has low confidence in the suggestion |
| `unknown_vendor` | Vendor is not recognized |
| `unusual_amount` | Amount is unusually high or low |
| `missing_vat` | VAT information is missing |
| `unclear_description` | Description is unclear or ambiguous |
| `duplicate_invoice` | Possible duplicate detected |
| `processing_error` | Error occurred during processing |
| `manual_review_required` | Requires manual review by policy |

---

## Priority Levels

| Level | Description |
|-------|-------------|
| `low` | Can be reviewed at convenience |
| `medium` | Should be reviewed within 1-2 days |
| `high` | Should be reviewed within 24 hours |
| `urgent` | Requires immediate attention |

---

## Database Schema

### Review Queue Item

The `review_queue` table has been extended with a `type` field:

```sql
CREATE TYPE vouchertype AS ENUM (
    'SUPPLIER_INVOICE',
    'EMPLOYEE_EXPENSE',
    'INVENTORY_ADJUSTMENT',
    'MANUAL_CORRECTION',
    'OTHER'
);

ALTER TABLE review_queue 
ADD COLUMN type vouchertype NOT NULL DEFAULT 'SUPPLIER_INVOICE';

CREATE INDEX ix_review_queue_type ON review_queue(type);
```

---

## Testing

### Test Data

Test data can be created using the provided script:

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
python scripts/create_other_vouchers_test_data.py
```

This creates:
- 5 employee expenses
- 3 inventory adjustments
- 2 manual corrections

All test data is created for client ID: `09409ccf-d23e-45e5-93b9-68add0b96277`

### Manual Testing

```bash
# 1. List pending other vouchers
curl "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"

# 2. Get statistics
curl "http://localhost:8000/api/other-vouchers/stats?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"

# 3. Get single voucher details
curl "http://localhost:8000/api/other-vouchers/{voucher_id}"

# 4. Filter by type
curl "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&type=employee_expense"

# 5. Approve an item
curl -X POST 'http://localhost:8000/api/other-vouchers/{item_id}/approve' \
  -H 'Content-Type: application/json' \
  -d '{"notes": "Approved"}'

# 6. Reject and correct an item
curl -X POST 'http://localhost:8000/api/other-vouchers/{item_id}/reject' \
  -H 'Content-Type: application/json' \
  -d '{"bookingEntries": [{"account_number": "7650", "vat_code": "0", "amount": 845}], "notes": "Corrected"}'
```

---

## Future Enhancements

### TODO

1. **Feedback System**: Update `review_queue_feedback` table to support other voucher types (currently only supports vendor_invoices)
2. **Authentication**: Add user authentication and authorization
3. **General Ledger Integration**: Auto-book approved items to general ledger based on voucher type
4. **Bulk Operations**: Add endpoints for bulk approve/reject
5. **Search**: Add full-text search across descriptions
6. **Filters**: Add more advanced filtering (date range, amount range, etc.)
7. **Webhooks**: Add webhook notifications for status changes
8. **Audit Trail**: Enhanced audit logging for all actions

---

## Migration

The database migration for adding the `type` field has been applied:

```
Migration: 20260214_1625_simple
Status: ✅ Applied
Description: Add type field to review_queue (simple)
```

---

## Integration with Frontend

### Example React Component Usage

```typescript
// Fetch pending other vouchers
const response = await fetch(
  `/api/other-vouchers/pending?client_id=${clientId}&type=employee_expense`
);
const data = await response.json();

// Approve item
await fetch(`/api/other-vouchers/${itemId}/approve`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ notes: 'Approved by manager' })
});

// Reject and correct
await fetch(`/api/other-vouchers/${itemId}/reject`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    bookingEntries: [{ account_number: '7650', vat_code: '0', amount: 845 }],
    notes: 'Changed account'
  })
});
```

---

## Support

For questions or issues, contact the development team or open an issue in the project repository.

**Last Updated**: 2026-02-14 (Updated with new endpoints: /stats and /{voucher_id})  
**API Version**: 1.1.0  
**Module**: MODUL 3 - Backend Other Vouchers

---

## Changelog

### Version 1.1.0 (2026-02-14)
- ✨ Added `GET /api/other-vouchers/stats` - Statistics endpoint
- ✨ Added `GET /api/other-vouchers/{voucher_id}` - Single voucher details endpoint
- 🐛 Fixed route order bug (parameterized routes now come last)
- 🐛 Fixed SQL type casting in stats queries
- 📝 Updated documentation with new endpoints

### Version 1.0.0 (Initial)
- Initial release with list, approve, and reject endpoints
