# 🚀 Kontali ERP - Bruksanvisning

**Sist oppdatert:** 2026-02-05 22:03 UTC

---

## 📋 Forhåndskrav

Du må være koblet til EC2 via **VS Code Remote SSH**.

### Slik kobler du til:

1. Åpne VS Code
2. Trykk `Cmd+Shift+P` (Mac) / `Ctrl+Shift+P` (Windows)
3. Søk: "Remote-SSH: Connect to Host"
4. Velg EC2-serveren din
5. Vent til "SSH: ec2..." vises i nedre venstre hjørne

**Port forwarding skjer automatisk** når du er koblet til via Remote SSH!

---

## 🌐 Linker (bookmarks)

### 1. Missionboard (Roadmap)
**http://localhost:3001**
- Viser alle 20 moduler og 72 features
- Progress tracking per modul
- Timeline view

### 2. Chat Interface (NEW!)
**http://localhost:3000/chat**
- Chat med AI-orkestrator
- 70% chat / 30% review list
- Kommandoer: `help`, `show reviews`, `approve [id]`, `reject [id]`, `status`

### 3. Review Queue (Classic)
**http://localhost:3000**
- Tradisjonell Review Queue UI
- Invoice details
- Approve/Correct buttons

### 4. Backend API Docs
**http://localhost:8000/docs**
- FastAPI Swagger UI
- Test API endpoints
- Interactive documentation

---

## ✅ Sjekk at alt kjører

Åpne terminalen i VS Code (`` Ctrl+` ``) og kjør:

```bash
# Sjekk backend
curl http://localhost:8000/health

# Sjekk frontend
curl http://localhost:3000 | head -5

# Sjekk roadmap
curl http://localhost:3001 | head -5
```

**Forventet resultat:**
- Backend: `{"status":"healthy"}`
- Frontend: HTML-kode
- Roadmap: HTML-kode

---

## 🔧 Hvis noe ikke fungerer

### Problem: "This site can't be reached"

**Årsak:** Du er ikke koblet til via VS Code Remote SSH, eller serverne kjører ikke.

**Løsning:**
1. Sjekk at du ser "SSH: ec2..." i nedre venstre hjørne av VS Code
2. Kjør disse kommandoene i VS Code terminalen:

```bash
# Sjekk om servere kjører
ps aux | grep -E "uvicorn|next dev"

# Start backend (hvis ikke kjører)
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &

# Start frontend (hvis ikke kjører)
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &

# Start roadmap (hvis ikke kjører)
cd /home/ubuntu/.openclaw/workspace/ai-erp/roadmap
nohup npm run dev -- -p 3001 > /tmp/roadmap.log 2>&1 &
```

3. Vent 10 sekunder og prøv lenken igjen

### Problem: Backend gir feilmelding

**Sjekk logger:**
```bash
tail -50 /tmp/backend.log
```

**Vanlige årsaker:**
- Database ikke koblet til (PostgreSQL må kjøre)
- Environment variables mangler (sjekk `.env`)
- Dependencies ikke installert

### Problem: Frontend gir blank side

**Sjekk logger:**
```bash
tail -50 /tmp/frontend.log
```

**Vanlige årsaker:**
- Backend ikke tilgjengelig (sjekk port 8000)
- Build-feil i React-kode

---

## 📱 Tips for testing

### Test Chat Interface:
1. Gå til http://localhost:3000/chat
2. Skriv: `help`
3. Prøv: `show reviews`
4. Prøv: `status`

### Test Review Queue:
1. Gå til http://localhost:3000
2. Se pending reviews (hvis data finnes)
3. Klikk på en invoice for detaljer

### Test Missionboard:
1. Gå til http://localhost:3001
2. Se modulkort med progress rings
3. Klikk på et kort for detaljer
4. Prøv timeline-visning

---

## 🆘 Hjelp!

Hvis ingenting fungerer:

1. **Spør Nikoline** - jeg fikser det!
2. Sjekk at VS Code Remote SSH er koblet til
3. Kjør `ps aux | grep -E "uvicorn|next"` for å se hva som kjører
4. Sjekk logs: `/tmp/backend.log`, `/tmp/frontend.log`, `/tmp/roadmap.log`

---

## 🎯 Quick Start Checklist

- [ ] Koblet til EC2 via VS Code Remote SSH
- [ ] Backend kjører (http://localhost:8000/health)
- [ ] Frontend kjører (http://localhost:3000)
- [ ] Roadmap kjører (http://localhost:3001)
- [ ] Bookmarks lagret i nettleseren

**Når alle 5 er krysset av → alt fungerer!** 🎉
