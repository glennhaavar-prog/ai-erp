# Frontend Coding Standards

## Date/Time Handling - Preventing Hydration Errors

### The Problem

React hydration errors occur when server-rendered HTML doesn't match client-rendered HTML. This commonly happens with date/time formatting because:

- **Server** renders dates in UTC timezone
- **Client** renders dates in user's local timezone
- The mismatch causes React to throw hydration warnings

### The Solution: Use Client-Safe Utilities

We have created utility functions in `/src/lib/date-utils.ts` to handle date/time formatting safely.

### ❌ DON'T DO THIS

```typescript
// WRONG - Causes hydration error
<p>{new Date(timestamp).toLocaleTimeString('nb-NO')}</p>
<p>{new Date(date).toLocaleDateString('nb-NO')}</p>
<p>{new Date(datetime).toLocaleString('nb-NO')}</p>

// WRONG - date-fns without client-side check
<p>{format(new Date(timestamp), 'HH:mm')}</p>
```

### ✅ DO THIS INSTEAD

#### Option 1: Use `<ClientSafeTimestamp>` Component (Recommended)

```typescript
import { ClientSafeTimestamp } from '@/lib/date-utils';

// Time only (HH:MM)
<ClientSafeTimestamp date={message.timestamp} format="time" />

// Date only (DD.MM.YYYY)
<ClientSafeTimestamp date={invoice.date} format="date" />

// Date + Time (DD.MM.YYYY HH:MM)
<ClientSafeTimestamp date={entry.createdAt} format="datetime" />

// Relative time ("2 timer siden", "i går")
<ClientSafeTimestamp date={notification.createdAt} format="relative" />
```

#### Option 2: Use `useClientOnly()` Hook + Format Functions

```typescript
import { useClientOnly, formatTime, formatDate, formatDateTime } from '@/lib/date-utils';

function MyComponent({ timestamp }) {
  const mounted = useClientOnly();

  return (
    <div>
      {/* Conditional rendering - only show on client */}
      {mounted && <p>{formatTime(timestamp)}</p>}
    </div>
  );
}
```

### Available Utilities

#### Hooks

- **`useClientOnly()`** - Returns `true` only after component mounts (client-side)

#### Format Functions (Client-side only)

- **`formatTime(date)`** - Returns `"HH:MM"` (Norwegian format)
- **`formatDate(date)`** - Returns `"DD.MM.YYYY"`
- **`formatDateTime(date)`** - Returns `"DD.MM.YYYY HH:MM"`
- **`formatRelativeTime(date)`** - Returns `"2 timer siden"`, `"i går"`, etc.

#### Components

- **`<ClientSafeTimestamp date={...} format="time|date|datetime|relative" />`** - Safe wrapper component

### When to Use Each Approach

**Use `<ClientSafeTimestamp>` when:**
- Simple date/time display
- No custom styling needed
- Recommended for most cases

**Use `useClientOnly()` + format functions when:**
- Need custom rendering logic
- Complex conditional display
- Combining date with other dynamic content

**Use `formatRelativeTime()` when:**
- Chat messages
- Notification timestamps
- Activity feeds
- Recent updates

### Migration Checklist

When fixing existing date rendering:

1. ✅ Add import: `import { ClientSafeTimestamp } from '@/lib/date-utils';`
2. ✅ Replace `new Date(...).toLocaleTimeString()` → `<ClientSafeTimestamp format="time" />`
3. ✅ Replace `new Date(...).toLocaleDateString()` → `<ClientSafeTimestamp format="date" />`
4. ✅ Replace `new Date(...).toLocaleString()` → `<ClientSafeTimestamp format="datetime" />`
5. ✅ Replace `format(new Date(...), 'HH:mm')` → `<ClientSafeTimestamp format="time" />`
6. ✅ Test: Hard refresh (Ctrl+Shift+R) and check console for hydration warnings

### Testing

After implementing date utilities:

1. **Open browser DevTools console**
2. **Hard refresh** the page (Ctrl+Shift+R / Cmd+Shift+R)
3. **Look for warnings:**
   - ✅ **GOOD:** No hydration warnings
   - ❌ **BAD:** "Text content does not match server-rendered HTML"
   - ❌ **BAD:** "Hydration failed because the initial UI does not match..."

### Example: Complete Migration

**Before:**
```typescript
export function MessageList({ messages }) {
  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>
          <p>{msg.content}</p>
          <span>{new Date(msg.timestamp).toLocaleTimeString('nb-NO')}</span>
        </div>
      ))}
    </div>
  );
}
```

**After:**
```typescript
import { ClientSafeTimestamp } from '@/lib/date-utils';

export function MessageList({ messages }) {
  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>
          <p>{msg.content}</p>
          <ClientSafeTimestamp date={msg.timestamp} format="time" />
        </div>
      ))}
    </div>
  );
}
```

---

## Other Best Practices

(Add other coding standards here as needed)

### Component Structure

- Always use `'use client'` directive for components with hooks or browser APIs
- Keep components focused and single-responsibility
- Extract reusable logic into custom hooks

### TypeScript

- Define interfaces for all props and data structures
- Avoid `any` type - use `unknown` or proper typing
- Use optional chaining (`?.`) and nullish coalescing (`??`) for safety

### Styling

- Use Tailwind utility classes consistently
- Follow the dark theme color palette defined in theme
- Maintain responsive design with `sm:`, `md:`, `lg:` breakpoints

### Performance

- Use React.memo() for expensive components
- Implement loading states for async operations
- Debounce/throttle frequent operations (search, scroll, resize)
