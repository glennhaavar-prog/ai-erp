# 🧪 Testing Guide for Glenn - AI Chat

## Quick Start (5 minutter)

### 1. Start applikasjonen
```bash
# Terminal 1 - Backend
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
npm run dev
```

### 2. Åpne AI Chat
1. Gå til http://localhost:3002
2. Klikk "VERKTØY" i venstremenyen
3. Klikk "AI Chat"

---

## 🎯 Test Scenarios

### ✅ Test 1: Basic Chat (30 sek)
1. Skriv: "Hva er status på klient?"
2. Trykk Enter eller "Send"
3. **Forventet:** AI svarer med statusinfo

### ✅ Test 2: Drag-and-Drop (1 min)
1. Finn en PDF-faktura på maskinen din
2. Dra den inn i chat-input området
3. **Forventet:** Fil vises med navn og størrelse
4. Skriv: "Bokfør dette bilag på debet kto 7000 og kredit 2990"
5. Trykk "Send"
6. **Forventet:** Melding sendes med vedlegg-ikon

### ✅ Test 3: Click to Browse (30 sek)
1. Klikk på vedlegg-knappen (📎) til venstre
2. Velg fil fra dialog
3. **Forventet:** Fil lastes opp og vises
4. Klikk X for å fjerne fil
5. **Forventet:** Fil fjernes

### ✅ Test 4: Multiple Files (1 min)
1. Dra 2-3 filer samtidig
2. **Forventet:** Alle vises i liste
3. Fjern én fil
4. Send melding med resten
5. **Forventet:** Kun gjenværende filer sendes

### ✅ Test 5: File Validation (30 sek)
1. Prøv å laste opp en .exe eller .zip fil
2. **Forventet:** Feilmelding "ugyldig filtype"
3. Prøv å laste opp fil > 10MB
4. **Forventet:** Feilmelding "for stor"

### ✅ Test 6: Session Persistence (30 sek)
1. Send 2-3 meldinger
2. Refresh siden (F5)
3. **Forventet:** All chat-historikk er der
4. Send ny melding
5. **Forventet:** Fungerer normalt

### ✅ Test 7: Clear Conversation (15 sek)
1. Klikk "Tøm samtale" (oppe til høyre)
2. Bekreft dialog
3. **Forventet:** Chat tømmes, ny sesjon starter

### ✅ Test 8: Error Handling (30 sek)
1. Stopp backend (Ctrl+C i Terminal 1)
2. Send melding
3. **Forventet:** Feilmelding vises
4. Start backend igjen
5. Klikk "Lukk" på feilmeldingen
6. Send ny melding
7. **Forventet:** Fungerer igjen

### ✅ Test 9: Mobile View (1 min)
1. Åpne DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Velg iPhone eller Android
4. **Forventet:** Layout fungerer, ingen overlap
5. Test scroll, input, send

### ✅ Test 10: Quick Actions (30 sek)
1. På tom chat, se forslag-knappene
2. Klikk "Hva er status på klient?"
3. **Forventet:** Sendes automatisk som melding

---

## 🐛 Common Issues & Fixes

### Issue: "Cannot find module '@/contexts/ClientContext'"
**Fix:** Sjekk at ClientContext.tsx eksisterer i `src/contexts/`

### Issue: "404 /api/chat-booking/message"
**Fix:** 
1. Sjekk at backend kjører på port 8000
2. Verifiser `.env` har `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Issue: "Ingen klient valgt" i header
**Fix:** Velg en klient i toppmeny først

### Issue: Files not uploading
**Fix:** 
1. Sjekk console for errors
2. Verifiser fil er < 10MB
3. Sjekk filtype (kun PDF, JPG, PNG)

### Issue: Chat doesn't persist
**Fix:** Sjekk at localStorage ikke er blokkert i nettleser

---

## 📸 Expected Look

### Empty State
- Robot-ikon
- "Hei! Jeg er Kontali AI"
- Tre quick-action knapper

### Chat with Messages
- User messages: Høyre side, blå bakgrunn
- AI messages: Venstre side, grå bakgrunn
- Timestamps under hver melding
- Loading dots mens AI "tenker"

### With Attachments
- Vedlegg-knapp lyser opp når filer er valgt
- Filnavn + størrelse vises
- X-knapp for å fjerne
- Ikon viser filtype (dokument/bilde)

---

## ✅ Success Checklist

- [ ] AI Chat finnes i VERKTØY-menyen
- [ ] Kan sende tekstmeldinger
- [ ] Kan dra-og-slippe filer
- [ ] Kan klikke for å velge filer
- [ ] Filer vises før sending
- [ ] Kan fjerne filer
- [ ] AI svarer på meldinger
- [ ] Chat bevares ved refresh
- [ ] Feilmeldinger vises tydelig
- [ ] Fungerer på mobil
- [ ] All tekst er på norsk

---

## 💡 Tips for Testing

1. **Test med ekte data:** Bruk faktiske fakturaer hvis mulig
2. **Test edge cases:** Lange meldinger, mange filer, langsom nett
3. **Test på flere nettlesere:** Chrome, Firefox, Safari
4. **Test keyboard shortcuts:** Enter to send, Shift+Enter for newline
5. **Check responsiveness:** Resize window mellom 320px - 2560px

---

## 🚨 If Something Breaks

1. **Check browser console** (F12 → Console tab)
2. **Check network tab** (F12 → Network tab)
3. **Check backend logs** (Terminal 1)
4. **Clear localStorage:**
   ```javascript
   localStorage.removeItem('kontali-chat-session')
   ```
5. **Hard refresh:** Ctrl+Shift+R

---

## 📞 Report Issues

Når du finner feil, noter:
1. **Hva gjorde du?** (steps to reproduce)
2. **Hva forventet du?**
3. **Hva skjedde i stedet?**
4. **Console errors?** (screenshot)
5. **Hvilken nettleser/enhet?**

---

## ⏱️ Estimated Test Time

- Quick smoke test: **5 minutter**
- Full test suite: **15 minutter**
- Edge cases + mobile: **30 minutter**

---

**Lykke til med testingen, Glenn!** 🎉

Hvis alt fungerer, er du klar til å bokføre fakturaer med AI! 🤖💼
