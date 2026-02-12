# Trust & Safety Requirements for Kontali ERP

**Date:** 2026-02-06  
**Author:** Glenn Håvar Brottveit  
**Status:** Core Product Requirement

---

## The Trust Problem

> "Det er svært viktig at regnskapsfører føler seg trygg på Kontali."

Regnskapsførere ser **INGENTING** av hva som faktisk foregår inne i "Kontali-motoren". De må stole blindt på at systemet:

- ✅ Har mottatt alle EHF-fakturaer
- ✅ Har behandlet alle banktransaksjoner
- ✅ Ikke har "glemt" noe
- ✅ Har bokført korrekt

**Dette er scary!** Uten synlighet og kontroll vil ingen regnskapsfører stole på systemet.

---

## The Skyggemodus Example

**Skyggemodus** er det perfekte eksemplet på hvordan man bygger tillit:

- Regnskapsfører fortsetter å jobbe i PowerOffice som normalt
- Kontali mottar samme bilag i bakgrunnen
- Kontali AI bokfører alt parallelt, uten å påvirke "ekte" regnskap
- Etter 2-4 uker: Rapport sammenligner Kontali vs. PowerOffice

**Hvorfor dette fungerer:**
- **Zero risk** - ingenting endres i det eksisterende systemet
- **Transparent** - regnskapsfører ser med egne øyne at det fungerer
- **Measurable** - harde tall på nøyaktighet og tidsbesparelse
- **Trust-building** - produktet beviser seg selv

**This is the gold standard for trust-building.**

---

## Trust Dashboard Requirements

### 1. Receipt Verification Dashboard

**Goal:** Bevis på at INGEN bilag ligger og "flyter rundt i intet"

**Must display:**

| Source | Received | Processed | Pending | Status |
|--------|----------|-----------|---------|--------|
| EHF (PEPPOL) | 247 | 245 | 2 | ⚠️ 2 pending |
| Bank (PSD2) | 1,834 | 1,834 | 0 | ✅ All processed |
| PDF Upload | 45 | 43 | 2 | ⚠️ 2 stuck in OCR |
| **TOTAL** | **2,126** | **2,122** | **4** | **⚠️ 4 need attention** |

**Requirements:**
- Real-time counters (updates every 30 seconds)
- Click on "Pending" shows list of items
- Drill-down to see WHY something is pending
- "Nothing is floating around" = Green light across the board

---

### 2. Traffic Light Status

**Goal:** Quick visual "is everything OK?" indicator

**Three states:**

🟢 **GREEN** - All systems operational
- All bilag processed
- No errors in last 24h
- Review queue under control

🟡 **YELLOW** - Some items need attention
- X items in review queue
- Y items stuck in processing
- No critical errors

🔴 **RED** - Critical issues detected
- Processing errors
- System failures
- Urgent review items

**Requirements:**
- One global status at top of dashboard
- Per-module status indicators (EHF, Bank, OCR, etc.)
- Click on status shows details
- Real-time updates

---

### 3. Exception Reports (Avviksrapporter)

**Goal:** Transparent reporting on what went wrong

**Must include:**

1. **Failed Processing Log**
   - What failed? (EHF parsing, OCR, AI analysis)
   - When? (timestamp)
   - Why? (error message in plain language)
   - What to do? (suggested action)

2. **Unmatched Transactions**
   - Bank transactions with no matching invoice
   - Invoices with no payment
   - Duplicate detection

3. **Low Confidence Items**
   - All items sent to Review Queue
   - Reason for low confidence
   - Time in queue

4. **Vendor Mismatches**
   - Vendor name changes
   - New vendors detected
   - Suspicious vendor patterns

**Requirements:**
- Daily summary email
- Export to Excel for analysis
- Filter by date range, type, severity
- Search functionality

---

### 4. Event Log (Hendelseslogg)

**Goal:** Full audit trail of everything the system does

**Must log:**

1. **AI Decisions**
   - What: "Suggested booking: 6300 Kontorrekvisita, 1200 NOK"
   - Why: "Matched vendor pattern, 85% confidence"
   - When: "2026-02-06 14:32:15 UTC"
   - Outcome: "Approved by user@example.com"

2. **User Actions**
   - Who approved/rejected what
   - Manual corrections made
   - Settings changed
   - Exports performed

3. **System Events**
   - EHF received
   - OCR completed
   - Bank sync successful
   - Backup completed

**Requirements:**
- Searchable (by date, user, action type, keyword)
- Filterable (show only AI decisions, or only errors)
- Exportable (for compliance/audit)
- Retention: 7 years (Norwegian accounting law)

---

### 5. Message Center

**Goal:** Important system messages don't get lost

**Types of messages:**

1. **Urgent** (Red badge)
   - Processing errors requiring immediate action
   - Security alerts
   - System outages

2. **Important** (Orange badge)
   - New EHF received
   - Review queue items waiting >24h
   - Vendor mismatches

3. **Info** (Blue badge)
   - Daily summary
   - Tips and best practices
   - System updates

**Requirements:**
- Unread count visible in dashboard header
- Email/SMS alerts for urgent messages
- Actionable messages ("Approve invoice directly from notification")
- Mark as read/unread
- Archive old messages

---

## Implementation Priority

### Phase 1: MVP (Week 1-2)
1. ✅ Receipt Verification Dashboard (EHF counter)
2. ✅ Traffic Light Status (basic green/yellow/red)
3. ✅ Event Log (log all AI decisions)

### Phase 2: Trust Building (Week 3-4)
1. Exception Reports (daily summary)
2. Message Center (basic notifications)
3. Bank transaction monitoring

### Phase 3: Full Transparency (Week 5-6)
1. Advanced filtering/search
2. Export functionality
3. Email alerts

---

## Success Metrics

**How do we know trust is being built?**

1. **Adoption rate** - % of regnskapsførere who use Kontali daily
2. **Review time** - Time spent in Review Queue (should decrease over time)
3. **Confidence** - % of AI suggestions approved without changes
4. **NPS** - Net Promoter Score from regnskapsførere
5. **Retention** - % of customers who renew after 6 months

**Target:** 
- 90% of users feel "in control" after 2 weeks
- 95% trust AI suggestions after 3 months
- NPS > 50

---

## Key Principle

> **Regnskapsfører must feel that "alt er håndtert" - even though they can't see inside the engine.**

This is the **invisible foundation** that makes Kontali trustworthy. Without it, no one will adopt the system - no matter how good the AI is.

**Trust Dashboard is not a "nice to have" - it's the reason customers will choose Kontali over competitors.**
