# Pagination Integration Guide - Kontali ERP Frontend

This guide shows how to integrate the `PaginationControls` component into existing pages.

## Quick Start

### 1. Import the Component

```typescript
import { PaginationControls } from '@/components/PaginationControls';
```

### 2. Add State Variables

```typescript
const [currentPage, setCurrentPage] = useState(1);
const [pageSize, setPageSize] = useState(50);
const [items, setItems] = useState([]);
const [total, setTotal] = useState(0);
const [loading, setLoading] = useState(false);
```

### 3. Fetch Data with Pagination

```typescript
useEffect(() => {
  fetchItems();
}, [currentPage, pageSize]);

const fetchItems = async () => {
  if (!clientId) return;
  
  setLoading(true);
  try {
    const offset = (currentPage - 1) * pageSize;
    const url = `http://localhost:8000/api/endpoint?client_id=${clientId}&limit=${pageSize}&offset=${offset}`;
    const response = await fetch(url);
    if (response.ok) {
      const data = await response.json();
      setItems(data.items);
      setTotal(data.total);
    }
  } catch (error) {
    console.error('Failed to fetch items:', error);
  } finally {
    setLoading(false);
  }
};
```

### 4. Add Pagination Controls

```typescript
<PaginationControls
  currentPage={currentPage}
  pageSize={pageSize}
  total={total}
  onPageChange={setCurrentPage}
  onPageSizeChange={(newPageSize) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page
  }}
/>
```

## Complete Example - Customer Invoices Page

Here's a complete example showing how to implement pagination:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';
import { PaginationControls } from '@/components/PaginationControls';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CustomerInvoice {
  id: string;
  invoice_number: string;
  customer_name: string;
  total_amount: number;
  payment_status: string;
  invoice_date: string;
}

export default function CustomerInvoicesPage() {
  const { selectedClient } = useClient();
  const clientId = selectedClient?.id;

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // Filter state
  const [paymentStatus, setPaymentStatus] = useState<string>('');

  useEffect(() => {
    if (clientId) {
      fetchInvoices();
    }
  }, [clientPage, pageSize, paymentStatus, clientId]);

  const fetchInvoices = async () => {
    if (!clientId) return;
    
    setLoading(true);
    try {
      const offset = (currentPage - 1) * pageSize;
      let url = `http://localhost:8000/api/customer-invoices?client_id=${clientId}&limit=${pageSize}&offset=${offset}`;
      
      if (paymentStatus) {
        url += `&payment_status=${paymentStatus}`;
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setInvoices(data.items);
        setTotal(data.total);
      }
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'bg-green-100 text-green-800';
      case 'unpaid': return 'bg-red-100 text-red-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Kundefakturaer</h1>
        
        {/* Filter */}
        <select 
          value={paymentStatus}
          onChange={(e) => {
            setPaymentStatus(e.target.value);
            setCurrentPage(1); // Reset to first page when filtering
          }}
          className="px-3 py-2 border rounded-md"
        >
          <option value="">Alle statuser</option>
          <option value="paid">Betalt</option>
          <option value="unpaid">Ubetalt</option>
          <option value="partial">Delvis betalt</option>
        </select>
      </div>

      {/* Invoice List */}
      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-8">Laster...</div>
        ) : invoices.length > 0 ? (
          invoices.map(invoice => (
            <Card key={invoice.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <h3 className="font-semibold">{invoice.invoice_number}</h3>
                    <p className="text-sm text-gray-600">{invoice.customer_name}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(invoice.invoice_date).toLocaleDateString('no-NO')}
                    </p>
                  </div>
                  <div className="text-right space-y-2">
                    <p className="font-semibold">{invoice.total_amount.toFixed(2)} NOK</p>
                    <Badge className={getStatusColor(invoice.payment_status)}>
                      {invoice.payment_status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">Ingen fakturaer funnet</div>
        )}
      </div>

      {/* Pagination Controls */}
      {total > 0 && (
        <PaginationControls
          currentPage={currentPage}
          pageSize={pageSize}
          total={total}
          onPageChange={setCurrentPage}
          onPageSizeChange={(newPageSize) => {
            setPageSize(newPageSize);
            setCurrentPage(1);
          }}
        />
      )}
    </div>
  );
}
```

## Integration Checklist for Each Page

### For Each of the 6 Pages:

1. **Import the pagination component**
   ```typescript
   import { PaginationControls } from '@/components/PaginationControls';
   ```

2. **Add pagination state**
   ```typescript
   const [currentPage, setCurrentPage] = useState(1);
   const [pageSize, setPageSize] = useState(50);
   const [items, setItems] = useState([]);
   const [total, setTotal] = useState(0);
   ```

3. **Update fetch function to use pagination**
   - Add `offset` calculation: `(currentPage - 1) * pageSize`
   - Add `limit` and `offset` query parameters
   - Update state with `data.items` and `data.total`

4. **Add dependency on pagination state**
   ```typescript
   useEffect(() => {
     fetchItems();
   }, [currentPage, pageSize, /* filters */, clientId]);
   ```

5. **Add PaginationControls component to JSX**
   - Place after the item list
   - Wire up `onPageChange` and `onPageSizeChange`

6. **Reset pagination on filter changes**
   ```typescript
   setCurrentPage(1); // Reset to first page
   ```

## API Response Format

All paginated endpoints return this format:

```json
{
  "items": [...],           // Array of items
  "total": 1000,            // Total item count
  "limit": 50,              // Items per page
  "offset": 0,              // Starting index
  "page_number": 1          // Calculated page number
}
```

## Common Patterns

### Pattern 1: With Single Filter

```typescript
const [filterValue, setFilterValue] = useState('');

useEffect(() => {
  if (clientId) {
    fetchItems();
  }
}, [currentPage, pageSize, filterValue, clientId]);

const fetchItems = async () => {
  const offset = (currentPage - 1) * pageSize;
  let url = `http://localhost:8000/api/items?client_id=${clientId}&limit=${pageSize}&offset=${offset}`;
  
  if (filterValue) {
    url += `&filter=${filterValue}`;
  }
  
  // ... fetch
};

const handleFilterChange = (newFilter: string) => {
  setFilterValue(newFilter);
  setCurrentPage(1); // Reset to page 1
};
```

### Pattern 2: With Multiple Filters

```typescript
const [filters, setFilters] = useState({
  status: '',
  search: '',
  dateFrom: '',
  dateTo: ''
});

useEffect(() => {
  if (clientId) {
    fetchItems();
  }
}, [currentPage, pageSize, filters, clientId]);

const fetchItems = async () => {
  const offset = (currentPage - 1) * pageSize;
  const params = new URLSearchParams({
    client_id: clientId,
    limit: pageSize.toString(),
    offset: offset.toString()
  });
  
  if (filters.status) params.append('status', filters.status);
  if (filters.search) params.append('search', filters.search);
  if (filters.dateFrom) params.append('date_from', filters.dateFrom);
  if (filters.dateTo) params.append('date_to', filters.dateTo);
  
  const url = `http://localhost:8000/api/items?${params}`;
  // ... fetch
};

const handleFilterChange = (key: string, value: string) => {
  setFilters(prev => ({ ...prev, [key]: value }));
  setCurrentPage(1);
};
```

### Pattern 3: With Search and Pagination

```typescript
const [searchQuery, setSearchQuery] = useState('');

useEffect(() => {
  if (clientId) {
    fetchItems();
  }
}, [currentPage, pageSize, searchQuery, clientId]);

const fetchItems = async () => {
  const offset = (currentPage - 1) * pageSize;
  let url = `http://localhost:8000/api/items?client_id=${clientId}&limit=${pageSize}&offset=${offset}`;
  
  if (searchQuery) {
    url += `&search=${encodeURIComponent(searchQuery)}`;
  }
  
  // ... fetch
};

const handleSearch = (query: string) => {
  setSearchQuery(query);
  setCurrentPage(1); // Reset to page 1 on new search
};
```

## State Management Tips

1. **Reset to page 1 on filter changes**
   ```typescript
   setCurrentPage(1);
   ```

2. **Keep pagination state separate from filters**
   ```typescript
   // Good
   const [page, setPage] = useState(1);
   const [filters, setFilters] = useState({...});
   
   // Instead of
   // const [state, setState] = useState({ page: 1, filters: {...} });
   ```

3. **Prevent fetching before clientId is available**
   ```typescript
   if (!clientId) return;
   ```

## Performance Optimization

### 1. Debounce Search Input
```typescript
import { useDebounce } from '@/hooks/useDebounce';

const [searchInput, setSearchInput] = useState('');
const searchQuery = useDebounce(searchInput, 500);

useEffect(() => {
  if (clientId) {
    fetchItems();
  }
}, [currentPage, pageSize, searchQuery, clientId]);
```

### 2. Memoize Fetch Function
```typescript
const fetchItems = useCallback(async () => {
  // ... fetch logic
}, [clientId, currentPage, pageSize, filters]);
```

### 3. Cache Results (Optional)
```typescript
const [cache, setCache] = useState<Record<string, any>>({});

const fetchItems = async () => {
  const cacheKey = `${clientId}-${currentPage}-${pageSize}`;
  
  if (cache[cacheKey]) {
    setItems(cache[cacheKey].items);
    setTotal(cache[cacheKey].total);
    return;
  }
  
  // ... fetch
};
```

## Testing Pagination

### Manual Testing Checklist

- [ ] First page loads correctly
- [ ] Navigate to next page
- [ ] Navigate to previous page
- [ ] Navigate to specific page number
- [ ] Change page size (25, 50, 100, 200)
- [ ] Apply filters while on page 2+
- [ ] Verify page resets to 1 on filter change
- [ ] Verify "Showing X-Y of Z" updates correctly
- [ ] Test with 0 results
- [ ] Test with 1 result
- [ ] Test with exactly 1 page
- [ ] Test with multiple pages

### Test Data Generation

For testing, generate test data:
```sql
-- Example: Generate 250 invoices for testing
INSERT INTO customer_invoice (client_id, customer_name, total_amount, payment_status, invoice_date)
SELECT 
  'client-id',
  'Customer ' || ROW_NUMBER() OVER(),
  RANDOM() * 10000,
  CASE WHEN RANDOM() < 0.3 THEN 'paid' WHEN RANDOM() < 0.7 THEN 'unpaid' ELSE 'partial' END,
  CURRENT_DATE - INTERVAL '1 day' * (ROW_NUMBER() OVER() % 365)
FROM generate_series(1, 250);
```

## Troubleshooting

### Issue: Pagination controls not showing
**Solution:** Check that `total > 0`
```typescript
{total > 0 && (
  <PaginationControls {...props} />
)}
```

### Issue: Page resets when data loads
**Solution:** Ensure fetch doesn't run unnecessarily
```typescript
// Bad: Will cause infinite loop
useEffect(() => {
  fetchItems();
}, [...]); // Missing dependencies

// Good: Add all dependencies
useEffect(() => {
  fetchItems();
}, [currentPage, pageSize, filters, clientId]);
```

### Issue: Filters not applied when paginating
**Solution:** Include filters in fetch URL
```typescript
// Bad: Missing filter in URL
const url = `...?limit=${pageSize}&offset=${offset}`;

// Good: Include all filters
if (filters.status) url += `&status=${filters.status}`;
```

### Issue: "Showing X-Y of Z" counter wrong
**Solution:** Ensure backend returns correct `total` count
```typescript
// Backend should return total for ALL filtered items
// not just current page
{
  "items": [...],
  "total": 1000,  // All items matching filters
  "limit": 50,
  "offset": 0
}
```

## Next Steps

1. Pick one page to implement pagination first
2. Copy the example pattern
3. Test thoroughly with the checklist
4. Move to the next page
5. Test pagination with other team members

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example implementation
3. Verify API response format with backend team
4. Check browser console for errors
