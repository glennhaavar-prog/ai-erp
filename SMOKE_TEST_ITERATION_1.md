# Smoke Test – Iterasjon 1
**Dato:** 12. februar 2026, 22:26 UTC  
**Tester:** Nikoline (AI-agent)  
**Mål:** Verifisere kjerneflyten (opprett klient → åpningsbalanse → bokføring → rapporter)

---

## Fase 0: Skills ✅ FULLFØRT

- ✅ kontali-debug v2: Verifisert installert
- ✅ Skills-vurdering: Besvart (anbefaling: GJENNOMFØR med endringer)
- ✅ Reminder satt: 13. feb kl 06:00 (Telegram)

---

## Fase 1: Teknisk Opprydding ✅ FULLFØRT

### 1.1 Fjern MUI → shadcn ✅
- Konvertert: `upload/page.tsx`, `nlq/page.tsx`  
- Avinstallert: @mui/material, @mui/icons-material, @emotion/*  
- Verifisert: 0 MUI-imports gjenstår  
- **Commit:** `chore: konsolidert UI til shadcn, ryddet rot-markdown`

### 1.2 react-query → TanStack Query v5 ✅ SKIPPED
- **Oppdagelse:** Kontali bruker IKKE react-query  
- Frontend bruker native `fetch()` for API-kall  
- **TODO:** Oppdater kontali-debug SKILL.md (fjern react-query-referanser)

### 1.3 Rydd rot-markdown ✅
- Flyttet: 88 markdown-filer til `docs/archive/`  
- Flyttet: Test-scripts til `scripts/testing/`  
- Resultat: Rot inneholder kun `README.md` + config

### 1.4 Verifiser ✅
- ✅ Backend: http://localhost:8000 (healthy)  
- ✅ Frontend: http://localhost:3002 (Next.js 14.1.0)  
- ✅ TypeScript: 0 feil  
- ✅ MUI: 0 imports  
- ✅ react-query: 0 imports

---

## Fase 2: Smoke Test (Iterasjon 1)

### Test 1: Opprett klient ✅ BESTÅTT

**Forventet:** Klient opprettes via API eller finnes allerede  
**Resultat:** ✅ Klient funnet i database

**Detaljer:**
- Klient ID: `09409ccf-d23e-45e5-93b9-68add0b96277`  
- Navn: GHB AS Test  
- Org: 123456789  
- Status: active  
- Tenant: `c23eacc0-fbe8-4390-866b-7fc031002cea`

**API-endepunkt:**  
`GET /api/clients/` → returnerer klienter (paginated, limit=50, total=103)

**Notater:**
- Veldig mange demo-klienter (103 totalt)
- API krever `tenant_id`, `start_date`, `fiscal_year_start` for POST

---

### Test 2: Sett åpningsbalanse ⚠️ DELVIS BESTÅTT

**Forventet:**  
- Åpningsbalanse: debet = kredit = 500 000 NOK  
- Synlig i Saldobalanse og Balanse

**Resultat:** ⚠️ Importert til hovedbok, men IKKE synlig i saldobalanse

**Workflow:**
1. ✅ POST `/api/opening-balance/import` → status: "draft"
2. ✅ POST `/api/opening-balance/validate` → status: "valid"
3. ✅ POST `/api/opening-balance/import-to-ledger/{id}` → voucher: 2026-0001

**Åpningsbalanse:**
```
1920 Bankinnskudd:       500000 D
2000 Aksjekapital:        30000 K
2050 Annen egenkapital:  470000 K
-------------------------
Total debet:  500000
Total kredit: 500000 ✅ Balanserer
```

**Verifisering i database:**
```sql
-- general_ledger
id: 97603bcf-4692-4a0d-8b1b-aaa01c09b74b
voucher_number: 2026-0001
accounting_date: 2026-01-01
source_type: opening_balance ✅
status: posted ✅

-- general_ledger_lines
1920 D 500000
2000 K  30000
2050 K 470000
✅ Posteringer finnes!
```

**Verifisering i saldobalanse:**
```
GET /api/reports/saldobalanse/?client_id=...&period=2026-01

{
  "balances": [
    {
      "account_code": "1920",
      "opening_balance": 0.0,  ❌ SKAL VÆRE 500000!
      "current_balance": 0.0,
      "balance_change": 0.0
    }
  ]
}
```

---

### 🐛 BUG #1: Åpningsbalanse ikke synlig i saldobalanse (KRITISK)

**Symptom:**  
Saldobalanse viser `opening_balance = 0` for alle kontoer selv om åpningsbalanse er importert til hovedbok.

**Verifisering:**
- ✅ Posteringer finnes i `general_ledger` med `source_type="opening_balance"`
- ✅ Status: "posted"
- ❌ Saldobalanse-API returnerer `opening_balance = 0`

**Root cause (hypotese):**  
`/api/reports/saldobalanse/` beregner ikke `opening_balance` korrekt. Må sjekke:
1. Query i `app/api/routes/saldobalanse.py`
2. Service-lag logikk
3. Hvordan `opening_balance` kalkuleres (fra `general_ledger_lines`?)

**Impact:**  
🔴 **Blokkerende** – Bruker kan ikke se åpningsbalanse i rapporter.  
Regnskapsfører må kunne verifisere åpningsbalanse før videre bokføring.

**Prioritet:** 1 (må fikses før Test 3-6)

---

### Test 3: Bokfør leverandørfakturaer ⏸️ PAUSET

**Status:** Startet, men pauset for å fikse Bug #1 først.

**Problemanalyse:**  
Glenn's smoke test beskriver "bokfør 5 fakturaer manuelt via Bilagsføring eller Chat".  
Men API-en krever kompleks workflow:

1. Opprett `vendor_invoice` først
2. Parse/OCR (hvis PDF)
3. AI-booking → Review Queue
4. Godkjenn i Review Queue → hovedbok

**Alternativ API prøvd:**  
`POST /api/auto-booking/process-single` → krever `invoice_id` (faktura må eksistere først)

**Anbefaling:**  
For å fullføre Test 3-6 må jeg:
1. Forstå riktig workflow (trenger `kontali-accounting` SKILL)
2. Fikse Bug #1 først (åpningsbalanse)
3. Deretter lage 5 vendor_invoices → Review Queue → godkjenn

**Status:** ⏸️ Pauset til Bug #1 er fikset

---

### Test 4-6: ⏸️ IKKE STARTET

Test 4: Verifiser i hovedbok  
Test 5: Leverandørreskontro  
Test 6: Bilagsjournal

**Status:** Avhenger av Test 3

---

## Oppsummering Iterasjon 1

### ✅ Fullført:
- Fase 0: Skills
- Fase 1: Teknisk opprydding (MUI fjernet, rot ryddet)
- Test 1: Opprett klient
- Test 2: Åpningsbalanse (delvis)

### 🐛 Bugs funnet:
1. **Åpningsbalanse ikke synlig i saldobalanse** (KRITISK)

### ⏸️ Blokkert:
- Test 3-6 (avhenger av Bug #1 + riktig workflow-forståelse)

---

## Neste steg (Iterasjon 2)

### Prioritet 1: Fikse Bug #1
**Fil:** `/backend/app/api/routes/saldobalanse.py`  
**Mål:** `opening_balance` skal vise korrekt verdi fra `general_ledger` med `source_type="opening_balance"`

**Debugging-plan:**
1. Les `saldobalanse.py` – hvordan kalkuleres `opening_balance`?
2. Sjekk service-lag (hvis eksisterer)
3. Fikse query/beregning
4. Verifiser: `GET /api/reports/saldobalanse/` skal vise opening_balance = 500000 for konto 1920

### Prioritet 2: Forstå bokførings-workflow
**Skill:** `kontali-accounting`  
**Mål:** Forstå riktig flyt for Test 3-6

### Prioritet 3: Fullføre Test 3-6
Når Bug #1 er fikset og workflow forstått.

---

**Konklusjon:** Teknisk opprydding fullført ✅. Smoke test startet, men blokkert av kritisk bug. Fortsetter med iterasjon 2 for å fikse bugs.
