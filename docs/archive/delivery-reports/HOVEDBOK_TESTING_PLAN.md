# Hovedbok Testing Plan

**Goal:** Verify end-to-end hovedbok functionality before 19:00 UTC report

---

## ✅ Pre-Testing Checklist

- [ ] Backend API `/api/reports/hovedbok/` exists and responds
- [ ] Frontend component `HovedbokReport.tsx` built
- [ ] Demo data generated (50-100 GL entries)
- [ ] Services running (backend on 8000, frontend on 3000)
- [ ] Database has general_ledger and general_ledger_lines tables

---

## 🧪 Test Scenarios

### 1. Auto-Booking Flow (≥85% confidence)
**Steps:**
1. Upload/create a new vendor invoice (high confidence scenario)
2. Verify AI analysis returns confidence ≥85%
3. Check that General Ledger entry is automatically created
4. Verify voucher number generated (AP-XXXXXX)
5. Verify debit = credit balance
6. Check huvudbok shows the entry

**Expected Result:**
- Invoice status = "auto_approved"
- GL entry created with correct lines
- Huvudbok displays entry immediately

---

### 2. Manual Approval Flow (<85% confidence)
**Steps:**
1. Create invoice with low confidence (48-72%)
2. Verify it goes to Review Queue
3. Open Review Queue, find the item
4. Click "Approve"
5. Verify GL entry is created
6. Check huvudbok shows the entry

**Expected Result:**
- Invoice goes to review queue first
- After approval, GL entry created
- Huvudbok updated

---

### 3. Huvudbok Report Filtering
**Steps:**
1. Open /huvudbok page
2. Test date range filter (Jan 2026, Feb 2026)
3. Test account number filter (6100, 2400, etc.)
4. Test vendor filter
5. Test sorting (date, amount)
6. Test pagination (if >50 entries)

**Expected Result:**
- Filters work correctly
- Data updates instantly
- No errors in console

---

### 4. Balance Validation
**Steps:**
1. Query all GL entries for a period
2. Sum all debit amounts
3. Sum all credit amounts
4. Verify debit = credit

**SQL Query:**
```sql
SELECT 
  SUM(debit_amount) as total_debit,
  SUM(credit_amount) as total_credit
FROM general_ledger_lines
JOIN general_ledger ON general_ledger_lines.general_ledger_id = general_ledger.id
WHERE general_ledger.client_id = '<client_id>'
  AND general_ledger.accounting_date BETWEEN '2026-01-01' AND '2026-02-28';
```

**Expected Result:**
- total_debit = total_credit
- If not balanced → BLOCKER, send Telegram alert

---

### 5. Reversal (Correction) Flow
**Steps:**
1. Identify a GL entry to reverse
2. Call reverse_general_ledger_entry() API (manual test)
3. Verify reversal entry created with opposite signs
4. Verify original entry marked as is_reversed=True
5. Check huvudbok shows both entries

**Expected Result:**
- Reversal entry created
- Original entry immutable but marked reversed
- Net effect = zero

---

### 6. UI/UX Testing
**Steps:**
1. Check responsive design (desktop, tablet)
2. Verify dark theme consistent
3. Test loading states
4. Test error handling (disconnect backend, check error message)
5. Verify Norwegian language in all labels

**Expected Result:**
- Professional accounting report look
- User-friendly error messages
- No broken UI elements

---

### 7. Performance Testing
**Steps:**
1. Generate 200-500 GL entries (larger dataset)
2. Query hovedbok with no filters
3. Measure response time
4. Test pagination performance
5. Test sorting performance

**Expected Result:**
- Query time <2 seconds
- Pagination smooth
- No browser lag

---

## 🚨 Blocker Scenarios (Send Telegram Alert)

**If any of these occur, STOP and alert Glenn:**

1. **Balance mismatch** - Debit ≠ Credit in any GL entry
2. **Database error** - Cannot insert GL entries
3. **API failure** - Backend endpoint returns 500
4. **Data loss** - Invoices booked but not visible in huvudbok
5. **Critical bug** - System crashes during booking

---

## 📊 Success Criteria

### Minimum for 19:00 Report:
- [ ] At least 50 GL entries in database
- [ ] Huvudbok report displays entries correctly
- [ ] Filtering works (date, account)
- [ ] Auto-booking flow tested (at least 3 invoices)
- [ ] Manual approval flow tested (at least 2 invoices)
- [ ] Balance validated (debit = credit)
- [ ] No critical bugs

### Nice-to-Have:
- [ ] Excel export working
- [ ] PDF viewer integration
- [ ] Reversal flow tested
- [ ] Performance optimized

---

## 🔄 Continuous Monitoring

**While sub-agents work:**
1. Check sub-agent progress every 15 minutes
2. If sub-agent stuck >30 min → intervene
3. If sub-agent completes → immediately test deliverable
4. If sub-agent fails → reassign task or do manually

---

## 📝 Testing Notes Template

```
## Test Run: [Time]

**Scenario:** [Name]
**Result:** ✅ Pass / ❌ Fail
**Details:** 
- [What worked]
- [What didn't work]
- [Observations]

**Next Steps:**
- [Actions needed]
```

---

**Testing starts when all 3 sub-agents complete their tasks.**
