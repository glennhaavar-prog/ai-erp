# Invoice Upload API - Quick Start Guide

## Testing the API

### Option 1: Simple Shell Script (Recommended)
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
./test_upload_simple.sh
```

This will:
1. Create a test PDF invoice
2. Upload it to the API
3. Verify it appears in the review queue
4. Show complete results

### Option 2: Manual cURL
```bash
# Create a test PDF first (or use any PDF)
curl -X POST http://localhost:8000/api/invoices/upload/ \
  -F "file=@/path/to/invoice.pdf" \
  -F "client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

### Option 3: Python Test Script
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
python test_invoice_upload.py
```

## API Endpoints

### 1. Upload Invoice
```
POST /api/invoices/upload/
Content-Type: multipart/form-data

Parameters:
  - file: PDF file (required)
  - client_id: UUID (required)

Response: {
  "success": true,
  "invoice_id": "...",
  "confidence_score": 95,
  "status": "pending_review",
  ...
}
```

### 2. List Invoices
```
GET /api/invoices/?client_id={uuid}&status={pending|approved}

Response: [
  {
    "id": "...",
    "invoice_number": "INV-001",
    "total_amount": 10000.0,
    "vendor_name": "Test Vendor",
    ...
  }
]
```

### 3. Get Invoice Details
```
GET /api/invoices/{invoice_id}

Response: {
  "id": "...",
  "invoice_number": "INV-001",
  "ai_booking_suggestion": [...],
  ...
}
```

### 4. Review Queue (Integration)
```
GET /api/review-queue/?client_id={uuid}

Response: [
  {
    "id": "...",
    "supplier": "Test Vendor",
    "confidence": 95,
    "status": "pending",
    ...
  }
]
```

## Example Response

```json
{
  "success": true,
  "invoice_id": "bb6606d2-b479-4ebf-ac28-9d985ec81663",
  "document_id": "812eb5d7-57ac-4268-ba45-a08cb470f42b",
  "review_queue_id": "95db1b2b-8c2e-4442-aad9-2efdb4cbd039",
  "s3_url": "s3://kontali-erp-documents-eu-west-1/invoices/.../test_invoice.pdf",
  "status": "pending_review",
  "confidence_score": 95,
  "ai_suggestion": [
    {
      "account": "6300",
      "debit": 8000,
      "credit": 0,
      "description": "Office supplies and licenses"
    },
    {
      "account": "2740",
      "debit": 2000,
      "credit": 0,
      "description": "Input VAT 25%"
    },
    {
      "account": "2400",
      "debit": 0,
      "credit": 10000,
      "description": "Accounts payable"
    }
  ],
  "vendor": {
    "name": "Test Leverandor AS",
    "org_number": "987654321"
  },
  "invoice_details": {
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-02-07",
    "due_date": "2024-03-07",
    "total_amount": 10000.0,
    "currency": "NOK"
  },
  "message": "Invoice uploaded and added to review queue successfully"
}
```

## What Happens Behind the Scenes

1. **Upload** - PDF uploaded to S3 (kontali-erp-documents-eu-west-1)
2. **OCR** - AWS Textract extracts text from PDF
3. **AI Analysis** - Claude analyzes and suggests booking
4. **Database** - Invoice + Document + Review Queue records created
5. **Response** - Complete details returned to frontend

## Troubleshooting

### Server not running?
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Check server status
```bash
curl http://localhost:8000/health
```

### View logs
```bash
tail -f /tmp/backend.log
# or
tail -f backend.log
```

### Database issues?
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
PGPASSWORD=erp_password psql -h localhost -U erp_user -d ai_erp
```

## API Documentation

Full interactive API docs available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Files

- `test_upload_simple.sh` - Quick test script
- `test_invoice_upload.py` - Python test with reportlab PDF generation
- `app/services/ocr_service.py` - OCR service
- `app/api/routes/invoices.py` - Upload endpoint
- `INVOICE_UPLOAD_IMPLEMENTATION.md` - Full technical documentation
- `DELIVERY_SUMMARY.md` - Summary and delivery notes

## Support

For issues or questions, check:
1. `INVOICE_UPLOAD_IMPLEMENTATION.md` - Technical details
2. `DELIVERY_SUMMARY.md` - Summary and test results
3. Server logs: `/tmp/backend.log`
4. Database: PostgreSQL on localhost:5432

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-02-07
