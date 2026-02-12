# Emoji → Lucide Icon Mapping for Kontali

## Primary Navigation Icons

| Emoji | Lucide Icon | Component |
|-------|-------------|-----------|
| 📊 | `LayoutDashboard` | Dashboard |
| 📥 | `Inbox` | Innboks |
| 📋 | `ClipboardList` | Bilagsoversikt |
| 📄 | `FileText` | Bilagsføring / Documents |
| 🏦 | `Building2` | Bank |
| 📈 | `TrendingUp` | Rapporter |
| 💰 | `DollarSign` eller `Banknote` | Fakturering |
| 📖 | `BookOpen` | Hovedbok |
| ⚖️ | `Scale` | Balanse |
| 🏢 | `Building` | Kunder & Leverandører |
| 👤 | `User` | Bruker / Single person |
| 👥 | `Users` | Kunder / Multiple people |
| 🔁 | `RefreshCw` | Sync / Reconciliation |
| 📦 | `Package` | Produkter / Inventory |
| 📁 | `FolderOpen` | Filer / Documents |
| 🏛️ | `Landmark` | Mva / Tax |
| 🗂️ | `Archive` | Arkiv |
| ⚙️ | `Settings` | Innstillinger |
| 🔌 | `Plug` | Integrasjoner |
| 💬 | `MessageSquare` | Chat / AI Chat |
| ✓ | `Check` eller `CheckCircle` | Completed / Verified |
| · | `Circle` (size w-1.5 h-1.5) | Sub-menu bullet |

## Status & Action Icons (add these)

| Use Case | Lucide Icon |
|----------|-------------|
| Review/Pending | `AlertCircle` |
| Approved | `CheckCircle2` |
| Rejected | `XCircle` |
| Loading | `Loader2` (with animate-spin) |
| Search | `Search` |
| Filter | `Filter` |
| Sort | `ArrowUpDown` |
| More options | `MoreVertical` |
| Close | `X` |
| Back | `ArrowLeft` |
| Forward | `ArrowRight` |
| Download | `Download` |
| Upload | `Upload` |

## Implementation Guidelines

1. **Import at top of file:**
```tsx
import { 
  LayoutDashboard, 
  Inbox, 
  FileText, 
  Building2,
  // ... other icons
} from 'lucide-react'
```

2. **Standard sizing:**
   - Menu items: `className="w-5 h-5"`
   - Buttons: `className="w-4 h-4"`
   - Headers: `className="w-6 h-6"`

3. **Replace emoji strings with JSX:**
```tsx
// Before
icon: '📊'

// After
icon: <LayoutDashboard className="w-5 h-5" />
```

OR if icon is used as component:

```tsx
// Before
<span>{item.icon}</span>

// After
import { iconMap } from '@/lib/iconMap'
const IconComponent = iconMap[item.iconName]
<IconComponent className="w-5 h-5" />
```

## Files to Update

1. `/src/config/menuConfig.ts` - Primary menu configuration
2. `/src/components/Sidebar.tsx` - Sidebar navigation
3. Any other components using emoji icons

## Testing Checklist

- [ ] All menu items show proper SVG icons
- [ ] Icons scale consistently
- [ ] Icons work in both light and dark mode
- [ ] No emojis remain in UI
- [ ] Hover states work properly
- [ ] Icons align properly with text
