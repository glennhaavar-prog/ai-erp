# ChatWindow - Quick Reference 🚀

## 30-Second Integration

```typescript
// 1. Wrap your page with ChatProvider
import { ChatProvider } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';

export default function YourPage() {
  return (
    <ChatProvider initialModule="your-module" clientId="client-id">
      <YourContent />
      <ChatWindow />
    </ChatProvider>
  );
}

// 2. Update context when selection changes
import { useChatContext } from '@/contexts/ChatContext';

function YourContent() {
  const { setSelectedItems } = useChatContext();
  
  useEffect(() => {
    setSelectedItems(selectedIds);
  }, [selectedIds, setSelectedItems]);
  
  return <div>Your UI</div>;
}
```

## Test It Now

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
npm run dev
```

Open: `http://localhost:3002/demo-chat`

## What You Get

✅ Fixed chat button (bottom-right)  
✅ Expands to 300px panel  
✅ Markdown-formatted AI responses  
✅ Auto-focus after AI replies  
✅ Context-aware (module + selected items)  
✅ Last 10 messages history  
✅ Typing indicator  
✅ Smooth animations  

## API Format

**POST /api/chat**

```json
{
  "message": "User message",
  "context": {
    "module": "review-queue",
    "selected_items": ["id-1", "id-2"]
  }
}
```

## Files

- `src/contexts/ChatContext.tsx` - Context provider
- `src/components/ChatWindow.tsx` - UI component
- `app/demo-chat/page.tsx` - Demo page
- `CHAT_INTEGRATION.md` - Full docs

## Module Names

- `review-queue` - Gjennomgangskø
- `bank-recon` - Bankavstemming
- `customer-invoices` - Kundefakturaer
- `supplier-invoices` - Leverandørfakturaer
- `general` - Generell hjelp

## Customization

### Change colors:
```tsx
// In ChatWindow.tsx line ~80
className="bg-gradient-to-r from-blue-600 to-indigo-600"
```

### Change height:
```tsx
// In ChatWindow.tsx line ~60
animate={{ height: 300, opacity: 1 }}
```

### Show more messages:
```tsx
// In ChatWindow.tsx line ~112
const displayMessages = messages.slice(-10);
```

## Next Steps

1. ✅ Demo works → Test at `/demo-chat`
2. 🔧 Integrate → Add to your module
3. 🔌 Backend → Implement `/api/chat` endpoint
4. 🎨 Customize → Colors, height, position

---

**Full docs:** `CHAT_INTEGRATION.md`  
**Testing guide:** `CHATWINDOW_README.md`
