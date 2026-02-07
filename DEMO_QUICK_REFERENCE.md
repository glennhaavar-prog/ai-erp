# 🎭 Kontali Demo Environment - Quick Reference Card

## ⚡ Quick Commands

### Initial Setup (First Time Only)
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate

# 1. Run migration
python -m alembic upgrade head

# 2. Create demo environment
python scripts/create_demo_environment.py
# Copy the DEMO_TENANT_ID from output

# 3. Update .env
echo "DEMO_MODE_ENABLED=true" >> .env
echo "DEMO_TENANT_ID=<your-tenant-id>" >> .env
echo "ENVIRONMENT=demo" >> .env

# 4. Restart backend
pm2 restart ai-erp-backend
```

### Daily Usage

**Check Status:**
```bash
curl http://localhost:8000/api/demo/status | jq
```

**Reset Demo:**
```bash
curl -X POST http://localhost:8000/api/demo/reset
```

**Generate Test Data:**
```bash
curl -X POST http://localhost:8000/api/demo/run-test \
  -H "Content-Type: application/json" \
  -d '{"invoices_per_client": 20}'
```

**Run Test Script:**
```bash
./test_demo_system.sh
```

---

## 🌐 URLs

| Service | URL |
|---------|-----|
| Demo Control Panel | http://localhost:3000/demo-control |
| API Status | http://localhost:8000/api/demo/status |
| API Documentation | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/demo/status` | Get demo stats |
| POST | `/api/demo/reset` | Reset all data |
| POST | `/api/demo/run-test` | Generate test data |
| GET | `/api/demo/task/{id}` | Check task status |

---

## 🎮 UI Quick Actions

**Demo Control Panel:** `http://localhost:3000/demo-control`

1. **View Status** - Top cards show tenant, clients, last reset
2. **Generate Data** - Fill form, click "Run Test"
3. **Watch Progress** - Real-time progress bar updates
4. **Reset** - Click "Reset Demo Environment", confirm

---

## 🧪 Common Test Scenarios

### High Confidence Test (90% Auto-Book)
```json
{
  "invoices_per_client": 20,
  "high_confidence_ratio": 0.9
}
```

### Review Queue Test (70% Manual Review)
```json
{
  "invoices_per_client": 20,
  "high_confidence_ratio": 0.3
}
```

### Edge Cases Test
```json
{
  "invoices_per_client": 20,
  "include_duplicates": true,
  "include_edge_cases": true
}
```

### Load Test
```json
{
  "invoices_per_client": 100,
  "transactions_per_client": 150
}
```

---

## 📋 Demo Environment Contents

- **Tenant:** Demo Regnskapsbyrå AS (999000001)
- **Clients:** 15 (diverse industries)
- **Accounts:** 195 (13 per client)
- **Flag:** `is_demo=true` on all data

---

## 🔒 Security Notes

- Demo endpoints blocked in production unless `DEMO_MODE_ENABLED=true`
- All demo data marked with `is_demo=true`
- Demo banner shows on all pages
- Reset requires confirmation

---

## 🚨 Troubleshooting

**Demo environment not found?**
```bash
python scripts/create_demo_environment.py
```

**Endpoints return 403?**
- Check `.env` has `DEMO_MODE_ENABLED=true`
- Restart backend: `pm2 restart ai-erp-backend`

**UI not updating?**
- Check backend is running: `pm2 status`
- Check API: `curl http://localhost:8000/health`
- Clear browser cache

**Task stuck?**
- Check backend logs: `pm2 logs ai-erp-backend`
- Restart backend: `pm2 restart ai-erp-backend`
- Re-run test generation

---

## 📚 Documentation

- **Full Implementation:** `KONTALI_DEMO_ENV_IMPLEMENTATION.md`
- **Summary:** `DEMO_IMPLEMENTATION_COMPLETE.md`
- **This Card:** `DEMO_QUICK_REFERENCE.md`
- **API Docs:** `http://localhost:8000/docs`

---

## ⏱️ Estimated Times

| Action | Time |
|--------|------|
| Initial setup | 5 min |
| Generate 20 invoices/client | 10s |
| Reset environment | 1s |
| Status check | <50ms |

---

## 🎯 Success Indicators

✅ Demo banner shows on pages  
✅ `/demo-control` loads correctly  
✅ Status shows 15 clients  
✅ Can generate test data  
✅ Can reset successfully  
✅ Progress tracking works  

---

**Quick Start:** Run `./test_demo_system.sh` to verify everything works!

**Time to first demo:** < 5 minutes 🚀
