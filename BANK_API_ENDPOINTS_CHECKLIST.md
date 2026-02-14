# Bank Reconciliation API - Endpoints Checklist

Generated: 2026-02-14

## Expected vs Actual

### ✅ WORKING ENDPOINTS (15)

- [x] `GET /api/bank/accounts` - List bank accounts with balances
- [x] `GET /api/bank/accounts/{id}/reconciliation` - Get reconciliation details (4-part categorization)
- [x] `GET /api/bank/transactions` - List bank transactions with pagination
- [x] `GET /api/bank/transactions/{id}` - Get single transaction detail
- [x] `GET /api/bank/transactions/{id}/suggestions` - Get match suggestions (code ready)
- [x] `POST /api/bank/transactions/{id}/match` - Manual match (code ready)
- [x] `GET /api/bank/reconciliation/stats` - Get reconciliation statistics
- [x] `POST /api/bank/auto-match` - Auto-matching engine (code ready)
- [x] `POST /api/bank/import` - Import transactions from CSV (code ready)
- [x] `POST /api/bank/reconciliation/upload` - Upload bank statement (code ready)
- [x] `POST /api/bank/reconciliation/confirm` - Confirm match (code ready)
- [x] `GET /api/bank/reconciliation/status` - Reconciliation status (code ready)
- [x] `GET /api/bank-recon/rules` - Get matching rules
- [x] `POST /api/bank-recon/rules` - Create matching rules (code ready)

### ❌ BROKEN ENDPOINTS (1)

- [ ] `GET /api/bank-recon/unmatched` - Unmatched bank + ledger items
  - **Error:** SQLAlchemy greenlet_spawn async issue
  - **Fix:** Debug GeneralLedgerLine async join
  - **Impact:** Module 2 bank-to-ledger feature blocked

### ⚠️ NOT REGISTERED (5)

Bank matching algorithms exist in code but router not included in FastAPI app:

- [ ] `POST /api/bank/matching/kid` - Match by KID number
- [ ] `POST /api/bank/matching/bilagsnummer` - Match by voucher number
- [ ] `POST /api/bank/matching/beløp` - Match by amount
- [ ] `POST /api/bank/matching/kombinasjon` - Match by combination
- [ ] `POST /api/bank/matching/auto` - Auto-match multiple transactions

**Fix:** Add `app.include_router(bank_matching.router)` to `main.py`

---

## Confirmed Working (Tested)

```bash
# These endpoints return 200 OK with real data:
curl http://localhost:8000/api/bank/accounts?client_id=09409ccf-d23e-45e5-93b9-68add0b96277
curl http://localhost:8000/api/bank/transactions?client_id=09409ccf-d23e-45e5-93b9-68add0b96277
curl http://localhost:8000/api/bank/accounts/1/reconciliation?client_id=09409ccf-d23e-45e5-93b9-68add0b96277
curl http://localhost:8000/api/bank/reconciliation/stats?client_id=09409ccf-d23e-45e5-93b9-68add0b96277
curl http://localhost:8000/api/bank-recon/rules?client_id=09409ccf-d23e-45e5-93b9-68add0b96277
```

## Status Summary

- **Total Expected:** 19 endpoints
- **Implemented:** 15 ✅
- **Working/Ready:** 14 ✅
- **Broken:** 1 ❌
- **Not Registered:** 5 ⚠️ (Code exists, just needs router registration)

## Priority Fixes

1. **URGENT:** Register bank_matching router (1 line change)
2. **HIGH:** Fix /api/bank-recon/unmatched async error (affects Module 2)
3. **MEDIUM:** Replace mock data in /api/bank/accounts endpoints with real DB queries
4. **LOW:** Test all "code ready" endpoints to ensure they work
