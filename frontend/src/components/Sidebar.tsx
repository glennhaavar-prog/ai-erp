'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

// Interfaces
interface NavItem {
  id: string;
  label: string;
  icon: string;
  path?: string;
  badge?: string | number;
  badgeVariant?: 'blue' | 'amber' | 'green' | 'red';
  enabled: boolean;
  children?: NavItem[];
}

interface NavSection {
  label: string;
  items: NavItem[];
}

export const Sidebar = () => {
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['innboks']));

  // Complete menu structure from wireframe
  const navSections: NavSection[] = [
    {
      label: 'Oversikt',
      items: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          icon: '📊',
          path: '/',
          enabled: true,
        },
        {
          id: 'innboks',
          label: 'Innboks',
          icon: '📥',
          badge: 12,
          badgeVariant: 'amber',
          enabled: true,
          children: [
            {
              id: 'review-queue',
              label: 'Review Queue',
              icon: '·',
              path: '/review-queue',
              badge: 8,
              badgeVariant: 'blue',
              enabled: true,
            },
            {
              id: 'leverandorfakturaer',
              label: 'Leverandørfakturaer',
              icon: '·',
              path: '/upload',
              enabled: true,
            },
            {
              id: 'banktransaksjoner',
              label: 'Banktransaksjoner',
              icon: '·',
              path: '/bank',
              enabled: true,
            },
            {
              id: 'kundefakturaer',
              label: 'Kundefakturaer',
              icon: '·',
              path: '/customer-invoices',
              enabled: true,
            },
          ],
        },
      ],
    },
    {
      label: 'Regnskap',
      items: [
        {
          id: 'bokforing',
          label: 'Bokføring',
          icon: '📒',
          enabled: true,
          children: [
            {
              id: 'hovedbok',
              label: 'Hovedbok',
              icon: '·',
              path: '/hovedbok',
              enabled: true,
            },
            {
              id: 'bilagsoversikt',
              label: 'Bilagsoversikt',
              icon: '·',
              path: '/audit',
              enabled: true,
            },
            {
              id: 'kontoplan',
              label: 'Kontoplan',
              icon: '·',
              path: '/accounts',
              enabled: true,
            },
          ],
        },
        {
          id: 'fakturering',
          label: 'Fakturering',
          icon: '💰',
          enabled: false,
          children: [
            {
              id: 'ny-faktura',
              label: 'Ny faktura',
              icon: '·',
              enabled: false,
            },
            {
              id: 'fakturaoversikt',
              label: 'Fakturaoversikt',
              icon: '·',
              enabled: false,
            },
          ],
        },
        {
          id: 'kontakter',
          label: 'Kunder & Leverandører',
          icon: '👥',
          enabled: false,
          children: [
            {
              id: 'kunderegister',
              label: 'Kunderegister',
              icon: '·',
              enabled: false,
            },
            {
              id: 'leverandorregister',
              label: 'Leverandørregister',
              icon: '·',
              enabled: false,
            },
          ],
        },
        {
          id: 'periodisering',
          label: 'Periodisering',
          icon: '📅',
          path: '/accruals',
          enabled: true,
        },
        {
          id: 'period-close',
          label: 'Månedsavslutning',
          icon: '🔒',
          path: '/period-close',
          enabled: true,
        },
      ],
    },
    {
      label: 'Analyse',
      items: [
        {
          id: 'rapporter',
          label: 'Rapporter',
          icon: '📈',
          enabled: true,
          children: [
            {
              id: 'resultatregnskap',
              label: 'Resultatregnskap',
              icon: '·',
              enabled: false,
            },
            {
              id: 'balanse',
              label: 'Balanse',
              icon: '·',
              path: '/saldobalanse',
              enabled: true,
            },
            {
              id: 'mva-oppgave',
              label: 'MVA-oppgave',
              icon: '·',
              path: '/vat',
              enabled: true,
            },
          ],
        },
      ],
    },
    {
      label: 'Verktøy',
      items: [
        {
          id: 'ai-chat',
          label: 'AI Chat',
          icon: '💬',
          path: '/chat',
          enabled: true,
        },
      ],
    },
  ];

  const footerItems: NavItem[] = [
    {
      id: 'innstillinger',
      label: 'Innstillinger',
      icon: '⚙️',
      enabled: false,
    },
  ];

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const isActive = (item: NavItem): boolean => {
    if (!item.path) return false;
    if (pathname === item.path) return true;
    // Check if any child is active
    if (item.children) {
      return item.children.some(child => child.path === pathname);
    }
    return false;
  };

  const renderNavItem = (item: NavItem, isChild: boolean = false) => {
    const active = isActive(item);
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedSections.has(item.id);

    // Non-implemented items
    if (!item.enabled) {
      return (
        <div
          key={item.id}
          className={`
            flex items-center gap-2.5 px-3 rounded-md cursor-not-allowed
            ${isChild ? 'py-1.5 text-[13px]' : 'py-2 text-[13.5px]'}
            text-text-muted font-medium
            opacity-35
            relative group
          `}
          title="Kommer snart"
        >
          <span className="w-[18px] flex items-center justify-center text-[15px] shrink-0">
            {item.icon}
          </span>
          <span>{item.label}</span>
          {item.badge && (
            <span className={`ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full min-w-[20px] text-center ${
              item.badgeVariant === 'amber' ? 'bg-accent-amber text-black' :
              item.badgeVariant === 'green' ? 'bg-accent-green text-black' :
              item.badgeVariant === 'red' ? 'bg-accent-red text-white' :
              'bg-accent-blue text-white'
            }`}>
              {item.badge}
            </span>
          )}
          {hasChildren && (
            <span className="ml-auto text-[11px] text-text-muted">▶</span>
          )}
        </div>
      );
    }

    // Parent items with children (accordion)
    if (hasChildren) {
      return (
        <div key={item.id}>
          <div
            onClick={() => toggleSection(item.id)}
            className={`
              flex items-center gap-2.5 px-3 rounded-md cursor-pointer
              py-2 text-[13.5px]
              transition-all duration-150
              ${active 
                ? 'bg-bg-active text-accent-blue' 
                : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
              }
              font-medium select-none
            `}
          >
            <span className={`w-[18px] flex items-center justify-center text-[15px] shrink-0 ${active ? 'opacity-100' : 'opacity-60'}`}>
              {item.icon}
            </span>
            <span>{item.label}</span>
            {item.badge && (
              <span className={`ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full min-w-[20px] text-center ${
                item.badgeVariant === 'amber' ? 'bg-accent-amber text-black' :
                item.badgeVariant === 'green' ? 'bg-accent-green text-black' :
                item.badgeVariant === 'red' ? 'bg-accent-red text-white' :
                'bg-accent-blue text-white'
              }`}>
                {item.badge}
              </span>
            )}
            <span className={`ml-auto text-[11px] text-text-muted transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}>
              ▶
            </span>
          </div>
          {isExpanded && (
            <div className="pl-4 mt-0.5 space-y-0.5">
              {item.children?.map(child => renderNavItem(child, true))}
            </div>
          )}
        </div>
      );
    }

    // Leaf items with links
    const ItemContent = (
      <>
        <span className={`w-[18px] flex items-center justify-center text-[15px] shrink-0 ${active ? 'opacity-100' : 'opacity-60'}`}>
          {item.icon}
        </span>
        <span>{item.label}</span>
        {item.badge && (
          <span className={`ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full min-w-[20px] text-center ${
            item.badgeVariant === 'amber' ? 'bg-accent-amber text-black' :
            item.badgeVariant === 'green' ? 'bg-accent-green text-black' :
            item.badgeVariant === 'red' ? 'bg-accent-red text-white' :
            'bg-accent-blue text-white'
          }`}>
            {item.badge}
          </span>
        )}
      </>
    );

    if (item.path) {
      return (
        <Link
          key={item.id}
          href={item.path}
          className={`
            flex items-center gap-2.5 px-3 rounded-md
            ${isChild ? 'py-1.5 text-[13px]' : 'py-2 text-[13.5px]'}
            transition-all duration-150
            ${active 
              ? isChild 
                ? 'bg-accent-blue-dim text-accent-blue' 
                : 'bg-bg-active text-accent-blue'
              : isChild
                ? 'text-text-muted hover:text-text-secondary'
                : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
            }
            font-medium
          `}
        >
          {ItemContent}
        </Link>
      );
    }

    return (
      <div
        key={item.id}
        className={`
          flex items-center gap-2.5 px-3 rounded-md
          ${isChild ? 'py-1.5 text-[13px]' : 'py-2 text-[13.5px]'}
          text-text-secondary font-medium
        `}
      >
        {ItemContent}
      </div>
    );
  };

  return (
    <aside className="w-[260px] h-screen bg-bg-sidebar border-r border-border flex flex-col shrink-0 overflow-y-auto scrollbar-thin scrollbar-thumb-border-light scrollbar-track-transparent">
      {/* Logo */}
      <div className="px-[22px] py-5 pb-4 border-b border-border flex items-center gap-2.5">
        <div className="w-8 h-8 bg-gradient-to-br from-accent-blue to-accent-purple rounded-lg flex items-center justify-center font-bold text-[15px] text-white tracking-tight">
          K
        </div>
        <span className="text-[18px] font-bold tracking-tight bg-gradient-to-br from-text-primary to-[#a0a4b8] bg-clip-text text-transparent">
          Kontali
        </span>
        <span className="ml-auto text-[9px] font-semibold uppercase tracking-wider text-accent-blue bg-accent-blue-dim px-1.5 py-0.5 rounded">
          AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2.5 py-3">
        {navSections.map((section, idx) => (
          <div key={idx} className="mb-4">
            <div className="text-[10px] font-semibold uppercase tracking-[1.2px] text-text-muted px-3 pt-4 pb-1.5">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.items.map(item => renderNavItem(item))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-2.5 py-3 border-t border-border">
        <div className="space-y-0.5">
          {footerItems.map(item => renderNavItem(item))}
        </div>
      </div>
    </aside>
  );
};
