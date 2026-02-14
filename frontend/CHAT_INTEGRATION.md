# ChatWindow Integration Guide

## Overview

The **ChatWindow** component provides a context-sensitive AI chat interface for Kontali ERP modules. It's always visible as a floating button and expands to a 300px collapsible chat panel.

## Architecture

```
┌─────────────────────────────────────┐
│        ChatProvider                 │  ← Context provider
│  - module: string                   │
│  - selectedItems: string[]          │
│  - sendMessage()                    │
│  - messages[]                       │
│  - loading: boolean                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        ChatWindow                   │  ← UI Component
│  - Collapsible (icon ↔ 300px)      │
│  - Fixed bottom-right position      │
│  - Markdown rendering               │
│  - Typing indicator                 │
│  - Auto-focus                       │
│  - Last 10 messages                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Backend API                  │
│  POST /api/chat                     │
│  {                                  │
│    message: "...",                  │
│    context: {                       │
│      module: "review-queue",        │
│      selected_items: ["id-123"]     │
│    }                                │
│  }                                  │
└─────────────────────────────────────┘
```

## Quick Start

### 1. Wrap your module with ChatProvider

```typescript
// app/review-queue/page.tsx
import { ChatProvider } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';

export default function ReviewQueuePage() {
  return (
    <ChatProvider 
      initialModule="review-queue"
      clientId="your-client-id"
      userId="your-user-id"
    >
      <div className="relative min-h-screen">
        {/* Your module content */}
        <YourModuleContent />
        
        {/* Chat window - always at bottom right */}
        <ChatWindow />
      </div>
    </ChatProvider>
  );
}
```

### 2. Update context dynamically

```typescript
import { useChatContext } from '@/contexts/ChatContext';

function ReviewQueueContent() {
  const { setModule, setSelectedItems } = useChatContext();
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);

  // Update chat context when user selects invoices
  useEffect(() => {
    setSelectedItems(selectedInvoices);
  }, [selectedInvoices, setSelectedItems]);

  return (
    <div>
      {/* Your content */}
    </div>
  );
}
```

## ChatContext API

### Context Value

```typescript
interface ChatContextValue {
  module: string;                         // Current module name
  selectedItems: string[];                // IDs of selected items
  messages: ChatMessage[];                // Chat history
  loading: boolean;                       // Is AI responding?
  sendMessage: (msg: string) => Promise<void>;
  setModule: (module: string) => void;
  setSelectedItems: (items: string[]) => void;
  clearHistory: () => void;
}
```

### ChatMessage Structure

```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  action?: string;                        // Optional action type
  data?: Record<string, any>;             // Optional structured data
}
```

## Backend Integration

### API Endpoint Format

```json
POST /api/chat

Request:
{
  "message": "Post denne mot konto 4000",
  "context": {
    "module": "review-queue",
    "selected_items": ["invoice-uuid-123", "invoice-uuid-456"]
  },
  "client_id": "client-abc",
  "user_id": "user-xyz",
  "session_id": "session-123",
  "conversation_history": [
    {
      "role": "user",
      "content": "Vis fakturaer"
    },
    {
      "role": "assistant",
      "content": "Her er 3 fakturaer..."
    }
  ]
}

Response:
{
  "message": "✅ Bokført mot konto 4000\n\n**Detaljer:**\n- Faktura: INV-123\n- Beløp: 4500 NOK",
  "action": "booking_completed",
  "data": {
    "invoice_id": "invoice-uuid-123",
    "account": "4000"
  },
  "timestamp": "2025-02-14T13:30:00Z"
}
```

### Module Names Convention

- `review-queue` - Gjennomgangskø
- `bank-recon` - Bankavstemming
- `customer-invoices` - Kundefakturaer
- `supplier-invoices` - Leverandørfakturaer
- `general` - Generell hjelp

## UI Features

### 1. Collapsible Design

- **Minimized:** Floating button with icon (56x56px)
- **Expanded:** 300px height panel with full chat UI
- **Animation:** Smooth framer-motion transitions

### 2. Markdown Rendering

AI responses support markdown:
- **Bold** and *italic*
- Lists (ordered and unordered)
- `Inline code`
- Line breaks

### 3. Auto-focus

When AI responds, the input field automatically receives focus for quick follow-up.

### 4. Typing Indicator

Three animated dots show when AI is "thinking".

### 5. Message History

Shows last 10 messages (configurable in `displayMessages.slice(-10)`).

### 6. Notification Badge

Red badge appears when new AI message arrives while chat is minimized.

## Examples

### Example 1: Review Queue Integration

```typescript
// pages/review-queue/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { ChatProvider, useChatContext } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';
import InvoiceList from './InvoiceList';

function ReviewQueueContent() {
  const { setSelectedItems } = useChatContext();
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);

  // Sync selection with chat context
  useEffect(() => {
    setSelectedItems(selectedInvoices);
  }, [selectedInvoices, setSelectedItems]);

  return (
    <div>
      <h1>Gjennomgangskø</h1>
      <InvoiceList 
        selected={selectedInvoices}
        onSelectionChange={setSelectedInvoices}
      />
    </div>
  );
}

export default function ReviewQueuePage() {
  const clientId = useClient()?.id || 'default';
  const userId = useAuth()?.user?.id || 'default';

  return (
    <ChatProvider 
      initialModule="review-queue"
      clientId={clientId}
      userId={userId}
    >
      <ReviewQueueContent />
      <ChatWindow />
    </ChatProvider>
  );
}
```

### Example 2: Bank Reconciliation

```typescript
'use client';

import { ChatProvider, useChatContext } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';

function BankReconContent() {
  const { setModule, setSelectedItems } = useChatContext();
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);

  // Set module on mount
  useEffect(() => {
    setModule('bank-recon');
  }, [setModule]);

  // Update selected items
  useEffect(() => {
    setSelectedItems(selectedTransactions);
  }, [selectedTransactions, setSelectedItems]);

  return (
    <div>
      <h1>Bankavstemming</h1>
      {/* Your bank recon UI */}
    </div>
  );
}

export default function BankReconPage() {
  return (
    <ChatProvider initialModule="bank-recon">
      <BankReconContent />
      <ChatWindow />
    </ChatProvider>
  );
}
```

## Styling

Uses **Tailwind CSS** and **shadcn/ui** components:
- `Button`
- `Input`
- `Card`
- `ScrollArea`
- `Badge`

### Customization

To change colors, modify the gradient in `ChatWindow.tsx`:

```tsx
// Header gradient
className="bg-gradient-to-r from-blue-600 to-indigo-600"

// Button gradient
className="bg-gradient-to-r from-blue-600 to-indigo-600"
```

## Testing

### Run Demo

```bash
cd frontend
npm run dev
```

Navigate to: `http://localhost:3002/demo-chat`

### Test Checklist

- [ ] Chat expands/collapses smoothly
- [ ] Input field auto-focuses on AI response
- [ ] Markdown renders correctly
- [ ] Typing indicator shows during loading
- [ ] Last 10 messages display
- [ ] Context (module + selectedItems) updates correctly
- [ ] API receives proper payload
- [ ] Error handling works (shows error message)

## Performance

- **Token limit:** Last 9 messages sent as conversation history (configurable)
- **Render optimization:** Only last 10 messages rendered
- **Lazy loading:** Consider React.lazy for large modules

## Troubleshooting

### Chat not appearing

Check that:
1. `ChatProvider` wraps your component
2. `ChatWindow` is rendered inside the provider
3. No z-index conflicts (ChatWindow uses `z-50`)

### Context not updating

Ensure you call `setSelectedItems()` whenever selection changes:

```typescript
useEffect(() => {
  setSelectedItems(selectedInvoices);
}, [selectedInvoices, setSelectedItems]);
```

### API errors

Check:
1. `NEXT_PUBLIC_API_URL` environment variable
2. Backend `/api/chat` endpoint is running
3. CORS settings if backend is on different domain

## Future Enhancements

- [ ] Voice input support
- [ ] File attachments
- [ ] Conversation persistence (localStorage)
- [ ] Multi-language support
- [ ] Keyboard shortcuts (Ctrl+K to open)
- [ ] Chat templates per module
- [ ] Export conversation
- [ ] AI suggestions based on context

---

**Version:** 1.0  
**Last updated:** February 14, 2025  
**Maintainer:** AI ERP Team
