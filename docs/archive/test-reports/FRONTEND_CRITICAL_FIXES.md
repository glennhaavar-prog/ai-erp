# 🔧 CRITICAL FIXES - Frontend Fase 2

**Prioritet:** HØYEST  
**Estimert tid:** 2-3 timer  
**Blokkerer:** Production release

---

## Fix #1: Add FloatingChat to Layout (5 minutter)

### Problem
FloatingChat-komponenten er implementert men **aldri importert** i layout.  
Resultatet: Chat-knappen (💬) vises ikke på noen sider.

### Løsning

**Fil:** `src/app/layout.tsx` eller `src/components/layout/AppLayout.tsx`

**Alternativ A - I AppLayout.tsx (anbefalt):**
```tsx
'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import Breadcrumbs from './Breadcrumbs';
import { FloatingChat } from '@/components/FloatingChat';  // ← ADD
import { useClient } from '@/contexts/ClientContext';      // ← ADD

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { currentClient } = useClient();  // ← ADD

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <Breadcrumbs />

        <main className="flex-1 overflow-y-auto p-8 bg-background">
          <AnimatePresence mode="wait">
            <motion.div
              key={typeof window !== 'undefined' ? window.location.pathname : 'default'}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ← ADD FloatingChat */}
      <FloatingChat 
        clientId={currentClient?.id || '00000000-0000-0000-0000-000000000001'} 
      />
    </div>
  );
}
```

**Test:**
1. Start dev server: `npm run dev`
2. Navigate til any page
3. Look for 💬 button in bottom-right corner
4. Click → chat window should open

---

## Fix #2: Replace alert() with Toast Notifications (30 minutter)

### Problem
Error handling bruker `alert()` og `console.error()` - dårlig UX.

### Løsning

**Installer Sonner (anbefalt toast library):**
```bash
cd frontend
npm install sonner
```

**Setup i layout:**
```tsx
// src/app/layout.tsx
import { Toaster } from 'sonner';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nb" className="dark">
      <body className="font-body">
        <ViewModeProvider>
          <ClientProvider>
            <DemoBanner />
            <AppLayout>{children}</AppLayout>
            <Toaster position="top-right" richColors />  {/* ← ADD */}
          </ClientProvider>
        </ViewModeProvider>
      </body>
    </html>
  );
}
```

**Replace alerts i ReviewQueue.tsx:**
```tsx
// Before:
alert('Failed to approve item. Please try again.');

// After:
import { toast } from 'sonner';
toast.error('Failed to approve item. Please try again.');
```

**Replace i BankReconciliation.tsx:**
```tsx
// Before:
alert(`✅ Uploaded ${result.transactions_imported} transactions!`);

// After:
toast.success(`Uploaded ${result.transactions_imported} transactions!`, {
  description: `Auto-matched: ${result.auto_matched} (${result.match_rate}%)`
});
```

**Files å oppdatere:**
- `src/components/ReviewQueue.tsx` (2 alerts)
- `src/components/BankReconciliation.tsx` (4 alerts)
- `src/components/CorrectButton.tsx` (1 alert?)

---

## Fix #3: Fix Review Queue API UUID Error (Backend)

### Problem
Backend endpoint `/api/review-queue/items` kaster UUID parsing error:
```
ValueError: badly formed hexadecimal UUID string
```

### Løsning

**Fil:** `backend/app/api/routes/review_queue.py`

**Finn linje ~110:**
```python
# Current (broken):
selectinload(VendorInvoice.vendor)
```

**Problem:** UUID string blir sendt istedenfor UUID object.

**Fix:**
```python
from uuid import UUID

@router.get("/items")
async def get_review_items(
    client_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Validate UUID
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    # Continue with query...
```

**Test:**
```bash
curl http://localhost:8000/api/review-queue/items?client_id=00000000-0000-0000-0000-000000000001
```

Expected: JSON array, not error stacktrace.

---

## Fix #4: Autocomplete Hints in Chat (1 time)

### Problem
Spec krever autocomplete hints, men de er ikke implementert.

### Løsning

**Fil:** `src/components/chat/ChatInput.tsx`

**Add autocomplete suggestions:**
```tsx
'use client';

import React, { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

const COMMANDS = [
  'Vis meg fakturaer som venter',
  'Bokfør faktura ',
  'Godkjenn faktura ',
  'Vis status for ',
  'Hva er duplikater?',
];

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleInputChange = (value: string) => {
    setInput(value);
    
    // Show suggestions
    if (value.length > 0) {
      const matches = COMMANDS.filter(cmd => 
        cmd.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(matches);
    } else {
      setSuggestions([]);
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      onSend(input);
      setInput('');
      setSuggestions([]);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative">
      {/* Suggestions dropdown */}
      {suggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 bg-white border border-gray-200 rounded-t-lg shadow-lg mb-1">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => {
                setInput(suggestion);
                setSuggestions([]);
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700"
            >
              💡 {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input field */}
      <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Skriv en melding..."
            disabled={disabled}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## Testing Checklist ✅

Etter fixes er implementert:

### Manual Testing:
- [ ] FloatingChat button vises (bottom-right)
- [ ] Chat åpner ved klikk
- [ ] Autocomplete suggestions vises ved typing
- [ ] Toast notifications vises istedenfor alerts
- [ ] Review Queue laster uten UUID error
- [ ] Approve button fungerer (toast, ikke alert)
- [ ] Bank Reconciliation upload viser toast

### Regression Testing:
- [ ] Dashboard loads normally
- [ ] Navigation fungerer
- [ ] Dark mode fungerer
- [ ] No console errors

### Quick Test Script:
```bash
# Start services
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000 &
cd frontend && npm run dev &

# Wait 10 seconds
sleep 10

# Test endpoints
curl -s http://localhost:8000/api/review-queue/items?client_id=00000000-0000-0000-0000-000000000001
curl -s http://localhost:8000/demo/status
curl -s http://localhost:3002/dashboard | grep -q "Dashboard" && echo "✅ Frontend OK" || echo "❌ Frontend FAIL"

# Open browser
xdg-open http://localhost:3002/dashboard
```

---

## Deployment Checklist

**Before deploying to production:**

1. ✅ All 4 critical fixes implemented
2. ✅ Manual testing completed
3. ✅ No console errors in browser
4. ✅ Toast notifications working
5. ✅ FloatingChat visible and functional
6. ✅ Review Queue loads without errors
7. ✅ Bank Reconciliation tested with CSV upload
8. ✅ Demo Test Button verified

**Environment variables check:**
```bash
# Frontend
NEXT_PUBLIC_API_URL=https://api.kontali.no

# Backend
DATABASE_URL=postgresql://...
CLAUDE_API_KEY=sk-...
```

---

## Rollback Plan

If issues occur after deployment:

```bash
# Revert to previous commit
git revert HEAD
git push

# Or rollback specific file
git checkout HEAD~1 -- src/app/layout.tsx
```

---

**Sist oppdatert:** 2026-02-08 14:43 UTC  
**Ansvarlig:** Frontend team  
**Review:** Glenn (before merge)
