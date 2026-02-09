# 🚨 Hydration Error Fix - Date/Time Rendering

**Date:** 2026-02-08  
**Issue:** Server-rendered timestamps caused hydration mismatches  
**Root cause:** Server uses UTC, client uses local timezone

---

## Problem Statement

When components render timestamps during server-side rendering (SSR), Next.js generates HTML with UTC time. When the browser hydrates the component, it re-renders with local timezone, causing a mismatch:

```
Server: "21:39" (UTC)
Client: "22:39" (CET/CEST)
→ React Hydration Error
```

This breaks the entire React tree and forces client-side rendering fallback.

---

## Affected Components (18 total)

- ✅ `FixedChatPanel.tsx` - FIXED (manual)
- 🔄 17 other components being fixed systematically by agent

---

## Robust Solution

### 1. Utility Library Created

**File:** `/home/ubuntu/.openclaw/workspace/ai-erp/frontend/src/lib/date-utils.ts`

Provides client-safe date/time formatting:
- `useClientOnly()` hook
- `formatTime()`, `formatDate()`, `formatDateTime()`, `formatRelativeTime()`
- `<ClientSafeTimestamp />` component

### 2. Fix Pattern

**Before (causes hydration error):**
```typescript
<p>{message.timestamp.toLocaleTimeString('nb-NO', {
  hour: '2-digit',
  minute: '2-digit'
})}</p>
```

**After (client-safe):**
```typescript
import { useClientOnly, formatTime } from '@/lib/date-utils';

const mounted = useClientOnly();

return (
  {mounted && <p>{formatTime(message.timestamp)}</p>}
);
```

**Or use component:**
```typescript
import { ClientSafeTimestamp } from '@/lib/date-utils';

<ClientSafeTimestamp date={message.timestamp} format="time" />
```

---

## Best Practices (Going Forward)

### ❌ NEVER do this in components:
```typescript
// Direct date formatting in render - causes hydration errors
const time = new Date().toLocaleTimeString();
const date = someDate.toLocaleDateString();
```

### ✅ ALWAYS do this instead:
```typescript
import { useClientOnly, formatTime } from '@/lib/date-utils';

const mounted = useClientOnly();

// Conditional rendering
{mounted && <span>{formatTime(date)}</span>}

// Or use component
<ClientSafeTimestamp date={date} format="time" />
```

---

## Why This Is Production-Ready

1. **Centralized logic** - All date formatting in one utility file
2. **Consistent behavior** - Same formatting everywhere
3. **Norwegian locale** - All functions use 'nb-NO' by default
4. **Type-safe** - TypeScript interfaces prevent misuse
5. **Documented** - Clear examples and JSDoc comments
6. **Testable** - Can mock `useClientOnly()` in tests

---

## Verification Checklist

After making changes:
1. Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Open DevTools console
3. Look for "Hydration error" or "Text content did not match"
4. Should see ZERO errors
5. Timestamps should render correctly in local timezone

---

## Lesson Learned

**Glenn's directive:** "Alltid fikse feil permanent og robust løsning"

- ❌ Quick fix: Fix one component
- ✅ Robust fix: Create utility + fix ALL components + document pattern

**This is what "ordentlig fikset" means:**
- Not just working now
- Works forever
- Prevents future developers from making same mistake
- Documented and maintainable

---

**Status:** ✅ Utility created, agent fixing all components systematically
