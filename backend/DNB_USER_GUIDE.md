# DNB Open Banking - User Guide for Glenn

Step-by-step guide for using the DNB automatic transaction import feature.

---

## 🎯 What This Does

Instead of manually downloading CSV files from DNB and uploading them to Kontali ERP, this feature:

1. **Connects directly to your DNB account** (secure OAuth2)
2. **Automatically fetches transactions every night** (last 7 days)
3. **Matches transactions with invoices** (using AI)
4. **Creates tasks for unmatched items** (for your review)

---

## 🚀 Getting Started

### Step 1: Connect Your DNB Account

1. **Login to Kontali ERP**
   - Navigate to: **Settings → Bank Connections**

2. **Click "Connect DNB Account"**
   - A popup will open

3. **Login with BankID**
   - You'll be redirected to DNB's secure login page
   - Login with your BankID (just like normal DNB banking)

4. **Grant Access**
   - DNB will ask permission to share your account information
   - **Important:** You're only granting read access (Kontali can't make payments!)
   - Click "Authorize"

5. **Select Account**
   - If you have multiple accounts, select which one to connect
   - Usually you want your main business account
   - Click "Connect"

6. **Initial Sync**
   - Kontali will now import the last 90 days of transactions
   - This takes 10-30 seconds depending on transaction volume
   - You'll see a progress indicator

7. **Done!**
   - You'll see a success message
   - Transactions are now in the system
   - Auto-matching has run

---

## 🔄 How Automatic Sync Works

### Nightly Updates

Every night at **03:00 UTC** (04:00 Norwegian time in winter, 05:00 in summer):

1. Kontali connects to DNB
2. Fetches transactions from last 7 days
3. Checks for duplicates (skips already imported)
4. Stores new transactions
5. Runs auto-matching
6. Creates review tasks if needed

### Manual Sync (Optional)

If you need to fetch the latest transactions immediately:

1. Go to **Bank Connections**
2. Find your DNB connection
3. Click **"Sync Now"**
4. Wait 5-10 seconds
5. Done! Latest transactions imported

---

## 📊 What Happens After Import

### Auto-Matching

Kontali's AI automatically tries to match each transaction with:

1. **Vendor Invoices** (incoming invoices you've received)
   - Matches by amount, date, KID number, vendor name
   - High confidence matches (>85%) are auto-booked
   - Low confidence goes to review queue

2. **Customer Invoices** (outgoing invoices you've sent)
   - Matches customer payments with your invoices
   - Updates invoice status to "Paid"

3. **Known Patterns** (AI learns over time)
   - Recurring payments (rent, subscriptions)
   - Payroll transfers
   - Tax payments

### Review Queue

Transactions that couldn't be matched automatically appear in the **Review Queue**:

1. Navigate to **Bank Reconciliation → Review Queue**
2. You'll see:
   - Unmatched transactions
   - Low-confidence matches (for your approval)
   - Suggested matches (AI recommendations)

3. For each item:
   - **Approve Match:** Accept AI suggestion
   - **Correct Match:** Select different invoice
   - **Create Voucher:** For one-off transactions
   - **Ignore:** Mark as not relevant

---

## 🔐 Security & Access

### What DNB Access Grants

- **Read access to:**
  - Account balance
  - Transaction history (up to 90 days)
  - Account name and number

- **Cannot:**
  - Make payments
  - Transfer money
  - Change account settings
  - See other accounts (only selected one)

### Token Management

- OAuth tokens are **encrypted** in database
- Tokens **expire after 90 days** (DNB requirement)
- Automatic refresh (you won't notice)
- You can revoke access anytime (see below)

### Revoking Access

To disconnect your DNB account:

1. Go to **Settings → Bank Connections**
2. Find DNB connection
3. Click **"Disconnect"**
4. Confirm

This will:
- Revoke Kontali's access to your DNB account
- Stop automatic syncing
- Keep existing transactions (historical data not deleted)

---

## 🎛️ Configuration Options

### Sync Frequency

Default: Every 24 hours (nightly)

To change:
1. Go to **Bank Connections**
2. Click **Edit** on your DNB connection
3. Set **Sync Frequency** (in hours)
   - `6` = Every 6 hours (4 times per day)
   - `12` = Twice per day
   - `24` = Once per day (default)
4. Save

### Auto-Matching Threshold

Default: 85% confidence

To adjust:
1. Go to **Client Settings**
2. Find **AI Auto-Matching Threshold**
3. Adjust slider (0-100%)
   - **Higher (90-95%):** Fewer auto-matches, more manual review (safer)
   - **Lower (75-85%):** More auto-matches, faster (requires trust in AI)
4. Save

### Email Notifications

Get notified when manual review is needed:

1. Go to **User Settings → Notifications**
2. Enable **"Bank Reconciliation Alerts"**
3. Choose frequency:
   - Immediate (as items appear)
   - Daily digest (9:00 AM)
   - Weekly summary (Monday morning)

---

## 📝 Common Workflows

### Scenario 1: Reconciling Month-End

1. **Run manual sync** (fetch latest)
2. Go to **Review Queue**
3. Sort by **Date** (oldest first)
4. Work through unmatched items:
   - Match with invoices
   - Create vouchers for other transactions
5. When queue is empty → month is reconciled!

### Scenario 2: Large Payment Received

Customer paid a big invoice:

1. Transaction automatically imported
2. AI matches with customer invoice
3. Invoice status → **"Paid"**
4. You get notification (if enabled)
5. Nothing to do! ✓

### Scenario 3: Unknown Transaction

A transaction appears that you don't recognize:

1. Appears in **Review Queue** as "Unmatched"
2. Click **"View Details"**
3. Check description, counterparty, amount
4. Options:
   - **If it's a vendor invoice you haven't uploaded yet:**
     - Upload invoice first
     - Then match transaction
   - **If it's a one-off expense:**
     - Click "Create Voucher"
     - Select account (e.g., 6340 for office supplies)
     - Add description
     - Save
   - **If it's a refund or adjustment:**
     - Similar process, but credit account

---

## 🐛 Troubleshooting

### "Connection Failed" Error

**Cause:** OAuth token expired or revoked

**Solution:**
1. Go to **Bank Connections**
2. Click **"Reconnect"** on your DNB connection
3. Login with BankID again
4. Re-authorize

### No New Transactions Imported

**Possible Causes:**
1. No new transactions at DNB (check DNB banking app)
2. Sync not due yet (check "Last Sync" timestamp)
3. All transactions already imported (duplicates skipped)

**Solution:**
- Click **"Sync Now"** to force update
- If still no transactions, check DNB banking app to confirm they exist

### Duplicate Transactions

**Should not happen** - system checks for duplicates by:
- Date
- Amount
- Reference number
- Description

**If you see duplicates:**
1. Take screenshot
2. Contact support (this is a bug)
3. Mark one as "Ignore" in review queue

### Slow Sync (Takes >1 Minute)

**Normal for:**
- First sync (90 days of history)
- After long period without sync (e.g., after vacation)

**Abnormal for:**
- Daily sync (should be <10 seconds)

**Solution:**
- Check internet connection
- Check DNB status page (may be maintenance)
- If persistent, contact support

---

## ✅ Best Practices

### Daily Routine

**Morning (9:00 AM):**
1. Check email for review queue notifications
2. If any, go to **Review Queue**
3. Spend 5-10 minutes approving/matching
4. Done!

**Weekly (Monday):**
1. Run manual sync (to catch weekend transactions)
2. Review all unmatched items
3. Ensure all invoices matched

**Month-End:**
1. Run manual sync
2. Complete all review queue items
3. Generate reports (transactions are reconciled!)

### Tips for Faster Reconciliation

1. **Upload invoices promptly**
   - When you receive an invoice, upload it same day
   - AI will match it when payment arrives

2. **Use consistent vendor names**
   - If vendor name in DNB differs from invoice, AI may not match
   - You can teach AI (it learns from corrections)

3. **Add KID numbers**
   - Norwegian KID numbers help matching
   - Always include KID when paying invoices

4. **Review small amounts last**
   - Focus on large transactions first (>10,000 NOK)
   - Small amounts (<1,000 NOK) can wait

### Security Tips

1. **Don't share your BankID**
   - Only you should authorize DNB access
   - Don't let others login on your behalf

2. **Check connection status regularly**
   - Go to **Bank Connections** weekly
   - Ensure status is "Active"
   - If "Expired", reconnect

3. **Review sync logs**
   - Check that nightly sync is working
   - Look for "Success" status
   - If errors, investigate

---

## 🎓 Understanding the AI

### How Auto-Matching Works

The AI looks at:

1. **Amount Match**
   - Exact or close match (within 1 NOK)
   - Most important factor

2. **Date Proximity**
   - Transaction date near invoice due date
   - Within ±7 days usually

3. **KID Number**
   - If transaction has KID, lookup invoice
   - High confidence match

4. **Vendor/Customer Name**
   - Fuzzy matching (handles typos)
   - "Acme AS" matches "Acme ASA"

5. **Historical Patterns**
   - Learns from your corrections
   - If you always match "Rent - Building X" to account 6200, AI remembers

### Confidence Scores

- **95-100%:** Almost certain (auto-booked if threshold allows)
- **85-94%:** Very likely (shown as suggestion)
- **70-84%:** Possible (lower priority in queue)
- **<70%:** Unlikely (not shown as suggestion)

### Teaching the AI

When you correct a match:

1. AI saves your correction
2. Next time similar transaction appears, AI remembers
3. Gradually, fewer items need manual review
4. After ~3 months, most transactions auto-match

---

## 📞 Support

### Need Help?

**In-App Support:**
- Click **Help** icon (top right)
- Start chat with AI assistant
- For bank reconciliation: "Help with DNB transactions"

**Email:**
- support@kontali.no
- Include:
  - Your client name
  - Screenshot of issue
  - Transaction ID if applicable

**Urgent Issues:**
- Call: +47 XXX XX XXX (during business hours)

### Known Issues

- **None currently** (integration newly deployed)

### Feature Requests

Want something improved? Let us know!
- Email: feedback@kontali.no
- Or use in-app feedback button

---

## 🎉 Summary

### What You Should Do

1. **Once:** Connect your DNB account (15 minutes)
2. **Daily:** Check review queue (5-10 minutes)
3. **Weekly:** Ensure sync is working (1 minute check)
4. **Monthly:** Complete all reconciliation (for reports)

### What Happens Automatically

- ✅ Nightly transaction import
- ✅ Auto-matching with invoices
- ✅ Token refresh (no re-login needed)
- ✅ Duplicate prevention
- ✅ Error logging

### Expected Time Savings

**Before DNB Integration:**
- Download CSV: 2 min
- Upload to Kontali: 1 min
- Manual matching: 30-45 min
- **Total: ~50 min/day**

**After DNB Integration:**
- Review auto-matched: 5-10 min
- Match remaining: 5-10 min
- **Total: ~15 min/day**

**Savings: ~35 minutes per day = 3 hours per week!**

---

**Questions?** Don't hesitate to reach out. We're here to help make your accounting work easier!

---

**Last Updated:** 2026-02-10  
**Version:** 1.0  
**Integration Status:** ✅ Production Ready
