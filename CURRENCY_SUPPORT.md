# Currency Exchange Rate System - Complete Implementation

## Overview

Complete multi-currency support system for Kontali ERP with automatic exchange rate updates from official sources.

## Supported Currencies

| Currency | Code | Source | Update Frequency |
|----------|------|--------|------------------|
| Norwegian Krone | NOK | Base currency | N/A |
| US Dollar | USD | Norges Bank API | Daily |
| Euro | EUR | Norges Bank API | Daily |
| Swedish Krona | SEK | Norges Bank API | Daily |
| Danish Krone | DKK | Norges Bank API | Daily |
| Bitcoin | BTC | CoinGecko API | Daily |

## Features

### ✅ Backend Implementation

1. **Database Model** (`CurrencyRate`)
   - Stores exchange rates with date and source
   - High precision for crypto currencies (20,6 decimal places)
   - Indexed for fast lookups by currency and date

2. **Currency Rate Service** (`CurrencyRateService`)
   - Fetch rates from Norges Bank API (fiat currencies)
   - Fetch BTC rate from CoinGecko API
   - Store and update rates in database
   - Convert between any supported currencies
   - Historical rate lookups

3. **REST API Endpoints**
   ```
   GET  /api/currencies/supported         - List supported currencies
   GET  /api/currencies/rates             - Get latest rates
   GET  /api/currencies/rates/{currency}  - Get specific currency rate
   GET  /api/currencies/rates/{currency}/history - Historical rates
   POST /api/currencies/rates/refresh     - Manual rate refresh
   POST /api/currencies/convert           - Convert between currencies
   ```

4. **Client Settings Integration**
   - `supported_currencies` - Array of enabled currencies per client
   - `auto_update_rates` - Enable/disable automatic updates
   - `last_rate_update` - Timestamp of last update

### ✅ Frontend Implementation

1. **Currency Management Component**
   - Visual currency selection with flags
   - Real-time rate display
   - Manual refresh button
   - Auto-update toggle
   - Last update timestamp

2. **Integration in Firmainnstillinger**
   - Added to "Regnskapsoppsett" (Accounting Settings) tab
   - Seamlessly integrated with existing settings
   - Auto-save functionality

### ✅ Automation

1. **Daily Rate Updates**
   - Script: `backend/scripts/update_currency_rates.py`
   - Fetches all rates from APIs
   - Updates database
   - Updates client settings timestamps
   - Logs results

2. **Cron Job Setup**
   ```bash
   # Add to crontab (daily at 9:00 AM)
   0 9 * * * cd /path/to/backend && python scripts/update_currency_rates.py
   ```

## Implementation Files

### Backend
```
backend/
├── app/
│   ├── models/
│   │   └── currency_rate.py                    # CurrencyRate model
│   ├── services/
│   │   └── currency_rate_service.py            # Rate fetching & conversion service
│   └── api/
│       └── routes/
│           └── currencies.py                    # REST API endpoints
├── alembic/
│   └── versions/
│       └── 20260211_1310_add_currency_rates.py # Database migration
└── scripts/
    └── update_currency_rates.py                 # Daily update script
```

### Frontend
```
frontend/
├── src/
│   ├── components/
│   │   └── CurrencyManagement.tsx              # Currency management UI
│   ├── api/
│   │   └── client-settings.ts                  # Updated types
│   └── pages/
│       └── Innstillinger/
│           └── Firmainnstillinger.tsx          # Updated with currency section
```

## Setup Instructions

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This creates:
- `currency_rates` table
- Adds currency fields to `client_settings` table

### 2. Initial Rate Import

```bash
cd backend
python -m uvicorn app.main:app --reload &
sleep 5
curl -X POST http://localhost:8000/api/currencies/rates/refresh
```

### 3. Setup Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (adjust path):
0 9 * * * cd /home/ubuntu/.openclaw/workspace/ai-erp/backend && /usr/bin/python3 scripts/update_currency_rates.py >> /var/log/currency_updates.log 2>&1
```

### 4. Frontend Build

```bash
cd frontend
npm install  # If needed
npm run build
```

## API Examples

### Get Latest Rates

```bash
curl http://localhost:8000/api/currencies/rates
```

Response:
```json
{
  "rates": {
    "USD": {
      "rate": 10.55,
      "date": "2026-02-11",
      "source": "norges_bank"
    },
    "EUR": {
      "rate": 11.82,
      "date": "2026-02-11",
      "source": "norges_bank"
    },
    "BTC": {
      "rate": 875000.50,
      "date": "2026-02-11",
      "source": "coingecko"
    }
  },
  "last_updated": "2026-02-11T09:00:00"
}
```

### Convert Currency

```bash
curl -X POST http://localhost:8000/api/currencies/convert \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "from_currency": "USD",
    "to_currency": "NOK"
  }'
```

Response:
```json
{
  "original_amount": 100,
  "original_currency": "USD",
  "converted_amount": 1055.00,
  "converted_currency": "NOK",
  "rate": 10.55,
  "conversion_date": "2026-02-11"
}
```

### Historical Rates

```bash
curl "http://localhost:8000/api/currencies/rates/USD/history?days=30"
```

## Testing

### 1. Test External APIs

```bash
cd backend
python test_currency_apis.py
```

This tests:
- Norges Bank API connectivity
- CoinGecko API connectivity
- Data parsing and rate extraction

### 2. Test Backend APIs

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, run tests
cd backend
python test_currency_apis.py
```

### 3. Test Frontend

1. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to: `http://localhost:3000/innstillinger/firmainnstillinger`
4. Go to "Regnskapsoppsett" tab
5. Scroll down to "Valutastøtte" section
6. Test:
   - Enable/disable currencies
   - Click "Oppdater kurser" button
   - Verify rates display correctly
   - Save settings

## Usage in Invoices

When creating invoices in foreign currency:

1. **Store Original Amount**: Keep original currency and amount
2. **Store NOK Equivalent**: Convert using current rate
3. **Reference Rate Date**: Store which rate was used

Example:
```python
from app.services.currency_rate_service import CurrencyRateService
from decimal import Decimal
from datetime import date

# In your invoice creation code
service = CurrencyRateService(db)

original_amount = Decimal("1000.00")
original_currency = "USD"
invoice_date = date.today()

# Convert to NOK
nok_amount = service.convert_amount(
    amount=original_amount,
    from_currency=original_currency,
    to_currency="NOK",
    target_date=invoice_date
)

# Store in invoice
invoice.amount = original_amount
invoice.currency = original_currency
invoice.nok_amount = nok_amount
invoice.exchange_rate_date = invoice_date
```

## Monitoring

### Check Last Update

```bash
curl http://localhost:8000/api/currencies/rates | jq '.last_updated'
```

### Check Cron Job Logs

```bash
tail -f /var/log/currency_updates.log
```

### Manual Update

```bash
curl -X POST http://localhost:8000/api/currencies/rates/refresh
```

## API Rate Limits

### Norges Bank API
- No official rate limit
- Recommended: Max 100 requests/hour
- Our usage: 4 requests/day (well within limits)

### CoinGecko API (Free Tier)
- Rate limit: 10-50 calls/minute
- Monthly limit: ~30,000 calls
- Our usage: 1 request/day (well within limits)

## Troubleshooting

### Rates Not Updating

1. Check cron job is running:
   ```bash
   crontab -l | grep currency
   ```

2. Check logs:
   ```bash
   tail -100 /var/log/currency_updates.log
   ```

3. Test manual update:
   ```bash
   cd backend
   python scripts/update_currency_rates.py
   ```

### API Errors

1. **Norges Bank 404**: Currency not available for that date
   - Solution: Use fallback to most recent available rate

2. **CoinGecko Rate Limit**: Too many requests
   - Solution: Our daily updates are well within limits
   - If testing frequently, add delay between requests

3. **Network Timeout**: External API unreachable
   - Solution: Implement retry logic (already built-in with 10s timeout)

### Frontend Not Showing Rates

1. Check API is running:
   ```bash
   curl http://localhost:8000/api/currencies/rates
   ```

2. Check browser console for errors

3. Verify CORS settings in backend

## Future Enhancements

### Possible Additions

1. **More Currencies**
   - GBP (British Pound)
   - CHF (Swiss Franc)
   - JPY (Japanese Yen)
   - More cryptocurrencies

2. **Advanced Features**
   - Custom exchange rates (manual override)
   - Forward rates (future dated)
   - Rate alerts (notify on significant changes)
   - Rate history charts
   - Automatic revaluation of open invoices

3. **Reporting**
   - Currency gain/loss reports
   - Multi-currency balance sheet
   - Exchange rate variance analysis

## Compliance & Best Practices

### Norwegian Accounting Standards

- Base currency: NOK (required)
- Exchange rates: Official rates from Norges Bank (recommended)
- Documentation: Store rate date and source (implemented)
- Revaluation: Open balances should be revalued at period end

### Data Retention

- Keep historical rates for audit trail
- Minimum 5 years (Norwegian requirement)
- Currently: No automatic deletion (keeps all history)

## Conclusion

The currency exchange rate system is fully implemented and production-ready:

✅ Complete backend with models, service, and API
✅ Beautiful frontend UI with real-time rates
✅ Automatic daily updates from official sources
✅ Comprehensive error handling
✅ Full documentation
✅ Testing scripts included
✅ Norwegian accounting compliance

**Ready to use!** 🚀
