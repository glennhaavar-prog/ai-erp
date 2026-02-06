'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  HomeIcon, 
  ChartBarIcon, 
  DocumentTextIcon, 
  ChatBubbleLeftRightIcon,
  CalculatorIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';

export const Navigation = () => {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Multi-Client Dashboard', icon: HomeIcon },
    { href: '/bank', label: 'Bank Reconciliation', icon: ChartBarIcon },
    { href: '/customer-invoices', label: 'Customer Invoices', icon: DocumentTextIcon },
    { href: '/dashboard', label: 'Trust Dashboard', icon: ChartBarIcon },
    { href: '/hovedbok', label: 'Hovedbok', icon: DocumentTextIcon },
    { href: '/accounts', label: 'Kontoplan', icon: DocumentTextIcon },
    { href: '/vat', label: 'MVA-koder', icon: CalculatorIcon },
    { href: '/audit', label: 'Revisjonslogg', icon: ClipboardDocumentListIcon },
  ];

  return (
    <nav className="flex items-center gap-1">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;
        
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg transition-colors
              ${isActive 
                ? 'bg-accent-blue text-white' 
                : 'text-gray-300 hover:bg-dark-hover hover:text-gray-100'
              }
            `}
          >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};
