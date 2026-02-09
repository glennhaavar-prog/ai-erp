'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, Menu, X } from 'lucide-react';
import { getMenuForView, chatMenuItem, type MenuItem, type MenuCategory } from '@/config/menuConfig';
import { useViewMode } from '@/contexts/ViewModeContext';
import { getIcon } from '@/lib/iconMap';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const { viewMode } = useViewMode();
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['regnskap']));
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Get filtered menu based on view mode
  const filteredMenuConfig = getMenuForView(viewMode === 'client' ? 'client' : 'multi');

  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleItem = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const isActive = (route?: string) => {
    if (!route) return false;
    // Case-insensitive matching
    const normalizedPathname = pathname?.toLowerCase();
    const normalizedRoute = route.toLowerCase();
    return normalizedPathname === normalizedRoute || normalizedPathname?.startsWith(normalizedRoute + '/');
  };

  const renderMenuItem = (item: MenuItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.id);
    const active = isActive(item.route);
    const IconComponent = getIcon(item.icon);

    if (hasChildren) {
      // Parent item with children
      return (
        <div key={item.id} className="mb-1">
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleItem(item.id);
            }}
            className={`
              w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer
              ${collapsed ? 'justify-center' : ''}
              ${active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}
            `}
            style={{ paddingLeft: collapsed ? undefined : `${level * 12 + 16}px` }}
          >
            <IconComponent className="w-5 h-5 flex-shrink-0" />
            {!collapsed && (
              <>
                <span className="flex-1 text-left">{item.label}</span>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </>
            )}
          </button>

          <AnimatePresence>
            {isExpanded && !collapsed && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                {item.children?.map(child => renderMenuItem(child, level + 1))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    }

    // Leaf item (no children)
    const ItemContent = (
      <div
        className={`
          flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
          ${collapsed ? 'justify-center' : ''}
          ${active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}
          ${item.disabled ? 'opacity-35 cursor-not-allowed' : 'cursor-pointer'}
        `}
        style={{ paddingLeft: collapsed ? undefined : `${level * 12 + 16}px` }}
        title={item.disabled ? item.tooltip : undefined}
      >
        <IconComponent className="w-5 h-5 flex-shrink-0" />
        {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
      </div>
    );

    if (item.disabled || !item.route) {
      return (
        <div key={item.id} className="mb-1">
          {ItemContent}
        </div>
      );
    }

    return (
      <Link key={item.id} href={item.route} className="block mb-1">
        {ItemContent}
      </Link>
    );
  };

  const renderChatItem = () => {
    const active = isActive(chatMenuItem.route);
    const ChatIcon = getIcon(chatMenuItem.icon);
    
    const ItemContent = (
      <div
        className={`
          flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer
          ${collapsed ? 'justify-center' : ''}
          ${active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}
        `}
      >
        <ChatIcon className="w-5 h-5 flex-shrink-0" />
        {!collapsed && <span className="flex-1 text-left">{chatMenuItem.label}</span>}
      </div>
    );

    if (!chatMenuItem.route) {
      return <div key={chatMenuItem.id} className="mb-1">{ItemContent}</div>;
    }

    return (
      <Link key={chatMenuItem.id} href={chatMenuItem.route} className="block mb-1">
        {ItemContent}
      </Link>
    );
  };

  return (
    <aside
      className={`
        relative bg-card border-r border-border transition-all duration-300 flex flex-col
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <Link href="/fremdrift">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
            >
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold">
                K
              </div>
              <span className="text-lg font-bold text-foreground">Kontali</span>
            </motion.div>
          </Link>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground"
        >
          {collapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
        </button>
      </div>

      {/* Menu */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {filteredMenuConfig.map((category) => (
          <div key={category.id} className="mb-6">
            {!collapsed && (
              <div className="px-4 mb-2">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {category.label}
                </span>
              </div>
            )}
            {category.items.map(item => renderMenuItem(item))}
          </div>
        ))}

        {/* Chat standalone item */}
        {!collapsed && (
          <div className="mb-6 px-4">
            <div className="border-t border-border mb-4"></div>
          </div>
        )}
        {renderChatItem()}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-border">
          <div className="text-xs text-muted-foreground">
            <p className="font-medium">
              {viewMode === 'client' ? 'Klient-visning' : 'Multi-klient-visning'}
            </p>
            <p className="mt-1">Demo-miljø</p>
          </div>
        </div>
      )}
    </aside>
  );
}
