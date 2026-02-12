# MVP Coordination - 6 Feb 2026

**Kickoff:** 08:00 UTC  
**Demo Target:** 17:00 UTC (9 hours)  
**Team:** Nikoline (lead), Claude Code, Sonny, Harald

---

## 🎯 Demo Goals

1. **Trust Dashboard** - Grønne lys + counters
2. **Review Queue** - Real data from database
3. **Auto-booking** - Show 85%+ confidence flow
4. **Avstemming** - Game changer feature

---

## 👥 Team Assignments

### **Nikoline** (Frontend Lead - ME)
**Status:** 🟢 IN PROGRESS  
**Tasks:**
- [x] Analyze existing frontend (08:00-08:03)
- [ ] Fix API connection (port 4000 → 8000)
- [ ] Integrate Review Queue with `/api/chat/`
- [ ] Build Trust Dashboard MVP
- [ ] Testing & polish

**Timeline:**
- 08:00-10:00: Review Queue integration
- 10:00-12:00: Trust Dashboard
- 12:00-14:00: Testing
- 14:00: CHECKPOINT

---

### **Claude Code** (Backend - Avstemming)
**Status:** 🟡 PENDING START  
**Tasks:**
- [ ] Bank transaction model
- [ ] Matching algorithm (amount, date, vendor)
- [ ] Avstemmings-API endpoint
- [ ] Test with mock bank data

**Timeline:**
- 08:00-09:00: Model + migration
- 09:00-11:00: Matching algorithm
- 11:00-13:00: API endpoint
- 13:00-14:00: Testing
- 14:00: CHECKPOINT

---

### **Sonny** (Frontend - Avstemming UI)
**Status:** 🟡 WAITING FOR BACKEND  
**Tasks:**
- [ ] Reconciliation Dashboard component
- [ ] Show matched/unmatched transactions
- [ ] Manual match interface
- [ ] Polish UI

**Timeline:**
- 08:00-09:00: Design mockup
- 09:00-11:00: Build components (can use mock data)
- 11:00-13:00: Integrate with backend API
- 13:00-14:00: Testing
- 14:00: CHECKPOINT

---

### **Harald** (Demo Data + Polish)
**Status:** 🟡 PENDING START  
**Tasks:**
- [ ] Create realistic demo data (10-15 invoices)
- [ ] Generate mock bank transactions
- [ ] Test end-to-end demo flow
- [ ] Polish UI inconsistencies
- [ ] Prepare demo script

**Timeline:**
- 08:00-10:00: Generate demo data
- 10:00-12:00: Test demo flow
- 12:00-14:00: Polish + fixes
- 14:00: CHECKPOINT
- 14:00-17:00: Final polish + demo prep

---

## ⏰ Checkpoints

### 14:00 UTC
**Review:**
- Review Queue working with real data?
- Avstemmings backend ready?
- Demo data realistic?

**Decisions:**
- What's blocking?
- Re-prioritize if needed
- Cut scope if necessary

### 17:00 UTC
**Final Demo Prep:**
- Full walkthrough
- Fix critical bugs
- Practice pitch

---

## 🚨 Blockers / Risks

**Current:**
- Frontend API mismatch (FIXING NOW)
- Avstemming is new feature (might not finish)

**Mitigation:**
- Focus on Review Queue first (core)
- Avstemming can be "mock" if backend not ready
- Trust Dashboard can show static data for demo

---

## 📝 Progress Log

### 08:00-08:13 - Nikoline ✅ COMPLETE
- ✅ Analyzed frontend structure
- ✅ Identified API mismatch
- ✅ Fixed API base URL (port 4000 → 8000)
- ✅ Created new `/api/review-queue/` endpoint on backend
- ✅ Backend restarted successfully
- ✅ API tested - returns real database data!
- ✅ Updated ReviewQueue.tsx to use real API
- ✅ Added proper error handling
- ✅ Added polling for real-time updates
- ✅ Frontend restarted
- 🎯 **READY FOR TESTING**

**Next:** Trust Dashboard (starting now)

---

*This file will be updated throughout the day*
