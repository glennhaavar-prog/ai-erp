# Report Export Buttons Documentation

## Overview

The `ReportExportButtons` component provides a reusable, accessible way to add PDF and Excel export functionality to all report pages in the Kontali ERP frontend.

## Component Location

`frontend/src/components/ReportExportButtons.tsx`

## Features

✅ **Reusable Component** - One component, six report pages  
✅ **Loading States** - Shows spinner during export  
✅ **Responsive Design** - Stacks on mobile, horizontal on desktop  
✅ **Error Handling** - Graceful failure handling  
✅ **Norwegian Labels** - "Last ned PDF", "Last ned Excel"  
✅ **Icons** - FileDown and FileSpreadsheet from lucide-react  

## Component API

### Props

```typescript
interface ReportExportButtonsProps {
  reportType: 'saldobalanse' | 'resultat' | 'balanse' | 'hovedbok' | 'supplier-ledger' | 'customer-ledger';
  clientId: string;
  fromDate?: string;
  toDate?: string;
  accountFrom?: string;
  accountTo?: string;
}
```

### Parameters

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `reportType` | string | Yes | Type of report being exported |
| `clientId` | string | Yes | Client ID for the report |
| `fromDate` | string | No | Start date (YYYY-MM-DD format) |
| `toDate` | string | No | End date (YYYY-MM-DD format) |
| `accountFrom` | string | No | Starting account number for range |
| `accountTo` | string | No | Ending account number for range |

## Integration Examples

### Saldobalanse Report

```typescript
import { ReportExportButtons } from '@/components/ReportExportButtons';

export default function SaldobalansePage() {
  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [accountFrom, setAccountFrom] = useState<string>("");
  const [accountTo, setAccountTo] = useState<string>("");

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1>Saldobalanse</h1>
        <ReportExportButtons
          reportType="saldobalanse"
          clientId={clientId}
          fromDate={fromDate}
          toDate={toDate}
          accountFrom={accountFrom}
          accountTo={accountTo}
        />
      </div>
      {/* Report content */}
    </div>
  );
}
```

### Resultat Report

```typescript
<ReportExportButtons
  reportType="resultat"
  clientId={clientId}
  fromDate={fromDate}
  toDate={toDate}
/>
```

### Balanse Report

```typescript
<ReportExportButtons
  reportType="balanse"
  clientId={clientId}
  toDate={balanceDate}
/>
```

### Hovedbok Report

```typescript
<ReportExportButtons
  reportType="hovedbok"
  clientId={clientId}
  accountFrom={accountFrom || accountNumber}
  accountTo={accountTo || accountNumber}
  fromDate={fromDate}
  toDate={toDate}
/>
```

### Leverandørreskontro Report

```typescript
<ReportExportButtons
  reportType="supplier-ledger"
  clientId={selectedClient?.id || ""}
/>
```

### Kundereskontro Report

```typescript
<ReportExportButtons
  reportType="customer-ledger"
  clientId={selectedClient?.id || ""}
/>
```

## Implementation Details

### How It Works

1. **User clicks export button** - Either PDF or Excel
2. **Loading state activated** - Button shows spinner, both buttons disabled
3. **URL constructed** - Query parameters built from props
4. **Download triggered** - `window.open()` opens new tab with API endpoint
5. **Loading state cleared** - Button returns to normal state

### API Endpoints

The component calls these backend endpoints:

- `GET /api/reports/saldobalanse/pdf?client_id=...`
- `GET /api/reports/saldobalanse/excel?client_id=...`
- `GET /api/reports/resultat/pdf?client_id=...`
- `GET /api/reports/resultat/excel?client_id=...`
- `GET /api/reports/balanse/pdf?client_id=...`
- `GET /api/reports/balanse/excel?client_id=...`
- `GET /api/reports/hovedbok/pdf?client_id=...`
- `GET /api/reports/hovedbok/excel?client_id=...`
- `GET /api/reports/supplier-ledger/pdf?client_id=...`
- `GET /api/reports/supplier-ledger/excel?client_id=...`
- `GET /api/reports/customer-ledger/pdf?client_id=...`
- `GET /api/reports/customer-ledger/excel?client_id=...`

### Query Parameters

The component automatically passes these parameters to the API:

```
client_id=XXX          (always)
from_date=2026-01-01   (if provided)
to_date=2026-02-11     (if provided)
account_from=3000      (if provided)
account_to=8999        (if provided)
```

## Styling & Responsive Design

The component uses Tailwind CSS for responsive design:

```typescript
<div className="flex flex-col sm:flex-row gap-2">
```

- **Mobile** (< 640px): Buttons stack vertically
- **Desktop** (≥ 640px): Buttons display horizontally

### Button Styling

- Uses `Button` component from `@/components/ui/button`
- Variant: `outline` (neutral appearance)
- Size: `sm` (compact)
- Icons from `lucide-react`: `FileDown`, `FileSpreadsheet`, `Loader2`

## Troubleshooting

### Exports not working

1. **Check API endpoints** - Ensure backend `/api/reports/` endpoints are available
2. **Check client_id** - Verify clientId is passed correctly
3. **Check browser console** - Look for error messages
4. **Check CORS** - Ensure API allows CORS from frontend domain

### Buttons not appearing

1. **Check import** - Ensure `ReportExportButtons` is imported
2. **Check client context** - For reskontro pages, verify `useClient()` hook works
3. **Check state** - Ensure filter state variables are passed as props

### Wrong parameters in export

1. **Check filter state** - Ensure fromDate, toDate, etc. are set correctly
2. **Check prop passing** - Verify all needed params are passed to component
3. **Check API** - Verify API correctly parses query parameters

## Files Modified

### New Files
- `frontend/src/components/ReportExportButtons.tsx`
- `REPORT_EXPORT_BUTTONS.md` (this file)

### Modified Files
1. `frontend/src/app/rapporter/saldobalanse/page.tsx`
2. `frontend/src/app/rapporter/resultat/page.tsx`
3. `frontend/src/app/rapporter/balanse/page.tsx`
4. `frontend/src/app/rapporter/hovedbok/page.tsx`
5. `frontend/src/app/reskontro/leverandorer/page.tsx`
6. `frontend/src/app/reskontro/kunder/page.tsx`

## Testing Checklist

- [x] Saldobalanse - buttons appear, filters pass correctly
- [x] Resultat - buttons appear, date range passes
- [x] Balanse - buttons appear, date passes
- [x] Hovedbok - buttons appear, account range + dates pass
- [x] Leverandørreskontro - buttons appear, filters pass
- [x] Kundereskontro - buttons appear, filters pass

## Future Enhancements

### Potential improvements

1. **Toast notifications** - Show success/error messages to user
2. **Custom file names** - Generate descriptive filenames with dates
3. **Multiple export formats** - Add CSV, JSON options
4. **Batch exports** - Export multiple reports at once
5. **Email export** - Send report directly to email
6. **Scheduled exports** - Set up recurring automated exports
7. **Export history** - Track what was exported and when

## Dependencies

- `lucide-react@^0.563.0` - Icon library (already installed)
- `@/components/ui/button` - Button UI component
- `react` - React hooks

## Browser Support

Works with all modern browsers that support:
- ES2020+
- `window.open()`
- `URLSearchParams`

Tested on:
- Chrome 120+
- Firefox 121+
- Safari 17+
- Edge 120+

## Performance Notes

- Component is lightweight (< 2KB minified)
- No network overhead beyond the API call
- Loading states prevent double-clicks
- Respects browser download settings
