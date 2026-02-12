# Neste steg for Kontali MVP

**Analysert:** 2026-02-06 13:30 UTC  
**Nåværende status:** 7% ferdig (72 features totalt)  
**MVP-mål:** Demo-klar for potensielle kunder/investorer

---

## 🎯 MVP-definisjon (Core Value Proposition)

**Hva gjør Kontali spesiell?**
> "AI bokfører automatisk. Regnskapsfører godkjenner eller korrigerer. Systemet lærer. 80% tidsbesparing."

**Minimum for å demonstrere dette:**
1. ✅ **Invoice Agent** - AI foreslår bokføring (DONE)
2. ✅ **Review Queue** - Regnskapsfører godkjenner/korrigerer (DONE)
3. ✅ **Trust Dashboard** - "Alt er under kontroll" (DONE)
4. ⚠️ **Hovedbok** - Vise bokførte bilag (MANGLER)
5. ⚠️ **Learning System** - Corrections → bedre forslag (DELVIS)

---

## 🚀 Prioritert plan (3 faser)

### **Fase 1: Demo-Ready MVP (1-2 uker)**
*Mål: Kunne vise en overbevisende 15-minutters demo til potensielle kunder*

#### Uke 1 - Kritiske mangler
**Prioritet 1: Hovedbok-rapport** (2-3 dager)
- Vis alle bokførte bilag med detaljer
- Filter på dato, konto, leverandør
- Drilldown til PDF-bilag
- Export til Excel
- **Hvorfor:** Uten dette ser regnskapsfører ikke resultat av arbeidet

**Prioritet 2: Chart of Accounts management** (1-2 dager)
- Standard NS 4102 som default
- Opprett nye kontoer via chat ("Opprett konto 6999 - Annet kontorforbruk")
- Validering av kontonummer
- **Hvorfor:** Regnskapsfører må kunne tilpasse kontoplanen

**Prioritet 3: MVA-konfigurasjon** (1 dag)
- Standard norske MVA-koder (5=25%, 3=15%, 0=exempt)
- Kobling MVA-kode → konto (f.eks. 2740 = Inngående MVA 25%)
- **Hvorfor:** Nødvendig for korrekt bokføring i Norge

#### Uke 2 - Polish + Testing
**Prioritet 4: UI/UX polish** (2 dager)
- Match design fra din hjemmeside-link (trenger tilgang)
- Konsistent styling på alle sider
- Loading states, error handling
- Mobile responsiveness

**Prioritet 5: Learning System synlig** (1 dag)
- Vis i UI at systemet lærer fra corrections
- "Kontali lærer: Telenor → alltid konto 6900" (eksempel)
- Confidence score øker over tid (visualisering)

**Prioritet 6: End-to-end testing** (2 dager)
- 10 komplette test-scenarios
- Edge cases (dupliserte fakturaer, manglende MVA, etc.)
- Performance testing (100 fakturaer/dag)

---

### **Fase 2: Beta-Ready (2-3 uker etter Fase 1)**
*Mål: Første regnskapsbyrå kan teste med 5-10 ekte klienter*

**Kritisk for beta:**
1. **Autentisering** (JWT, multi-user) - 3 dager
2. **Multi-tenant isolering** (per-client data security) - 2 dager
3. **Bankavstemming** (matching algorithm + UI) - 5 dager
4. **Bokføringsregler** (leverandør → fast konto) - 3 dager
5. **Leverandørkort** (administrere leverandører) - 2 dager
6. **Rollestyring** (regnskapsfører vs. kunde-tilgang) - 3 dager

---

### **Fase 3: Launch-Ready (3-4 uker etter Fase 2)**
*Mål: 50-100 klienter i produksjon*

**Launch-kritiske features:**
1. **Rapporteringsmodul** (Resultat, Balanse, Saldobalanse) - 7 dager
2. **MVA-beregning** (Altinn-integrasjon) - 5 dager
3. **Periodesperre** (låse perioder etter MVA-innsending) - 2 dager
4. **Onboarding-agent** (migrering fra PowerOffice/Tripletex) - 7 dager
5. **Support chat** (AI-basert support) - 3 dager
6. **Audit log** (full hendelseslogg) - 3 dager

---

## 🎨 Om designet du sendte

Jeg kan ikke se linken (krever Lovable.dev login). Kan du:
1. Gi meg tilgang til Lovable-prosjektet, ELLER
2. Ta screenshots og last opp, ELLER
3. Fortell meg nøkkelpunktene i designet?

**Hva jeg trenger å vite:**
- Fargepalett (primary, secondary, accent colors)
- Typography (fonts, sizes)
- Layout (navbar, sidebar, spacing)
- Component styling (buttons, cards, inputs)

---

## 💡 Mitt råd for neste steg

### **Kortsiktig (denne uken):**
1. **Hovedbok-rapport** - Uten dette er MVP ufullstendig
2. **Chart of Accounts** - Nødvendig for tilpasning
3. **Design-matching** - Gjør det profesjonelt

### **Mellomlang (2-4 uker):**
1. **Bankavstemming** - THE killer feature (differentiator)
2. **Autentisering** - Kan ikke gå live uten
3. **Learning System synlig** - Viser verdien over tid

### **Langsiktig (2-3 måneder):**
1. **Onboarding-agent** - Eliminerer friksjon ved migrering
2. **Skyggemodus** - "Prøv før du kjøper" (genius sales-tool)
3. **Rapportering** - Fullstendig erstatning for PowerOffice

---

## ⚡ Quick Wins (kan gjøres i dag)

1. **Fix Review Queue route** (15 min)
   - Lag `/review-queue` page som bruker eksisterende ReviewQueue-komponent
   
2. **Add navigation menu** (30 min)
   - Dashboard, Review Queue, Hovedbok (placeholder), Innstillinger
   
3. **Improve error messages** (30 min)
   - Norske feilmeldinger i stedet for tekniske errors
   
4. **Add loading skeletons** (1 time)
   - Bedre UX mens data laster

---

## 📊 Suksess-kriterier for MVP-demo

**En god demo må vise:**
1. ✅ **Tillitsdashboard** - Grønt lys, alt under kontroll
2. ✅ **Review Queue** - AI foreslår, menneske godkjenner
3. ✅ **Auto-booking** - 80% automatisk (tidsbesparelse)
4. ⚠️ **Hovedbok** - Se resultat av bokføringer (MANGLER!)
5. ⚠️ **Læring** - Systemet blir smartere over tid (DELVIS)

**Dagens status:**
- 60% av demo-kriteriene er på plass
- **Hovedbok er den største gapet**
- Uten Hovedbok virker det som systemet ikke gjør noe med fakturaene

---

## 🤔 Spørsmål til deg

1. **Design-link:** Kan du gi meg tilgang til Lovable-prosjektet?
2. **Prioritering:** Enig i at Hovedbok er neste steg?
3. **Timeline:** Når trenger du MVP klar for ekte demo?
4. **Target audience:** Hvem skal se første demo? (investor, kunde, partner?)
5. **Scope:** Vil du kutte noen features for å fokusere på core?

---

**Bunnlinje:** Du har en solid foundation (70% av demo-infrastrukturen). Hovedbok-rapporten er den kritiske missing piece for å vise at systemet faktisk fungerer end-to-end.

**Min anbefaling:** Fokuser de neste 2-3 dagene på Hovedbok + Chart of Accounts + Design polish. Da har du et MVP du kan være stolt av å vise frem.
