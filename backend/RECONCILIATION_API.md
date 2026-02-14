# Reconciliation API Documentation

## Overview

The Reconciliation API provides endpoints for managing balance account reconciliations (Balansekontoavstemming) in the Kontali ERP system. This module allows accountants to reconcile balance sheet accounts by comparing ledger balances with external documentation.

**Base URL:** `/api/reconciliations`

## Features

- ✅ Automatic balance calculation from general ledger
- ✅ Period-based reconciliation tracking
- ✅ Multi-type support (bank, receivables, payables, inventory, other)
- ✅ File attachment support (PDF, images, spreadsheets)
- ✅ Approval workflow with audit trail
- ✅ Difference calculation between expected and actual balances

---

## Data Models

### Reconciliation

Main reconciliation record tracking the reconciliation of a balance account for a specific period.

```json
{
  "id": "uuid",
  "client_id": "uuid",
  "account_id": "uuid",
  "account_number": "string (e.g., 1920)",
  "account_name": "string (e.g., Bank Account NOK)",
  "period_start": "datetime (ISO 8601)",
  "period_end": "datetime (ISO 8601)",
  "opening_balance": "decimal (15,2)",
  "closing_balance": "decimal (15,2)",
  "expected_balance": "decimal (15,2) | null",
  "difference": "decimal (15,2) | null",
  "status": "pending | reconciled | approved",
  "reconciliation_type": "bank | receivables | payables | inventory | other",
  "notes": "string | null",
  "created_at": "datetime (ISO 8601)",
  "reconciled_at": "datetime (ISO 8601) | null",
  "reconciled_by": "uuid | null",
  "approved_at": "datetime (ISO 8601) | null",
  "approved_by": "uuid | null",
  "attachments_count": "integer"
}
```

### ReconciliationAttachment

File attachment for supporting documentation.

```json
{
  "id": "uuid",
  "reconciliation_id": "uuid",
  "file_name": "string (original filename)",
  "file_path": "string (relative path)",
  "file_type": "string (MIME type)",
  "file_size": "integer (bytes)",
  "uploaded_at": "datetime (ISO 8601)",
  "uploaded_by": "uuid | null"
}
```

---

## Enums

### ReconciliationStatus

| Value | Description |
|-------|-------------|
| `pending` | Initial state, awaiting reconciliation |
| `reconciled` | Reconciled (difference = 0 or manually marked) |
| `approved` | Approved by supervisor/manager |

### ReconciliationType

| Value | Description |
|-------|-------------|
| `bank` | Bank account reconciliation |
| `receivables` | Accounts receivable reconciliation |
| `payables` | Accounts payable reconciliation |
| `inventory` | Inventory account reconciliation |
| `other` | Other balance accounts |

---

## Auto-Calculation Logic

### Opening and Closing Balances

When creating a reconciliation, the system automatically calculates:

1. **Opening Balance**: Sum of all general ledger entries for the account **before** `period_start`
   ```sql
   SELECT SUM(amount) 
   FROM general_ledger 
   WHERE client_id = ? 
     AND account_id = ? 
     AND voucher_date < period_start
   ```

2. **Closing Balance**: Sum of all general ledger entries for the account **up to** `period_end`
   ```sql
   SELECT SUM(amount) 
   FROM general_ledger 
   WHERE client_id = ? 
     AND account_id = ? 
     AND voucher_date <= period_end
   ```

### Difference Calculation

When `expected_balance` is set (via PUT endpoint):

```
difference = closing_balance - expected_balance
```

- If `difference = 0`: Status automatically changes to `reconciled`
- If `difference ≠ 0`: Indicates discrepancy requiring investigation

---

## API Endpoints

### 1. List Reconciliations

**GET** `/api/reconciliations/`

List all reconciliations for a client with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | UUID | Yes | Client ID to filter reconciliations |
| `period` | string | No | Period filter in `YYYY-MM` format |
| `status` | string | No | Status filter: `pending`, `reconciled`, `approved` |
| `type` | string | No | Type filter: `bank`, `receivables`, `payables`, `inventory`, `other` |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/reconciliations/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&status=pending&type=bank"
```

**Response:**

```json
{
  "reconciliations": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "account_id": "uuid",
      "account_number": "1920",
      "account_name": "Bank Account NOK",
      "period_start": "2024-01-01T00:00:00",
      "period_end": "2024-01-31T23:59:59",
      "opening_balance": 100000.00,
      "closing_balance": 150000.00,
      "expected_balance": null,
      "difference": null,
      "status": "pending",
      "reconciliation_type": "bank",
      "notes": "January 2024 reconciliation",
      "created_at": "2024-02-01T10:00:00",
      "reconciled_at": null,
      "reconciled_by": null,
      "approved_at": null,
      "approved_by": null,
      "attachments_count": 0
    }
  ],
  "count": 1
}
```

---

### 2. Get Single Reconciliation

**GET** `/api/reconciliations/{reconciliation_id}`

Retrieve detailed information about a specific reconciliation.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**

Same as single item in list response, with full details and attachments count.

---

### 3. Create Reconciliation

**POST** `/api/reconciliations/`

Create a new reconciliation. The system automatically calculates opening and closing balances from the general ledger.

**Request Body:**

```json
{
  "client_id": "uuid",
  "account_id": "uuid",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59",
  "reconciliation_type": "bank",
  "notes": "Optional notes"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/reconciliations/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "09409ccf-d23e-45e5-93b9-68add0b96277",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-01-31T23:59:59",
    "reconciliation_type": "bank",
    "notes": "January 2024 bank reconciliation"
  }'
```

**Response:**

```json
{
  "id": "new-uuid",
  "client_id": "uuid",
  "account_id": "uuid",
  "account_number": "1920",
  "account_name": "Bank Account NOK",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59",
  "opening_balance": 100000.00,
  "closing_balance": 150000.00,
  "expected_balance": null,
  "difference": null,
  "status": "pending",
  "reconciliation_type": "bank",
  "notes": "January 2024 bank reconciliation",
  "created_at": "2024-02-01T10:00:00",
  "reconciled_at": null,
  "reconciled_by": null,
  "approved_at": null,
  "approved_by": null,
  "attachments_count": 0
}
```

---

### 4. Update Reconciliation

**PUT** `/api/reconciliations/{reconciliation_id}`

Update a reconciliation's expected balance and notes. The system automatically recalculates the difference.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |

**Request Body:**

```json
{
  "expected_balance": 150000.00,
  "notes": "Updated notes"
}
```

**Example Request:**

```bash
curl -X PUT "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "expected_balance": 150000.00,
    "notes": "Verified against bank statement"
  }'
```

**Response:**

Returns updated reconciliation with calculated `difference` field.

**Note:** If the calculated difference is 0, the status automatically changes to `reconciled`.

---

### 5. Approve Reconciliation

**POST** `/api/reconciliations/{reconciliation_id}/approve`

Mark a reconciliation as approved. Sets `approved_at` and `approved_by` fields.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | UUID | Yes | ID of the user performing the approval |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000/approve?user_id=123e4567-e89b-12d3-a456-426614174000"
```

**Response:**

Returns updated reconciliation with status `approved` and timestamp/user fields populated.

**Error Cases:**

- `400`: Reconciliation already approved
- `404`: Reconciliation not found

---

### 6. Upload Attachment

**POST** `/api/reconciliations/{reconciliation_id}/attachments`

Upload a supporting document (bank statement, confirmation letter, etc.).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |

**Request Body (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | File to upload |
| `user_id` | UUID | No | ID of the user uploading |

**File Restrictions:**

- **Max size:** 10 MB
- **Allowed types:** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.xlsx`, `.csv`

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000/attachments" \
  -F "file=@bank_statement_jan_2024.pdf" \
  -F "user_id=123e4567-e89b-12d3-a456-426614174000"
```

**Response:**

```json
{
  "id": "attachment-uuid",
  "reconciliation_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "bank_statement_jan_2024.pdf",
  "file_path": "reconciliations/550e8400-e29b-41d4-a716-446655440000/unique-id.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "uploaded_at": "2024-02-01T10:30:00",
  "uploaded_by": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Storage Location:**

Files are stored in: `/home/ubuntu/.openclaw/workspace/ai-erp/backend/uploads/reconciliations/{reconciliation_id}/`

**Error Cases:**

- `400`: File type not allowed
- `400`: File too large
- `404`: Reconciliation not found

---

### 7. List Attachments

**GET** `/api/reconciliations/{reconciliation_id}/attachments`

List all attachments for a reconciliation.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000/attachments"
```

**Response:**

```json
{
  "attachments": [
    {
      "id": "attachment-uuid",
      "reconciliation_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "bank_statement_jan_2024.pdf",
      "file_path": "reconciliations/550e8400-e29b-41d4-a716-446655440000/unique-id.pdf",
      "file_type": "application/pdf",
      "file_size": 1024000,
      "uploaded_at": "2024-02-01T10:30:00",
      "uploaded_by": "123e4567-e89b-12d3-a456-426614174000"
    }
  ],
  "count": 1
}
```

---

### 8. Delete Attachment

**DELETE** `/api/reconciliations/{reconciliation_id}/attachments/{attachment_id}`

Delete an attachment. Removes both the file from disk and the database record.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reconciliation_id` | UUID | ID of the reconciliation |
| `attachment_id` | UUID | ID of the attachment |

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/api/reconciliations/550e8400-e29b-41d4-a716-446655440000/attachments/attachment-uuid"
```

**Response:**

```json
{
  "message": "Attachment deleted successfully"
}
```

**Error Cases:**

- `404`: Attachment not found

---

## Typical Workflow

### 1. Create Monthly Reconciliation

```bash
# 1. Create reconciliation (auto-calculates balances)
POST /api/reconciliations/
{
  "client_id": "...",
  "account_id": "...",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59",
  "reconciliation_type": "bank",
  "notes": "January 2024"
}

# Response includes calculated opening_balance and closing_balance
```

### 2. Upload Supporting Documents

```bash
# 2. Upload bank statement
POST /api/reconciliations/{id}/attachments
  -F "file=@bank_statement.pdf"
```

### 3. Enter Expected Balance

```bash
# 3. Enter expected balance from bank statement
PUT /api/reconciliations/{id}
{
  "expected_balance": 150000.00,
  "notes": "Balance per bank statement matches"
}

# System calculates difference and may auto-reconcile if difference = 0
```

### 4. Review and Approve

```bash
# 4. Approve reconciliation
POST /api/reconciliations/{id}/approve?user_id={user_id}
```

---

## Error Responses

All endpoints follow standard HTTP status codes:

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad Request (validation error) |
| `404` | Not Found |
| `422` | Unprocessable Entity (invalid data) |
| `500` | Internal Server Error |

**Error Response Format:**

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Database Schema

### Reconciliations Table

```sql
CREATE TABLE reconciliations (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    account_id UUID REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    opening_balance NUMERIC(15,2) NOT NULL,
    closing_balance NUMERIC(15,2) NOT NULL,
    expected_balance NUMERIC(15,2),
    difference NUMERIC(15,2),
    status reconciliationstatus NOT NULL DEFAULT 'pending',
    reconciliation_type reconciliationtype NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reconciled_at TIMESTAMP,
    reconciled_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_reconciliations_client_id ON reconciliations(client_id);
CREATE INDEX idx_reconciliations_account_id ON reconciliations(account_id);
CREATE INDEX idx_reconciliations_period_start ON reconciliations(period_start);
CREATE INDEX idx_reconciliations_period_end ON reconciliations(period_end);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);
CREATE INDEX idx_reconciliations_type ON reconciliations(reconciliation_type);
```

### Reconciliation Attachments Table

```sql
CREATE TABLE reconciliation_attachments (
    id UUID PRIMARY KEY,
    reconciliation_id UUID REFERENCES reconciliations(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size NUMERIC(15,0),
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_reconciliation_attachments_reconciliation_id ON reconciliation_attachments(reconciliation_id);
```

---

## Testing

Run the comprehensive test script:

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
./test_reconciliations_api.sh
```

The test script validates all 8 endpoints with a complete workflow.

---

## Integration Notes

### Frontend Integration

The frontend should:

1. Display reconciliations in a table with filtering options
2. Show difference in red if non-zero, green if zero
3. Allow inline editing of expected_balance
4. Support drag-and-drop file uploads
5. Display attachment count badge
6. Show approval status with timestamp and user

### Permissions

Consider implementing role-based access:

- **Accountant**: Create, update, upload attachments
- **Supervisor**: Approve reconciliations
- **Auditor**: Read-only access

### Notifications

Future enhancements could include:

- Email notification when reconciliation needs approval
- Alert when difference exceeds threshold
- Reminder for pending reconciliations
