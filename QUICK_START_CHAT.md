# 🚀 Chat Interface - Quick Start

## Access
👉 **http://localhost:3000/chat**

## Try These Commands

### In Mock Mode (🎭)
```
help
show reviews
status
approve abc12345
reject def45678 Wrong amount
```

### In API Mode (🔌)
```
show review queue
what's my workload?
approve [item-id]
reject [item-id] because [reason]
```

## Toggle Modes
- **🎭 Mock**: Client-side with sample data
- **🔌 API**: Real backend with database

## Files
- Component: `/frontend/src/components/IntegratedChatReview.tsx`
- Page: `/frontend/src/app/chat/page.tsx`
- API Client: `/frontend/src/api/chat.ts`

## Docs
- `CHAT_INTEGRATION_COMPLETE.md` - Full report
- `SUBAGENT_CHAT_SUMMARY.md` - Executive summary
- `CHAT_INTEGRATION_README.md` - Implementation guide

## Status
✅ Complete and ready for testing!
