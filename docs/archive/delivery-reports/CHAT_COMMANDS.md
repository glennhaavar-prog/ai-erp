# Chat Commands Reference

This document describes all available commands for the Kontali AI Chat Assistant for invoice booking.

## Overview

The chat assistant provides a natural language interface for booking invoices, checking status, and managing the review queue. It maintains conversation context across messages, so you can have multi-turn conversations.

## Quick Start

Open the chat widget (💬 button in bottom-right corner) and try:

```
Vis meg fakturaer som venter
```

The assistant will show pending invoices. You can then say:

```
Bokfør faktura INV-12345
```

The assistant will analyze the invoice, suggest a booking, and ask for confirmation.

## Commands

### 1. Booking Commands

#### Book an Invoice

**Command:**
```
Bokfør denne faktura
Bokfør faktura INV-12345
Book invoice INV-12345
```

**What it does:**
1. Finds the invoice by invoice number or ID
2. Analyzes the invoice using AI
3. Suggests a booking with chart of accounts
4. Shows confidence score
5. Asks for confirmation ("Bokfør nå? ja/nei")

**Example conversation:**
```
You: Bokfør faktura INV-12345

AI: 📄 Faktura INV-12345

• Leverandør: Telenor Norge AS
• Beløp: 5,000 kr (ekskl mva: 4,000 kr, mva: 1,000 kr)

Foreslått bokføring (Confidence: 95%):

• Konto 6340: 4,000 kr (debet) - Telefon og internettkostnader
• Konto 2740: 1,000 kr (debet) - Inngående mva 25%
• Konto 2400: 5,000 kr (kredit) - Leverandørgjeld

Bokfør nå? (Svar 'ja' eller 'nei')

You: ja

AI: ✅ Faktura bokført på bilag AP-000123
```

#### Confirm Booking

**Command:**
```
ja
yes
ok
godkjenn
approve
```

**What it does:**
Executes the suggested booking and posts it to the general ledger.

#### Cancel Booking

**Command:**
```
nei
no
avbryt
cancel
```

**What it does:**
Cancels the current action without making changes.

---

### 2. Query Commands

#### Show Invoice Details

**Command:**
```
Vis meg faktura INV-12345
Show invoice INV-12345
Faktura INV-12345
```

**What it does:**
Displays detailed information about a specific invoice including:
- Vendor
- Amount
- Date
- Status (pending/booked)
- Voucher number (if booked)

**Example:**
```
You: Vis meg faktura INV-12345

AI: 📄 Faktura INV-12345

• Leverandør: Acme Consulting AS
• Beløp: 15,000 kr
• Dato: 2024-01-15
• Status: auto_approved
• Bokført: Ja ✓
• Bilag: AP-000098
```

#### List Pending Invoices

**Command:**
```
Vis meg fakturaer som venter
List pending invoices
Fakturaer som venter
Hvilke fakturaer må jeg behandle?
```

**What it does:**
Shows a list of invoices that are not yet booked.

**Example:**
```
You: Vis meg fakturaer som venter

AI: 📋 5 fakturaer venter på bokføring:

1. INV-12345 - Telenor Norge AS - 5,000 kr
2. INV-12346 - Equinor ASA - 125,000 kr
3. INV-12347 - Konsulent AS - 15,000 kr
4. INV-12348 - Office Supplies - 2,500 kr
5. INV-12349 - Cloud Services - 8,900 kr
```

#### List Low Confidence Invoices

**Command:**
```
Vis meg fakturaer med lav confidence
Show low confidence invoices
Fakturaer som trenger gjennomgang
```

**What it does:**
Filters and shows invoices that have low AI confidence scores (< 70%) and may need manual review.

**Example:**
```
You: Vis meg fakturaer med lav confidence

AI: 📋 3 fakturaer med lav confidence:

1. INV-99999 - Acme Consulting - 15,000 kr (confidence: 45%)
2. INV-88888 - Unknown Vendor - 8,500 kr (confidence: 38%)
3. INV-77777 - Consulting Services - 12,000 kr (confidence: 52%)

Klikk for å se detaljer...
```

---

### 3. Status Commands

#### Overall Status

**Command:**
```
Hva er status på alle fakturaer?
Status oversikt
Overall status
Hvor mange fakturaer har jeg?
```

**What it does:**
Shows statistics about all invoices:
- Total invoices
- Pending (not booked)
- Booked today
- In review queue

**Example:**
```
You: Hva er status på alle fakturaer?

AI: 📊 Status oversikt

• Total fakturaer: 156
• ⏳ Venter på bokføring: 12
• ✅ Bokført i dag: 8
• ⚠️ I Review Queue: 3
```

#### Invoice Status

**Command:**
```
Status for faktura INV-12345
Hva er status på faktura INV-12345?
```

**What it does:**
Shows status for a specific invoice.

---

### 4. Approval Commands

#### Approve Booking

**Command:**
```
Godkjenn bokføring for faktura INV-12345
Approve booking for INV-12345
Godkjenn
```

**What it does:**
Approves a booking that is in the review queue (items flagged for manual review).

**Example:**
```
You: Godkjenn bokføring for faktura INV-12345

AI: ✅ Bokføring godkjent!
```

---

### 5. Correction Commands

#### Correct Account

**Command:**
```
Korriger bokføring: bruk konto 6300 i stedet
Correct booking: use account 6340
Endre til konto 6340
```

**What it does:**
Modifies the account number in a booking. This requires a current invoice in context (you must have viewed or discussed an invoice in the current session).

**Example:**
```
You: Vis meg faktura INV-12345

AI: [shows invoice details]

You: Korriger bokføring: bruk konto 6300 i stedet

AI: ✅ Konto korrigert: 6340 → 6300
```

---

### 6. Help Command

**Command:**
```
help
hjelp
?
kommandoer
commands
```

**What it does:**
Shows a list of available commands with examples.

---

## Context Awareness

The chat maintains context across messages in a session:

### Current Invoice Context

When you view or discuss an invoice, it becomes the "current invoice" in context:

```
You: Vis meg faktura INV-12345
AI: [shows invoice details]

You: Bokfør denne
AI: [books the current invoice INV-12345]
```

### Conversation History

The chat remembers your last 10 messages, so it can understand follow-up questions:

```
You: Vis meg fakturaer som venter
AI: [shows 5 pending invoices]

You: Bokfør den første
AI: [books the first invoice from the list]
```

### Pending Confirmations

When the AI asks for confirmation, your next message is interpreted as yes/no:

```
AI: Bokfør nå? (ja/nei)
You: ja
AI: ✅ Faktura bokført
```

---

## Quick Actions

The chat window includes quick action buttons for common commands:

- **Fakturaer som venter** → "Vis meg fakturaer som venter"
- **Status oversikt** → "Hva er status på alle fakturaer?"
- **Lav confidence** → "Vis meg fakturaer med lav confidence"
- **Hjelp** → "help"

Click these buttons instead of typing for faster access.

---

## Tips

### 1. Use Natural Language

The AI understands natural Norwegian and English:

✅ "Kan du vise meg hvilke fakturaer som venter?"
✅ "Show me pending invoices"
✅ "fakturaer som venter"

All work the same way.

### 2. Use Command Palette

Press `/` in the chat input to open the command palette with suggestions. Use arrow keys to navigate and Enter/Tab to select.

### 3. Session Management

Each chat window maintains its own session. Context is preserved as long as the window is open. If you close and reopen the chat, a new session starts.

To clear context manually:
```
DELETE /api/chat-booking/session/{session_id}
```

### 4. Error Handling

If something goes wrong, the AI will tell you:

```
You: Bokfør faktura XYZ-999

AI: ❌ Fant ingen faktura XYZ-999
```

You can then correct your message or ask for help.

---

## API Integration

Frontend developers can integrate with the chat API:

### Send Message

```typescript
POST /api/chat-booking/message
{
  "message": "Bokfør faktura INV-12345",
  "client_id": "uuid",
  "user_id": "uuid",  // optional
  "session_id": "uuid"  // optional, auto-generated if not provided
}

Response:
{
  "message": "AI response text",
  "action": "book_invoice",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": "uuid"
}
```

### Get History

```typescript
GET /api/chat-booking/history/{session_id}

Response:
{
  "session_id": "uuid",
  "message_count": 5,
  "history": [ ... ],
  "current_invoice": "INV-12345",
  "last_intent": "book_invoice"
}
```

### Get Suggestions

```typescript
GET /api/chat-booking/suggestions

Response:
{
  "suggestions": [
    {
      "command": "Bokfør denne faktura",
      "description": "Start bokføring av en faktura",
      "category": "booking"
    },
    ...
  ]
}
```

---

## Intents

The chat classifies messages into these intents:

| Intent | Description | Example |
|--------|-------------|---------|
| `book_invoice` | Book an invoice | "Bokfør faktura INV-12345" |
| `show_invoice` | Show invoice details | "Vis meg faktura INV-12345" |
| `invoice_status` | Query invoice status | "Hva er status?" |
| `approve_booking` | Approve a booking | "Godkjenn" |
| `correct_booking` | Correct account | "Bruk konto 6340" |
| `list_invoices` | List invoices | "Vis fakturaer som venter" |
| `help` | Request help | "help" |
| `general` | General question | "Hvordan fungerer dette?" |

---

## Future Enhancements

Planned features:

- **Batch operations:** "Bokfør alle fakturaer med høy confidence"
- **Filters:** "Vis fakturaer fra Telenor"
- **Date ranges:** "Vis fakturaer fra siste uke"
- **Bulk approval:** "Godkjenn alle i review queue"
- **Export:** "Eksporter bokføringsjournal"
- **Voice input:** Speak commands instead of typing
- **Attachments:** "Upload invoice PDF"

---

## Support

For questions or issues:
- Type `help` in the chat
- Check the FAQ in the dashboard
- Contact support@kontali.ai
