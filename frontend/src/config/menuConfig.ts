/**
 * Menu Configuration for Kontali ERP
 * 
 * Based on kontali-menu-specification.md
 * Supports two visibility modes: Client View and Multi-Client View
 * 
 * Last updated: 2026-02-09
 */

export interface MenuItem {
  id: string;
  label: string;
  icon: string;
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
  items: MenuItem[];
}

export const menuConfig: MenuCategory[] = [
  {
    id: 'rapporter',
    label: 'RAPPORTER',
    items: [
      {
        id: 'saldobalanse',
        label: 'Saldobalanse',
        icon: '📋',
        route: '/rapporter/saldobalanse',
        visibility: 'client',
      },
      {
        id: 'resultatregnskap',
        label: 'Resultatregnskap',
        icon: '📊',
        route: '/rapporter/resultat',
        visibility: 'client',
      },
      {
        id: 'balanse',
        label: 'Balanse',
        icon: '⚖️',
        route: '/rapporter/balanse',
        visibility: 'client',
      },
      {
        id: 'hovedbok',
        label: 'Hovedbok',
        icon: '📖',
        route: '/rapporter/hovedbok',
        visibility: 'client',
      },
      {
        id: 'leverandorreskontro',
        label: 'Leverandørreskontro',
        icon: '🏢',
        route: '/rapporter/leverandorreskontro',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'kundereskontro',
        label: 'Kundereskontro',
        icon: '👤',
        route: '/rapporter/kundereskontro',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
    ],
  },
  {
    id: 'regnskap',
    label: 'REGNSKAP',
    items: [
      {
        id: 'bilagsforing',
        label: 'Bilagsføring',
        icon: '📄',
        route: '/bilagsforing',
        visibility: 'both',
      },
      {
        id: 'bankavstemming',
        label: 'Bankavstemming',
        icon: '🏦',
        route: '/bankavstemming',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'fremdrift',
        label: 'Fremdrift',
        icon: '📊',
        route: '/fremdrift',
        visibility: 'multi',
      },
      {
        id: 'dashboard-klient',
        label: 'Dashboard klient',
        icon: '📈',
        route: '/dashboard',
        visibility: 'client',
      },
      {
        id: 'avstemming',
        label: 'Avstemming',
        icon: '✓',
        route: '/avstemming',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
    ],
  },
  {
    id: 'salg',
    label: 'SALG',
    items: [
      {
        id: 'faktura',
        label: 'Faktura',
        icon: '💰',
        route: '/faktura',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'repeterende-faktura',
        label: 'Repeterende faktura',
        icon: '🔁',
        route: '/faktura/repeterende',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'produkter',
        label: 'Produkter',
        icon: '📦',
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
    items: [
      {
        id: 'kunder',
        label: 'Kunder',
        icon: '👤',
        route: '/kunder',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'leverandorer',
        label: 'Leverandører',
        icon: '🏢',
        route: '/leverandorer',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'ansatte',
        label: 'Ansatte',
        icon: '👥',
        route: '/ansatte',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'prosjekter',
        label: 'Prosjekter',
        icon: '📁',
        route: '/prosjekter',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'avdelinger',
        label: 'Avdelinger',
        icon: '🏛️',
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
    items: [
      {
        id: 'kontoplan',
        label: 'Kontoplan',
        icon: '🗂️',
        route: '/accounts',
        visibility: 'client',
      },
      {
        id: 'byrainnstillinger',
        label: 'Byråinnstillinger',
        icon: '⚙️',
        route: '/innstillinger/byra',
        visibility: 'multi',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'integrasjoner',
        label: 'Integrasjoner',
        icon: '🔌',
        route: '/innstillinger/integrasjoner',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
      {
        id: 'brukere',
        label: 'Brukere',
        icon: '👥',
        route: '/innstillinger/brukere',
        visibility: 'client',
        disabled: true,
        tooltip: 'Kommer snart',
      },
    ],
  },
];

/**
 * Standalone Chat item (not in any category)
 */
export const chatMenuItem: MenuItem = {
  id: 'chat',
  label: 'Chat',
  icon: '💬',
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
