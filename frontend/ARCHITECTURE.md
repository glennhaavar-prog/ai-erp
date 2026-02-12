# UX Improvements Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP LAYOUT (root)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ KeyboardShortcutsProvider                                 │  │
│  │  ├─ Listens for "?" → Shows help overlay                 │  │
│  │  ├─ Manages global shortcuts (Cmd+K, Esc, Cmd+S)         │  │
│  │  └─ Dispatches custom keyboard events                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ GlobalSearch Component                                    │  │
│  │  ├─ Triggered by: Cmd+K / Ctrl+K                         │  │
│  │  ├─ Searches: Suppliers, Customers, Vouchers, Accounts   │  │
│  │  ├─ Stores recent items in localStorage                  │  │
│  │  └─ Uses: cmdk library                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Toaster (sonner)                                          │  │
│  │  └─ Shows notifications for all actions                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Feature Integration Map

```
┌───────────────────────────────────────────────────────────────────┐
│                         PAGE LEVEL                                 │
│  (e.g., Suppliers List, Customers List, Vouchers List)           │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Header                                                       │ │
│  │  ┌────────────────┐  ┌────────────────┐                    │ │
│  │  │ QuickAddButton │  │ Regular Button │                    │ │
│  │  │ (Modal Overlay)│  │ (Full Form)    │                    │ │
│  │  └────────────────┘  └────────────────┘                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Search Bar                                                   │ │
│  │  "Søk... (Eller trykk Cmd+K for global søk)"               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Table with Bulk Selection                                   │ │
│  │                                                              │ │
│  │  ┌──┬────────────┬──────────┬──────────┬──────────┐        │ │
│  │  │☑│ Select All │ Column 1 │ Column 2 │ Actions  │        │ │
│  │  ├──┼────────────┼──────────┼──────────┼──────────┤        │ │
│  │  │☑│ Item 1     │ Data     │ Data     │ [Edit]   │  ← j/k │ │
│  │  │☑│ Item 2     │ Data     │ Data     │ [Edit]   │        │ │
│  │  │☐│ Item 3     │ Data     │ Data     │ [Edit]   │        │ │
│  │  └──┴────────────┴──────────┴──────────┴──────────┘        │ │
│  │                                                              │ │
│  │  Uses: useBulkSelection hook                                │ │
│  │  Uses: useListNavigation hook (j/k navigation)              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ BulkActions Bar (floating at bottom, when items selected)   │ │
│  │                                                              │ │
│  │  ┌─────────────────────────────────────────────────────────┐│ │
│  │  │ ✓ 3 av 10 valgt │ Export CSV │ Update Status │ Delete  ││ │
│  │  └─────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Keyboard Shortcuts (page-specific)                          │ │
│  │  n → New, e → Edit, d → Delete, j → Down, k → Up           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Global Search Flow
```
User Press Cmd+K
    ↓
GlobalSearch component opens
    ↓
User types query
    ↓
Debounced search (300ms)
    ↓
API calls to all endpoints in parallel
    ↓
Results grouped by type
    ↓
User selects result (Enter or click)
    ↓
Item saved to localStorage recent
    ↓
Router navigates to item
```

### 2. Brønnøysund API Flow
```
User enters org number in form
    ↓
ContactForm detects 9 digits
    ↓
useBrregLookup hook triggered (500ms debounce)
    ↓
API call to data.brreg.no
    ↓
Loading state: Blue spinner icon
    ↓
Success: Green checkmark + auto-fill form
    OR
Error: Red warning icon + error message
    ↓
User continues filling form
```

### 3. Quick Add Flow
```
User clicks "+ Ny Leverandør"
    ↓
QuickAddModal opens (overlay)
    ↓
User fills minimal fields
    ↓
(Optional) Org number triggers Brreg lookup
    ↓
User clicks "Lagre"
    ↓
Validation runs
    ↓
API POST request
    ↓
Success: Toast notification
    ↓
Modal closes
    ↓
Parent page refreshes list
```

### 4. Bulk Actions Flow
```
User checks multiple items
    ↓
useBulkSelection tracks selected IDs
    ↓
BulkActions bar appears (floating)
    ↓
User clicks action (Export/Delete/Status)
    ↓
Confirmation dialog (if destructive)
    ↓
API request with selected IDs
    ↓
Success: Toast notification
    ↓
Selection cleared
    ↓
List refreshes
```

### 5. Keyboard Shortcuts Flow
```
User presses key (e.g., "j")
    ↓
useKeyboardShortcuts hook intercepts
    ↓
Check if input is focused
    ↓
If focused: Ignore (unless global shortcut)
If not focused: Execute action
    ↓
Custom event dispatched (e.g., "keyboard:new")
    ↓
Page component listens and handles event
    ↓
Action executed (create new, navigate, etc.)
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ localStorage                                                │ │
│  │  ├─ globalSearch_recent (recent search items)              │ │
│  │  └─ keyboard_shortcuts_preferences (user customizations)   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ React Components                                            │ │
│  │  ├─ GlobalSearch                                            │ │
│  │  ├─ QuickAddModal                                           │ │
│  │  ├─ BulkActions                                             │ │
│  │  ├─ KeyboardShortcutsHelp                                   │ │
│  │  └─ ContactForm (with Brreg)                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          ↓↑                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Custom Hooks                                                │ │
│  │  ├─ useBrregLookup                                         │ │
│  │  ├─ useKeyboardShortcuts                                   │ │
│  │  ├─ useBulkSelection                                       │ │
│  │  └─ useListNavigation                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL APIS                               │
│                                                                  │
│  ┌───────────────────────┐  ┌──────────────────────────────┐   │
│  │ Internal Backend API  │  │ Brønnøysund Register API     │   │
│  │ localhost:3000/api    │  │ data.brreg.no/enhets...      │   │
│  │                       │  │                              │   │
│  │ /suppliers            │  │ GET /enheter/{orgnr}         │   │
│  │ /customers            │  │                              │   │
│  │ /vouchers             │  │ Returns:                     │   │
│  │ /accounts             │  │  - Company name              │   │
│  │ /suppliers/bulk-*     │  │  - Address                   │   │
│  │ /customers/bulk-*     │  │  - Industry code             │   │
│  │ /vouchers/bulk-*      │  │                              │   │
│  └───────────────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Event System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Custom Event System                           │
│                                                                  │
│  User Action                                                     │
│      ↓                                                           │
│  Keyboard Pressed                                                │
│      ↓                                                           │
│  useKeyboardShortcuts hook                                       │
│      ↓                                                           │
│  document.dispatchEvent(new CustomEvent('keyboard:action'))     │
│      ↓                                                           │
│  Page Components Listen:                                         │
│      document.addEventListener('keyboard:new', handleNew)        │
│      document.addEventListener('keyboard:edit', handleEdit)      │
│      document.addEventListener('keyboard:delete', handleDelete)  │
│      document.addEventListener('keyboard:save', handleSave)      │
│      document.addEventListener('keyboard:escape', handleEscape)  │
│      document.addEventListener('keyboard:help', handleHelp)      │
│      ↓                                                           │
│  Action Executed                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component State                               │
│                                                                  │
│  GlobalSearch:                                                   │
│    - open: boolean                                               │
│    - search: string                                              │
│    - results: SearchResult[]                                     │
│    - recentItems: SearchResult[]                                 │
│    - loading: boolean                                            │
│                                                                  │
│  QuickAddModal:                                                  │
│    - open: boolean                                               │
│    - formData: Record<string, any>                               │
│    - loading: boolean                                            │
│    - errors: Record<string, string>                              │
│                                                                  │
│  BulkSelection:                                                  │
│    - selectedIds: string[]                                       │
│    - isAllSelected: boolean                                      │
│    - isSomeSelected: boolean                                     │
│                                                                  │
│  Brønnøysund Lookup:                                            │
│    - loading: boolean                                            │
│    - error: string | null                                        │
│    - showSuccess: boolean                                        │
│                                                                  │
│  Keyboard Shortcuts:                                             │
│    - enabled: boolean                                            │
│    - shortcuts: KeyboardShortcut[]                               │
│    - preferences: Record<string, any> (from localStorage)        │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints Required

### Internal Backend

```
Search:
  GET  /api/suppliers?search={query}
  GET  /api/customers?search={query}
  GET  /api/vouchers?search={query}
  GET  /api/accounts?search={query}

Quick Add:
  POST /api/suppliers        { company_name, org_number, contact, address }
  POST /api/customers        { name, org_number, contact, address }
  POST /api/vouchers         { description, date, amount }

Bulk Actions:
  POST /api/suppliers/bulk-deactivate       { ids: string[] }
  POST /api/suppliers/export                { ids: string[] }
  POST /api/suppliers/bulk-update-status    { ids: string[], status: string }
  
  POST /api/customers/bulk-deactivate       { ids: string[] }
  POST /api/customers/export                { ids: string[] }
  POST /api/customers/bulk-update-status    { ids: string[], status: string }
  
  POST /api/vouchers/bulk-deactivate        { ids: string[] }
  POST /api/vouchers/export                 { ids: string[] }
  POST /api/vouchers/bulk-update-status     { ids: string[], status: string }
  
  POST /api/invoices/bulk-deactivate        { ids: string[] }
  POST /api/invoices/export                 { ids: string[] }
  POST /api/invoices/bulk-update-status     { ids: string[], status: string }
```

### External APIs

```
Brønnøysund:
  GET https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}
  
  Response:
  {
    "organisasjonsnummer": "988077917",
    "navn": "COMPANY NAME AS",
    "forretningsadresse": {
      "adresse": ["Street 123"],
      "postnummer": "0123",
      "poststed": "OSLO",
      "land": "Norge"
    },
    "naeringskode1": {
      "kode": "62.010",
      "beskrivelse": "Programmeringstjenester"
    }
  }
```

## Performance Optimizations

```
┌─────────────────────────────────────────────────────────────────┐
│                     Performance Features                         │
│                                                                  │
│  1. Debouncing                                                   │
│     - Global search: 300ms                                       │
│     - Brønnøysund lookup: 500ms                                  │
│     - Prevents excessive API calls                               │
│                                                                  │
│  2. LocalStorage Caching                                         │
│     - Recent search items (last 10)                              │
│     - Keyboard preferences                                       │
│     - Instant load without API call                              │
│                                                                  │
│  3. Parallel API Calls                                           │
│     - Global search queries all endpoints simultaneously         │
│     - Results appear as soon as available                        │
│                                                                  │
│  4. React Optimization                                           │
│     - useCallback for functions                                  │
│     - useMemo for computed values                                │
│     - Proper dependency arrays                                   │
│     - Clean up effect listeners                                  │
│                                                                  │
│  5. Event Delegation                                             │
│     - Single keyboard listener for all shortcuts                 │
│     - Event bubbling for table row selection                     │
└─────────────────────────────────────────────────────────────────┘
```

## Security Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│                        Security                                  │
│                                                                  │
│  1. API Security                                                 │
│     - All requests use axios                                     │
│     - HTTPS for external APIs (Brønnøysund)                      │
│     - API URL from environment variable                          │
│                                                                  │
│  2. Input Validation                                             │
│     - Form validation before submit                              │
│     - Org number format validation (9 digits)                    │
│     - XSS protection via React escaping                          │
│                                                                  │
│  3. User Permissions                                             │
│     - Bulk actions require confirmation                          │
│     - Delete operations are soft delete (deactivate)             │
│     - Backend should enforce authorization                       │
│                                                                  │
│  4. Data Privacy                                                 │
│     - Recent items stored locally (not shared)                   │
│     - No sensitive data in localStorage                          │
│     - GDPR compliance: user can clear history                    │
└─────────────────────────────────────────────────────────────────┘
```

---

**Architecture Summary:**

- **Modular:** Each feature is self-contained
- **Reusable:** Hooks and components can be used anywhere
- **Scalable:** Easy to add new shortcuts, bulk actions, or search types
- **Performant:** Debouncing, caching, and optimization built-in
- **Accessible:** Keyboard navigation, ARIA labels, focus management
- **Maintainable:** Clear separation of concerns, well-documented

All features work together harmoniously while remaining independent.
