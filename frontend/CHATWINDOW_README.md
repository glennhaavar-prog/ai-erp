# ChatWindow Component - Testing Guide

## 🎯 What Was Built

A fully functional, context-sensitive chat window component for Kontali ERP modules with:

✅ **ChatContext Provider** - Manages module context and selected items  
✅ **Collapsible ChatWindow** - Fixed position, expandable from icon to 300px panel  
✅ **Markdown Rendering** - AI responses support rich formatting  
✅ **Auto-focus** - Input focuses automatically after AI response  
✅ **Typing Indicator** - Animated dots during AI thinking  
✅ **Message History** - Shows last 10 messages  
✅ **API Integration** - POST to `/api/chat` with full context  
✅ **Demo Pages** - Two working examples  
✅ **Full Documentation** - Integration guide included  

## 🚀 Quick Start

### 1. Install Dependencies (if needed)

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend
npm install
```

All dependencies are already in `package.json`:
- `react-markdown` - For rendering AI responses
- `framer-motion` - For smooth animations
- `lucide-react` - For icons
- shadcn/ui components (already configured)

### 2. Run Development Server

```bash
npm run dev
```

Server starts at: `http://localhost:3002`

### 3. Test the Demo Pages

#### Demo 1: Basic Chat Demo
**URL:** `http://localhost:3002/demo-chat`

Features:
- Module selector (Review Queue, Bank Recon, General)
- Mock invoice selection
- Context display
- Full chat functionality

#### Demo 2: Integrated Review Queue
**URL:** `http://localhost:3002/review-queue-with-chat`

Features:
- Realistic review queue interface
- Checkbox selection
- Select all/none
- Auto-syncs selection with chat context

## 📁 Files Created

```
ai-erp/frontend/
├── src/
│   ├── contexts/
│   │   ├── ChatContext.tsx          ✨ NEW - Context provider
│   │   └── index.ts                 ✏️  Updated exports
│   │
│   ├── components/
│   │   ├── ChatWindow.tsx           ✨ NEW - Main component
│   │   └── chat/
│   │       └── index.ts             ✏️  Updated with notes
│   │
│   └── app/
│       ├── demo-chat/
│       │   └── page.tsx             ✨ NEW - Demo page
│       │
│       └── review-queue-with-chat/
│           └── page.tsx             ✨ NEW - Integration example
│
├── CHAT_INTEGRATION.md              ✨ NEW - Full documentation
└── CHATWINDOW_README.md             ✨ NEW - This file
```

## 🧪 Testing Checklist

### Visual Tests

- [ ] Chat button appears bottom-right corner
- [ ] Button expands to 300px height panel smoothly
- [ ] Panel has gradient header (blue to indigo)
- [ ] Messages display correctly (user right, AI left)
- [ ] Markdown renders (bold, lists, code blocks)
- [ ] Typing indicator shows 3 bouncing dots
- [ ] Input field and send button work
- [ ] Scroll area works for long conversations
- [ ] Panel collapses smoothly back to button

### Functional Tests

- [ ] Typing in input field works
- [ ] Send button sends message
- [ ] Enter key sends message
- [ ] Can't send empty messages
- [ ] Loading state disables input
- [ ] Auto-focus after AI response works
- [ ] Last 10 messages display correctly
- [ ] Notification badge shows on new AI message (when minimized)

### Context Tests

- [ ] Module selector updates context
- [ ] Selected items update context
- [ ] Context is sent in API request
- [ ] Multiple selections work correctly
- [ ] Clearing selection updates context

### API Tests

Check browser console (F12) → Network tab:

- [ ] POST request to `/api/chat`
- [ ] Request includes `message`, `context`, `client_id`, `user_id`, `session_id`
- [ ] Context includes `module` and `selected_items`
- [ ] Conversation history included (last 9 messages)
- [ ] Response message displays correctly

## 🎨 UI Features Demo

### Test Message Formats

Try these messages in the chat to test markdown rendering:

```
1. "This is **bold** and *italic* text"

2. "Here's a list:
   - Item one
   - Item two
   - Item three"

3. "Code example: `const x = 42;`"

4. "Multi-line message
   with line breaks
   works great!"
```

### Test Context

1. Select different modules → Check context display
2. Select/deselect items → Check selected_items array
3. Send message → Check API payload in Network tab

## 🔧 Customization

### Change Colors

Edit `/home/ubuntu/.openclaw/workspace/ai-erp/frontend/src/components/ChatWindow.tsx`:

```tsx
// Line ~80: Header gradient
className="bg-gradient-to-r from-blue-600 to-indigo-600"

// Change to green theme:
className="bg-gradient-to-r from-green-600 to-emerald-600"
```

### Change Height

```tsx
// Line ~60: Expanded height
animate={{ height: 300, opacity: 1 }}

// Make it taller:
animate={{ height: 500, opacity: 1 }}
```

### Change Message Limit

```tsx
// Line ~112: Message history limit
const displayMessages = messages.slice(-10);

// Show 20 messages:
const displayMessages = messages.slice(-20);
```

### Change Position

```tsx
// Line ~61: Fixed position
className="fixed bottom-16 right-6 w-96 z-50"

// Move to left side:
className="fixed bottom-16 left-6 w-96 z-50"
```

## 🐛 Troubleshooting

### Chat button doesn't appear

1. Check that `ChatProvider` wraps your component
2. Check that `ChatWindow` is rendered
3. Check z-index conflicts (ChatWindow uses `z-50`)

### Context not updating

Ensure you call `setSelectedItems()` in `useEffect`:

```typescript
const { setSelectedItems } = useChatContext();

useEffect(() => {
  setSelectedItems(selectedInvoices);
}, [selectedInvoices, setSelectedItems]);
```

### API errors (404 or 500)

1. Check backend is running: `http://localhost:8000/api/chat/health`
2. Check `NEXT_PUBLIC_API_URL` environment variable
3. Check browser console for error details

### Markdown not rendering

Check that `react-markdown` is installed:

```bash
npm list react-markdown
# Should show: react-markdown@10.1.0
```

## 📚 Documentation

Full integration guide: `CHAT_INTEGRATION.md`

Includes:
- Architecture overview
- API format details
- Module naming conventions
- Integration examples
- Advanced customization
- Performance tips

## 🎯 Next Steps

### For Backend Integration

1. Implement `/api/chat` endpoint
2. Parse `context.module` and `context.selected_items`
3. Return markdown-formatted responses
4. Optional: Add `action` and `data` fields for structured responses

### For Production Use

1. Replace mock data with real API calls
2. Add authentication (pass real `client_id` and `user_id`)
3. Persist conversation history (localStorage or database)
4. Add error boundary for graceful error handling
5. Add loading skeletons
6. Add file upload support (already in `/components/chat/FileUpload.tsx`)

### Suggested Enhancements

- [ ] Keyboard shortcut (Ctrl+K) to open chat
- [ ] Voice input button
- [ ] Export conversation as PDF
- [ ] Chat templates per module
- [ ] Dark mode support
- [ ] Multi-language support
- [ ] Conversation search

## ✅ Success Criteria

You know it's working when:

1. ✅ Click chat button → Panel expands smoothly
2. ✅ Type message + Enter → Message sends
3. ✅ AI response shows with markdown formatting
4. ✅ Input auto-focuses after AI response
5. ✅ Select items → Context updates in API request
6. ✅ Switch modules → Module name changes in context

## 📞 Support

- Documentation: `CHAT_INTEGRATION.md`
- Example: `app/review-queue-with-chat/page.tsx`
- Context API: `contexts/ChatContext.tsx`
- Component: `components/ChatWindow.tsx`

---

**Version:** 1.0  
**Built:** February 14, 2025  
**Framework:** Next.js 14 + React 18 + TypeScript  
**UI:** Tailwind CSS + shadcn/ui  
**Animations:** Framer Motion  
**Time Spent:** ~3 hours ⏱️
