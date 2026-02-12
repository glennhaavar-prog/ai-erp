# 🚀 AI Chat - Quick Reference Card

## Start App
```bash
# Terminal 1
cd ai-erp/backend && uvicorn app.main:app --reload

# Terminal 2  
cd ai-erp/frontend && npm run dev
```

## Access
**URL:** http://localhost:3002/chat  
**Menu:** VERKTØY → AI Chat

---

## 💬 Basic Usage

### Send Message
1. Type in input box
2. Press **Enter** (or click "Send")

### Upload File
**Method 1:** Drag file into input area  
**Method 2:** Click 📎 button → Browse

### Multiple Files
- Drag multiple files at once
- Click X to remove individual files

### Clear Chat
Click **"Tøm samtale"** (top right)

---

## ✅ What Works

✅ Text messages  
✅ File upload (PDF, JPG, PNG)  
✅ Drag-and-drop  
✅ Session persistence  
✅ Error handling  
✅ Mobile responsive  

---

## 🎯 Test Commands

```
"Hva er status på klient?"
"Bokfør dette bilag på debet kto 7000 og kredit 2990"
"Vis leverandørreskontro"
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 error | Check backend running on :8000 |
| Not loading | Hard refresh (Ctrl+Shift+R) |
| Files rejected | Max 10MB, PDF/JPG/PNG only |
| Chat not saving | Check localStorage not blocked |

**Clear session:**
```javascript
localStorage.removeItem('kontali-chat-session')
```

---

## 📸 Expected Look

**Empty:**  
🤖 Robot icon + Welcome + 3 suggestion buttons

**With messages:**  
👤 User (right, blue) | 🤖 AI (left, gray)

**With files:**  
📎 Button lights up | File list with X buttons

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Enter** | Send message |
| **Shift+Enter** | New line |
| **Ctrl+R** | Refresh page |
| **F12** | Open DevTools |

---

## 📊 File Limits

- **Max size:** 10MB per file
- **Types:** PDF, JPG, PNG
- **Multiple:** Yes, unlimited

---

## 🎉 Success = All These Work

- [ ] Send text message → AI responds
- [ ] Drag PDF → Shows in preview
- [ ] Send with file → ✅ Sent
- [ ] Refresh page → Chat restored
- [ ] Mobile view → No layout issues

---

**Time to test:** 5-15 minutes  
**Status:** ✅ Ready  
**Have fun!** 🎉
