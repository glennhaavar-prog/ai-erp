/**
 * Reconciliations Page
 * Module 3: Balance Account Reconciliation
 * Master-detail layout with filters, CRUD operations, and file uploads
 */
'use client';

import React, { useState, useEffect } from 'react';

// Force dynamic rendering (no static generation at build time)
export const dynamic = 'force-dynamic';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchReconciliations,
  fetchReconciliation,
  createReconciliation,
  updateReconciliation,
  approveReconciliation,
  uploadAttachment,
  fetchAttachments,
  deleteAttachment,
  Reconciliation,
  ReconciliationAttachment,
  CreateReconciliationRequest,
  UpdateReconciliationRequest,
} from '@/lib/api/reconciliations';
import { ReconciliationCard } from '@/components/reconciliations/ReconciliationCard';
import { ReconciliationFilters } from '@/components/reconciliations/ReconciliationFilters';
import { ReconciliationForm } from '@/components/reconciliations/ReconciliationForm';
import { MasterDetailLayout } from '@/components/MasterDetailLayout';

// Test client ID from specs
const TEST_CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

export default function ReconciliationsPage() {
  const queryClient = useQueryClient();

  // Filters
  const [periodYear, setPeriodYear] = useState(new Date().getFullYear());
  const [periodMonth, setPeriodMonth] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Selection
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Fetch reconciliations list
  const {
    data: reconciliations = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['reconciliations', TEST_CLIENT_ID, periodYear, periodMonth, statusFilter, typeFilter],
    queryFn: () =>
      fetchReconciliations({
        client_id: TEST_CLIENT_ID,
        status: statusFilter !== 'all' ? statusFilter as any : undefined,
        reconciliation_type: typeFilter !== 'all' ? typeFilter as any : undefined,
        // Note: Period filtering would need date range construction here if needed
      }),
  });

  // Fetch selected reconciliation details
  const { data: selectedReconciliation } = useQuery({
    queryKey: ['reconciliation', selectedId],
    queryFn: () => fetchReconciliation(selectedId!),
    enabled: !!selectedId && !showCreateForm,
  });

  // Fetch attachments for selected reconciliation
  const { data: attachments = [] } = useQuery({
    queryKey: ['reconciliation-attachments', selectedId],
    queryFn: () => fetchAttachments(selectedId!),
    enabled: !!selectedId && !showCreateForm,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CreateReconciliationRequest) => createReconciliation(data),
    onSuccess: (newReconciliation) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      setSelectedId(newReconciliation.id);
      setShowCreateForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateReconciliationRequest }) =>
      updateReconciliation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation', selectedId] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => approveReconciliation(id, 'Current User'), // TODO: Get real user
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation', selectedId] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ reconciliationId, file }: { reconciliationId: string; file: File }) =>
      uploadAttachment(reconciliationId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-attachments', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation', selectedId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({
      reconciliationId,
      attachmentId,
    }: {
      reconciliationId: string;
      attachmentId: string;
    }) => deleteAttachment(reconciliationId, attachmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-attachments', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation', selectedId] });
    },
  });

  // Handlers
  const handlePeriodChange = (year: number, month: number | null) => {
    setPeriodYear(year);
    setPeriodMonth(month);
  };

  const handleCreateNew = () => {
    setShowCreateForm(true);
    setSelectedId(null);
  };

  const handleSelectItem = (id: string) => {
    setSelectedId(id);
    setShowCreateForm(false);
  };

  const handleUpdate = async (data: UpdateReconciliationRequest) => {
    if (!selectedId) return;
    await updateMutation.mutateAsync({ id: selectedId, data });
  };

  const handleApprove = async () => {
    if (!selectedId) return;
    await approveMutation.mutateAsync(selectedId);
  };

  const handleUploadAttachment = async (file: File) => {
    if (!selectedId) return;
    await uploadMutation.mutateAsync({ reconciliationId: selectedId, file });
  };

  const handleDeleteAttachment = async (attachmentId: string) => {
    if (!selectedId) return;
    await deleteMutation.mutateAsync({ reconciliationId: selectedId, attachmentId });
  };

  const handleRefreshAttachments = async () => {
    await queryClient.invalidateQueries({ queryKey: ['reconciliation-attachments', selectedId] });
  };

  // Render detail view
  const renderDetail = (item: Reconciliation | null) => {
    if (showCreateForm) {
      return <CreateReconciliationView onCreate={(data) => createMutation.mutate(data)} />;
    }

    if (!item || !selectedReconciliation) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500 dark:text-gray-400">
            <svg
              className="mx-auto h-12 w-12 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p>Velg en avstemming for å se detaljer</p>
          </div>
        </div>
      );
    }

    return (
      <ReconciliationForm
        reconciliation={selectedReconciliation}
        attachments={attachments}
        onUpdate={handleUpdate}
        onApprove={handleApprove}
        onUploadAttachment={handleUploadAttachment}
        onDeleteAttachment={handleDeleteAttachment}
        onRefreshAttachments={handleRefreshAttachments}
      />
    );
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Feil ved henting av avstemminger: {(error as Error).message}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Balansekontoavstemming</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Avstem balansekontoer mot eksterne kilder
        </p>
      </div>

      {/* Filters */}
      <ReconciliationFilters
        periodYear={periodYear}
        periodMonth={periodMonth}
        onPeriodChange={handlePeriodChange}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        typeFilter={typeFilter}
        onTypeChange={setTypeFilter}
        onCreateNew={handleCreateNew}
      />

      {/* Master-Detail Layout */}
      <div className="flex-1 overflow-hidden">
        <MasterDetailLayout
          items={reconciliations}
          selectedId={selectedId}
          selectedIds={[]}
          onSelectItem={handleSelectItem}
          onMultiSelect={() => {}}
          renderItem={(item, isSelected) => (
            <ReconciliationCard
              reconciliation={item}
              isSelected={isSelected}
              onClick={() => handleSelectItem(item.id)}
            />
          )}
          renderDetail={renderDetail}
          loading={isLoading}
          multiSelectEnabled={false}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Create Reconciliation View
// ============================================================================

interface CreateReconciliationViewProps {
  onCreate: (data: CreateReconciliationRequest) => void;
}

const CreateReconciliationView: React.FC<CreateReconciliationViewProps> = ({ onCreate }) => {
  const [accountId, setAccountId] = useState('b99fcc63-be3d-43a0-959d-da29f70ea16d'); // Test account
  const [periodStart, setPeriodStart] = useState('2026-02-01T00:00:00');
  const [periodEnd, setPeriodEnd] = useState('2026-02-28T23:59:59');
  const [type, setType] = useState<'bank' | 'receivables' | 'payables' | 'inventory' | 'other'>(
    'bank'
  );
  const [expectedBalance, setExpectedBalance] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Convert date inputs to datetime format if needed
    const formatDateTime = (dateStr: string) => {
      if (dateStr.includes('T')) return dateStr;
      return `${dateStr}T00:00:00`;
    };

    const data: CreateReconciliationRequest = {
      client_id: TEST_CLIENT_ID,
      account_id: accountId,
      period_start: formatDateTime(periodStart),
      period_end: formatDateTime(periodEnd),
      reconciliation_type: type,
      notes: notes || undefined,
    };

    if (expectedBalance) {
      data.expected_balance = parseFloat(expectedBalance);
    }

    onCreate(data);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Ny avstemming</h2>

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Konto ID *
          </label>
          <input
            type="text"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Test konto: b99fcc63-be3d-43a0-959d-da29f70ea16d (Immatrielle eiendeler)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Periode start *
            </label>
            <input
              type="date"
              value={periodStart}
              onChange={(e) => setPeriodStart(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Periode slutt *
            </label>
            <input
              type="date"
              value={periodEnd}
              onChange={(e) => setPeriodEnd(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Type *
          </label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            required
          >
            <option value="bank">Bank</option>
            <option value="receivables">Kundefordringer</option>
            <option value="payables">Leverandørgjeld</option>
            <option value="inventory">Varelager</option>
            <option value="other">Annet</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Forventet balanse (valgfritt)
          </label>
          <input
            type="number"
            step="0.01"
            value={expectedBalance}
            onChange={(e) => setExpectedBalance(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="0.00"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Notater
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Legg til notater..."
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
          >
            Opprett avstemming
          </button>
        </div>
      </form>
    </div>
  );
};
