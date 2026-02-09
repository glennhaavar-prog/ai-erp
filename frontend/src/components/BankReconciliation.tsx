"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from '@/lib/toast';
import { useClient } from '@/contexts/ClientContext';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface BankTransaction {
  id: string;
  transaction_date: string;
  amount: number;
  transaction_type: 'credit' | 'debit';
  description: string;
  counterparty_name: string | null;
  kid_number: string | null;
  status: 'unmatched' | 'matched' | 'reviewed' | 'ignored';
  ai_match_confidence: number | null;
}

interface MatchSuggestion {
  type: string;
  invoice_id: string;
  invoice: any;
  confidence: number;
  reason: string;
  amount_difference: number;
}

interface BankStats {
  total_transactions: number;
  unmatched: number;
  matched: number;
  auto_match_count: number;
  manual_match_count: number;
  auto_match_rate: number;
}

export function BankReconciliation() {
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [stats, setStats] = useState<BankStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedTransaction, setSelectedTransaction] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<MatchSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Get selected client from context
  const { selectedClient, isLoading: clientLoading } = useClient();
  const clientId = selectedClient?.id;
  
  // TODO: Get userId from auth context when implemented
  const mockUserId = '00000000-0000-0000-0000-000000000001';

  useEffect(() => {
    if (clientId) {
      fetchTransactions();
      fetchStats();
    }
  }, [filterStatus, clientId]);

  const fetchTransactions = async () => {
    if (!clientId) return;
    
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/bank/transactions?client_id=${clientId}${filterStatus !== 'all' ? `&status=${filterStatus}` : ''}`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.transactions);
      }
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!clientId) return;
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/reconciliation/stats?client_id=${clientId}`
      );
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchSuggestions = async (transactionId: string) => {
    if (!clientId) return;
    
    setLoadingSuggestions(true);
    setSuggestions([]);
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/transactions/${transactionId}/suggestions?client_id=${clientId}`
      );
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !clientId) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/import?client_id=${clientId}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success(`✅ Uploaded ${result.transactions_imported} transactions!\n🤖 Auto-matched: ${result.auto_matched} (${result.match_rate}%)`);
        fetchTransactions();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(`❌ Upload failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('❌ Upload failed');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const runAutoMatching = async () => {
    if (!clientId) return;
    
    setMatching(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/auto-match?client_id=${clientId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success(`✅ Auto-matched ${result.summary.matched} of ${result.summary.total} transactions!\n⚠️ Low confidence: ${result.summary.low_confidence}`);
        fetchTransactions();
        fetchStats();
      }
    } catch (error) {
      console.error('Matching error:', error);
      toast.error('❌ Matching failed');
    } finally {
      setMatching(false);
    }
  };

  const handleManualMatch = async (transactionId: string, invoiceId: string, invoiceType: string) => {
    if (!clientId) return;
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/transactions/${transactionId}/match?client_id=${clientId}&invoice_id=${invoiceId}&invoice_type=${invoiceType}&user_id=${mockUserId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        toast.success('✅ Transaction matched successfully!');
        setSelectedTransaction(null);
        setSuggestions([]);
        fetchTransactions();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(`❌ Match failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Match error:', error);
      toast.error('❌ Match failed');
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      unmatched: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      matched: 'bg-green-100 text-green-800 border-green-200',
      reviewed: 'bg-blue-100 text-blue-800 border-blue-200',
      ignored: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return badges[status as keyof typeof badges] || badges.unmatched;
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 85) return 'bg-green-100 text-green-800 border-green-300';
    if (confidence >= 70) return 'bg-blue-100 text-blue-800 border-blue-300';
    if (confidence >= 50) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Bank Reconciliation
        </h1>
        <p className="text-gray-600">
          Upload bank statements and let AI match transactions to invoices
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
            <div className="text-sm text-gray-600">Total Transactions</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_transactions}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
            <div className="text-sm text-gray-600">Unmatched</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.unmatched}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
            <div className="text-sm text-gray-600">Matched</div>
            <div className="text-2xl font-bold text-green-600">{stats.matched}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-indigo-500">
            <div className="text-sm text-gray-600">Auto-Match Rate</div>
            <div className="text-2xl font-bold text-indigo-600">{stats.auto_match_rate}%</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
            <div className="text-sm text-gray-600">Manual Matches</div>
            <div className="text-2xl font-bold text-purple-600">{stats.manual_match_count}</div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mb-6 flex space-x-4">
        <label className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">
          {uploading ? '⏳ Uploading...' : '📤 Upload CSV'}
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>

        <button
          onClick={runAutoMatching}
          disabled={matching || !stats || stats.unmatched === 0}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {matching ? '⏳ Matching...' : '🤖 Run Auto-Match'}
        </button>

        <div className="flex-1"></div>

        {/* Filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Transactions</option>
          <option value="unmatched">Unmatched Only</option>
          <option value="matched">Matched Only</option>
        </select>
      </div>

      {/* Transactions Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading transactions...</p>
        </div>
      ) : transactions.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-4xl mb-2">📊</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No Transactions</h3>
          <p className="text-gray-600">Upload a CSV file to get started</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Counterparty
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((txn) => (
                <React.Fragment key={txn.id}>
                  <motion.tr
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <ClientSafeTimestamp date={txn.transaction_date} format="date" />
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {txn.description}
                      {txn.kid_number && (
                        <div className="text-xs text-gray-500">KID: {txn.kid_number}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {txn.counterparty_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span className={txn.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'}>
                        {txn.transaction_type === 'credit' ? '+' : '-'} {txn.amount.toFixed(2)} NOK
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getStatusBadge(txn.status)}`}>
                        {txn.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                      {txn.status === 'unmatched' && (
                        <button
                          onClick={() => {
                            setSelectedTransaction(selectedTransaction === txn.id ? null : txn.id);
                            if (selectedTransaction !== txn.id) {
                              fetchSuggestions(txn.id);
                            }
                          }}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {selectedTransaction === txn.id ? 'Hide' : 'Find Match'}
                        </button>
                      )}
                      {txn.status === 'matched' && (
                        <span className="text-green-600 font-medium">✓ Matched</span>
                      )}
                    </td>
                  </motion.tr>
                  
                  {/* Suggestions Dropdown */}
                  {selectedTransaction === txn.id && (
                    <tr>
                      <td colSpan={6} className="px-6 py-4 bg-blue-50">
                        <div className="max-w-4xl">
                          <h4 className="font-semibold text-gray-900 mb-3">Matching Suggestions</h4>
                          {loadingSuggestions ? (
                            <div className="text-center py-4">
                              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                            </div>
                          ) : suggestions.length === 0 ? (
                            <p className="text-gray-600">No matching suggestions found</p>
                          ) : (
                            <div className="space-y-2">
                              {suggestions.map((suggestion, idx) => (
                                <div
                                  key={idx}
                                  className="bg-white p-4 rounded-lg border border-gray-200 flex justify-between items-center"
                                >
                                  <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                      <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${getConfidenceBadge(suggestion.confidence)}`}>
                                        {suggestion.confidence.toFixed(0)}% confidence
                                      </span>
                                      <span className="text-sm text-gray-600">
                                        {suggestion.type === 'vendor_invoice' ? '📄 Vendor Invoice' : '📄 Customer Invoice'}
                                      </span>
                                    </div>
                                    <div className="text-sm text-gray-900">
                                      <strong>Invoice #{suggestion.invoice.invoice_number}</strong>
                                      {' - '}
                                      {suggestion.invoice.total_amount.toFixed(2)} NOK
                                      {' - '}
                                      Due: <ClientSafeTimestamp date={suggestion.invoice.due_date} format="date" />
                                    </div>
                                    <div className="text-xs text-gray-600 mt-1">
                                      {suggestion.reason}
                                      {suggestion.amount_difference !== 0 && (
                                        <span className="ml-2 text-yellow-600">
                                          (Diff: {suggestion.amount_difference.toFixed(2)} NOK)
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <button
                                    onClick={() => handleManualMatch(txn.id, suggestion.invoice_id, suggestion.type === 'vendor_invoice' ? 'vendor' : 'customer')}
                                    className="ml-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
                                  >
                                    Match
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
