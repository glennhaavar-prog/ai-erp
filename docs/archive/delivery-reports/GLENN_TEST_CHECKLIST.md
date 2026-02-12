# Glenn's Kontali ERP Testing Checklist

**Date:** February 10, 2026  
**Purpose:** Final acceptance testing via SSH tunnel  
**Estimated Time:** 45-60 minutes

---

## Prerequisites

### 1. SSH Tunnel Setup (Windows PowerShell)
```powershell
ssh -L 3002:localhost:3002 -L 8000:localhost:8000 ubuntu@<server-ip>
```

✅ **Verify:** Terminal stays open with message "Authenticated to..."

### 2. Test Connection
Open in your browser:
- Frontend: http://localhost:3002 ➡️ Should load dashboard
- Backend API Docs: http://localhost:8000/docs ➡️ Should show Swagger UI

---

## Testing Protocol

### Phase 1: Navigation & UI (10 minutes)

#### Dashboard
- [ ] Open http://localhost:3002
- [ ] Dashboard loads without errors
- [ ] Sidebar menu visible on left
- [ ] No hydration errors (check browser console with F12)
- [ ] Logo displays correctly at top

#### Menu Navigation
Test each menu item (just click and verify page loads):

- [ ] 🏠 Dashboard → `/`
- [ ] 📊 Rapporter (Reports submenu):
  - [ ] Saldobalanse → `/rapporter/saldobalanse`
  - [ ] Balanse → `/rapporter/balanse`
  - [ ] Resultat → `/rapporter/resultat` (if in menu)
- [ ] 📚 Hovedbok → `/hovedbok`
- [ ] 💰 Reskontro (Ledger submenu):
  - [ ] Leverandører → `/reskontro/leverandorer`
  - [ ] Kunder → `/reskontro/kunder`
- [ ] 📄 Bilag → `/bilag/journal`
- [ ] 🏦 Bankavstemming → `/bank-reconciliation`
- [ ] ✅ Oppgaver → `/clients/<client-id>/oppgaver` (pick a client)
- [ ] 📅 Period Close → `/period-close`
- [ ] 🧮 Accruals → `/accruals`
- [ ] 🧪 Test EHF → `/test/ehf`

**Expected:** All pages load within 3 seconds, no error messages, no blank pages.

---

### Phase 2: EHF Invoice Processing (15 minutes)

#### Navigate to Test EHF Page
- [ ] Go to http://localhost:3002/test/ehf
- [ ] Page displays with two tabs: "Upload EHF" and "Paste XML"

#### Test Upload Method
1. [ ] Click "Upload EHF" tab
2. [ ] Click "Choose File" or drag-and-drop zone
3. [ ] Browse to: `ai-erp\backend\tests\fixtures\ehf\`
4. [ ] Select `ehf_sample_1_simple.xml`
5. [ ] Click upload/submit button

**Expected Results:**
- [ ] Processing indicator shows
- [ ] Success message appears (green checkmark)
- [ ] Processing details display:
  - ✅ **Step 1:** Parse XML → SUCCESS
  - ✅ **Step 2:** Validate → SUCCESS
  - ✅ **Step 3:** Get/Create Vendor → SUCCESS
    - Vendor: Leverandør Demo AS
    - Org: 999100101
  - ✅ **Step 4:** Create Invoice → SUCCESS
    - Invoice ID: (some UUID)
    - Amount: 31,250.00 NOK
  - ✅ **Step 5:** AI Processing → SUCCESS
    - Confidence score: 0.XX
  - ✅ **Step 6:** Add to Review Queue → SUCCESS

#### Test Additional Files
- [ ] Upload `ehf_sample_2_multi_line.xml` (52,975 NOK)
  - Expected: SUCCESS with multiple line items
- [ ] Upload `ehf_sample_5_credit_note.xml` (-6,250 NOK)
  - Expected: SUCCESS with negative amount

#### Test Paste Method
1. [ ] Click "Paste XML" tab
2. [ ] Open `ehf_sample_1_simple.xml` in text editor
3. [ ] Copy entire XML content
4. [ ] Paste into text area
5. [ ] Click "Process XML" button

**Expected:** Same successful processing as upload method

---

### Phase 3: Review Queue (10 minutes)

#### Access Review Queue
- [ ] Navigate to Review Queue page (if in menu)
- [ ] Or use: http://localhost:8000/api/review-queue/

**Expected:**
- [ ] See list of invoices you just uploaded
- [ ] Each item shows:
  - Vendor name
  - Amount
  - Status (e.g., "pending_review")
  - AI confidence score
  - Date received

#### Review Invoice Details
- [ ] Click on one of the invoices
- [ ] Verify details page shows:
  - Full vendor information
  - Invoice number
  - Due date
  - Line items with amounts
  - VAT breakdown
  - Total amount

#### Approve Invoice (If UI supports it)
- [ ] Click "Approve" button
- [ ] Verify confirmation message
- [ ] Check voucher is created (note voucher ID)

---

### Phase 4: Accounting Reports (15 minutes)

#### Saldobalanse (Trial Balance)
- [ ] Navigate to `/rapporter/saldobalanse`
- [ ] Select a client from dropdown (e.g., "Advokat Demo 11")
- [ ] Report displays within 2 seconds
- [ ] Verify columns: Account Number, Account Name, Debit, Credit, Balance
- [ ] Check a few sample accounts:
  - 1500 (Kunder/Customers)
  - 2400 (Leverandører/Suppliers)
  - 5000-8999 (Expenses/Revenue)
- [ ] Verify totals: **Debit Total = Credit Total**

#### Balance Sheet (Balanse)
- [ ] Navigate to `/rapporter/balanse`
- [ ] Select same client
- [ ] Report displays three sections:
  - **ASSETS (Eiendeler)** - Accounts 1000-1999
  - **LIABILITIES (Gjeld)** - Accounts 2000-2999
  - **EQUITY (Egenkapital)** - Accounts 3000-3999
- [ ] Verify calculation: **Assets = Liabilities + Equity**

#### Income Statement (Resultat)
- [ ] Navigate to `/rapporter/resultat` or income statement page
- [ ] Select same client
- [ ] Report displays:
  - **INCOME (Inntekter)** - Accounts 3000-3999
  - **EXPENSES (Kostnader)** - Accounts 5000-8999
  - **NET PROFIT/LOSS** - Income minus Expenses
- [ ] Verify all amounts make sense (no absurd numbers)

#### Hovedbok (General Ledger)
- [ ] Navigate to `/hovedbok`
- [ ] Select an account from dropdown:
  - Try 2400 (Leverandører)
- [ ] View transaction list:
  - Date
  - Voucher number
  - Description
  - Debit amount
  - Credit amount
  - Running balance
- [ ] Click on a transaction to view voucher details

#### Leverandørreskontro (Supplier Ledger)
- [ ] Navigate to `/reskontro/leverandorer`
- [ ] Verify supplier list displays
- [ ] Check columns: Supplier Name, Org Number, Balance, Overdue
- [ ] Click on a supplier
- [ ] View transaction history for that supplier
- [ ] Verify balance matches Account 2400 for that supplier

#### Kundereskontro (Customer Ledger)
- [ ] Navigate to `/reskontro/kunder`
- [ ] Verify customer list displays
- [ ] Check columns: Customer Name, Org Number, Balance, Overdue
- [ ] Click on a customer
- [ ] View transaction history
- [ ] Verify balance matches Account 1500 for that customer

---

### Phase 5: Bank Reconciliation (5 minutes)

#### Access Bank Reconciliation
- [ ] Navigate to `/bank-reconciliation`
- [ ] Page loads without errors
- [ ] UI displays:
  - Transaction list (if data exists)
  - Match suggestions panel
  - Status indicators

#### Check Functionality (if test data available)
- [ ] Verify transaction list shows bank transactions
- [ ] Check auto-matching suggestions
- [ ] Verify match confidence scores
- [ ] Test filter/search (if UI has it)

**Note:** May have limited data if no CSV has been uploaded yet.

---

### Phase 6: Voucher Journal (5 minutes)

#### Access Voucher Journal
- [ ] Navigate to `/bilag/journal`
- [ ] Voucher list displays
- [ ] Columns: Voucher Number, Date, Description, Amount, Status

#### Verify Voucher Details
- [ ] Click on a voucher (preferably one created from EHF approval)
- [ ] View voucher details:
  - Header: Voucher number, date, description
  - Lines: Account, Debit, Credit, Description
  - Totals: Debit Total = Credit Total
- [ ] Check linked document (if available) - e.g., invoice PDF

---

### Phase 7: Task Administration (5 minutes)

#### Access Tasks
- [ ] Navigate to `/clients/<client-id>/oppgaver`
  - Or find "Oppgaver" in menu
- [ ] Task list displays for selected client
- [ ] Columns: Task Name, Due Date, Status, Priority

#### Check Task Categories
- [ ] Verify tasks are organized by category:
  - Bank reconciliation tasks
  - VAT reporting tasks
  - Period close tasks
  - Review queue tasks

#### Complete a Task (if UI supports it)
- [ ] Click on a task
- [ ] Mark as complete
- [ ] Verify status updates

---

## Verification Checklist

### ✅ Core Features Working
- [ ] All pages load without errors
- [ ] No hydration errors in browser console
- [ ] EHF invoices process successfully
- [ ] Vendors are created/updated correctly
- [ ] Review Queue populates with new invoices
- [ ] Reports display accurate data
- [ ] Vouchers balance (debit = credit)
- [ ] Leverandørreskontro matches Account 2400
- [ ] Kundereskontro matches Account 1500

### ✅ Performance Acceptable
- [ ] Pages load within 3 seconds
- [ ] API responses feel snappy
- [ ] Reports generate quickly (<2 seconds)
- [ ] EHF processing completes in <5 seconds

### ✅ UI/UX Quality
- [ ] Design looks professional
- [ ] Navigation is intuitive
- [ ] No broken links
- [ ] Buttons and forms work
- [ ] Error messages are clear (if any)
- [ ] Responsive design (try resizing browser)

---

## Known Issues (Expected)

These are NOT bugs:
1. **Some API endpoints require parameters** - e.g., vouchers need `client_id`
2. **Demo environment notice** - Header shows "x-demo-environment: true"
3. **Limited bank data** - Until CSV is uploaded
4. **Placeholder content** - Some sections may have sample data

---

## If Something Doesn't Work

### Troubleshooting Steps:

1. **Check browser console** (F12 → Console tab)
   - Look for error messages
   - Note the error text

2. **Check network requests** (F12 → Network tab)
   - Look for failed requests (red)
   - Note which API call failed

3. **Verify SSH tunnel is active**
   - Is the PowerShell terminal still open?
   - Try refreshing the page

4. **Check backend status**
   - Open http://localhost:8000/health
   - Should return: `{"status":"healthy",...}`

5. **Test API directly**
   - Open http://localhost:8000/docs
   - Try calling an endpoint manually

### Common Issues:

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Page won't load | SSH tunnel dropped | Restart SSH tunnel |
| 404 Not Found | Wrong URL | Check spelling, try trailing slash |
| Blank page | JS error | Check browser console |
| Slow loading | Server under load | Wait or refresh |
| "Client not found" | Wrong client ID | Select different client |

---

## Report Issues

If you find bugs, note:
1. **What you were doing** (steps to reproduce)
2. **What you expected** to happen
3. **What actually happened** (include error message)
4. **Screenshot** (if helpful)
5. **Browser console errors** (F12 → Console)

---

## Success Criteria

✅ **TEST PASSED** if:
- All pages in Phase 1 load successfully
- EHF processing completes without errors (Phase 2)
- At least one invoice visible in Review Queue (Phase 3)
- All reports display data correctly (Phase 4)
- No critical errors in browser console
- System feels responsive and professional

✅ **READY FOR PRODUCTION** if all above criteria met.

---

## After Testing

### Quick Health Check
Run this command on server:
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp
./quick-verification.sh
```

Should show all green checkmarks.

### Next Steps
1. ✅ Mark all completed checklist items
2. 📝 Note any issues found
3. 🎉 Celebrate if everything works!
4. 🚀 Proceed with production deployment

---

**Testing Time:** ~60 minutes  
**Difficulty:** Easy (just click through and verify)  
**Required:** SSH tunnel + web browser  
**Optional:** Text editor (for viewing XML files)

---

*Good luck with testing! 🚀*
