/**
 * Icon mapping utility for Kontali ERP
 * Maps icon names to Lucide React components
 */

import {
  LayoutDashboard,
  Inbox,
  ClipboardList,
  FileText,
  Building2,
  TrendingUp,
  Banknote,
  BookOpen,
  Scale,
  Building,
  User,
  Users,
  RefreshCw,
  Package,
  FolderOpen,
  Landmark,
  Archive,
  Settings,
  Plug,
  MessageSquare,
  Check,
  CheckCircle2,
  Circle,
  AlertCircle,
  XCircle,
  Loader2,
  Search,
  Filter,
  ArrowUpDown,
  MoreVertical,
  X,
  ArrowLeft,
  ArrowRight,
  Download,
  Upload,
  type LucideIcon,
} from 'lucide-react';

export const iconMap: Record<string, LucideIcon> = {
  // Primary Navigation
  dashboard: LayoutDashboard,
  inbox: Inbox,
  clipboardList: ClipboardList,
  fileText: FileText,
  building2: Building2,
  trendingUp: TrendingUp,
  banknote: Banknote,
  bookOpen: BookOpen,
  scale: Scale,
  building: Building,
  user: User,
  users: Users,
  refreshCw: RefreshCw,
  package: Package,
  folderOpen: FolderOpen,
  landmark: Landmark,
  archive: Archive,
  settings: Settings,
  plug: Plug,
  messageSquare: MessageSquare,
  check: Check,
  checkCircle2: CheckCircle2,
  circle: Circle,
  
  // Status & Actions
  alertCircle: AlertCircle,
  xCircle: XCircle,
  loader2: Loader2,
  search: Search,
  filter: Filter,
  arrowUpDown: ArrowUpDown,
  moreVertical: MoreVertical,
  x: X,
  arrowLeft: ArrowLeft,
  arrowRight: ArrowRight,
  download: Download,
  upload: Upload,
};

export type IconName = keyof typeof iconMap;

/**
 * Get icon component by name
 */
export function getIcon(name: IconName): LucideIcon {
  return iconMap[name] || FileText; // Fallback to FileText
}
