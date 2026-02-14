# MasterDetailLayout Component

Gjenbrukbar layout-komponent for master-detail views i Kontali ERP redesign.

## Features

✅ **Venstre panel (Master)**: Liste med items
- 400px fast bredde på desktop
- Full bredde på mobil (<768px)
- Scrollbar ved behov
- Select/hover states

✅ **Høyre panel (Detail)**: Detaljevisning
- flex-1 (tar opp tilgjengelig plass)
- Scrollbar ved behov
- Conditional rendering basert på valgt item

✅ **Bunn (Footer)**: Optional chat/action panel
- 60px fast høyde i collapsed state
- Utvides til 384px (h-96) ved focus
- Kollapses ved blur (når focus forlater footer)

✅ **Multiselect support**:
- Checkboxes per item (vises kun når `multiSelectEnabled=true`)
- Select all/deselect all checkbox i header
- Indeterminate state når noen (men ikke alle) er valgt
- `selectedIds` array håndteres via `onMultiSelect` callback

✅ **Responsive design**:
- Desktop (≥768px): Side-by-side layout
- Mobile (<768px): Stacked vertikalt

✅ **Loading states**:
- Spinner i master list
- Spinner i detail view
- Graceful empty states

## Props Interface

```typescript
interface MasterDetailLayoutProps<T> {
  // Data
  items: T[];                     // Array av items (må ha id: string)
  
  // Single selection
  selectedId: string | null;      // ID av valgt item
  onSelectItem: (id: string) => void;
  
  // Multi selection
  selectedIds: string[];          // Array av valgte IDs
  onMultiSelect: (ids: string[]) => void;
  multiSelectEnabled?: boolean;   // Default: false
  
  // Render functions
  renderItem: (
    item: T,
    isSelected: boolean,
    isMultiSelected: boolean
  ) => React.ReactNode;
  
  renderDetail: (item: T | null) => React.ReactNode;
  
  renderFooter?: () => React.ReactNode;  // Optional
  
  // State
  loading?: boolean;              // Default: false
}
```

## Usage Example

```typescript
import { MasterDetailLayout } from '@/components/MasterDetailLayout';

interface MyItem {
  id: string;
  title: string;
  description: string;
}

function MyComponent() {
  const [items, setItems] = useState<MyItem[]>([...]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  return (
    <MasterDetailLayout
      items={items}
      selectedId={selectedId}
      selectedIds={selectedIds}
      onSelectItem={setSelectedId}
      onMultiSelect={setSelectedIds}
      multiSelectEnabled={true}
      
      renderItem={(item, isSelected, isMultiSelected) => (
        <div className="p-4">
          <h3 className="font-medium">{item.title}</h3>
          <p className="text-sm text-gray-600">{item.description}</p>
        </div>
      )}
      
      renderDetail={(item) => {
        if (!item) return <div>Select an item</div>;
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold">{item.title}</h1>
            <p className="mt-4">{item.description}</p>
          </div>
        );
      }}
      
      renderFooter={() => (
        <div className="p-4">
          <input type="text" placeholder="Chat..." className="w-full" />
        </div>
      )}
    />
  );
}
```

## Demo

Se `/app/demo-master-detail/page.tsx` for full working demo med:
- 12 dummy items
- Status badges
- Priority indicators
- Metadata display
- Action buttons
- Chat footer
- Multiselect toggle

Kjør demo:
```bash
npm run dev
# Naviger til http://localhost:3000/demo-master-detail
```

## Styling

Komponenten bruker **Tailwind CSS** for all styling:
- Responsive breakpoint: `md:` (768px)
- Color scheme: Blue for selection states
- Transitions: 300ms ease-in-out
- Borders: Gray scale (50-200)

## TypeScript Support

Full TypeScript support med generics:
```typescript
MasterDetailLayout<MyItemType>
```

Komponenten krever at `T extends { id: string }` for å sikre at alle items har en unik ID.

## Accessibility

- ✅ Keyboard navigation (tab, enter)
- ✅ Focus states
- ✅ ARIA attributes (implicit via semantic HTML)
- ✅ Checkbox labels
- ✅ Indeterminate checkbox state for partial selection

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Virtualization: Not included (add `react-window` for large lists)
- Memoization: Consider wrapping `renderItem` callbacks with `useCallback`
- Debouncing: Consider debouncing `onMultiSelect` for bulk operations

## Next Steps

1. ✅ Component created
2. ✅ Demo page created
3. 🔄 Test in Review Queue context
4. 🔄 Add keyboard shortcuts (Shift+Click for range selection)
5. 🔄 Add drag & drop support (optional)
6. 🔄 Add virtualization for large datasets (optional)

---

**Status**: ✅ Ready for Review Queue
**Author**: Peter (Sonnet 4.5)
**Date**: 2026-02-14
