# DNB Integration - Deployment Checklist

Complete checklist for deploying DNB Open Banking integration to production.

---

## ✅ Pre-Deployment Tasks

### 1. DNB Developer Account Setup

- [ ] Register account at [developer.dnb.no](https://developer.dnb.no)
- [ ] Verify email and complete profile
- [ ] Accept DNB Developer Terms of Service
- [ ] Review API documentation

### 2. Create Production Application

- [ ] Create new application in DNB Developer Portal
- [ ] Application Name: "Kontali ERP - Production"
- [ ] Application Type: "Web Application"
- [ ] Select APIs:
  - [ ] Account Information Services (AIS)
  - [ ] PSD2 Accounts API
  - [ ] PSD2 Transactions API
- [ ] Note credentials:
  - Client ID: `____________________`
  - Client Secret: `____________________`
  - API Key: `____________________`

### 3. Configure OAuth2 Settings

- [ ] Add Redirect URI (production domain):
  - `https://erp.kontali.no/api/dnb/oauth/callback`
  - Or: `https://app.kontali.no/api/dnb/oauth/callback`
- [ ] Set allowed scopes:
  - `psd2:accounts:read`
  - `psd2:transactions:read`
- [ ] Enable production mode (not sandbox)
- [ ] Save and verify settings

### 4. Test in Sandbox First

- [ ] Create separate sandbox application
- [ ] Test full OAuth flow with sandbox credentials
- [ ] Verify transaction import works
- [ ] Test auto-matching
- [ ] Run test suite: `pytest tests/test_dnb_integration.py`
- [ ] Verify encryption/decryption
- [ ] Test token refresh
- [ ] Test error handling

---

## 🔧 Server Configuration

### 5. Environment Variables

Update production `.env` file:

```bash
# DNB Open Banking - PRODUCTION
DNB_CLIENT_ID=your-production-client-id
DNB_CLIENT_SECRET=your-production-client-secret  # KEEP SECRET!
DNB_API_KEY=your-production-api-key
DNB_REDIRECT_URI=https://erp.kontali.no/api/dnb/oauth/callback
DNB_USE_SANDBOX=false  # CRITICAL: Must be false for production!

# Security (generate new key for production!)
SECRET_KEY=generate-new-random-key-min-32-chars-use-openssl-rand
```

**Generate new SECRET_KEY:**
```bash
openssl rand -base64 32
```

Checklist:
- [ ] `DNB_CLIENT_ID` - Production client ID from DNB
- [ ] `DNB_CLIENT_SECRET` - Production secret (encrypted/vaulted)
- [ ] `DNB_API_KEY` - Production API key
- [ ] `DNB_REDIRECT_URI` - HTTPS production URL
- [ ] `DNB_USE_SANDBOX` - Set to `false`
- [ ] `SECRET_KEY` - New random key (rotate from dev)

### 6. Database Migration

- [ ] Backup database before migration
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify `bank_connections` table created:
  ```sql
  SELECT * FROM bank_connections LIMIT 1;
  ```
- [ ] Check indexes created
- [ ] Verify foreign keys to `clients` table

### 7. HTTPS/SSL Configuration

- [ ] Verify SSL certificate valid
- [ ] Test HTTPS access: `curl -I https://erp.kontali.no`
- [ ] Ensure redirect URI uses HTTPS (not HTTP)
- [ ] Test OAuth callback over HTTPS
- [ ] Verify DNB accepts your redirect URI

### 8. Firewall & Network

- [ ] Allow outbound HTTPS to DNB API:
  - `api.dnb.no` (port 443)
- [ ] No special inbound rules needed (OAuth uses redirect)
- [ ] Verify DNS resolution: `nslookup api.dnb.no`

---

## 🚀 Deployment Steps

### 9. Deploy Code

- [ ] Git commit all changes:
  ```bash
  git add .
  git commit -m "feat: Add DNB Open Banking integration"
  git push origin main
  ```
- [ ] Deploy to production server
- [ ] Verify files deployed:
  - `app/services/dnb/` (all files)
  - `app/models/bank_connection.py`
  - `app/api/routes/dnb.py`
  - `alembic/versions/XXX_add_bank_connections.py`

### 10. Install Dependencies

- [ ] Install Python packages:
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Verify imports work:
  ```bash
  python3 -c "from app.services.dnb.service import DNBService; print('OK')"
  ```

### 11. Restart Services

- [ ] Stop application: `systemctl stop kontali-backend`
- [ ] Run database migration: `alembic upgrade head`
- [ ] Start application: `systemctl start kontali-backend`
- [ ] Check logs: `journalctl -u kontali-backend -f`
- [ ] Verify no errors on startup

### 12. Health Check

- [ ] Test backend is running: `curl http://localhost:8000/health`
- [ ] Verify DNB endpoints registered:
  ```bash
  curl http://localhost:8000/docs | grep dnb
  ```
- [ ] Check logs for DNB service initialization

---

## 🧪 Production Testing

### 13. End-to-End Test (Internal Account)

- [ ] Login to production Kontali ERP
- [ ] Navigate to Bank Connections
- [ ] Click "Connect DNB Account"
- [ ] Complete OAuth flow with test/internal DNB account
- [ ] Verify account connected successfully
- [ ] Check `bank_connections` table for new record
- [ ] Verify tokens are encrypted (should not be readable)

### 14. Transaction Import Test

- [ ] Manually trigger sync: Click "Sync Now"
- [ ] Verify transactions imported:
  ```sql
  SELECT COUNT(*) FROM bank_transactions WHERE upload_batch_id IS NULL;
  ```
- [ ] Check for duplicates (should be 0):
  ```sql
  SELECT transaction_date, amount, description, COUNT(*)
  FROM bank_transactions
  GROUP BY transaction_date, amount, description
  HAVING COUNT(*) > 1;
  ```
- [ ] Verify auto-matching ran (check review_queue)

### 15. Error Handling Test

- [ ] Test invalid OAuth code (should show error message)
- [ ] Test expired token (disconnect and wait 1 hour, or force expiry in DB)
- [ ] Verify token auto-refresh works
- [ ] Test with no transactions (should complete without error)

---

## ⏰ Scheduled Jobs

### 16. Setup Cron Job

Create systemd timer:

```bash
# Create timer file
sudo nano /etc/systemd/system/dnb-sync.timer
```

Content:
```ini
[Unit]
Description=DNB Transaction Sync Timer

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Create service file
sudo nano /etc/systemd/system/dnb-sync.service
```

Content:
```ini
[Unit]
Description=DNB Transaction Sync

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -X POST http://localhost:8000/api/dnb/sync/all
StandardOutput=journal
StandardError=journal
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dnb-sync.timer
sudo systemctl start dnb-sync.timer
sudo systemctl status dnb-sync.timer
```

Checklist:
- [ ] Timer file created
- [ ] Service file created
- [ ] Timer enabled
- [ ] Timer started
- [ ] Verify next run time: `systemctl list-timers | grep dnb`

### 17. Test Cron Job

- [ ] Manually trigger: `systemctl start dnb-sync.service`
- [ ] Check logs: `journalctl -u dnb-sync.service`
- [ ] Verify transactions imported
- [ ] Wait for scheduled run (03:00 UTC)
- [ ] Check logs next morning

---

## 📊 Monitoring & Logging

### 18. Setup Monitoring

- [ ] Add health check for DNB connections:
  ```sql
  SELECT COUNT(*) FROM bank_connections WHERE connection_status != 'active';
  ```
- [ ] Alert if any connections in error state
- [ ] Monitor sync job execution (should run daily)
- [ ] Track transaction import volume (normal range)

### 19. Log Aggregation

- [ ] Ensure logs are captured:
  - `journalctl -u kontali-backend | grep DNB`
- [ ] Setup log rotation if needed
- [ ] Archive old logs (older than 90 days)

### 20. Metrics to Track

- [ ] Number of active bank connections
- [ ] Daily transaction import count
- [ ] Auto-match success rate (%)
- [ ] Token refresh success rate
- [ ] API error rate (should be <1%)

---

## 🔒 Security Audit

### 21. Token Security

- [ ] Verify tokens are encrypted in database:
  ```sql
  SELECT access_token FROM bank_connections LIMIT 1;
  -- Should see encrypted blob, not plaintext
  ```
- [ ] Test decryption works
- [ ] Verify SECRET_KEY is different from development
- [ ] Ensure SECRET_KEY is not in Git history
- [ ] Store SECRET_KEY in secure vault (not just .env)

### 22. Access Control

- [ ] Only authorized users can connect bank accounts
- [ ] Users can only see their own client's connections
- [ ] Test that Client A cannot access Client B's connections
- [ ] Verify OAuth state validation (CSRF protection)

### 23. Audit Trail

- [ ] All API calls logged with timestamps
- [ ] Connection creation logged
- [ ] Disconnection logged
- [ ] Token refresh logged
- [ ] Sync execution logged

---

## 📚 Documentation

### 24. Update Documentation

- [ ] Add DNB section to main README
- [ ] Link to DNB_INTEGRATION_README.md
- [ ] Update user guide for end users
- [ ] Document troubleshooting steps
- [ ] Add to runbook (ops team)

### 25. User Training

- [ ] Create training video (screen recording)
- [ ] Send email to Glenn explaining new feature
- [ ] Schedule training session if needed
- [ ] Prepare FAQ document

---

## 👥 Rollout Plan

### 26. Phased Rollout (Recommended)

**Phase 1: Internal Testing (1 week)**
- [ ] Connect 1-2 internal accounts (Kontali's own)
- [ ] Monitor daily
- [ ] Fix any issues

**Phase 2: Pilot Users (2 weeks)**
- [ ] Select 5-10 friendly clients
- [ ] Invite to try new feature
- [ ] Collect feedback
- [ ] Iterate based on feedback

**Phase 3: General Availability**
- [ ] Announce to all users
- [ ] Send instruction email
- [ ] Offer support for onboarding
- [ ] Monitor closely for first week

### 27. Communication

- [ ] Email to Glenn (feature ready)
- [ ] Release notes published
- [ ] In-app notification (optional)
- [ ] Update changelog

---

## ✅ Post-Deployment

### 28. Day 1 Checks

- [ ] Verify cron job ran (next morning)
- [ ] Check for any errors in logs
- [ ] Review newly imported transactions
- [ ] Verify auto-matching worked
- [ ] Check review queue (should have new items)

### 29. Week 1 Checks

- [ ] Daily sync is running
- [ ] No connection errors
- [ ] Users successfully connecting accounts
- [ ] Support tickets tracked
- [ ] Any bugs identified and prioritized

### 30. Month 1 Review

- [ ] Usage statistics:
  - Number of connections
  - Total transactions imported
  - Auto-match success rate
- [ ] User feedback survey
- [ ] Performance review (any slowdowns?)
- [ ] Security review (any incidents?)

---

## 🐛 Rollback Plan

If critical issues occur:

1. **Disable cron job:**
   ```bash
   sudo systemctl stop dnb-sync.timer
   ```

2. **Disable OAuth initiation** (emergency):
   - Comment out router in `app/main.py`
   - Restart backend

3. **Preserve data:**
   - Do NOT drop `bank_connections` table
   - Do NOT delete imported transactions
   - Keep for troubleshooting

4. **Notify users:**
   - Email explaining temporary issue
   - Expected resolution time
   - Alternative workflow (manual CSV upload)

---

## 📞 Support Contacts

- **DNB Support:** support@dnb.no
- **DNB Developer Portal:** [developer.dnb.no/support](https://developer.dnb.no/support)
- **API Status:** [status.dnb.no](https://status.dnb.no)
- **Internal Escalation:** [your team contact]

---

## ✅ Final Sign-Off

Deployment completed by: ________________  
Date: ________________  
Production URL: ________________  
First sync completed: Yes / No  
Issues encountered: ________________  

---

**Deployment Status:** ⏳ Pending  
**Target Date:** [To be determined when Glenn is ready]  
**Last Updated:** 2026-02-10
