/**
 * Menu Configuration for Kontali ERP
 * 
 * Based on kontali-menu-specification.md
 * Supports two visibility modes: Client View and Multi-Client View
 * 
 * Last updated: 2026-02-09
 */

import { type IconName } from '@/lib/iconMap';

export interface MenuItem {
  id: string;
  label: string;
  icon: IconName;
  route?: string;
  disabled?: boolean;
  tooltip?: string;
  children?: MenuItem[];
  /** Visibility: 'client' | 'multi' | 'both' */
  visibility: 'client' | 'multi' | 'both';
}

export interface MenuCategory {
  id: string;
  label: string;
  /** Icon color for this section (Tailwind color class) */
  color?: string;
  items: MenuItem[];
}

export const menuConfig: MenuCategory[] = [
  {
    id: 'oversikt',
    label: 'OVERSIKT',
    color: 'text-accent', // Cyan
    items: [
      {
        id: 'hovedoversikt',
        label: 'Hovedoversikt',
        icon: 'dashboard',
        route: '/',
        visibility: 'both',
      },
    ],
  },
  {
    id: 'innboks',
    label: 'INNBOKS',
    color: 'text-success', // Green
    items: [
      {
        id: 'behandlingsko',
        label: 'Leverandørbilag',
        icon: 'checkCircle2',
        route: '/review-queue',
        visibility: 'both',
      },
      {
        id: 'andre-bilag',
        label: 'Andre bilag',
        icon: 'clipboardList',
        route: '/andre-bilag',
        visibility: 'both',
      },
    ],
  },
  {
    id: 'rapporter',
    label: 'RAPPORTER',
    color: 'text-warning', // Amber
    items: [
      {
        id: 'saldobalanse',
        label: 'Saldobalanse',
        icon: 'clipboardList',
        route: '/rapporter/saldobalanse',
        visibility: 'client',
      },
      {
        id: 'resultatregnskap',
        label: 'Resultatregnskap',
        icon: 'trendingUp',
        route: '/rapporter/resultat',
        visibility: 'client',
      },
      {
        id: 'balanse',
        label: 'Balanse',
        icon: 'scale',
        route: '/rapporter/balanse',
        visibility: 'client',
      },
      {
        id: 'hovedbok',
        label: 'Hovedbok',
        icon: 'bookOpen',
        route: '/rapporter/hovedbok',
        visibility: 'client',
      },
      {
        id: 'leverandorreskontro',
        label: 'Leverandørreskontro',
        icon: 'building',
        route: '/reskontro/leverandorer',
        visibility: 'client',
      },
      {
        id: 'kundereskontro',
        label: 'Kundereskontro',
        icon: 'user',
        route: '/reskontro/kunder',
        visibility: 'client',
      },
    ],
  },
  {
    id: 'analyse',
    label: 'ANALYSE',
    color: 'text-primary', // Teal
    items: [
      {
        id: 'bilagssplit',
        label: 'Bilagssplit og kontroll',
        icon: 'barChart3',
        route: '/bilagssplit',
        visibility: 'both',
        disabled: false,
        tooltip: 'Oversikt over alle bilag med behandlingshistorikk og audit trail',
      },
    ],
  },
  {
    id: 'regnskap',
    label: 'REGNSKAP',
    color: 'text-accent', // Cyan
    items: [
      {
        id: 'bilagsforing',
        label: 'Bilagsføring',
        icon: 'fileText',
        route: '/bilagsforing',
        visibility: 'both',
      },
      {
        id: 'bilagsjournal',
        label: 'Bilagsjournal',
        icon: 'bookOpen',
        route: '/bilag/journal',
        visibility: 'client',
      },
      {
        id: 'bankavstemming',
        label: 'Bankavstemming',
        icon: 'building2',
        route: '/bank-reconciliation',
        visibility: 'client',
        disabled: false,
      },
      {
        id: 'oppgaver',
        label: 'Oppgaver',
        icon: 'checkCircle2',
        route: '/oppgaver',
        visibility: 'client',
        disabled: false,
      },
    ],
  },
  {
    id: 'salg',
    label: 'SALG',
    color: 'text-success', // Green
    items: [
      {
        id: 'faktura',
        label: 'Faktura',
        icon: 'banknote',
        route: '/faktura',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'repeterende-faktura',
        label: 'Repeterende faktura',
        icon: 'refreshCw',
        route: '/faktura/repeterende',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'produkter',
        label: 'Produkter',
        icon: 'package',
        route: '/produkter',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
    ],
  },
  {
    id: 'register',
    label: 'REGISTER',
    color: 'text-secondary', // Violet
    items: [
      {
        id: 'kunder',
        label: 'Kunder',
        icon: 'user',
        route: '/kontakter/kunder',
        visibility: 'client',
        disabled: false,
      },
      {
        id: 'leverandorer',
        label: 'Leverandører',
        icon: 'building',
        route: '/kontakter/leverandorer',
        visibility: 'client',
        disabled: false,
      },
      {
        id: 'ansatte',
        label: 'Ansatte',
        icon: 'users',
        route: '/ansatte',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'prosjekter',
        label: 'Prosjekter',
        icon: 'folderOpen',
        route: '/prosjekter',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'avdelinger',
        label: 'Avdelinger',
        icon: 'landmark',
        route: '/avdelinger',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
    ],
  },
  {
    id: 'innstillinger',
    label: 'INNSTILLINGER',
    color: 'text-muted-foreground', // Muted gray
    items: [
      {
        id: 'kontoplan',
        label: 'Kontoplan',
        icon: 'archive',
        route: '/accounts',
        visibility: 'client',
      },
      {
        id: 'firmainnstillinger',
        label: 'Firmainnstillinger',
        icon: 'settings',
        route: '/innstillinger',
        visibility: 'client',
      },
      {
        id: 'aapningsbalanse',
        label: 'Åpningsbalanse',
        icon: 'clipboardList',
        route: '/aapningsbalanse',
        visibility: 'client',
      },
      {
        id: 'klienter',
        label: 'Klienter',
        icon: 'building',
        route: '/innstillinger/klienter',
        visibility: 'multi',
        disabled: false,
      },
      {
        id: 'byrainnstillinger',
        label: 'Byråinnstillinger',
        icon: 'settings',
        route: '/innstillinger/byra',
        visibility: 'multi',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'integrasjoner',
        label: 'Integrasjoner',
        icon: 'plug',
        route: '/innstillinger/integrasjoner',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'brukere',
        label: 'Brukere',
        icon: 'users',
        route: '/innstillinger/brukere',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'bankintegrasjon',
        label: 'Bankintegrasjon (Tink)',
        icon: 'plug',
        route: '/import/bankintegrasjon',
        visibility: 'both',
      },
    ],
  },
  {
    id: 'verktoy',
    label: 'VERKTØY',
    color: 'text-primary', // Teal
    items: [
      {
        id: 'ai-chat',
        label: 'AI Chat',
        icon: 'messageSquare',
        route: '/chat',
        visibility: 'both',
        disabled: false,
      },
      {
        id: 'nlq',
        label: 'Spør data',
        icon: 'search',
        route: '/nlq',
        visibility: 'both',
        disabled: false,
        tooltip: 'Naturlig språk spørring - still spørsmål om regnskapsdata',
      },
      {
        id: 'tillitsmodell',
        label: 'Tillitsmodell',
        icon: 'shield',
        route: '/trust',
        visibility: 'client',
        disabled: false,
        tooltip: 'Oversikt og kontroll - ingenting forsvinner',
      },
    ],
  },
  {
    id: 'arkiv',
    label: 'ARKIV',
    color: 'text-muted-foreground', // Gray
    items: [
      {
        id: 'leverandorfakturaer',
        label: 'Leverandørfakturaer',
        icon: 'archive',
        route: '/upload',
        visibility: 'both',
      },
      {
        id: 'kundefakturaer',
        label: 'Kundefakturaer',
        icon: 'archive',
        route: '/customer-invoices',
        visibility: 'both',
      },
      {
        id: 'banktransaksjoner',
        label: 'Banktransaksjoner',
        icon: 'upload',
        route: '/import/banktransaksjoner',
        visibility: 'both',
      },
    ],
  },
];

/**
 * Standalone Chat item (not in any category) - kept for backwards compatibility
 */
export const chatMenuItem: MenuItem = {
  id: 'chat',
  label: 'Chat',
  icon: 'messageSquare',
  route: '/chat',
  visibility: 'both',
};

/**
 * Get menu items filtered by view mode
 * @param viewMode 'client' or 'multi'
 */
export function getMenuForView(viewMode: 'client' | 'multi'): MenuCategory[] {
  return menuConfig
    .map(category => ({
      ...category,
      items: category.items.filter(item => 
        item.visibility === viewMode || item.visibility === 'both'
      ),
    }))
    .filter(category => category.items.length > 0); // Hide empty categories
}

/**
 * Flatten menu structure for route matching
 */
export function getAllRoutes(): string[] {
  const routes: string[] = [];
  
  function traverse(items: MenuItem[]) {
    items.forEach(item => {
      if (item.route && !item.disabled) {
        routes.push(item.route);
      }
      if (item.children) {
        traverse(item.children);
      }
    });
  }
  
  menuConfig.forEach(category => traverse(category.items));
  
  // Add chat route
  if (chatMenuItem.route && !chatMenuItem.disabled) {
    routes.push(chatMenuItem.route);
  }
  
  return routes;
}

/**
 * Find menu item by route (case-insensitive matching)
 */
export function findMenuItemByRoute(route: string): MenuItem | null {
  const normalizedRoute = route.toLowerCase();
  
  function search(items: MenuItem[]): MenuItem | null {
    for (const item of items) {
      if (item.route?.toLowerCase() === normalizedRoute) return item;
      if (item.children) {
        const found = search(item.children);
        if (found) return found;
      }
    }
    return null;
  }
  
  for (const category of menuConfig) {
    const found = search(category.items);
    if (found) return found;
  }
  
  // Check chat item
  if (chatMenuItem.route?.toLowerCase() === normalizedRoute) {
    return chatMenuItem;
  }
  
  return null;
}
