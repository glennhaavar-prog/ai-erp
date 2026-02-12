/**
 * Kunder (Customers) List Page
 * KONTAKTREGISTER - Customer Management
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
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline';
import { useClient } from '@/contexts/ClientContext';
import { customersApi, Customer } from '@/api/contacts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { BulkUpload } from '@/components/BulkUpload';

export const Kunder: React.FC = () => {
  const router = useRouter();
  const { selectedClient } = useClient();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('active');
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    if (selectedClient?.id) {
      fetchCustomers();
    }
  }, [selectedClient, searchQuery, statusFilter]);

  const fetchCustomers = async () => {
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

      const data = await customersApi.list(params);
      setCustomers(data);
    } catch (error) {
      console.error('Error fetching customers:', error);
      toast.error('Kunne ikke laste kunder');
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    router.push('/kontakter/kunder/ny');
  };

  const handleView = (customerId: string) => {
    router.push(`/kontakter/kunder/${customerId}`);
  };

  const handleEdit = (customerId: string) => {
    router.push(`/kontakter/kunder/${customerId}/rediger`);
  };

  const handleDeactivate = async (customer: Customer) => {
    if (!confirm(`Er du sikker på at du vil deaktivere ${customer.name}?`)) {
      return;
    }

    try {
      await customersApi.deactivate(customer.id);
      toast.success(`${customer.name} er deaktivert`);
      fetchCustomers();
    } catch (error) {
      console.error('Error deactivating customer:', error);
      toast.error('Kunne ikke deaktivere kunde');
    }
  };

  const formatCurrency = (amount?: number) => {
    if (amount === undefined) return '-';
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
    }).format(amount);
  };

  if (!selectedClient) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Velg en klient for å se kunder</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Kunder</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Administrer kundekort og kundedata
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowUploadModal(true)}
            variant="outline"
            className="flex items-center gap-2"
          >
            <ArrowUpTrayIcon className="w-5 h-5" />
            Last opp kunder
          </Button>
          <Button onClick={handleCreateNew} className="flex items-center gap-2">
            <PlusIcon className="w-5 h-5" />
            Ny kunde
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Søk etter navn, org.nr eller fødselsnr..."
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

      {/* Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 dark:text-gray-400 mt-4">Laster kunder...</p>
        </div>
      ) : customers.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400">Ingen kunder funnet</p>
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
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Kundenr
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Navn
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Org.nr / Fødselsnr
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
                {customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {customer.customer_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {customer.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {customer.is_company ? 'Bedrift' : 'Privatperson'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {customer.org_number || customer.birth_number || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      <div>{customer.contact?.email || '-'}</div>
                      <div className="text-xs">{customer.contact?.phone || ''}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {customer.financial?.payment_terms_days || 14} dager
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          customer.status === 'active'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {customer.status === 'active' ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleView(customer.id)}
                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                          title="Vis detaljer"
                        >
                          <EyeIcon className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleEdit(customer.id)}
                          className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
                          title="Rediger"
                        >
                          <PencilIcon className="w-5 h-5" />
                        </button>
                        {customer.status === 'active' && (
                          <button
                            onClick={() => handleDeactivate(customer)}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                            title="Deaktiver"
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
      )}

      {/* Summary */}
      {!loading && customers.length > 0 && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Viser {customers.length} kunde{customers.length !== 1 ? 'r' : ''}
        </div>
      )}

      {/* Bulk Upload Modal */}
      <BulkUpload
        type="customers"
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onSuccess={() => {
          fetchCustomers();
        }}
      />
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    props: {},
  };
};

export default Kunder;
