# FASE 2.5: Quick Start Guide

## 🚀 Kom i gang med Demo-miljøet

### Forutsetninger
- Backend kjører på http://localhost:8000
- Frontend kjører på http://localhost:3002
- Demo-miljø er satt opp (check med `curl http://localhost:8000/demo/status`)

---

## 📋 Manual Testing Guide

### 1. Verifiser at tjenestene kjører
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp
./status.sh
```

**Forventet output:**
- ✓ Backend (port 8000): Running
- ✓ Frontend (port 3002): Running

### 2. Test Backend API
```bash
# Check demo status
curl http://localhost:8000/demo/status | jq .

# Forventet: demo_environment_exists = true
```

### 3. Test Frontend Dashboard

**Åpne Dashboard:**
```
http://localhost:3002/dashboard
```

**Forventet:**
- [ ] DemoBanner vises øverst (gul banner med "🎭 Demo Environment")
- [ ] "Kjør Test" knapp vises i header (lilla/purple, top-right)
- [ ] Dashboard viser current data (invoices, transactions, etc.)

### 4. Test "Kjør Test" Button

**Steg-for-steg:**
1. Klikk på "Kjør Test" knappen
2. Modal åpnes med norsk tekst:
   - "Generer testdata"
   - Liste over hva som genereres
   - "⚠️ Dette vil legge til nye testdata i systemet"
3. Klikk "Fortsett"
4. Progress bar starter (0% → 100%)
5. Stats vises når ferdig:
   - Leverandører: X
   - Fakturaer: Y
   - Kundefakturaer: Z
   - Transaksjoner: W
6. Modal kan lukkes
7. Dashboard oppdateres med nye data

### 5. Verifiser Generert Data

**Check Review Queue:**
```
http://localhost:3002/review-queue
```
**Forventet:**
- Fakturaer med `needs_review` status vises
- Variert confidence score (35-75%)

**Check Dashboard Stats:**
```bash
curl http://localhost:8000/demo/status | jq '.stats'
```
**Forventet:**
- vendor_invoices økt
- bank_transactions økt
- general_ledger_entries økt

---

## 🧪 Automated Testing

### Full System Test
```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp
./test_demo_environment.sh
```

**Dette tester:**
1. Demo status check
2. Test data generation (small batch)
3. Task status polling
4. Data verification
5. Review queue check
6. Dashboard verification

**Forventet output:**
```
==================================
  FASE 2.5: Demo Environment Test
==================================

Test 1: Checking demo environment status...
✓ Demo environment exists
✓ Found X demo clients

Test 2: Generating test data (small batch)...
✓ Test data generation started (Task ID: ...)

Test 3: Polling task status...
  Progress: 0% - Starting...
  Progress: 33% - Creating vendors...
  Progress: 66% - Creating invoices...
  Progress: 100% - Completed
✓ Test data generation completed

Test 4: Verifying generated data...
✓ Vendor Invoices: X
✓ Customer Invoices: Y
✓ Bank Transactions: Z

Test 5: Checking review queue...
✓ Review queue has N items

Test 6: Checking dashboard verification...
✓ Dashboard overall status: green/yellow/red

==================================
  All tests passed! ✓
==================================
```

---

## 🐛 Feilsøking

### Problem: "Kjør Test" knapp vises ikke
**Løsning:**
1. Check at backend kjører: `curl http://localhost:8000/demo/status`
2. Check browser console for errors (F12)
3. Verifiser at `demo_environment_exists = true`

### Problem: Modal åpnes ikke
**Løsning:**
1. Check browser console for React errors
2. Verifiser at Dialog component eksisterer: `frontend/src/components/ui/dialog.tsx`

### Problem: Progress bar oppdateres ikke
**Løsning:**
1. Check network tab (F12) - skal se polling requests hver 2 sekund
2. Verifiser task_id returneres fra `/demo/run-test`
3. Check backend logs: `tail -f backend/backend.log`

### Problem: Test data generation feiler
**Løsning:**
1. Check backend logs for Python errors
2. Verifiser database connection
3. Check at demo clients eksisterer:
   ```bash
   curl http://localhost:8000/demo/status | jq '.stats.clients'
   ```

---

## 📊 Data Forklaring

### Generert Data
Når du klikker "Kjør Test" genereres:

**Per klient (default: 15 klienter):**
- 5-8 norske leverandører (random selection fra 20+ navn)
- 20 leverandørfakturaer:
  - 70% høy tillit (85-98%) → auto_approved
  - 30% lav tillit (35-75%) → needs_review
  - 2 duplikater (confidence 25%)
- 10 kundefakturaer:
  - 50% betalt
  - 50% ubetalt
- 30 banktransaksjoner:
  - 70% matched til fakturaer
  - 30% unmatched

**Total (15 klienter):**
- ~75-120 leverandører
- ~300+ leverandørfakturaer
- ~150 kundefakturaer
- ~450 banktransaksjoner

### Confidence Scoring
- **95-98%:** Perfekte fakturaer, auto-booked instantly
- **85-95%:** Gode fakturaer, auto-approved
- **70-85%:** Medium confidence, kan auto-approve med review
- **35-70%:** Lav confidence, needs_review (manual check)
- **<35%:** Duplikater, edge cases, requires manual intervention

---

## 🎯 Skattefunn Validation Points

Dette demo-miljøet validerer:

### AI Automation (70%+ target)
- ✅ 70% av fakturaer auto-approved (high confidence)
- ✅ 30% går til review queue (low confidence)
- ✅ Duplikat-deteksjon fungerer (flagges with 25% confidence)

### Bank Matching (70%+ target)
- ✅ 70% av transaksjoner matches automatisk
- ✅ 30% forblir unmatched (krever manuell handling)

### Data Quality
- ✅ Realistiske norske leverandørnavn
- ✅ Realistiske norske beskrivelser
- ✅ Realistiske beløp og datoer
- ✅ Varierte betalingsbetingelser

### Edge Cases
- ✅ Duplikater detekteres
- ✅ Fakturaer uten beskrivelse flagges
- ✅ Ukjente kategorier sendes til review
- ✅ Unmatched transaksjoner håndteres

---

## 🔄 Reset Demo Data

Hvis du vil starte på nytt:

```bash
curl -X POST http://localhost:8000/demo/reset
```

**Obs:** Dette sletter ALLE demo-data:
- Leverandørfakturaer
- Kundefakturaer
- Banktransaksjoner
- General ledger entries

**Preserveres:**
- Klienter
- Leverandører
- Kontoplan (Chart of Accounts)

---

## 📚 Videre Lesning

- **Full dokumentasjon:** `FASE_2_5_COMPLETE.md`
- **API dokumentasjon:** `backend/app/api/routes/demo.py`
- **Test data generator:** `backend/app/services/demo/test_data_generator.py`
- **Frontend button:** `frontend/src/components/DemoTestButton.tsx`

---

## ✅ Success Checklist

- [ ] Backend og frontend kjører
- [ ] Demo status returnerer `demo_environment_exists = true`
- [ ] DemoBanner vises på dashboard
- [ ] "Kjør Test" knapp vises og er klikkbar
- [ ] Modal åpnes med norsk tekst og confirmation
- [ ] Progress bar oppdateres under generering
- [ ] Stats vises når generering er ferdig
- [ ] Dashboard oppdateres med nye data
- [ ] Review queue viser fakturaer med lav confidence
- [ ] Automated test script passerer alle tester

---

**Lykke til med testing!** 🚀

*Hvis du finner bugs eller problemer, dokumenter dem og rapporter til Glenn.*
