/**
 * Global Search Command Palette (Cmd+K / Ctrl+K)
 * Search across: Suppliers, Customers, Invoices, Vouchers, Accounts
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Command } from 'cmdk';
import { useRouter } from 'next/navigation';
import { 
  MagnifyingGlassIcon, 
  UserIcon, 
  BuildingOfficeIcon,
  DocumentTextIcon,
  ReceiptPercentIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';

interface SearchResult {
  id: string;
  type: 'supplier' | 'customer' | 'invoice' | 'voucher' | 'account';
  title: string;
  subtitle?: string;
  url: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentItems, setRecentItems] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // Load recent items from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('globalSearch_recent');
    if (stored) {
      try {
        setRecentItems(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent items:', e);
      }
    }
  }, []);

  // Save recent items to localStorage
  const saveRecentItem = useCallback((item: SearchResult) => {
    setRecentItems((prev) => {
      const filtered = prev.filter((i) => i.id !== item.id || i.type !== item.type);
      const updated = [item, ...filtered].slice(0, 10);
      localStorage.setItem('globalSearch_recent', JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Search across all entities
  const performSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const [suppliers, customers, vouchers, accounts] = await Promise.all([
        axios.get(`${API_BASE_URL}/suppliers?search=${encodeURIComponent(query)}`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE_URL}/customers?search=${encodeURIComponent(query)}`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE_URL}/vouchers?search=${encodeURIComponent(query)}`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE_URL}/accounts?search=${encodeURIComponent(query)}`).catch(() => ({ data: [] })),
      ]);

      const searchResults: SearchResult[] = [
        ...(suppliers.data || []).slice(0, 5).map((s: any) => ({
          id: s.id || s.supplier_id,
          type: 'supplier' as const,
          title: s.company_name || s.name,
          subtitle: s.org_number,
          url: `/kontakter/leverandorer/${s.id || s.supplier_id}`,
        })),
        ...(customers.data || []).slice(0, 5).map((c: any) => ({
          id: c.id || c.customer_id,
          type: 'customer' as const,
          title: c.name,
          subtitle: c.org_number || c.birth_number,
          url: `/kontakter/kunder/${c.id || c.customer_id}`,
        })),
        ...(vouchers.data || []).slice(0, 5).map((v: any) => ({
          id: v.id || v.voucher_id,
          type: 'voucher' as const,
          title: `Bilag #${v.voucher_number || v.id}`,
          subtitle: v.description || v.supplier_name,
          url: `/bilag/${v.id || v.voucher_id}`,
        })),
        ...(accounts.data || []).slice(0, 5).map((a: any) => ({
          id: a.id || a.account_id,
          type: 'account' as const,
          title: `${a.account_number} - ${a.account_name}`,
          subtitle: a.account_type,
          url: `/accounts?highlight=${a.account_number}`,
        })),
      ];

      setResults(searchResults);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search, performSearch]);

  // Keyboard shortcut: Cmd+K / Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleSelect = useCallback((item: SearchResult) => {
    saveRecentItem(item);
    setOpen(false);
    setSearch('');
    router.push(item.url);
  }, [router, saveRecentItem]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'supplier': return <BuildingOfficeIcon className="w-4 h-4" />;
      case 'customer': return <UserIcon className="w-4 h-4" />;
      case 'voucher': return <DocumentTextIcon className="w-4 h-4" />;
      case 'invoice': return <ReceiptPercentIcon className="w-4 h-4" />;
      case 'account': return <BanknotesIcon className="w-4 h-4" />;
      default: return <MagnifyingGlassIcon className="w-4 h-4" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'supplier': return 'Leverandør';
      case 'customer': return 'Kunde';
      case 'voucher': return 'Bilag';
      case 'invoice': return 'Faktura';
      case 'account': return 'Konto';
      default: return '';
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50" onClick={() => setOpen(false)}>
      <div className="fixed left-1/2 top-1/3 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl">
        <Command 
          className="rounded-lg border border-gray-300 dark:border-gray-700 shadow-2xl bg-white dark:bg-gray-900"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center border-b border-gray-200 dark:border-gray-700 px-3">
            <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 mr-2" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Søk etter leverandører, kunder, bilag, kontoer..."
              className="flex h-12 w-full bg-transparent py-3 text-sm outline-none placeholder:text-gray-400 disabled:cursor-not-allowed disabled:opacity-50 text-gray-900 dark:text-gray-100"
            />
            <kbd className="hidden sm:inline-block pointer-events-none h-5 select-none items-center gap-1 rounded border border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-1.5 font-mono text-[10px] font-medium text-gray-600 dark:text-gray-400 ml-2">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-[400px] overflow-y-auto p-2">
            {loading && (
              <div className="py-6 text-center text-sm text-gray-500">
                Søker...
              </div>
            )}

            {!loading && search && results.length === 0 && (
              <div className="py-6 text-center text-sm text-gray-500">
                Ingen resultater funnet
              </div>
            )}

            {!search && recentItems.length > 0 && (
              <Command.Group heading="Nylig besøkt">
                {recentItems.map((item) => (
                  <Command.Item
                    key={`${item.type}-${item.id}`}
                    value={`${item.type}-${item.id}`}
                    onSelect={() => handleSelect(item)}
                    className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 aria-selected:bg-gray-100 dark:aria-selected:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <div className="text-gray-500 dark:text-gray-400">
                      {getIcon(item.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{item.title}</div>
                      {item.subtitle && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {item.subtitle}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500">
                      {getTypeLabel(item.type)}
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {!loading && search && results.length > 0 && (
              <>
                {['supplier', 'customer', 'voucher', 'account'].map((type) => {
                  const typeResults = results.filter((r) => r.type === type);
                  if (typeResults.length === 0) return null;

                  return (
                    <Command.Group key={type} heading={getTypeLabel(type)}>
                      {typeResults.map((item) => (
                        <Command.Item
                          key={`${item.type}-${item.id}`}
                          value={`${item.type}-${item.id}-${item.title}`}
                          onSelect={() => handleSelect(item)}
                          className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 aria-selected:bg-gray-100 dark:aria-selected:bg-gray-800 text-gray-900 dark:text-gray-100"
                        >
                          <div className="text-gray-500 dark:text-gray-400">
                            {getIcon(item.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{item.title}</div>
                            {item.subtitle && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                {item.subtitle}
                              </div>
                            )}
                          </div>
                        </Command.Item>
                      ))}
                    </Command.Group>
                  );
                })}
              </>
            )}
          </Command.List>

          <div className="border-t border-gray-200 dark:border-gray-700 px-3 py-2 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center justify-between">
              <span>Bruk piltaster for å navigere</span>
              <div className="flex gap-2">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-700">
                  ↑↓
                </kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-700">
                  Enter
                </kbd>
              </div>
            </div>
          </div>
        </Command>
      </div>
    </div>
  );
}
