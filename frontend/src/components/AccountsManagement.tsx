'use client';

import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PlusIcon, MagnifyingGlassIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useClient } from '@/contexts/ClientContext';

interface Account {
  id: string;
  client_id: string;
  account_number: string;
  account_name: string;
  account_type: string;
  parent_account_number: string | null;
  account_level: number;
  default_vat_code: string | null;
  vat_deductible: boolean;
  requires_reconciliation: boolean;
  ai_usage_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AccountFormData {
  account_number: string;
  account_name: string;
  account_type: string;
  parent_account_number: string;
  default_vat_code: string;
  vat_deductible: boolean;
  requires_reconciliation: boolean;
}

const ACCOUNT_TYPES = [
  { value: 'asset', label: 'Eiendel (Asset)' },
  { value: 'liability', label: 'Gjeld (Liability)' },
  { value: 'equity', label: 'Egenkapital (Equity)' },
  { value: 'revenue', label: 'Inntekt (Revenue)' },
  { value: 'expense', label: 'Kostnad (Expense)' },
];

const VAT_CODES = [
  { value: '', label: 'Ingen MVA' },
  { value: '0', label: '0 - Unntak' },
  { value: '3', label: '3 - 15% redusert sats' },
  { value: '5', label: '5 - 25% alminnelig sats' },
  { value: '6', label: '6 - Inngående avgift' },
];

export const AccountsManagement: React.FC = () => {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);

  const [formData, setFormData] = useState<AccountFormData>({
    account_number: '',
    account_name: '',
    account_type: 'expense',
    parent_account_number: '',
    default_vat_code: '',
    vat_deductible: true,
    requires_reconciliation: false,
  });

  // Fetch accounts when client changes
  useEffect(() => {
    if (selectedClient?.id) {
      fetchAccounts();
    }
  }, [selectedClient, searchQuery, filterType]);

  const fetchAccounts = async () => {
    if (!selectedClient?.id) return;
    
    try {
      setLoading(true);
      const params = new URLSearchParams({
        client_id: selectedClient.id,
        active_only: 'true',
      });
      
      if (searchQuery) params.append('search', searchQuery);
      if (filterType) params.append('account_type', filterType);

      const response = await fetch(`http://localhost:8000/api/accounts/?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAccounts(data.accounts || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching accounts:', err);
      setError('Kunne ikke laste kontoer. Vennligst prøv igjen.');
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    if (!selectedClient?.id) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/accounts/?client_id=${selectedClient.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Kunne ikke opprette konto');
      }

      // Reset form and close modal
      setFormData({
        account_number: '',
        account_name: '',
        account_type: 'expense',
        parent_account_number: '',
        default_vat_code: '',
        vat_deductible: true,
        requires_reconciliation: false,
      });
      setShowCreateModal(false);
      
      // Refresh accounts list
      fetchAccounts();
    } catch (err) {
      console.error('Error creating account:', err);
      toast.error(err instanceof Error ? err.message : 'Kunne ikke opprette konto');
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    if (!confirm('Er du sikker på at du vil deaktivere denne kontoen?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/accounts/${accountId}?soft_delete=true`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Kunne ikke slette konto');
      }

      fetchAccounts();
    } catch (err) {
      console.error('Error deleting account:', err);
      toast.error('Kunne ikke slette konto');
    }
  };

  const getAccountTypeLabel = (type: string) => {
    const found = ACCOUNT_TYPES.find(t => t.value === type);
    return found ? found.label : type;
  };

  // Show loading state
  if (clientLoading || loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">
            {clientLoading ? "Laster klient..." : "Laster kontoplan..."}
          </p>
        </div>
      </div>
    );
  }

  // Show no client selected
  if (!selectedClient) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            Velg en klient fra menyen øverst for å se kontoplan
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Kontoplan</h1>
          <p className="text-sm text-gray-400 mt-1">
            {accounts.length} kontoer registrert
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-accent-blue hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          Ny konto
        </button>
      </div>

      {/* Search & Filter */}
      <div className="bg-dark-card border border-dark-border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Søk på kontonummer eller navn..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            />
          </div>

          {/* Filter by type */}
          <div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            >
              <option value="">Alle kontotyper</option>
              {ACCOUNT_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Accounts Table */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-blue"></div>
        </div>
      )}

      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-4">
          <p className="text-accent-red">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-hover border-b border-dark-border">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Kontonr
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Kontonavn
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    MVA-kode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    AI Bruk
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Handlinger
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {accounts.map((account) => (
                  <tr key={account.id} className="hover:bg-dark-hover transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-gray-100">{account.account_number}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-100">{account.account_name}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-400">{getAccountTypeLabel(account.account_type)}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-400">
                        {account.default_vat_code || '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-400">{account.ai_usage_count}x</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDeleteAccount(account.id)}
                        className="text-accent-red hover:text-red-400 transition-colors"
                        title="Deaktiver konto"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {accounts.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-400">Ingen kontoer funnet</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Account Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
          <div className="bg-dark-card border border-dark-border rounded-lg p-6 w-full max-w-2xl">
            <h2 className="text-xl font-bold text-gray-100 mb-4">Opprett ny konto</h2>

            <div className="space-y-4">
              {/* Account Number */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Kontonummer *
                </label>
                <input
                  type="text"
                  placeholder="F.eks. 4000, 6800"
                  value={formData.account_number}
                  onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
                />
                <p className="text-xs text-gray-500 mt-1">Minst 4 siffer (NS 4102 standard)</p>
              </div>

              {/* Account Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Kontonavn *
                </label>
                <input
                  type="text"
                  placeholder="F.eks. Kontorrekvisita, Markedsføring"
                  value={formData.account_name}
                  onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
                />
              </div>

              {/* Account Type */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Kontotype *
                </label>
                <select
                  value={formData.account_type}
                  onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
                >
                  {ACCOUNT_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              {/* VAT Code */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Standard MVA-kode
                </label>
                <select
                  value={formData.default_vat_code}
                  onChange={(e) => setFormData({ ...formData, default_vat_code: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
                >
                  {VAT_CODES.map(code => (
                    <option key={code.value} value={code.value}>{code.label}</option>
                  ))}
                </select>
              </div>

              {/* Checkboxes */}
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.vat_deductible}
                    onChange={(e) => setFormData({ ...formData, vat_deductible: e.target.checked })}
                    className="w-4 h-4 text-accent-blue bg-dark-bg border-dark-border rounded focus:ring-accent-blue focus:ring-2"
                  />
                  <span className="text-sm text-gray-300">MVA fradragsberettiget</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.requires_reconciliation}
                    onChange={(e) => setFormData({ ...formData, requires_reconciliation: e.target.checked })}
                    className="w-4 h-4 text-accent-blue bg-dark-bg border-dark-border rounded focus:ring-accent-blue focus:ring-2"
                  />
                  <span className="text-sm text-gray-300">Krever avstemming</span>
                </label>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg text-sm font-medium transition-colors"
              >
                Avbryt
              </button>
              <button
                onClick={handleCreateAccount}
                className="px-4 py-2 bg-accent-blue hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Opprett konto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountsManagement;
