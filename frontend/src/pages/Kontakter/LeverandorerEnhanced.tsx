/**
 * Leverandører (Suppliers) List Page - ENHANCED with UX improvements
 * Features:
 * - Bulk selection with checkboxes
 * - Quick add modal
 * - Keyboard shortcuts (j/k navigation, n for new, d for delete)
 * - Global search integration (Cmd+K)
 */
'use client';

import { GetServerSideProps } from 'next';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  EyeIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useClient } from '@/contexts/ClientContext';
import { suppliersApi, Supplier } from '@/api/contacts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { QuickAddButton } from '@/components/QuickAddModal';
import { BulkActions, useBulkSelection } from '@/components/BulkActions';
import { useKeyboardShortcuts, useListNavigation } from '@/hooks/useKeyboardShortcuts';

export const LeverandorerEnhanced: React.FC = () => {
  const router = useRouter();
  const { selectedClient } = useClient();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('active');
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Bulk selection
  const {
    selectedIds,
    toggleSelection,
    toggleAll,
    clearSelection,
    isSelected,
    isAllSelected,
    isSomeSelected,
  } = useBulkSelection(suppliers);

  useEffect(() => {
    if (selectedClient?.id) {
      fetchSuppliers();
    }
  }, [selectedClient, searchQuery, statusFilter]);

  const fetchSuppliers = async () => {
    if (!selectedClient?.id) return;

    try {
      setLoading(true);
      const params: any = {
        client_id: selectedClient.id,
        limit: 100,
      };

      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      if (searchQuery) {
        params.search = searchQuery;
      }

      const data = await suppliersApi.list(params);
      setSuppliers(data);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      toast.error('Kunne ikke laste leverandører');
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    router.push('/kontakter/leverandorer/ny');
  };

  const handleView = (supplierId: string) => {
    router.push(`/kontakter/leverandorer/${supplierId}`);
  };

  const handleEdit = (supplierId: string) => {
    router.push(`/kontakter/leverandorer/${supplierId}/rediger`);
  };

  const handleDeactivate = async (supplier: Supplier) => {
    if (!confirm(`Er du sikker på at du vil deaktivere ${supplier.company_name}?`)) {
      return;
    }

    try {
      await suppliersApi.deactivate(supplier.id);
      toast.success(`${supplier.company_name} er deaktivert`);
      fetchSuppliers();
    } catch (error) {
      console.error('Error deactivating supplier:', error);
      toast.error('Kunne ikke deaktivere leverandør');
    }
  };

  // Keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'n',
        description: 'Ny leverandør',
        category: 'actions',
        action: handleCreateNew,
      },
      {
        key: 'd',
        description: 'Deaktiver valgt',
        category: 'actions',
        action: () => {
          if (focusedIndex >= 0 && focusedIndex < suppliers.length) {
            handleDeactivate(suppliers[focusedIndex]);
          }
        },
      },
    ],
  });

  // List navigation with j/k
  useListNavigation(
    suppliers,
    focusedIndex,
    setFocusedIndex,
    (index) => handleView(suppliers[index].id)
  );

  // Listen for custom keyboard events
  useEffect(() => {
    const handleKeyboardNew = () => handleCreateNew();
    const handleKeyboardDelete = () => {
      if (focusedIndex >= 0) {
        handleDeactivate(suppliers[focusedIndex]);
      }
    };

    document.addEventListener('keyboard:new', handleKeyboardNew);
    document.addEventListener('keyboard:delete', handleKeyboardDelete);

    return () => {
      document.removeEventListener('keyboard:new', handleKeyboardNew);
      document.removeEventListener('keyboard:delete', handleKeyboardDelete);
    };
  }, [focusedIndex, suppliers]);

  if (!selectedClient) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Velg en klient for å se leverandører</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with Quick Add */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Leverandører</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Administrer leverandørkort og leverandørdata
          </p>
        </div>
        <div className="flex gap-2">
          <QuickAddButton type="supplier" onSuccess={fetchSuppliers} />
          <Button onClick={handleCreateNew} variant="outline" className="flex items-center gap-2">
            <PlusIcon className="w-5 h-5" />
            Fullstendig skjema
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Søk etter navn eller org.nr... (Eller trykk Cmd+K for global søk)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              statusFilter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            Alle
          </button>
          <button
            onClick={() => setStatusFilter('active')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              statusFilter === 'active'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            Aktive
          </button>
          <button
            onClick={() => setStatusFilter('inactive')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              statusFilter === 'inactive'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            Inaktive
          </button>
        </div>
      </div>

      {/* Table with Bulk Actions */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 dark:text-gray-400 mt-4">Laster leverandører...</p>
        </div>
      ) : suppliers.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400">Ingen leverandører funnet</p>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-blue-600 hover:text-blue-700 mt-2 text-sm"
            >
              Fjern søkefilter
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    {/* Bulk select checkbox */}
                    <th className="px-6 py-3 text-left">
                      <Checkbox
                        checked={isAllSelected}
                        onCheckedChange={toggleAll}
                        aria-label="Velg alle"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Leverandørnr
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Firmanavn
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Org.nr
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Kontakt
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Betalingsbetingelser
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Handlinger
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {suppliers.map((supplier, index) => (
                    <tr
                      key={supplier.id}
                      className={`hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                        focusedIndex === index ? 'ring-2 ring-blue-500' : ''
                      } ${isSelected(supplier.id) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
                    >
                      {/* Checkbox */}
                      <td className="px-6 py-4">
                        <Checkbox
                          checked={isSelected(supplier.id)}
                          onCheckedChange={() => toggleSelection(supplier.id)}
                          aria-label={`Velg ${supplier.company_name}`}
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                        {supplier.supplier_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {supplier.company_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {supplier.org_number || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        <div>{supplier.contact?.email || '-'}</div>
                        <div className="text-xs">{supplier.contact?.phone || ''}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {supplier.financial?.payment_terms_days || 30} dager
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            supplier.status === 'active'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {supplier.status === 'active' ? 'Aktiv' : 'Inaktiv'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleView(supplier.id)}
                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                            title="Vis detaljer"
                          >
                            <EyeIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleEdit(supplier.id)}
                            className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
                            title="Rediger (eller trykk E)"
                          >
                            <PencilIcon className="w-5 h-5" />
                          </button>
                          {supplier.status === 'active' && (
                            <button
                              onClick={() => handleDeactivate(supplier)}
                              className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                              title="Deaktiver (eller trykk D)"
                            >
                              <XMarkIcon className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bulk Actions Bar */}
          <BulkActions
            selectedIds={selectedIds}
            totalCount={suppliers.length}
            entityType="suppliers"
            onClearSelection={clearSelection}
            onRefresh={fetchSuppliers}
          />
        </>
      )}

      {/* Summary with keyboard hint */}
      {!loading && suppliers.length > 0 && (
        <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
          <span>
            Viser {suppliers.length} leverandør{suppliers.length !== 1 ? 'er' : ''}
          </span>
          <span className="text-xs">
            Tips: Trykk <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-700">?</kbd> for tastatursnarveier
          </span>
        </div>
      )}
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    props: {},
  };
};

export default LeverandorerEnhanced;
