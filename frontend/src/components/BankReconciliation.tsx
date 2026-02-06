"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

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

interface BankStats {
  total: number;
  unmatched: number;
  matched: number;
  match_rate: number;
}

export function BankReconciliation() {
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [stats, setStats] = useState<BankStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const mockClientId = '00000000-0000-0000-0000-000000000001';

  useEffect(() => {
    fetchTransactions();
    fetchStats();
  }, [filterStatus]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/bank/transactions?client_id=${mockClientId}${filterStatus !== 'all' ? `&status=${filterStatus}` : ''}`;
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
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/stats?client_id=${mockClientId}`
      );
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/upload?client_id=${mockClientId}&bank_account=12345678901`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Uploaded ${result.transactions_imported} transactions!`);
        fetchTransactions();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`❌ Upload failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('❌ Upload failed');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const runAIMatching = async () => {
    setMatching(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/match?client_id=${mockClientId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Matched ${result.summary.matched} of ${result.summary.total} transactions!`);
        fetchTransactions();
        fetchStats();
      }
    } catch (error) {
      console.error('Matching error:', error);
      alert('❌ Matching failed');
    } finally {
      setMatching(false);
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

  const filteredTransactions = transactions;

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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
            <div className="text-sm text-gray-600">Total Transactions</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
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
            <div className="text-sm text-gray-600">Match Rate</div>
            <div className="text-2xl font-bold text-indigo-600">{stats.match_rate}%</div>
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
          onClick={runAIMatching}
          disabled={matching || !stats || stats.unmatched === 0}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {matching ? '⏳ Matching...' : '🤖 Run AI Matching'}
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
      ) : filteredTransactions.length === 0 ? (
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
                  AI Confidence
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.map((txn) => (
                <motion.tr
                  key={txn.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="hover:bg-gray-50"
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(txn.transaction_date).toLocaleDateString('nb-NO')}
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
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {txn.ai_match_confidence ? (
                      <div className="flex flex-col items-center">
                        <span className="font-semibold">{txn.ai_match_confidence}%</span>
                        <div className="w-16 h-2 bg-gray-200 rounded-full mt-1">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${txn.ai_match_confidence}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                    {txn.status === 'matched' && (
                      <button className="text-blue-600 hover:text-blue-800 font-medium">
                        Review
                      </button>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
