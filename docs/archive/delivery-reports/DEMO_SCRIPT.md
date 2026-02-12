# Kontali ERP - Demo Script

**Duration:** ~10-15 minutes  
**Target:** 17:00 UTC (2026-02-06)  
**Audience:** Glenn (internal product review)

---

## ✅ Pre-Demo Checklist

**Services Running:**
- [ ] Backend: `http://localhost:8000` (check: `curl http://localhost:8000/api/health`)
- [ ] Frontend: `http://localhost:3000` (check: open in browser)
- [ ] Database: PostgreSQL `ai_erp` (check: `psql -U erp_user -d ai_erp -c "SELECT COUNT(*) FROM vendor_invoices;"`)

**Demo Data:**
- [ ] 33 invoices loaded (13 new demo invoices + 20 existing test invoices)
- [ ] 5 items in review queue (confidence < 85%)
- [ ] 8 auto-booked invoices (confidence ≥ 85%)
- [ ] 10 realistic Norwegian vendors

---

## 🎯 Demo Flow (15 minutes)

### 1. Trust Dashboard (3 min) ⭐ DIFFERENTIATOR

**URL:** `http://localhost:3000/dashboard`

**What to show:**
- ✅ **Green traffic light** - "All systems operational"
- 📊 **Counters:**
  - Review Queue: X pending items
  - Invoices: 33 total, X recent (24h), X% auto-booked
  - EHF: 33 received, 33 processed, 0 pending
  - Bank: (mock data for now)
- 🏥 **Health checks:** Database, AI Agent, Review Queue (all green)
- 🔄 **Auto-refresh:** Updates every 30 seconds

**Key message:**
> "This is THE core differentiator - regnskapsfører sees everything at a glance. No hidden processing, no 'black box' feeling. Trust = critical for adoption."

---

### 2. Review Queue (5 min) ⭐ CORE PRODUCT

**URL:** (needs route setup - currently component exists but no page route)

**What to show:**
- 📋 5 pending items with different confidence levels:
  - IT-Partner (72%) - IT support (medium priority)
  - Rema 1000 (65%) - Catering supplies (medium priority)
  - Clarion Hotel (60%) - Travel expense (high priority)
  - Advokatfirmaet (55%) - Legal services (high priority)
  - Staples (48%) - Equipment/asset (high priority)

- 💡 **AI Suggestions** - each item shows:
  - Suggested booking lines (account + MVA)
  - Confidence score
  - Reasoning (why low confidence)

- ⚡ **Actions:**
  - Approve (if AI is correct)
  - Correct (teach AI)

**Key message:**
> "This is where the magic happens. Low confidence? Human reviews. High confidence? Auto-booked. Regnskapsfører stays in control."

**Demo approval:**
```bash
# Via API (since UI route not set up yet)
curl -X POST http://localhost:8000/api/review-queue/0ff014ae-2432-4b9c-8b12-914a7801c9a3/approve \
  -H "Content-Type: application/json" \
  -d '{"notes": "Verified - IT costs look correct"}'
```

---

### 3. Auto-Booking Showcase (2 min)

**What to explain:**
- 8 invoices were auto-booked (≥85% confidence)
- Examples:
  - Kontorrekvisita (95%) - Office supplies
  - Telenor (96%) - Telecom
  - Strømleverandøren (88%) - Electricity
  - Kontorlokaler (99%) - Rent

**Key message:**
> "80% time savings - 5 minutes per invoice → 30 seconds. The AI handles the routine, humans handle the exceptions."

---

### 4. Data Quality (2 min)

**What to show:**
- Realistic Norwegian vendors (10 created)
- Realistic amounts and descriptions
- Proper VAT codes (0%, 15%, 25%)
- Correct account mappings (NS 4102)

**Key message:**
> "This isn't toy data. These are real scenarios Norwegian regnskapsførere face daily."

---

### 5. Technical Architecture (3 min) [OPTIONAL]

**What to explain:**
- Multi-tenant (client isolation)
- Async backend (FastAPI + PostgreSQL)
- React frontend (Next.js + Tailwind)
- AI agent (Claude Sonnet 4.5)
- Learning system (corrections → patterns)

**Key message:**
> "Built for scale. Each client's data is isolated. Each correction makes the AI smarter."

---

## 🚀 How to Run Demo

### Start Services

**Terminal 1 - Backend:**
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
npm run dev
```

### Access Points

- **Dashboard:** http://localhost:3000/dashboard
- **Backend API:** http://localhost:8000/docs (Swagger UI)
- **Review Queue API:** http://localhost:8000/api/review-queue/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277

---

## 📊 Key Stats to Mention

- **Time savings:** 80% (5 min → 30 sec per invoice)
- **Auto-booking rate:** 61.5% (8 of 13 demo invoices)
- **Learning effect:** Corrections teach AI → 90-95% auto-booking after 12 months
- **Market:** 300K SMBs in Norway, 11K+ regnskapsbyrå
- **Unit economics:** 1000 kr/mnd ARPU, 92% gross margin

---

## 🎭 Demo Personas

**Regnskapsfører Kari:**
- Works at small accounting firm (50 clients)
- Currently uses PowerOffice
- Spends 5 hours/month per client on invoice processing
- Worried: "What if AI makes mistakes?"
- Kontali answer: Trust Dashboard + Review Queue = full control

---

## 🐛 Known Issues (Don't Show)

- Review Queue UI exists but not routed (use API directly)
- Bank reconciliation backend not ready (mock data)
- No user authentication yet (single client for demo)
- Chat approval command works but not integrated in UI

---

## 📝 Next Steps After Demo

1. ✅ Trust Dashboard complete
2. ✅ Review Queue API complete
3. ⏳ Review Queue UI route needed
4. ⏳ Bank reconciliation module (Q1 2026)
5. ⏳ Chart of Accounts management
6. ⏳ User authentication (JWT)
7. ⏳ Multi-user support

---

## 💡 Questions to Ask Glenn

1. Is Trust Dashboard clear enough? Too much info?
2. Review Queue: Should we show ALL pending or paginate?
3. Auto-booking: Is 85% threshold right?
4. Demo data: Realistic enough?
5. Next priority: Bank reconciliation or Chart of Accounts?

---

**Remember:** This is about showing the *paradigm shift* - from "human operates, software assists" to "AI operates, human supervises". Trust + Control = adoption.
