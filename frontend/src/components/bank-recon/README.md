# Bank Reconciliation Components

**Module 2: Bank-to-Ledger Reconciliation**

This directory contains components for the bank reconciliation feature, which matches bank transactions against general ledger entries (hovedbok).

---

## Components

### 1. **BankTransactionList.tsx** (3.4 KB)
Left panel component displaying unmatched bank transactions.

**Props:**
```typescript
{
  items: BankTransaction[];
  selectedIds: string[];
  onToggleSelection: (id: string) => void;
  loading?: boolean;
}
```

**Features:**
- Checkbox multi-select
- Amount color-coding (green=credit, red=debit)
- KID display when available
- Click to select/deselect
- Loading and empty states

---

### 2. **LedgerEntryList.tsx** (4.4 KB)
Right panel component displaying unmatched ledger entries.

**Props:**
```typescript
{
  items: GeneralLedger[];
  selectedIds: string[];
  onToggleSelection: (id: string) => void;
  loading?: boolean;
}
```

**Features:**
- Checkbox multi-select
- Shows voucher number, account, debit/credit lines
- Net amount calculation
- Click to select/deselect
- Loading and empty states

---

### 3. **MatchingActions.tsx** (2.6 KB)
Middle panel component with action buttons.

**Props:**
```typescript
{
  selectedBankCount: number;
  selectedLedgerCount: number;
  onMatch: () => void;
  onAutoMatch: () => void;
  onCreateRule: () => void;
  isMatching?: boolean;
  isAutoMatching?: boolean;
}
```

**Features:**
- "Avstem valgte" button (manual match)
- "Auto-avstemming" button (trigger algorithm)
- "Opprett regel" button (open rule dialog)
- Selection summary
- Disabled states when no selection
- Loading states

---

### 4. **MatchedItemsList.tsx** (5.2 KB)
Bottom panel component showing already matched pairs.

**Props:**
```typescript
{
  items: MatchedItem[];
  onUnlink: (bankTransactionId: string, ledgerEntryId: string) => void;
  loading?: boolean;
}
```

**Features:**
- Shows bank ↔ ledger pairs
- Match type badges (Auto/Manuell/Regel)
- Confidence score visualization
- "Fjern" button to break matches
- Loading and empty states

---

### 5. **RuleDialog.tsx** (9.9 KB)
Modal dialog for creating matching rules.

**Props:**
```typescript
{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (rule: CreateRuleRequest) => void;
  clientId: string;
  isSubmitting?: boolean;
}
```

**Features:**
- Rule types: KID, Amount, Description, Date Range
- Dynamic form fields based on rule type
- Validation and submission
- Priority setting (1-100)
- Loading states

**Rule Types:**
- **KID:** Match by KID pattern (wildcard support)
- **Amount:** Match by amount range
- **Description:** Match by description pattern
- **Date Range:** Match within N days

---

## Usage Example

```typescript
import { BankTransactionList } from '@/components/bank-recon/BankTransactionList';
import { LedgerEntryList } from '@/components/bank-recon/LedgerEntryList';
import { MatchingActions } from '@/components/bank-recon/MatchingActions';
import { MatchedItemsList } from '@/components/bank-recon/MatchedItemsList';
import { RuleDialog } from '@/components/bank-recon/RuleDialog';

function BankReconciliationPage() {
  const [selectedBankIds, setSelectedBankIds] = useState<string[]>([]);
  const [selectedLedgerIds, setSelectedLedgerIds] = useState<string[]>([]);
  const [showRuleDialog, setShowRuleDialog] = useState(false);

  const { data: unmatchedData } = useQuery({
    queryKey: ['unmatched-items', clientId],
    queryFn: () => fetchUnmatchedItems(clientId),
  });

  const handleMatch = () => {
    // Create matches for selected items
    selectedBankIds.forEach(bankId => {
      selectedLedgerIds.forEach(ledgerId => {
        createMatch({ bank_transaction_id: bankId, ledger_entry_id: ledgerId });
      });
    });
  };

  return (
    <div className="flex">
      {/* Left: Bank Transactions */}
      <BankTransactionList
        items={unmatchedData?.bank_transactions || []}
        selectedIds={selectedBankIds}
        onToggleSelection={(id) => setSelectedBankIds(prev => 
          prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        )}
      />

      {/* Middle: Actions */}
      <MatchingActions
        selectedBankCount={selectedBankIds.length}
        selectedLedgerCount={selectedLedgerIds.length}
        onMatch={handleMatch}
        onAutoMatch={() => autoMatch(clientId)}
        onCreateRule={() => setShowRuleDialog(true)}
      />

      {/* Right: Ledger Entries */}
      <LedgerEntryList
        items={unmatchedData?.ledger_entries || []}
        selectedIds={selectedLedgerIds}
        onToggleSelection={(id) => setSelectedLedgerIds(prev => 
          prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        )}
      />

      {/* Rule Dialog */}
      <RuleDialog
        isOpen={showRuleDialog}
        onClose={() => setShowRuleDialog(false)}
        onSubmit={(rule) => createMatchingRule(rule)}
        clientId={clientId}
      />
    </div>
  );
}
```

---

## API Integration

These components work with `/lib/api/bank-recon.ts`:

```typescript
import {
  fetchUnmatchedItems,
  fetchMatchedItems,
  createMatch,
  unmatch,
  autoMatch,
  createMatchingRule,
} from '@/lib/api/bank-recon';
```

See API documentation in `/lib/api/bank-recon.ts` for full endpoint details.

---

## Styling

All components use **Tailwind CSS** with consistent patterns:
- **Selection:** `bg-blue-100 border-l-4 border-blue-600`
- **Hover:** `hover:bg-blue-50`
- **Disabled:** `opacity-50 cursor-not-allowed`
- **Credit amounts:** `text-green-600`
- **Debit amounts:** `text-red-600`
- **Loading:** Spinner with `animate-spin`

---

## Testing

Run the page with:
```bash
npm run dev
# Navigate to http://localhost:3002/bank-reconciliation
```

Test data:
- Client: `09409ccf-d23e-45e5-93b9-68add0b96277`
- Account: `1920`
- Period: `2026-02-01` to `2026-02-28`

---

## Dependencies

- **React** (18+)
- **React Query** (@tanstack/react-query)
- **Tailwind CSS**
- **Heroicons** (@heroicons/react)
- **Next.js** (14+)

---

**Created:** 2026-02-14  
**Author:** Sonny (Sonnet 4.5)  
**Module:** 2 - Bank Reconciliation
