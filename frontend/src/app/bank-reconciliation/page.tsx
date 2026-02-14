/**
 * Bank Reconciliation Page - Module 2
 * Bank-to-Ledger Reconciliation (NEW PARADIGM)
 * 
 * Matches bank transactions against general ledger entries (hovedbok)
 * instead of vendor invoices.
 */
'use client';

export const dynamic = 'force-dynamic';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useClient } from '@/contexts/ClientContext';
import { toast } from '@/lib/toast';
import {
  fetchUnmatchedItems,
  fetchMatchedItems,
  createMatch,
  unmatch,
  autoMatch,
  createMatchingRule,
  fetchBankAccounts,
  CreateRuleRequest,
} from '@/lib/api/bank-recon';
import { BankTransactionList } from '@/components/bank-recon/BankTransactionList';
import { LedgerEntryList } from '@/components/bank-recon/LedgerEntryList';
import { MatchingActions } from '@/components/bank-recon/MatchingActions';
import { MatchedItemsList } from '@/components/bank-recon/MatchedItemsList';
import { RuleDialog } from '@/components/bank-recon/RuleDialog';
import { Button } from '@/components/ui/button';

// Test client from specs
const TEST_CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

export default function BankReconciliationPage() {
  const { selectedClient } = useClient();
  const queryClient = useQueryClient();

  // Use test client if no client selected (for development)
  const clientId = selectedClient?.id || TEST_CLIENT_ID;

  // Filters
  const [account, setAccount] = useState<string>('1920');
  const [startDate, setStartDate] = useState<string>('2026-02-01');
  const [endDate, setEndDate] = useState<string>('2026-02-28');
  const [showMatched, setShowMatched] = useState<boolean>(false);

  // Selection state
  const [selectedBankIds, setSelectedBankIds] = useState<string[]>([]);
  const [selectedLedgerIds, setSelectedLedgerIds] = useState<string[]>([]);

  // Dialog state
  const [showRuleDialog, setShowRuleDialog] = useState(false);

  // ==================== Queries ====================

  // Fetch bank accounts for dropdown
  const { data: bankAccounts = [] } = useQuery({
    queryKey: ['bank-accounts', clientId],
    queryFn: () => fetchBankAccounts(clientId),
  });

  // Fetch unmatched items
  const {
    data: unmatchedData,
    isLoading: isLoadingUnmatched,
    refetch: refetchUnmatched,
  } = useQuery({
    queryKey: ['unmatched-items', clientId, account, startDate, endDate],
    queryFn: () => fetchUnmatchedItems(clientId, account, startDate, endDate),
    enabled: !showMatched,
  });

  // Fetch matched items
  const {
    data: matchedItems = [],
    isLoading: isLoadingMatched,
    refetch: refetchMatched,
  } = useQuery({
    queryKey: ['matched-items', clientId, account, startDate, endDate],
    queryFn: () => fetchMatchedItems(clientId, account, startDate, endDate),
    enabled: showMatched,
  });

  // ==================== Mutations ====================

  // Create match mutation
  const matchMutation = useMutation({
    mutationFn: createMatch,
    onSuccess: () => {
      toast.success('Avstemming opprettet!');
      // Clear selections
      setSelectedBankIds([]);
      setSelectedLedgerIds([]);
      // Refetch data
      queryClient.invalidateQueries({ queryKey: ['unmatched-items'] });
      queryClient.invalidateQueries({ queryKey: ['matched-items'] });
    },
    onError: (error: Error) => {
      toast.error(`Feil ved avstemming: ${error.message}`);
    },
  });

  // Unmatch mutation
  const unmatchMutation = useMutation({
    mutationFn: (params: { bank_transaction_id: string; ledger_entry_id: string }) =>
      unmatch({
        client_id: clientId,
        bank_transaction_id: params.bank_transaction_id,
        ledger_entry_id: params.ledger_entry_id,
      }),
    onSuccess: () => {
      toast.success('Avstemming fjernet!');
      queryClient.invalidateQueries({ queryKey: ['unmatched-items'] });
      queryClient.invalidateQueries({ queryKey: ['matched-items'] });
    },
    onError: (error: Error) => {
      toast.error(`Feil ved fjerning: ${error.message}`);
    },
  });

  // Auto-match mutation
  const autoMatchMutation = useMutation({
    mutationFn: () => autoMatch(clientId, account, startDate, endDate),
    onSuccess: (result) => {
      toast.success(`Auto-avstemming fullført! ${result.matched_count} treff.`);
      queryClient.invalidateQueries({ queryKey: ['unmatched-items'] });
      queryClient.invalidateQueries({ queryKey: ['matched-items'] });
    },
    onError: (error: Error) => {
      toast.error(`Feil ved auto-avstemming: ${error.message}`);
    },
  });

  // Create rule mutation
  const createRuleMutation = useMutation({
    mutationFn: createMatchingRule,
    onSuccess: () => {
      toast.success('Regel opprettet!');
      setShowRuleDialog(false);
    },
    onError: (error: Error) => {
      toast.error(`Feil ved opprettelse av regel: ${error.message}`);
    },
  });

  // ==================== Handlers ====================

  const handleMatch = () => {
    if (selectedBankIds.length === 0 || selectedLedgerIds.length === 0) {
      toast.error('Velg minst én banktransaksjon og én hovedbokføring');
      return;
    }

    // Create matches for all selected combinations
    selectedBankIds.forEach((bankId) => {
      selectedLedgerIds.forEach((ledgerId) => {
        matchMutation.mutate({
          client_id: clientId,
          bank_transaction_id: bankId,
          ledger_entry_id: ledgerId,
          match_type: 'manual',
        });
      });
    });
  };

  const handleAutoMatch = () => {
    if (window.confirm('Kjøre auto-avstemming for valgt periode?')) {
      autoMatchMutation.mutate();
    }
  };

  const handleCreateRule = () => {
    setShowRuleDialog(true);
  };

  const handleUnlink = (bankTransactionId: string, ledgerEntryId: string) => {
    if (window.confirm('Fjerne denne avstemmingen?')) {
      unmatchMutation.mutate({ bank_transaction_id: bankTransactionId, ledger_entry_id: ledgerEntryId });
    }
  };

  const handleToggleBankSelection = (id: string) => {
    setSelectedBankIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleToggleLedgerSelection = (id: string) => {
    setSelectedLedgerIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSubmitRule = (rule: CreateRuleRequest) => {
    createRuleMutation.mutate(rule);
  };

  // ==================== Render ====================

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header with Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Bankavstemming</h1>
          
          <div className="flex items-center gap-4">
            {/* Account Selector */}
            <div>
              <label htmlFor="account" className="text-sm text-gray-600 mr-2">
                Konto:
              </label>
              <select
                id="account"
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1920">1920 - Bankkonto</option>
                {bankAccounts.map((acc: any) => (
                  <option key={acc.account} value={acc.account}>
                    {acc.account} - {acc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Period Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Periode:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-500">-</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* View Toggle */}
            <Button
              onClick={() => setShowMatched(!showMatched)}
              variant={showMatched ? 'default' : 'outline'}
              size="sm"
            >
              {showMatched ? 'Vis uavstemt' : 'Vis avstemt'}
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        {unmatchedData && !showMatched && (
          <div className="mt-4 flex items-center gap-6 text-sm">
            <div>
              <span className="text-gray-600">Bank transaksjoner:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {unmatchedData.summary.bank_count}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Hovedbokføringer:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {unmatchedData.summary.ledger_count}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Bank total:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK' }).format(
                  unmatchedData.summary.total_bank_amount
                )}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Hovedbok total:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK' }).format(
                  unmatchedData.summary.total_ledger_amount
                )}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Main Content - Three Panel Layout */}
      {!showMatched ? (
        <div className="flex flex-1 overflow-hidden">
          {/* Left Panel - Bank Transactions */}
          <div className="w-1/3 bg-white border-r border-gray-200 overflow-y-auto">
            <div className="sticky top-0 bg-gray-50 border-b border-gray-200 px-4 py-3">
              <h2 className="text-lg font-semibold text-gray-900">Banktransaksjoner</h2>
              <p className="text-xs text-gray-500 mt-1">
                {selectedBankIds.length > 0 && `${selectedBankIds.length} valgt`}
              </p>
            </div>
            <BankTransactionList
              items={unmatchedData?.bank_transactions || []}
              selectedIds={selectedBankIds}
              onToggleSelection={handleToggleBankSelection}
              loading={isLoadingUnmatched}
            />
          </div>

          {/* Middle Panel - Actions */}
          <div className="flex-shrink-0 w-80 flex items-center justify-center">
            <MatchingActions
              selectedBankCount={selectedBankIds.length}
              selectedLedgerCount={selectedLedgerIds.length}
              onMatch={handleMatch}
              onAutoMatch={handleAutoMatch}
              onCreateRule={handleCreateRule}
              isMatching={matchMutation.isPending}
              isAutoMatching={autoMatchMutation.isPending}
            />
          </div>

          {/* Right Panel - Ledger Entries */}
          <div className="w-1/3 bg-white border-l border-gray-200 overflow-y-auto">
            <div className="sticky top-0 bg-gray-50 border-b border-gray-200 px-4 py-3">
              <h2 className="text-lg font-semibold text-gray-900">Hovedbokføringer</h2>
              <p className="text-xs text-gray-500 mt-1">
                {selectedLedgerIds.length > 0 && `${selectedLedgerIds.length} valgt`}
              </p>
            </div>
            <LedgerEntryList
              items={unmatchedData?.ledger_entries || []}
              selectedIds={selectedLedgerIds}
              onToggleSelection={handleToggleLedgerSelection}
              loading={isLoadingUnmatched}
            />
          </div>
        </div>
      ) : (
        /* Matched Items View */
        <div className="flex-1 bg-white overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">Avstemte poster</h2>
            <p className="text-sm text-gray-500 mt-1">
              Viser {matchedItems.length} avstemte {matchedItems.length === 1 ? 'post' : 'poster'}
            </p>
          </div>
          <MatchedItemsList
            items={matchedItems}
            onUnlink={handleUnlink}
            loading={isLoadingMatched}
          />
        </div>
      )}

      {/* Rule Dialog */}
      <RuleDialog
        isOpen={showRuleDialog}
        onClose={() => setShowRuleDialog(false)}
        onSubmit={handleSubmitRule}
        clientId={clientId}
        isSubmitting={createRuleMutation.isPending}
      />
    </div>
  );
}
