# 🏗️ Frontend Architecture Map - Fase 2

**Visual guide til komponenter og dataflyt**

---

## 📂 Fil-struktur

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home (MultiClientDashboard)
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Dashboard med DemoTestButton
│   │   ├── review-queue/
│   │   │   ├── page.tsx          # Review Queue route
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Review item detail (optional)
│   │   └── bank/
│   │       └── page.tsx          # Bank Reconciliation route
│   │
│   ├── components/               # Reusable components
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx     # Main layout wrapper ⚠️ ADD FLOATINGCHAT HERE
│   │   │   ├── Sidebar.tsx       # Left navigation
│   │   │   ├── Topbar.tsx        # Header bar
│   │   │   └── Breadcrumbs.tsx   # Navigation breadcrumbs
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx    # Chat UI container
│   │   │   ├── ChatMessage.tsx   # Message rendering
│   │   │   ├── ChatInput.tsx     # Input field ⚠️ ADD AUTOCOMPLETE
│   │   │   └── QuickActions.tsx  # Quick action buttons
│   │   │
│   │   ├── FloatingChat.tsx      # Chat button + modal ⚠️ NOT IN LAYOUT
│   │   │
│   │   ├── ReviewQueue.tsx       # Main review queue component
│   │   ├── ReviewQueueItem.tsx   # List item
│   │   ├── ReviewQueueDetail.tsx # Detail view
│   │   ├── FilterBar.tsx         # Search + filters
│   │   ├── ApproveButton.tsx     # Approve action
│   │   ├── CorrectButton.tsx     # Correct modal
│   │   ├── InvoiceDetails.tsx    # Invoice preview
│   │   ├── BookingDetails.tsx    # Booking entries
│   │   ├── PatternList.tsx       # Pattern suggestions
│   │   │
│   │   ├── BankReconciliation.tsx # Bank recon (monolithic)
│   │   │
│   │   ├── DemoTestButton.tsx    # Test data generator button
│   │   ├── DemoBanner.tsx        # Demo environment banner
│   │   └── ...
│   │
│   ├── api/                      # API integration layer
│   │   ├── review-queue.ts       # Review Queue API calls
│   │   ├── chat.ts               # Chat API calls
│   │   ├── audit.ts              # Audit trail
│   │   └── hovedbok.ts           # General ledger
│   │
│   ├── contexts/                 # React Context providers
│   │   ├── ClientContext.tsx     # Current client state
│   │   └── ViewModeContext.tsx   # View mode (accountant/client)
│   │
│   ├── types/                    # TypeScript types
│   │   └── review-queue.ts       # Review queue types
│   │
│   └── styles/
│       └── globals.css           # Global styles + Tailwind
│
├── public/                       # Static assets
├── package.json
├── next.config.js
└── tailwind.config.ts
```

---

## 🗺️ Component Hierarchy

```
RootLayout (layout.tsx)
├── ViewModeProvider
│   └── ClientProvider
│       ├── DemoBanner
│       └── AppLayout
│           ├── Sidebar
│           ├── Topbar
│           ├── Breadcrumbs
│           ├── Main Content
│           │   └── Page Component (via children)
│           │       ├── /dashboard → DashboardPage
│           │       │   ├── DemoTestButton
│           │       │   ├── ReceiptVerificationDashboard
│           │       │   └── TrustDashboard
│           │       │
│           │       ├── /review-queue → ReviewQueuePage
│           │       │   └── ReviewQueue
│           │       │       ├── FilterBar
│           │       │       ├── ReviewQueueItem[]
│           │       │       └── Detail Panel
│           │       │           ├── InvoiceDetails
│           │       │           ├── Tabs
│           │       │           │   ├── BookingDetails
│           │       │           │   ├── ChatInterface
│           │       │           │   └── PatternList
│           │       │           └── Actions
│           │       │               ├── ApproveButton
│           │       │               └── CorrectButton
│           │       │
│           │       └── /bank → BankReconciliationPage
│           │           └── BankReconciliation
│           │               ├── Stats Cards
│           │               ├── Actions Bar
│           │               └── Transactions Table
│           │
│           └── ⚠️ FloatingChat (MISSING - NEEDS TO BE ADDED)
│               └── ChatWindow
│                   ├── QuickActions
│                   ├── ChatMessage[]
│                   └── ChatInput
```

---

## 🔄 Data Flow

### Review Queue Flow

```
User Action
    ↓
ReviewQueue Component
    ↓
reviewQueueApi.getReviewItems()
    ↓
Axios → http://localhost:8000/api/review-queue/items?client_id=...
    ↓
Backend FastAPI
    ↓
PostgreSQL Database
    ↓
JSON Response
    ↓
ReviewQueue State Update
    ↓
UI Re-render
```

### Chat Flow

```
User types message
    ↓
ChatInput (onSend)
    ↓
ChatWindow.sendMessage()
    ↓
POST http://localhost:8000/api/chat-booking/message
    ↓
Backend AI Agent (Claude)
    ↓
Response with action + data
    ↓
ChatWindow state update
    ↓
ChatMessage rendered
```

### Bank Reconciliation Flow

```
User uploads CSV
    ↓
File input onChange
    ↓
FormData upload → POST /api/bank/import
    ↓
Backend parses CSV
    ↓
Transactions stored in DB
    ↓
Auto-matching triggered
    ↓
Response with stats
    ↓
UI shows toast notification
    ↓
fetchTransactions() + fetchStats()
    ↓
Table updates
```

---

## 🎨 Styling System

### Tailwind Configuration

```javascript
// tailwind.config.ts
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom colors
        'accent-blue': '#3B82F6',
        'dark-card': '#1F2937',
        'dark-border': '#374151',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: 'hsl(var(--primary))',
        // ... more
      },
      fontFamily: {
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
};
```

### Component Styling Patterns

```tsx
// Standard card
<div className="bg-dark-card border border-dark-border rounded-lg p-6">

// Button
<button className="px-4 py-2 bg-accent-blue hover:bg-blue-600 text-white rounded-lg transition-colors">

// Badge
<span className="px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">

// Loading spinner
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
```

---

## 📡 API Endpoints Used

### Review Queue
```
GET    /api/review-queue/items?client_id=...
GET    /api/review-queue/items/:id
POST   /api/review-queue/items/:id/approve
POST   /api/review-queue/items/:id/correct
POST   /api/review-queue/items/:id/chat
GET    /api/review-queue/items/:id/chat
```

### Chat
```
POST   /api/chat-booking/message
GET    /api/chat/history?client_id=...
GET    /api/chat/health
```

### Bank Reconciliation
```
GET    /api/bank/transactions?client_id=...&status=...
GET    /api/bank/reconciliation/stats?client_id=...
POST   /api/bank/import?client_id=...
POST   /api/bank/auto-match?client_id=...
GET    /api/bank/transactions/:id/suggestions?client_id=...
POST   /api/bank/transactions/:id/match?client_id=...&invoice_id=...
```

### Demo System
```
GET    /demo/status
POST   /demo/run-test
GET    /demo/task/:taskId
```

---

## 🔐 Context & State Management

### ClientContext
```tsx
// Provides current client info globally
const { currentClient, setCurrentClient } = useClient();

// Used by:
- Topbar (client selector)
- API calls (client_id parameter)
- FloatingChat (clientId prop)
```

### ViewModeContext
```tsx
// Accountant vs Client view mode
const { viewMode, setViewMode } = useViewMode();

// Used by:
- Sidebar (conditional menu items)
- Dashboard (different widgets)
```

### Local Component State
```tsx
// ReviewQueue.tsx
const [items, setItems] = useState<ReviewItem[]>([]);
const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null);
const [loading, setLoading] = useState(true);

// BankReconciliation.tsx
const [transactions, setTransactions] = useState<BankTransaction[]>([]);
const [stats, setStats] = useState<BankStats | null>(null);
const [selectedTransaction, setSelectedTransaction] = useState<string | null>(null);

// ChatWindow.tsx
const [messages, setMessages] = useState<Message[]>([]);
const [sessionId, setSessionId] = useState<string>('');
```

---

## 🎭 Animation System (Framer Motion)

### Page Transitions
```tsx
// AppLayout.tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.2 }}
>
  {children}
</motion.div>
```

### FloatingChat
```tsx
<motion.button
  whileHover={{ scale: 1.1 }}
  whileTap={{ scale: 0.9 }}
>
  💬
</motion.button>

<motion.div
  initial={{ opacity: 0, y: 20, scale: 0.95 }}
  animate={{ opacity: 1, y: 0, scale: 1 }}
  exit={{ opacity: 0, y: 20, scale: 0.95 }}
>
  <ChatWindow />
</motion.div>
```

### Bank Transactions
```tsx
<motion.tr
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
>
  {/* transaction row */}
</motion.tr>
```

---

## 🧩 Third-Party Libraries

| Library | Purpose | Used In |
|---------|---------|---------|
| Next.js 14 | Framework | App Router, SSR |
| React 18 | UI library | All components |
| TypeScript | Type safety | Everything |
| Tailwind CSS | Styling | All components |
| Framer Motion | Animations | Page transitions, FloatingChat, etc. |
| Shadcn UI | Component library | DemoTestButton (Dialog, Progress) |
| Lucide React | Icons | Topbar, buttons |
| Axios | HTTP client | API calls |
| date-fns | Date formatting | Timestamps |

### Recommended Additions:
- **Sonner** - Toast notifications (to replace alerts)
- **React Hook Form** - Form management
- **Zod** - Runtime validation

---

## 🔍 Performance Considerations

### Current Implementation

**Good:**
- ✅ Server-side rendering (Next.js)
- ✅ Code splitting per route
- ✅ Lazy loading with Suspense boundaries (implicit)
- ✅ Debounced polling (30s intervals)
- ✅ Conditional rendering (loading states)

**Could Improve:**
- ⚠️ No React Query / SWR (caching, revalidation)
- ⚠️ No pagination on long lists
- ⚠️ No virtualization for large tables
- ⚠️ No image optimization (not needed yet)

### Optimization Recommendations:

```tsx
// Add React Query for better data management
import { useQuery } from '@tanstack/react-query';

const { data, isLoading } = useQuery({
  queryKey: ['review-items', clientId],
  queryFn: () => reviewQueueApi.getReviewItems(),
  refetchInterval: 30000, // Auto-refetch
});

// Add pagination
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['transactions'],
  queryFn: ({ pageParam = 0 }) => fetchTransactions(pageParam),
  getNextPageParam: (lastPage) => lastPage.nextCursor,
});

// Add virtualization for large lists
import { useVirtualizer } from '@tanstack/react-virtual';
```

---

## 📦 Build & Deploy

### Development
```bash
npm run dev          # Start dev server (port 3002)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint
npm run type-check   # TypeScript check
```

### Environment Variables
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development
```

### Production Build Size
```
Route (app)                              Size     First Load JS
┌ ○ /                                    5.2 kB         92.1 kB
├ ○ /bank                                3.8 kB         90.7 kB
├ ○ /dashboard                           8.1 kB         95.0 kB
└ ○ /review-queue                        6.5 kB         93.4 kB

○  (Static)  prerendered as static content
```

---

## 🧪 Testing Strategy

### Unit Tests (Recommended)
```tsx
// ReviewQueue.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewQueue } from '@/components/ReviewQueue';

test('displays review items', async () => {
  render(<ReviewQueue />);
  expect(screen.getByText('Review Queue')).toBeInTheDocument();
  // ...
});
```

### E2E Tests (Recommended)
```typescript
// e2e/review-queue.spec.ts
import { test, expect } from '@playwright/test';

test('approve invoice workflow', async ({ page }) => {
  await page.goto('/review-queue');
  await page.click('[data-testid="approve-button"]');
  await expect(page.locator('.toast')).toContainText('Approved');
});
```

---

**Sist oppdatert:** 2026-02-08 14:43 UTC  
**Versjon:** Fase 2 (post-implementation)  
**Neste review:** Post-fixes
