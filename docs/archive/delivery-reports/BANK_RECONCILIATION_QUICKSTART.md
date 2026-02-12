# Bank Reconciliation - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start the Frontend

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
npm run dev
```

### Step 3: Test the System

Open your browser to `http://localhost:3000/bank` and:

1. **Upload Test CSV:**
   - Click "📤 Upload CSV"
   - Select `/backend/test_bank_statement.csv`
   - Watch auto-matching happen automatically

2. **Review Results:**
   - Check the statistics dashboard
   - See matched vs unmatched transactions
   - View auto-match rate

3. **Manual Matching:**
   - Click "Find Match" on unmatched transactions
   - Review confidence scores
   - Click "Match" to approve

---

## 🧪 API Testing with cURL

### Import Bank Statement
```bash
curl -X POST "http://localhost:8000/api/bank/import?client_id=09409ccf-d23e-45e5-93b9-68add0b96277" \
  -F "file=@backend/test_bank_statement.csv"
```

### Get Transactions
```bash
curl "http://localhost:8000/api/bank/transactions?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&status=unmatched"
```

### Get Match Suggestions
```bash
curl "http://localhost:8000/api/bank/transactions/{transaction_id}/suggestions?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

### Get Statistics
```bash
curl "http://localhost:8000/api/bank/reconciliation/stats?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

### Run Auto-Matching
```bash
curl -X POST "http://localhost:8000/api/bank/auto-match?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
```

---

## 📊 Expected Results

Using the test CSV (10 transactions):

- **Auto-match rate:** 60-80%
- **Matched automatically:** 6-8 transactions
- **Needs manual review:** 2-4 transactions
- **Confidence scores:** 
  - High (≥85%): 6-8 transactions
  - Medium (50-84%): 1-2 transactions
  - Low (<50%): 0-2 transactions

---

## 🔍 Troubleshooting

### Backend won't start
```bash
# Check database connection
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
alembic upgrade head
```

### No matches found
- Ensure vendor invoices exist in database
- Check that invoice amounts match transaction amounts
- Verify due dates are close to transaction dates
- Review matching criteria in logs

### CSV import fails
- Check CSV format (semicolon-separated)
- Verify Norwegian date format (DD.MM.YYYY)
- Ensure amount columns use comma for decimals
- See `/backend/test_bank_statement.csv` for reference

---

## 📖 Test Data Details

The test CSV includes:

1. **Vendor Payments (Debit):**
   - 5000 NOK to ABC Leverandører AS
   - 2500 NOK to Elkjøp AS
   - 8000 NOK to XYZ Norge AS
   - 7500 NOK to Glenn Wilsen
   - 500 NOK to DigitalOcean
   - 3000 NOK to Meta Ads

2. **Customer Receipts (Credit):**
   - 15000 NOK from Kontali AS (KID: 123456789)
   - 12000 NOK payment (KID: 987654321)
   - 8500 NOK from Test Kunde AS

**Note:** For best testing results, create matching vendor invoices before importing.

---

## 🎯 Quick Demo Script

1. **Setup (2 min):**
   - Start backend and frontend
   - Open browser to /bank

2. **Import (30 sec):**
   - Upload test CSV
   - Observe auto-matching

3. **Review Stats (1 min):**
   - Check match rate
   - View confidence scores
   - Analyze unmatched

4. **Manual Match (1 min):**
   - Find unmatched transaction
   - Click "Find Match"
   - Review suggestions
   - Approve match

**Total Demo Time:** ~5 minutes

---

## 📝 Next Steps

After successful testing:

1. **Production Data:**
   - Export real bank statement
   - Create vendor invoices
   - Import and test matching

2. **Tune Algorithm:**
   - Adjust confidence thresholds
   - Add custom matching rules
   - Train on historical data

3. **Integrate:**
   - Connect bank API
   - Schedule automatic imports
   - Set up notifications

---

## ✅ Success Indicators

You'll know it's working when:

- ✅ CSV imports without errors
- ✅ Statistics dashboard shows counts
- ✅ Auto-match rate > 80%
- ✅ Suggestions appear for unmatched
- ✅ Manual matching works smoothly
- ✅ Database records created correctly

---

Ready to go! 🚀
