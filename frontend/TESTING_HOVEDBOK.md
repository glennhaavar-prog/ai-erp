# Testing Hovedbok Report Component

## Quick Start

```bash
# Navigate to frontend directory
cd /home/ubuntu/.openclaw/workspace/ai-erp/frontend

# Install dependencies (if not already done)
npm install

# Run development server
npm run dev

# Open in browser
# http://localhost:3000/hovedbok
```

## Visual Component Check

### Expected Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Hovedbok                           [Eksporter til Excel] Button │
│ Viser X av Y posteringer                                        │
├─────────────────────────────────────────────────────────────────┤
│ Filters (Dark Card Background):                                 │
│ [Fra dato] [Til dato] [Kontonr] [Leverandør ▼] [Status ▼]     │
│                                         [Nullstill filtre]      │
├─────────────────────────────────────────────────────────────────┤
│ TABLE HEADER (Dark Hover Background):                           │
│ Bilagsnr│Dato ▼│Konto│Debet│Kredit│Tekst│MVA│Bilagsart│Saldo  │
├─────────────────────────────────────────────────────────────────┤
│ (Table rows - hover effect on each row)                         │
│ Click any row → Opens detail modal                              │
├─────────────────────────────────────────────────────────────────┤
│ Side X av Y                      [Forrige] [Neste] Buttons     │
└─────────────────────────────────────────────────────────────────┘
```

## Without Backend API (Frontend Only)

The component will show:
- ✅ All UI elements render correctly
- ✅ Dark theme styling applied
- ✅ Loading spinner initially
- ✅ Error message: "Kunne ikke laste hovedboken. Vennligst prøv igjen."
- ✅ Empty state: "Ingen posteringer funnet"

### What to Verify:

1. **Dark Theme**
   - Background: Very dark blue (#0f172a)
   - Cards: Lighter dark blue (#1e293b)
   - Text: Light gray on dark background
   - Buttons: Blue accent colors

2. **Responsive Design**
   - Resize browser window
   - Filter grid should stack on mobile
   - Table should scroll horizontally if needed

3. **Filter UI**
   - Date pickers should open calendar
   - Account number accepts text input
   - Status dropdown has 3 options (Alle/Postert/Reversert)
   - Vendor dropdown shows "Alle leverandører" (empty until API)

4. **Buttons**
   - Green "Eksporter til Excel" button (top right)
   - Gray "Nullstill filtre" text button
   - Gray "Forrige"/"Neste" pagination buttons

## With Backend API (Full Integration)

### Mock API Setup (Optional)

Create a mock server for testing:

```bash
# Install json-server for quick API mocking
npm install -g json-server

# Create mock data file
cat > mock-hovedbok.json << 'EOF'
{
  "entries": [
    {
      "id": "1",
      "voucher_number": "BIL-2024-001",
      "accounting_date": "2024-02-01",
      "account_number": "2400",
      "account_name": "Leverandørgjeld",
      "debit_amount": 0,
      "credit_amount": 25000.00,
      "description": "Innkjøp datautstyr",
      "vat_code": "3",
      "source_type": "invoice",
      "vendor_id": "v1",
      "vendor_name": "Tech Supply AS",
      "status": "posted",
      "created_at": "2024-02-01T10:00:00Z"
    },
    {
      "id": "2",
      "voucher_number": "BIL-2024-002",
      "accounting_date": "2024-02-02",
      "account_number": "1920",
      "account_name": "Utstyr",
      "debit_amount": 20000.00,
      "credit_amount": 0,
      "description": "Innkjøp datautstyr",
      "vat_code": "3",
      "source_type": "invoice",
      "vendor_id": "v1",
      "vendor_name": "Tech Supply AS",
      "status": "posted",
      "created_at": "2024-02-01T10:00:00Z"
    },
    {
      "id": "3",
      "voucher_number": "BIL-2024-002",
      "accounting_date": "2024-02-02",
      "account_number": "2700",
      "account_name": "Utgående MVA",
      "debit_amount": 5000.00,
      "credit_amount": 0,
      "description": "Innkjøp datautstyr",
      "vat_code": "3",
      "source_type": "invoice",
      "vendor_id": "v1",
      "vendor_name": "Tech Supply AS",
      "status": "posted",
      "created_at": "2024-02-01T10:00:00Z"
    }
  ],
  "total_count": 3,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
EOF

# Start mock server
json-server --watch mock-hovedbok.json --port 8000
```

Then update `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Test Scenarios

#### 1. Basic Data Display
- [ ] Table shows all entries
- [ ] All columns display correct data
- [ ] Currency formatted as NOK (kr 25.000,00)
- [ ] Dates formatted as DD.MM.YYYY
- [ ] Running balance calculates correctly

#### 2. Filtering
- [ ] Date range filters results
- [ ] Account number filters (exact match or partial?)
- [ ] Vendor dropdown filters by vendor_id
- [ ] Status filters posted/reversed entries
- [ ] "Nullstill filtre" clears all filters
- [ ] Page resets to 1 when filter changes

#### 3. Sorting
- [ ] Click "Dato" header toggles sort
- [ ] Arrow icon rotates (▼ vs ▲)
- [ ] Default is DESC (newest first)
- [ ] Sorting persists across pagination

#### 4. Pagination
- [ ] Shows correct page count
- [ ] "Forrige" disabled on page 1
- [ ] "Neste" disabled on last page
- [ ] Page navigation updates data
- [ ] Shows "Side X av Y" correctly

#### 5. Detail Modal
- [ ] Clicking row opens modal
- [ ] All entry details displayed
- [ ] Reversed entries show warning banner
- [ ] Currency and dates formatted
- [ ] "Lukk" button closes modal
- [ ] Click outside modal closes it
- [ ] X button closes modal

#### 6. Export
- [ ] Button triggers download
- [ ] File named: hovedbok_YYYY-MM-DD.xlsx
- [ ] Excel file contains filtered data
- [ ] Shows error if API fails

#### 7. Edge Cases
- [ ] Empty results show "Ingen posteringer funnet"
- [ ] API error shows red error banner
- [ ] Loading spinner shows during fetch
- [ ] Handles missing optional fields (vat_code, vendor_name)
- [ ] Very long descriptions truncate with ellipsis
- [ ] Large numbers format correctly (millions)

#### 8. Running Balance
- [ ] Calculates debit - credit
- [ ] Green for positive, red for negative
- [ ] Skips reversed entries in calculation
- [ ] Updates per row in table

## Performance Testing

### Load Test (with real backend)

```bash
# Generate large dataset
# Test with 1,000 entries
# Test with 10,000 entries
# Test with 100,000 entries (via pagination)
```

Expected behavior:
- Initial load < 2 seconds
- Filter change < 1 second
- Pagination < 500ms
- Modal open instant (no API call)

## Browser Testing

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)

Check:
- [ ] All features work
- [ ] Styling consistent
- [ ] No console errors
- [ ] Date pickers work correctly

## Mobile Testing

Test responsive design:
- [ ] iPhone SE (375px width)
- [ ] iPad (768px width)
- [ ] Desktop (1920px width)

Verify:
- [ ] Filters stack vertically on mobile
- [ ] Table scrolls horizontally if needed
- [ ] Modal fits screen on mobile
- [ ] Touch interactions work

## Accessibility Testing

- [ ] Keyboard navigation (Tab through elements)
- [ ] Screen reader compatibility
- [ ] Color contrast (check with WAVE tool)
- [ ] Focus indicators visible
- [ ] ARIA labels present

## TypeScript Verification

```bash
# Check for type errors
npx tsc --noEmit

# Should show NO errors related to:
# - HovedbokReport
# - hovedbok.ts
# - HovedbokEntry
```

## Build Verification

```bash
# Production build
npm run build

# Should complete with:
# ✓ Compiled successfully
# ✓ Generating static pages
# Route /hovedbok should be listed
```

## Common Issues & Solutions

### Issue: Component not rendering
**Solution**: Check React DevTools, verify import paths

### Issue: API calls failing
**Solution**: Check NEXT_PUBLIC_API_URL in .env.local

### Issue: Styling broken
**Solution**: Verify Tailwind CSS config, check globals.css

### Issue: TypeScript errors
**Solution**: Run `npm install`, verify type definitions

### Issue: Filters not working
**Solution**: Check browser console for API errors

### Issue: Modal not showing
**Solution**: Check z-index (should be 50), verify state updates

## Screenshot Checklist

Capture these views for documentation:
1. [ ] Full table view with data
2. [ ] Empty state
3. [ ] Loading state
4. [ ] Error state
5. [ ] Filters panel
6. [ ] Detail modal
7. [ ] Mobile responsive view
8. [ ] Pagination controls

## Sign-off Checklist

Before marking as complete:
- [ ] All UI elements present
- [ ] Dark theme applied correctly
- [ ] TypeScript compiles without errors
- [ ] Build succeeds
- [ ] No console warnings in dev mode
- [ ] Responsive design works
- [ ] API integration ready
- [ ] Documentation complete
- [ ] Code follows project conventions
- [ ] Git commit with clear message

## Report Template

```
Testing Date: ________
Tester Name: _________
Environment: Development / Staging / Production

Components Tested:
[ ] UI Rendering
[ ] Filters
[ ] Sorting
[ ] Pagination
[ ] Detail Modal
[ ] Export
[ ] Responsive Design
[ ] Error Handling

Issues Found: _______________________________________

Status: PASS / FAIL / BLOCKED

Notes: _______________________________________________
```

---

**Ready to test?** Start with the Quick Start section above! 🚀
