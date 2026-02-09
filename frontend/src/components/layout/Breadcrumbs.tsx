'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home, Building2 } from 'lucide-react';
import { findMenuItemByRoute } from '@/config/menuConfig';
import { useTenant } from '@/contexts/TenantContext';
import { useClient } from '@/contexts/ClientContext';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  const { tenantId } = useTenant();
  const { selectedClient } = useClient(); // Task 8: Always include client name
  const [clientName, setClientName] = useState<string | null>(null);

  // Fetch client name when on client detail page
  useEffect(() => {
    const fetchClientName = async () => {
      if (!pathname || !tenantId) return;
      
      // Check if we're on a client detail page: /clients/[id]
      const clientMatch = pathname.match(/^\/clients\/([a-f0-9-]+)$/);
      if (clientMatch) {
        const clientId = clientMatch[1];
        try {
          // Fetch all clients and find this one
          const response = await fetch(`http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=${tenantId}`);
          if (response.ok) {
            const data = await response.json();
            const client = data.clients.find((c: any) => c.id === clientId);
            if (client) {
              setClientName(client.name);
            }
          }
        } catch (error) {
          console.error('Failed to fetch client name for breadcrumb:', error);
        }
      } else {
        setClientName(null);
      }
    };
    
    fetchClientName();
  }, [pathname, tenantId]);

  // Build breadcrumb trail from pathname
  const buildBreadcrumbs = (): BreadcrumbItem[] => {
    if (!pathname || pathname === '/') {
      return [{ label: 'Dashboard' }];
    }

    const crumbs: BreadcrumbItem[] = [];
    
    // Task 8: ALWAYS include client name when in client context (Glenn's feedback 2026-02-09)
    // Format: 🏠 > Bergen Byggeservice AS > Resultatregnskap
    if (selectedClient && pathname !== '/') {
      crumbs.push({ 
        label: selectedClient.name, 
        href: `/clients/${selectedClient.id}` 
      });
    }
    
    // Try to find menu item for current route (with null check)
    const menuItem = pathname ? findMenuItemByRoute(pathname) : null;
    
    if (menuItem) {
      // Simple breadcrumb based on menu structure
      crumbs.push({ label: menuItem.label, href: menuItem.route });
    } else if (pathname) {
      // Special handling for /clients/[id]
      const clientMatch = pathname.match(/^\/clients\/([a-f0-9-]+)$/);
      if (clientMatch) {
        // Already added client name above, so just show "Overview" or similar
        crumbs.push({ 
          label: 'Oversikt',
          href: pathname 
        });
      } else {
        // Fallback: build from pathname segments (skip if client already added)
        const segments = pathname.split('/').filter(Boolean);
        const startIndex = selectedClient ? 0 : 0; // Start from beginning if client added
        
        segments.slice(startIndex).forEach((segment, index) => {
          const href = '/' + segments.slice(0, startIndex + index + 1).join('/');
          const label = segment
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          
          // Skip adding duplicate client name
          if (label.toLowerCase() !== 'clients' && label !== selectedClient?.name) {
            crumbs.push({ label, href });
          }
        });
      }
    }

    return crumbs;
  };

  const breadcrumbs = buildBreadcrumbs();

  // Don't show breadcrumbs on dashboard/home
  if (breadcrumbs.length === 0 || (breadcrumbs.length === 1 && breadcrumbs[0].label === 'Dashboard')) {
    return null;
  }

  return (
    <nav className="h-12 border-b border-border bg-card/50 flex items-center px-6">
      <div className="flex items-center gap-2 text-sm">
        {/* Home link - Task 16: Contextual home icon */}
        {selectedClient ? (
          <Link 
            href={`/clients/${selectedClient.id}`}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Klientens dashboard"
          >
            <Home className="w-4 h-4" />
          </Link>
        ) : (
          <Link 
            href="/" 
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Global oversikt"
          >
            <Building2 className="w-4 h-4" />
          </Link>
        )}

        {/* Breadcrumb items */}
        {breadcrumbs.map((crumb, index) => (
          <React.Fragment key={index}>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
            {index === breadcrumbs.length - 1 ? (
              // Last item (current page) - not clickable
              <span className="font-medium text-foreground">{crumb.label}</span>
            ) : (
              // Intermediate items - clickable
              <Link
                href={crumb.href || '#'}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </React.Fragment>
        ))}
      </div>
    </nav>
  );
}
