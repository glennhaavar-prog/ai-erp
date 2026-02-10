# DNB Open Banking Integration

Complete integration with DNB's PSD2 Open Banking API for automatic bank transaction import and reconciliation.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
- [Usage](#usage)
- [Scheduled Sync](#scheduled-sync)
- [Security](#security)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This integration enables Kontali ERP to automatically fetch bank transactions from DNB using the PSD2 Account Information Services (AIS) API. Transactions are automatically matched with invoices using AI, reducing manual reconciliation work.

### Key Benefits

- ✅ **Automatic transaction import** - No more manual CSV uploads
- ✅ **Real-time OAuth2 authentication** - Secure, standards-based
- ✅ **Automatic matching** - AI matches transactions to invoices
- ✅ **Scheduled sync** - Nightly updates (configurable)
- ✅ **Audit trail** - All transactions and API calls logged
- ✅ **Secure storage** - Tokens encrypted at rest

---

## ✨ Features

### Implemented

1. **OAuth2 Authentication**
   - Authorization Code Flow with DNB
   - Token refresh (automatic)
   - Token revocation
   - CSRF protection (state parameter)

2. **Transaction Fetching**
   - Fetch last 90 days of transactions
   - Pagination support
   - Deduplication (prevents importing same transaction twice)
   - Raw response storage for audit

3. **Database Integration**
   - `bank_connections` table for OAuth tokens and account mappings
   - Encrypted token storage
   - Link to existing `bank_transactions` table
   - Client-specific connections

4. **Auto-Matching**
   - Triggers existing auto-matching service after import
   - Updates Review Queue with new matches
   - Creates tasks for manual review when needed

5. **Scheduled Sync**
   - Configurable sync frequency (default: 24 hours)
   - Error handling and retry logic
   - Sync status tracking per connection

6. **Security**
   - Tokens encrypted using Fernet (symmetric encryption)
   - Key derived from app SECRET_KEY
   - Secure OAuth2 state management
   - Sandbox/Production environment separation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kontali ERP                              │
│                                                               │
│  ┌────────────────┐        ┌────────────────┐              │
│  │  API Endpoints │───────▶│  DNB Service   │              │
│  │  /api/dnb/*    │        │                │              │
│  └────────────────┘        └────────┬───────┘              │
│                                     │                        │
│  ┌─────────────────────────────────▼──────────────────┐    │
│  │                DNB Integration Layer                 │    │
│  │                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │ OAuth2 Client│  │  API Client  │  │Encryption│ │    │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │    │
│  └──────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Database Layer                       │    │
│  │  ┌────────────────┐  ┌────────────────┐         │    │
│  │  │bank_connections│  │bank_transactions│         │    │
│  │  └────────────────┘  └────────────────┘         │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────┘
                                │ HTTPS + OAuth2
                                ▼
                    ┌───────────────────────┐
                    │   DNB Open Banking    │
                    │   API (PSD2)          │
                    └───────────────────────┘
```

### Components

1. **API Endpoints** (`app/api/routes/dnb.py`)
   - `/api/dnb/oauth/initiate` - Start OAuth flow
   - `/api/dnb/oauth/callback` - OAuth redirect target
   - `/api/dnb/connect` - Complete connection setup
   - `/api/dnb/sync` - Manual sync trigger
   - `/api/dnb/connections` - List connections
   - `/api/dnb/sync/all` - Cron job endpoint

2. **Services** (`app/services/dnb/`)
   - `oauth_client.py` - OAuth2 authentication
   - `api_client.py` - DNB API calls
   - `service.py` - Main orchestration
   - `encryption.py` - Token security

3. **Models**
   - `bank_connection.py` - Connection & token storage
   - `bank_transaction.py` - Transaction records (existing)

---

## 🚀 Setup

### 1. Register with DNB Developer Portal

Visit [developer.dnb.no](https://developer.dnb.no) and:

1. Create an account
2. Register a new application
3. Configure OAuth2 redirect URI: `http://localhost:8000/api/dnb/oauth/callback`
4. Note your credentials:
   - Client ID
   - Client Secret
   - API Key

### 2. Environment Configuration

Add to `.env`:

```bash
# DNB Open Banking
DNB_CLIENT_ID=your_client_id_here
DNB_CLIENT_SECRET=your_client_secret_here
DNB_API_KEY=your_api_key_here
DNB_REDIRECT_URI=http://localhost:8000/api/dnb/oauth/callback
DNB_USE_SANDBOX=true  # Set to false for production

# Encryption (use a strong random key in production!)
SECRET_KEY=your-secret-key-here-change-in-production
```

### 3. Run Database Migration

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
alembic upgrade head
```

This creates the `bank_connections` table.

### 4. Start Backend

```bash
uvicorn app.main:app --reload
```

---

## 📡 API Endpoints

### POST `/api/dnb/oauth/initiate`

Start OAuth2 authorization flow.

**Request:**
```json
{
  "client_id": "uuid-of-client"
}
```

**Response:**
```json
{
  "success": true,
  "authorization_url": "https://api.sandbox.dnb.no/oauth2/authorize?...",
  "state": "csrf-token",
  "message": "Visit the authorization URL to grant access"
}
```

### GET `/api/dnb/oauth/callback`

OAuth2 callback (DNB redirects here after user authorization).

**Query Parameters:**
- `code` - Authorization code
- `state` - CSRF token

**Response:**
```json
{
  "success": true,
  "accounts": [
    {
      "accountId": "acc-123",
      "iban": "NO1234567890123",
      "name": "Business Account"
    }
  ],
  "next_step": "Call POST /api/dnb/connect with selected account"
}
```

### POST `/api/dnb/connect`

Complete connection after OAuth authorization.

**Request:**
```json
{
  "client_id": "uuid",
  "code": "auth-code",
  "state": "csrf-token",
  "account_id": "acc-123",
  "account_number": "12345678901",
  "account_name": "Business Account"
}
```

**Response:**
```json
{
  "success": true,
  "connection_id": "uuid",
  "initial_sync": {
    "fetched": 45,
    "new": 45,
    "duplicates": 0,
    "errors": 0
  },
  "message": "Bank account connected successfully!"
}
```

### POST `/api/dnb/sync`

Manually trigger transaction sync.

**Request:**
```json
{
  "connection_id": "uuid",
  "from_date": "2024-01-01",  // Optional
  "to_date": "2024-02-10"      // Optional
}
```

**Response:**
```json
{
  "success": true,
  "sync_result": {
    "fetched": 12,
    "new": 10,
    "duplicates": 2,
    "errors": 0
  }
}
```

### GET `/api/dnb/connections`

List bank connections for a client.

**Query Parameters:**
- `client_id` - Client UUID

**Response:**
```json
{
  "success": true,
  "connections": [
    {
      "id": "uuid",
      "bank_name": "DNB",
      "bank_account_number": "12345678901",
      "auto_sync_enabled": true,
      "last_sync_at": "2024-02-10T03:00:00Z",
      "total_transactions_imported": 450
    }
  ]
}
```

### DELETE `/api/dnb/connections/{connection_id}`

Disconnect (revoke) bank connection.

**Response:**
```json
{
  "success": true,
  "message": "Bank connection disconnected successfully"
}
```

---

## 🎮 Usage

### End-User Flow (Glenn's Perspective)

1. **Connect Bank Account**
   - Navigate to Bank Connections in ERP
   - Click "Connect DNB Account"
   - Login with DNB BankID
   - Grant access to account
   - Select which account to connect

2. **Initial Sync**
   - System automatically fetches last 90 days of transactions
   - Transactions are matched with invoices
   - Review Queue shows unmatched items

3. **Automatic Updates**
   - Every night at 03:00 UTC, new transactions are imported
   - Auto-matching runs automatically
   - Email notification if manual review needed

4. **Manual Sync (Optional)**
   - Click "Sync Now" to fetch latest transactions
   - Useful after reconciling a large batch

### Developer Integration

```python
from app.services.dnb.service import DNBService

# Initialize service
dnb_service = DNBService(
    client_id=settings.DNB_CLIENT_ID,
    client_secret=settings.DNB_CLIENT_SECRET,
    api_key=settings.DNB_API_KEY,
    redirect_uri=settings.DNB_REDIRECT_URI,
    use_sandbox=True
)

# Create connection after OAuth
connection = await dnb_service.create_bank_connection(
    db=db,
    client_id=client_uuid,
    token_data=token_response,
    account_id="acc-123",
    account_number="12345678901"
)

# Fetch transactions
result = await dnb_service.fetch_and_store_transactions(
    db=db,
    connection=connection,
    from_date=date(2024, 1, 1),
    to_date=date.today()
)

# Trigger auto-matching
await dnb_service.trigger_auto_matching(db, client_id)
```

---

## ⏰ Scheduled Sync

### Cron Job Setup

Add to crontab:

```bash
# Sync DNB transactions every night at 03:00 UTC
0 3 * * * curl -X POST http://localhost:8000/api/dnb/sync/all
```

Or use systemd timer (recommended):

```ini
# /etc/systemd/system/dnb-sync.timer
[Unit]
Description=DNB Transaction Sync Timer

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/dnb-sync.service
[Unit]
Description=DNB Transaction Sync

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -X POST http://localhost:8000/api/dnb/sync/all
```

Enable and start:
```bash
sudo systemctl enable dnb-sync.timer
sudo systemctl start dnb-sync.timer
```

### Configuration

Per-connection sync frequency can be configured:

```sql
UPDATE bank_connections 
SET sync_frequency_hours = 12  -- Sync twice per day
WHERE id = 'connection-uuid';
```

---

## 🔒 Security

### Token Encryption

OAuth2 tokens are encrypted before storage using Fernet (symmetric encryption):

- **Key Derivation:** PBKDF2 with SHA256, 100,000 iterations
- **Base Key:** Derived from `SECRET_KEY` in settings
- **Salt:** Per-connection (in production, use unique salt)
- **Algorithm:** AES-128-CBC with HMAC authentication

### Best Practices

1. **Never commit credentials** - Use `.env` file (in `.gitignore`)
2. **Rotate SECRET_KEY** regularly in production
3. **Use HTTPS** for OAuth redirect URI
4. **Monitor token usage** - Rate limiting per connection
5. **Audit all API calls** - Logged with timestamps

### OAuth2 Security

- **CSRF Protection:** State parameter validated
- **Token Expiry:** Automatic refresh (tokens expire after 1 hour)
- **Scope Limitation:** Only request necessary scopes
- **Revocation:** Tokens revoked when connection deleted

---

## 🧪 Testing

### Run Unit Tests

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
pytest tests/test_dnb_integration.py -v
```

### Run Integration Tests

```bash
pytest tests/test_dnb_integration.py -v -m integration
```

### Manual Testing (Sandbox)

1. Set `DNB_USE_SANDBOX=true` in `.env`
2. Use DNB test credentials from developer portal
3. Test SSN: `12345678910` (sandbox test user)
4. Follow OAuth flow in browser

### Expected Results

- ✅ OAuth flow completes without errors
- ✅ Accounts fetched successfully
- ✅ Transactions imported (90 days)
- ✅ No duplicates on re-sync
- ✅ Tokens refreshed automatically
- ✅ Auto-matching triggered

---

## 🐛 Troubleshooting

### Common Issues

#### 1. OAuth Authorization Fails

**Symptoms:** "Invalid state parameter" error

**Solution:**
- Check that `DNB_REDIRECT_URI` matches exactly in:
  - `.env` file
  - DNB developer portal settings
  - OAuth client initialization

#### 2. Token Refresh Fails

**Symptoms:** "Token refresh failed" error after 1 hour

**Possible Causes:**
- Refresh token expired (consent revoked)
- Network connectivity issues
- DNB API downtime

**Solution:**
- Check `bank_connections.connection_status`
- Re-authenticate (disconnect + reconnect)
- Check DNB status page

#### 3. No Transactions Imported

**Symptoms:** `sync_result.new = 0`

**Possible Causes:**
- Date range outside transaction history
- Account has no transactions
- Duplicates (all transactions already imported)

**Solution:**
- Check `from_date` and `to_date`
- Verify transactions exist in DNB (login manually)
- Check `bank_transactions` table for duplicates

#### 4. Decryption Error

**Symptoms:** "Failed to decrypt token"

**Possible Causes:**
- `SECRET_KEY` changed
- Database corruption
- Migration issue

**Solution:**
- Don't change `SECRET_KEY` after encryption
- Re-authenticate all connections if key changed
- Check database integrity

### Debug Logging

Enable debug logging:

```python
# app/main.py
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
tail -f backend.log | grep DNB
```

### Support

- DNB Developer Forum: [developer.dnb.no/forum](https://developer.dnb.no/forum)
- DNB Support: support@dnb.no
- API Status: [status.dnb.no](https://status.dnb.no)

---

## 📚 References

- [DNB Developer Portal](https://developer.dnb.no/)
- [PSD2 Standard](https://www.europeanpaymentscouncil.eu/what-we-do/psd2)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)

---

## ✅ Checklist for Production Deployment

- [ ] Register production app at developer.dnb.no
- [ ] Update redirect URI to production domain
- [ ] Set `DNB_USE_SANDBOX=false`
- [ ] Update environment variables (production credentials)
- [ ] Rotate `SECRET_KEY` (and re-encrypt all tokens)
- [ ] Setup HTTPS for OAuth redirect
- [ ] Configure cron job / systemd timer
- [ ] Enable error monitoring (Sentry, etc.)
- [ ] Test with real DNB account (internal testing)
- [ ] Document for Glenn (user guide)
- [ ] Monitor first week of production sync

---

**Status:** ✅ Complete and ready for testing

**Last Updated:** 2026-02-10

**Author:** AI Agent (OpenClaw)
