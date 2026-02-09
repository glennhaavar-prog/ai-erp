# Glenn's Feedback - Neste Steg (Prioritert)

**Fullstendig analyse:** Se `GLENN_FEEDBACK_ANALYSIS.md`  
**Visuelle mockups:** Se `VISUAL_REPORT.md`

---

## 🎯 HURTIG STATUS

| ✅ Allerede fikset | ❌ Må fikses | 💡 Nye forslag |
|-------------------|-------------|---------------|
| 6 tasks | 5 tasks | 7 tasks |

---

## 🔴 KRITISK (Start her!)

### 1. Forenkle navigasjon - FJERN TRE DASHBOARDS
**Problem:** Klientoversikt, Kontrollsentral, Fremdrift → forvirrende  
**Løsning:** Unified Navigation Architecture  
**Estimat:** 4-6 timer

**Hva gjøres:**
```
FJERN:
❌ /dashboard → Flytt til /clients/:id/review
❌ /fremdrift → Integrer i multi-client view
❌ /kontrollsentral → Forkast konseptet

BEHOLD:
✅ / (root) → Multi-client eller single-client landing
✅ /clients/:id → Klient-spesifikt dashboard
```

**Filer å endre:**
- `frontend/src/app/page.tsx` - Unified landing
- `frontend/src/app/dashboard/page.tsx` - Fjern eller flytt
- `frontend/src/app/fremdrift/page.tsx` - Integrer i multi-client
- `frontend/src/components/layout/Navigation.tsx` - Oppdater meny

---

### 2. Forbedre søkefelt-kontrast
**Problem:** Grått søkefelt vanskelig å se  
**Løsning:** Hvit tekst, klarere border, søkeikon  
**Estimat:** 1 time

**CSS-endring:**
```tsx
// FØR
className="bg-gray-800 text-gray-400"

// ETTER
className="bg-gray-700 text-white ring-1 ring-gray-600 focus:ring-primary"
```

**Filer å endre:**
- `frontend/src/components/SearchInput.tsx` (eller hvor søkefelt ligger)
- `frontend/src/app/globals.css` (hvis global styling)

---

### 3. K-logo skal til startside (ikke Kontrollsentral)
**Problem:** K-logo leder til feil sted, X-knapp forvirrende  
**Løsning:** K-logo alltid til `/`, fjern X-knapp  
**Estimat:** 30 min

**Endring:**
```tsx
// layout.tsx eller Header.tsx
<Link href="/" className="flex items-center gap-2">
  <Logo /> {/* Fjern X-knapp */}
</Link>
```

**Filer å endre:**
- `frontend/src/app/layout.tsx`
- `frontend/src/components/layout/Header.tsx`

---

## 🟡 VIKTIG (Etter kritiske tasks)

### 4. Breadcrumb må alltid inkludere klientnavn
**Problem:** Viser `🏠 > Resultatregnskap` uten klientnavn  
**Løsning:** `🏠 > Nordic Tech Solutions AS > Resultatregnskap`  
**Estimat:** 1-2 timer

**Endring:**
```tsx
// Breadcrumbs.tsx
const breadcrumbs = [
  { label: 'Hjem', href: '/', icon: Home },
  { label: clientName, href: `/clients/${clientId}` }, // LEGG TIL
  { label: 'Resultatregnskap', href: `/rapporter/resultat` },
];
```

**Filer å endre:**
- `frontend/src/components/layout/Breadcrumbs.tsx`
- Alle sider som bruker breadcrumbs

---

### 5. Reduser scrolling i rapporter
**Problem:** For mye scrolling i Resultatregnskap  
**Løsning:** Accordion, sticky totals, zoom-kontroll  
**Estimat:** 2-3 timer

**Implementasjon:**
```tsx
// A) Accordion for kontogrupper
<Accordion>
  <AccordionItem title="5000 Lønnskostnader - 1 234 567 kr">
    <SubAccounts /> {/* Ekspander kun ved klikk */}
  </AccordionItem>
</Accordion>

// B) Sticky totals
<div className="sticky bottom-0 bg-background border-t">
  <div>Total Resultat: 1 777 778 kr</div>
</div>

// C) Zoom-nivå kontroll
<ButtonGroup>
  <Button onClick={() => setZoom('summary')}>Sammendrag</Button>
  <Button onClick={() => setZoom('detailed')}>Detaljert</Button>
</ButtonGroup>
```

**Filer å endre:**
- `frontend/src/app/rapporter/resultatregnskap/page.tsx`
- `frontend/src/components/ui/accordion.tsx` (opprett hvis mangler)

---

## 🟢 NICE-TO-HAVE (Når tid tillater)

### 6. Fjern demo-banner duplikater (15 min)
**Problem:** Demo-banner vises både i header og innhold  
**Løsning:** Vis kun én gang (i header)

### 7. Tekniske ID-er → lesbare navn (30 min)
**Problem:** Breadcrumb viser UUID: `E7f14097...`  
**Løsning:** Vis `Faktura #1234 - Nordic Tech`

### 8. Klarere ikon-tooltips (30 min)
**Problem:** Grid-ikon og dokument-ikon har uklar funksjon  
**Løsning:** Legg til tooltips på ALLE ikoner

### 9. Forbedret balanse-feilmelding (1 time)
**Problem:** "Balansen balanserer ikke" uten løsning  
**Løsning:** Legg til "Hvordan fikse dette?" link

### 10. Kontekstuelle hjem-ikoner (1 time)
**Problem:** Uklar hvor hus-ikon leder  
**Løsning:** Bruk 🏢 for global, 🏠 for klient-hjem

### 11. Fargebruk i rapporter (1 time)
**Problem:** Lite fargebruk i Resultatregnskap  
**Løsning:** Grønn for inntekter, rød for kostnader

### 12. Status-indikator badges (30 min)
**Problem:** "Aktiv klient" undertekst tar plass  
**Løsning:** Erstatt med badge/ikon

---

## 📊 TOTAL ESTIMAT

| Prioritet | Tasks | Tid |
|-----------|-------|-----|
| 🔴 Kritisk | 3 | 5.5 - 7.5 timer |
| 🟡 Viktig | 2 | 3 - 5 timer |
| 🟢 Nice-to-have | 7 | 5 timer |
| **TOTAL** | **12** | **13.5 - 17.5 timer** |

---

## 🚀 ANBEFALT REKKEFØLGE

### Dag 1 (6-8 timer):
1. Task 1: Forenkle navigasjon (4-6 timer) 🔴
2. Task 2: Søkefelt-kontrast (1 time) 🔴
3. Task 3: K-logo til startside (30 min) 🔴
4. Task 4: Breadcrumb med klientnavn (1-2 timer) 🟡

### Dag 2 (3-4 timer):
5. Task 5: Reduser scrolling (2-3 timer) 🟡
6. Tasks 6-12: Nice-to-have (1-2 timer utvalgte) 🟢

---

## ✅ ALLEREDE IMPLEMENTERT (Ikke gjør igjen!)

1. ✅ Customer Invoice Overdue fjernet fra review queue
2. ✅ Søkefelt i header (men trenger bedre kontrast)
3. ✅ Komprimerte klient-kort
4. ✅ Unified Dashboard (multi-client view)
5. ✅ ViewModeToggle (Multi-Client / Single Client)
6. ✅ TaskTypeFilter (Bilag / Bank / Avstemming)
7. ✅ RightPanel (detaljer 40% + chat 60%)

---

## 📝 VERIFISER FØRST

Før du starter implementasjon:

1. **Sjekk at dagens kode faktisk har disse problemene**
   - Video fra Glenn kan være gammelt UI
   - Flere tasks er allerede fikset (se liste over)

2. **Test i browser:**
   ```bash
   cd /home/ubuntu/.openclaw/workspace/ai-erp
   npm run dev
   ```
   - Åpne http://localhost:3000
   - Verifiser at problemene fortsatt eksisterer

3. **Prioriter med Glenn:**
   - Få bekreftelse på prioritering
   - Avklar hvilke tasks som er mest kritiske

---

## 📂 DOKUMENTASJON

- **Fullstendig analyse:** `GLENN_FEEDBACK_ANALYSIS.md` (18 KB)
- **Visuelle mockups:** `VISUAL_REPORT.md` (14 KB)
- **Video-frames:** `frames/frame_*.jpg` (15 screenshots)
- **Original video:** https://www.loom.com/share/83e74492cad9453199df91dd9a3bb82e

---

**Generert:** 2026-02-09  
**Subagent:** kontali-video2-analysis  
**Status:** ✅ Klar for implementasjon

**Start med Task 1 (Forenkle navigasjon) - mest kritisk! 🔴**
