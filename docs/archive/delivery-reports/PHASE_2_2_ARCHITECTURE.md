# Phase 2.2: AI Chat System Architecture

**Date:** February 8, 2026  
**Status:** ✅ COMPLETE

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Frontend (React/Next.js) - Port 3002                      │     │
│  │                                                             │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │     │
│  │  │ FloatingChat │  │  ChatWindow  │  │ ChatMessage  │     │     │
│  │  │   (💬 btn)   │  │  (Container) │  │  (Display)   │     │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │     │
│  │         │                 │                                │     │
│  │  ┌──────┴─────────────────┴─────┐  ┌──────────────┐       │     │
│  │  │      ChatInput                │  │ QuickActions │       │     │
│  │  │  (Autocomplete, Command /)   │  │  (Buttons)   │       │     │
│  │  └──────────────────────────────┘  └──────────────┘       │     │
│  └─────────────────────────│───────────────────────────────┘     │
│                            │ HTTP POST /api/chat-booking/message  │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND API (FastAPI) - Port 8000               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Chat Booking Router (/api/chat-booking/*)                   │   │
│  │                                                               │   │
│  │  POST /message         GET /history/{id}                     │   │
│  │  DELETE /session/{id}  GET /suggestions                      │   │
│  │  GET /health                                                 │   │
│  └───────────────────────────┬──────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              CHAT SERVICE (Main Orchestrator)                │   │
│  │                                                               │   │
│  │  • Process incoming message                                  │   │
│  │  • Manage conversation flow                                  │   │
│  │  • Coordinate between components                             │   │
│  │  • Generate responses                                        │   │
│  └───────┬──────────────────────────────┬───────────────────────┘   │
│          │                              │                           │
│          ▼                              ▼                           │
│  ┌──────────────────┐          ┌──────────────────┐                │
│  │ INTENT           │          │ CONTEXT          │                │
│  │ CLASSIFIER       │          │ MANAGER          │                │
│  │                  │          │                  │                │
│  │ • Claude API     │          │ • Session store  │                │
│  │ • NLP processing │          │ • History (10)   │                │
│  │ • Entity extract │          │ • Current invoice│                │
│  │ • Confidence     │          │ • Pending confirm│                │
│  │ • Fallback       │          │ • 30min expiry   │                │
│  └─────────┬────────┘          └──────────────────┘                │
│            │                                                        │
│            ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              ACTION HANDLERS (Intent Router)                │   │
│  │                                                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           │   │
│  │  │ Booking    │  │ Status     │  │ Approval   │           │   │
│  │  │ Handler    │  │ Handler    │  │ Handler    │           │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │   │
│  │        │               │               │                   │   │
│  │  ┌─────┴───────────────┴───────────────┴──────┐            │   │
│  │  │          Correction Handler                 │            │   │
│  │  └─────────────────────┬────────────────────────┘            │   │
│  └────────────────────────┼─────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │            EXISTING SERVICES & AGENTS                        │   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│  │  │ InvoiceAgent │  │ BookingService│ │ ReviewQueue  │       │   │
│  │  │              │  │              │  │              │       │   │
│  │  │ • AI analysis│  │ • GL posting │  │ • Approval   │       │   │
│  │  │ • Account ID │  │ • Voucher #  │  │ • Rejection  │       │   │
│  │  │ • Confidence │  │ • Balance    │  │ • Queue mgmt │       │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘   │
└────────────┼──────────────────┼──────────────────┼───────────────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                     │
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │  PostgreSQL Database │  │   External APIs      │                │
│  │                      │  │                      │                │
│  │ • VendorInvoice      │  │ • Claude/Anthropic   │                │
│  │ • GeneralLedger      │  │ • AWS Textract       │                │
│  │ • ReviewQueue        │  │ • AWS S3             │                │
│  │ • Vendor             │  │                      │                │
│  │ • Client             │  │                      │                │
│  └──────────────────────┘  └──────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Message Flow

### 1. User Sends Message

```
User types: "Bokfør faktura INV-12345"
                ↓
          ChatInput
                ↓
         ChatWindow.sendMessage()
                ↓
     POST /api/chat-booking/message
         {
           message: "Bokfør faktura INV-12345",
           client_id: "uuid",
           session_id: "uuid"
         }
```

### 2. Backend Processing

```
         ChatService.process_message()
                ↓
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
ContextManager         IntentClassifier
    │                       │
    │ Update context        │ Call Claude API
    │ Add to history        │ Extract entities
    │                       │
    └───────────┬───────────┘
                ▼
         Intent: book_invoice
         Entities: {invoice_number: "INV-12345"}
                ↓
    BookingActionHandler.handle_book_invoice()
                ↓
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
InvoiceAgent           Database Query
    │                       │
    │ AI analysis           │ SELECT invoice...
    │ Suggest booking       │
    │                       │
    └───────────┬───────────┘
                ▼
    Generate response with preview
                ↓
    Set pending confirmation in context
                ↓
    Return response to frontend
```

### 3. Frontend Display

```
    ChatWindow receives response
                ↓
    Add assistant message to state
                ↓
    ChatMessage renders markdown
                ↓
    User sees:
    
    📄 Faktura INV-12345
    • Leverandør: Telenor
    • Beløp: 5,000 kr
    
    Foreslått bokføring (95%):
    • Konto 6340: 4,000 kr
    • Konto 2740: 1,000 kr
    • Konto 2400: 5,000 kr
    
    Bokfør nå? (ja/nei)
```

### 4. User Confirmation

```
User types: "ja"
                ↓
    POST /api/chat-booking/message
         {message: "ja", ...}
                ↓
    ChatService detects pending confirmation
                ↓
    BookingActionHandler.execute_booking()
                ↓
    BookingService.post_to_general_ledger()
                ↓
    Database: INSERT INTO general_ledger...
                ↓
    Return success response
                ↓
    User sees: ✅ Faktura bokført på bilag AP-000123
```

---

## 🧩 Component Details

### Frontend Components

#### FloatingChat.tsx
```typescript
Props: {
  clientId: string,
  userId?: string
}

State: {
  isOpen: boolean
}

Features:
- Animated toggle button (💬)
- Floating modal container
- Pass props to ChatWindow
```

#### ChatWindow.tsx
```typescript
Props: {
  clientId: string,
  userId?: string
}

State: {
  messages: Message[],
  loading: boolean,
  sessionId: string
}

Features:
- Session management
- API communication
- Message history
- Auto-scroll
- Welcome message
```

#### ChatMessage.tsx
```typescript
Props: {
  role: 'user' | 'assistant',
  content: string,
  action?: string,
  data?: any
}

Features:
- Markdown rendering (react-markdown)
- Emoji support
- Conditional styling (user vs AI)
- Rich data display
```

#### ChatInput.tsx
```typescript
State: {
  message: string,
  showSuggestions: boolean,
  selectedIndex: number
}

Features:
- Text input
- Command palette (/)
- Keyboard navigation
- Send button
- Loading state
```

#### QuickActions.tsx
```typescript
Props: {
  onAction: (message: string) => void
}

Features:
- 4 quick action buttons
- Collapsible
- Color-coded
- Grid layout
```

---

### Backend Components

#### ChatService (chat_service.py)
```python
Methods:
- process_message(db, session_id, client_id, user_id, message)
- _handle_confirmation(...)
- _route_intent(...)
- _handle_help()

Responsibilities:
- Main orchestrator
- Message flow coordination
- Context management
- Response generation
```

#### IntentClassifier (intent_classifier.py)
```python
Methods:
- classify(message, context)
- _classify_with_claude(message, context)
- _fallback_classify(message)

Responsibilities:
- NLP with Claude API
- Intent detection (8+ intents)
- Entity extraction
- Confidence scoring
- Fallback to keywords
```

#### ContextManager (context_manager.py)
```python
Methods:
- get_context(session_id)
- update_context(session_id, **kwargs)
- add_message(session_id, role, content, metadata)
- get_pending_confirmation(session_id)
- set_pending_confirmation(session_id, action, data, question)
- clear_pending_confirmation(session_id)

Responsibilities:
- Session storage (in-memory)
- Conversation history (last 10)
- Current invoice tracking
- Pending confirmation handling
- Auto-expiration (30 min)
```

#### ActionHandlers (action_handlers.py)
```python
Classes:
- BookingActionHandler
- StatusQueryHandler
- ApprovalHandler
- CorrectionHandler

Methods (BookingActionHandler):
- handle_book_invoice(db, client_id, entities, context)
- analyze_invoice(db, invoice_id)
- book_invoice(db, invoice_id, user_id)

Methods (StatusQueryHandler):
- get_invoice_status(db, client_id, entities)
- get_overall_status(db, client_id)
- list_pending_invoices(db, client_id, entities)

Methods (ApprovalHandler):
- handle_approval(db, entities, context)

Methods (CorrectionHandler):
- handle_correction(db, entities, context)

Responsibilities:
- Execute actions based on intent
- Call appropriate services
- Format responses
- Handle errors
```

---

## 🔐 Security Architecture

```
Request
   ↓
┌──────────────────────┐
│ API Endpoint         │
│ • UUID validation    │
│ • Pydantic models    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ ChatService          │
│ • Session isolation  │
│ • Context validation │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Action Handlers      │
│ • Input sanitization │
│ • Read-only by default│
│ • No delete ops      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Database Layer       │
│ • SQLAlchemy ORM     │
│ • SQL injection safe │
│ • Audit logging      │
└──────────────────────┘
```

**Security Layers:**
1. **Input validation** - UUID format, Pydantic schemas
2. **Session isolation** - Per-client context separation
3. **No destructive ops** - Delete operations not exposed
4. **Audit trail** - All actions logged with timestamp
5. **SQL injection protection** - SQLAlchemy ORM
6. **Context expiration** - Auto-cleanup after 30 min

---

## 📊 Data Flow

### Session Context Structure
```python
{
    'session_id': 'uuid',
    'client_id': 'uuid',
    'user_id': 'uuid | None',
    'current_invoice_id': 'uuid | None',
    'current_invoice_number': 'INV-12345 | None',
    'conversation_history': [
        {
            'role': 'user',
            'content': 'Bokfør faktura INV-12345',
            'timestamp': '2026-02-08T13:00:00Z'
        },
        {
            'role': 'assistant',
            'content': '📄 Faktura INV-12345...',
            'timestamp': '2026-02-08T13:00:01Z',
            'metadata': {
                'action': 'book_invoice',
                'invoice_id': 'uuid'
            }
        }
    ],
    'last_intent': 'book_invoice',
    'pending_confirmation': {
        'action': 'book_invoice',
        'data': {'invoice_id': 'uuid'},
        'question': 'Bokfør nå? (ja/nei)'
    },
    'entities': {
        'invoice_number': 'INV-12345',
        'account_number': None
    },
    'last_activity': datetime
}
```

### Message Structure
```python
{
    'role': 'user' | 'assistant',
    'content': 'Message text',
    'timestamp': '2026-02-08T13:00:00Z',
    'action': 'book_invoice | status | help | ...',
    'data': {
        'success': True,
        'message': 'Response message',
        'invoice': {...},
        'booking': {...}
    }
}
```

---

## 🎯 Integration Points

### With Existing Systems

```
Chat System
    ↓
┌───────────────────────────────┐
│ Integration Layer             │
│                               │
│ ┌──────────┐ ┌──────────┐    │
│ │ Invoice  │ │ Booking  │    │
│ │ Agent    │ │ Service  │    │
│ └────┬─────┘ └────┬─────┘    │
│      │            │           │
│ ┌────┴─────┐ ┌────┴─────┐    │
│ │ Review   │ │ General  │    │
│ │ Queue    │ │ Ledger   │    │
│ └──────────┘ └──────────┘    │
└───────────────────────────────┘
    ↓
Database / External APIs
```

**Reused Services:**
- ✅ InvoiceAgent - AI analysis and booking suggestions
- ✅ BookingService - GL posting and voucher generation
- ✅ ReviewQueue API - Approval/rejection
- ✅ Database models - VendorInvoice, GeneralLedger, etc.

**No Duplication:** Chat system acts as a natural language interface layer on top of existing services.

---

## 📈 Scalability Considerations

### Current Architecture (MVP/Pilot)
```
Single Instance
    ↓
In-Memory Session Store
    ↓
Direct Database Connections
    ↓
Suitable for: 10-100 concurrent users
```

### Production Architecture (Recommended)
```
Load Balancer
    ↓
Multiple Backend Instances
    ↓
Redis Session Store
    ↓
Connection Pool (PgBouncer)
    ↓
Suitable for: 1,000+ concurrent users
```

**Migration Path:**
1. Keep current in-memory for pilot (Q1 2026)
2. Add Redis when scaling to 50+ users
3. Add load balancing when scaling to 200+ users
4. Add caching layer for frequently accessed data

---

## 🔄 Future Enhancements

### Phase 2.3 (Potential)
- WebSocket support for real-time updates
- Batch operations ("Bokfør alle med høy confidence")
- Advanced filtering ("Vis fakturaer fra Telenor siste uke")
- Voice input (Web Speech API)

### Phase 3 (Advanced)
- Multi-language support (English, Swedish, Danish)
- Learning system (improve from corrections)
- Report generation via chat
- Export functionality
- Notification system

---

## 🎉 Conclusion

**Phase 2.2 Chat System Architecture:**
- ✅ Clean separation of concerns
- ✅ Modular and extensible
- ✅ Integrates with existing services
- ✅ Security at every layer
- ✅ Scalable design
- ✅ Well-documented

**Status:** PRODUCTION-READY for pilot deployment

---

**Documented by:** AI Subagent (ai-chat-agent)  
**Date:** February 8, 2026  
**Status:** ✅ COMPLETE
