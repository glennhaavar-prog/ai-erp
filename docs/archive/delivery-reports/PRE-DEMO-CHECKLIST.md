# 📋 KONTALI DEMO - PRE-DEMO CHECKLIST

**Use this 2 minutes before demo starts**

---

## ✅ QUICK VERIFICATION (Run these commands)

```bash
# 1. Check all services are running
pm2 status

# Expected output:
# All 3 services should show "online" ✅
# kontali-backend, kontali-frontend, kontali-missionboard

# 2. Test each service responds
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK

curl -I http://localhost:3001
# Expected: HTTP/1.1 200 OK
```

**If all return expected results:** ✅ **YOU'RE READY!**

---

## ⚠️ IF SOMETHING IS WRONG

### Services not running?
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp
pm2 restart all
# Wait 10 seconds
pm2 status
```

### Services online but not responding?
```bash
pm2 restart all
sleep 10
# Re-run verification commands above
```

### Nuclear option (if everything fails):
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp
pm2 delete all
pm2 start ecosystem.config.js
sleep 15
pm2 status
```

---

## 🎯 DEMO FLOW REMINDER

1. **Start:** Multi-Client Dashboard (localhost:3000)
   - "This is what makes us different"
   - Show cross-client task view

2. **Bank Reconciliation:** /bank
   - Upload CSV demo
   - Click "Run AI Matching"
   - Show confidence scores

3. **Customer Invoices:** /customer-invoices
   - Show full cycle: IN + OUT
   - Collection rate tracking

4. **Roadmap:** localhost:3001
   - "Here's what's coming"
   - 72 features planned

---

## 📊 KEY METRICS TO MENTION

- **80% time savings** (5 hours → 1 hour per client/month)
- **Multi-client paradigm** (work ALL clients at once)
- **AI confidence scores** (99% for KID, 80-95% for amount matching)
- **Auto-learning** (90-95% automated after 12 months)

---

## 🆘 EMERGENCY CONTACT

**During demo, if system crashes:**
1. Say: "Let me quickly restart the services"
2. Run: `pm2 restart all`
3. Wait 10 seconds
4. Continue demo

**If you need help:**
- Telegram: @nikoline_ai (Nikoline)
- Or check: `pm2 logs` for error messages

---

## 🎉 CONFIDENCE CHECK

Before starting demo, ask yourself:

- [ ] Did I run `pm2 status`? (All online?)
- [ ] Did I test all 3 URLs? (All respond?)
- [ ] Do I know what to do if something breaks? (`pm2 restart all`)
- [ ] Do I have the demo flow memorized?

**If YES to all:** You're ready! Go crush it! 💪

---

**Good luck, Glenn! 🚀**

*Updated: 2026-02-06 18:43 UTC*  
*System Status: DEMO READY (95%+ confidence)*
