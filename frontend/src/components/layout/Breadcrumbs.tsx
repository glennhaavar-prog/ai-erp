'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { findMenuItemByRoute } from '@/config/menuConfig';
import { useTenant } from '@/contexts/TenantContext';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  const { tenantId } = useTenant();
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
    if (!pathname || pathname === '/' || pathname === '/dashboard') {
      return [{ label: 'Dashboard' }];
    }

    const crumbs: BreadcrumbItem[] = [];
    
    // Try to find menu item for current route (with null check)
    const menuItem = pathname ? findMenuItemByRoute(pathname) : null;
    
    if (menuItem) {
      // Simple breadcrumb based on menu structure
      // TODO: Build full parent hierarchy
      crumbs.push({ label: menuItem.label, href: menuItem.route });
    } else if (pathname) {
      // Special handling for /clients/[id] - Glenn's feedback 2026-02-09
      const clientMatch = pathname.match(/^\/clients\/([a-f0-9-]+)$/);
      if (clientMatch) {
        crumbs.push({ label: 'Clients', href: '/' });
        crumbs.push({ 
          label: clientName || 'Loading...',
          href: pathname 
        });
      } else {
        // Fallback: build from pathname segments
        const segments = pathname.split('/').filter(Boolean);
        segments.forEach((segment, index) => {
          const href = '/' + segments.slice(0, index + 1).join('/');
          const label = segment
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          crumbs.push({ label, href });
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
        {/* Home link */}
        <Link 
          href="/dashboard" 
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <Home className="w-4 h-4" />
        </Link>

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
