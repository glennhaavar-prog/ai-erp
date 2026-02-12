# Export Endpoints - Quick Reference Card

## All 12 Export Endpoints

### Reports (`/api/reports`)

| Report | PDF Endpoint | Excel Endpoint |
|--------|-------------|----------------|
| **Saldobalanse** | `GET /api/reports/saldobalanse/pdf` | `GET /api/reports/saldobalanse/excel` |
| **Resultat** | `GET /api/reports/resultat/pdf` | `GET /api/reports/resultat/excel` |
| **Balanse** | `GET /api/reports/balanse/pdf` | `GET /api/reports/balanse/excel` |
| **Hovedbok** | `GET /api/reports/hovedbok/pdf` | `GET /api/reports/hovedbok/excel` |

### Ledgers

| Report | PDF Endpoint | Excel Endpoint |
|--------|-------------|----------------|
| **Leverandørreskontro** | `GET /supplier-ledger/pdf` | `GET /supplier-ledger/excel` |
| **Kundereskontro** | `GET /customer-ledger/pdf` | `GET /customer-ledger/excel` |

---

## Common Parameters

All endpoints require:
- `client_id` (UUID) - Required

Most also support:
- `from_date` (YYYY-MM-DD) - Optional
- `to_date` (YYYY-MM-DD) - Optional

---

## Copy-Paste Test Commands

Replace `CLIENT_ID` with your actual client UUID:

```bash
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
FROM="2026-01-01"
TO="2026-02-11"

# Saldobalanse
curl -o saldobalanse.pdf "http://localhost:8000/api/reports/saldobalanse/pdf?client_id=${CLIENT_ID}&from_date=${FROM}&to_date=${TO}"
curl -o saldobalanse.xlsx "http://localhost:8000/api/reports/saldobalanse/excel?client_id=${CLIENT_ID}&from_date=${FROM}&to_date=${TO}"

# Resultat
curl -o resultat.pdf "http://localhost:8000/api/reports/resultat/pdf?client_id=${CLIENT_ID}&from_date=${FROM}&to_date=${TO}"
curl -o resultat.xlsx "http://localhost:8000/api/reports/resultat/excel?client_id=${CLIENT_ID}&from_date=${FROM}&to_date=${TO}"

# Balanse
curl -o balanse.pdf "http://localhost:8000/api/reports/balanse/pdf?client_id=${CLIENT_ID}&to_date=${TO}"
curl -o balanse.xlsx "http://localhost:8000/api/reports/balanse/excel?client_id=${CLIENT_ID}&to_date=${TO}"

# Hovedbok
curl -o hovedbok.pdf "http://localhost:8000/api/reports/hovedbok/pdf?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=${FROM}&to_date=${TO}"
curl -o hovedbok.xlsx "http://localhost:8000/api/reports/hovedbok/excel?client_id=${CLIENT_ID}&account_from=1000&account_to=9999&from_date=${FROM}&to_date=${TO}"

# Leverandørreskontro
curl -o leverandor.pdf "http://localhost:8000/supplier-ledger/pdf?client_id=${CLIENT_ID}&status=all"
curl -o leverandor.xlsx "http://localhost:8000/supplier-ledger/excel?client_id=${CLIENT_ID}&status=all"

# Kundereskontro
curl -o kunde.pdf "http://localhost:8000/customer-ledger/pdf?client_id=${CLIENT_ID}&status=all"
curl -o kunde.xlsx "http://localhost:8000/customer-ledger/excel?client_id=${CLIENT_ID}&status=all"
```

---

## Browser URLs (for testing)

Replace `CLIENT_ID` with actual UUID:

```
# Saldobalanse PDF
http://localhost:8000/api/reports/saldobalanse/pdf?client_id=CLIENT_ID&from_date=2026-01-01&to_date=2026-02-11

# Resultat Excel
http://localhost:8000/api/reports/resultat/excel?client_id=CLIENT_ID&from_date=2026-01-01&to_date=2026-02-11

# Balanse PDF
http://localhost:8000/api/reports/balanse/pdf?client_id=CLIENT_ID&to_date=2026-02-11

# Hovedbok Excel (specific account)
http://localhost:8000/api/reports/hovedbok/excel?client_id=CLIENT_ID&account_number=1920&from_date=2026-01-01&to_date=2026-02-11

# Leverandørreskontro PDF (overdue only)
http://localhost:8000/supplier-ledger/pdf?client_id=CLIENT_ID&status=open

# Kundereskontro Excel (all)
http://localhost:8000/customer-ledger/excel?client_id=CLIENT_ID&status=all
```

---

## Frontend Integration

### JavaScript Fetch
```javascript
const downloadReport = async (endpoint, params) => {
  const url = `${endpoint}?${new URLSearchParams(params)}`;
  const response = await fetch(url);
  const blob = await response.blob();
  
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = url.split('/').pop().split('?')[0];
  a.click();
};

// Usage
downloadReport('/api/reports/saldobalanse/pdf', {
  client_id: '09409ccf-d23e-45e5-93b9-68add0b96277',
  from_date: '2026-01-01',
  to_date: '2026-02-11'
});
```

### React Button
```jsx
<button onClick={() => {
  const url = `/api/reports/saldobalanse/pdf?client_id=${clientId}&from_date=${fromDate}&to_date=${toDate}`;
  window.open(url, '_blank');
}}>
  📄 Eksporter PDF
</button>
```

---

## Status Filters

### Supplier Ledger
- `open` - Only unpaid invoices
- `partially_paid` - Partially paid invoices
- `paid` - Fully paid invoices
- `all` - All invoices (default if omitted)

### Customer Ledger
- `open` - Only unpaid invoices
- `partially_paid` - Partially paid invoices
- `paid` - Fully paid invoices
- `overdue` - Overdue invoices only
- `all` - All invoices (default if omitted)

---

## Response Types

### PDF
```
Content-Type: application/pdf
Content-Disposition: attachment; filename=Saldobalanse_GHB_AS_Test_2026-02-11.pdf
```

### Excel
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename=Saldobalanse_GHB_AS_Test_2026-02-11.xlsx
```

---

## Verification

Test all endpoints:
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
./test_all_exports.sh
```

Expected output:
```
Testing all 12 export endpoints...

1. Testing Saldobalanse PDF...
   ✓ Saldobalanse PDF created
2. Testing Saldobalanse Excel...
   ✓ Saldobalanse Excel created
...
12. Testing Kundereskontro Excel...
   ✓ Kundereskontro Excel created

Testing complete!
```
