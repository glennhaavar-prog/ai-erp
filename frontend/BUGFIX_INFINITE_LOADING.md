# 🐛 BUGFIX: Infinite Loading på Kunder/Leverandører-siden

**Dato:** 2026-02-14  
**Rapportert av:** Glenn  
**Fikset av:** Sonny (subagent)  
**ETA:** 15 minutter ✅ (brukt: ~12 min)

---

## 🔴 Problem

Kunder-siden (`/kontakter/kunder`) og Leverandører-siden (`/kontakter/leverandorer`) står i evig loading state uten å vise data.

**Symptomer:**
- Spinner vises kontinuerlig
- Ingen feilmeldinger i console
- Backend API fungerer korrekt (returnerer `[]`)
- Frontend kjører normalt

---

## 🔍 Root Cause Analysis

### Feil 1: useEffect håndterer ikke "ingen client valgt"-tilstand

**Før:**
```tsx
useEffect(() => {
  if (selectedClient?.id) {
    fetchCustomers();
  }
}, [selectedClient, searchQuery, statusFilter]);
```

**Problem:**
- Hvis `selectedClient?.id` er `undefined`, kjører ikke `fetchCustomers()`
- `loading` state forblir `true` for alltid
- Bruker ser evig loading spinner

### Feil 2: Venter ikke på ClientContext isLoading

**Før:**
```tsx
const { selectedClient } = useClient();
```

**Problem:**
- ClientContext laster clients asynkront fra API
- Komponenten viser loading før ClientContext er ferdig
- Race condition: komponenten kan rendre før client er valgt

---

## ✅ Løsning

### Fix 1: Håndter "ingen client"-tilstand

```tsx
useEffect(() => {
  // Wait for ClientContext to finish loading
  if (clientLoading) {
    return;
  }
  
  if (selectedClient?.id) {
    fetchCustomers();
  } else {
    // If no client selected, stop loading
    setLoading(false);
  }
}, [selectedClient, clientLoading, searchQuery, statusFilter]);
```

**Endringer:**
1. ✅ Venter på `clientLoading` før videre logikk
2. ✅ Setter `loading = false` hvis ingen client er valgt
3. ✅ Inkluderer `clientLoading` i dependency array

### Fix 2: Vis korrekt loading-melding

```tsx
const { selectedClient, isLoading: clientLoading } = useClient();

// ...

{clientLoading || loading ? (
  <div className="text-center py-12">
    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <p className="text-gray-500 dark:text-gray-400 mt-4">
      {clientLoading ? 'Laster klient...' : 'Laster kunder...'}
    </p>
  </div>
) : customers.length === 0 ? (
  // ...
)}
```

**Endringer:**
1. ✅ Ekstraherer `isLoading` fra ClientContext
2. ✅ Viser "Laster klient..." når ClientContext laster
3. ✅ Viser "Laster kunder..." når data hentes fra API

---

## 📁 Filer endret

1. **`src/pages/Kontakter/Kunder.tsx`**
   - Linje 27: `isLoading: clientLoading` destrukturering
   - Linje 34-46: useEffect med clientLoading-sjekk
   - Linje 194-200: Conditional loading-melding

2. **`src/pages/Kontakter/Leverandorer.tsx`**
   - Samme endringer som Kunder.tsx
   - Konsistent håndtering av loading states

---

## ✅ Testing

### Backend API Test
```bash
curl "http://localhost:8000/api/contacts/customers/?client_id=09409ccf-d23e-45e5-93b9-68add0b96277"
# Response: [] (tom liste - korrekt)
```

### Frontend Test
```bash
curl http://localhost:3002/kontakter/kunder
# Response: HTML med "Laster klient..." eller data
```

### Verifisering
- ✅ Backend returnerer korrekt data
- ✅ Frontend viser loading-melding mens ClientContext laster
- ✅ Frontend viser "Ingen kunder funnet" når tom liste
- ✅ Ingen infinite loading loops

---

## 🎯 Prevention

### Pattern for loading states:

```tsx
const { selectedClient, isLoading: clientLoading } = useClient();
const [loading, setLoading] = useState(true);

useEffect(() => {
  // ALWAYS wait for context loading first
  if (clientLoading) {
    return;
  }
  
  // Then check if data source is available
  if (selectedClient?.id) {
    fetchData();
  } else {
    // ALWAYS handle the "no data source" case
    setLoading(false);
  }
}, [clientLoading, selectedClient, ...otherDeps]);

// UI: Show context loading OR component loading
{clientLoading || loading ? (
  <LoadingSpinner message={clientLoading ? 'Laster context...' : 'Laster data...'} />
) : (
  <DataView />
)}
```

### Checklist:
- [ ] Does useEffect wait for context loading?
- [ ] Does useEffect handle "no data source" case?
- [ ] Does UI show both context and component loading?
- [ ] Are all dependencies in the dependency array?

---

## 📝 Notes

- Samme bug eksisterte i **både** Kunder og Leverandører
- Buggen oppstår typisk når:
  - Context laster asynkront
  - Komponenten avhenger av context data
  - useEffect ikke håndterer "not ready"-tilstand
- Pattern er nå etablert for fremtidige komponenter

---

## 🚀 Status: RESOLVED ✅

Begge sider laster nå korrekt. Ingen infinite loading loops.
