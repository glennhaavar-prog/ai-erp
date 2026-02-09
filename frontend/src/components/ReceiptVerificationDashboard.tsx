'use client';

import React, { useState, useEffect } from 'react';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface VerificationStatus {
  overall_status: 'green' | 'yellow' | 'red';
  status_message: string;
  timestamp: string;
  ehf_invoices: {
    received: number;
    processed: number;
    booked: number;
    pending: number;
    status: 'green' | 'yellow' | 'red';
    percentage_booked: number;
  };
  bank_transactions: {
    total: number;
    booked: number;
    unbooked: number;
    status: 'green' | 'yellow' | 'red';
    note: string;
  };
  review_queue: {
    pending: number;
    status: 'green' | 'yellow' | 'red';
  };
  summary: {
    total_items: number;
    fully_tracked: number;
    needs_attention: number;
    completion_rate: number;
  };
}

export const ReceiptVerificationDashboard: React.FC = () => {
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/verification');
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching verification status:', err);
        setError('Failed to load verification status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'green':
        return 'bg-green-600';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  };

  const getStatusBorder = (status: string) => {
    switch (status) {
      case 'green':
        return 'border-green-500';
      case 'yellow':
        return 'border-yellow-500';
      case 'red':
        return 'border-red-500';
      default:
        return 'border-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'green':
        return 'text-green-400';
      case 'yellow':
        return 'text-yellow-400';
      case 'red':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-green-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="p-8 text-center bg-gray-900 rounded-lg">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-gray-300">Loading verification dashboard...</p>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="p-8 text-center bg-gray-900 rounded-lg border border-red-500">
        <p className="text-red-400">{error || 'No data available'}</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header with Overall Status */}
      <div className={`bg-gray-900 rounded-lg shadow-xl p-6 border-l-4 ${getStatusBorder(status.overall_status)}`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Receipt Verification</h1>
            <p className="text-xl text-gray-300 mt-2">{status.status_message}</p>
            <p className="text-sm text-gray-500 mt-1">Proving to accountant: NOTHING is forgotten</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`w-24 h-24 rounded-full ${getStatusColor(status.overall_status)} flex items-center justify-center text-white text-5xl font-bold shadow-2xl animate-pulse`}>
              {status.overall_status === 'green' ? '✓' : status.overall_status === 'yellow' ? '⚠' : '✕'}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Completion Rate</span>
            <span className="font-bold text-white">{status.summary.completion_rate}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden">
            <div
              className={`h-full ${getProgressBarColor(status.summary.completion_rate)} transition-all duration-500 ease-out`}
              style={{ width: `${status.summary.completion_rate}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* EHF Invoices Card */}
        <div className={`bg-gray-900 rounded-lg shadow-xl p-6 border-l-4 ${getStatusBorder(status.ehf_invoices.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">EHF Invoices</h3>
            <div className={`w-3 h-3 rounded-full ${getStatusColor(status.ehf_invoices.status)} shadow-lg`}></div>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-baseline">
                <span className="text-4xl font-bold text-white">{status.ehf_invoices.received}</span>
                <span className="text-sm text-gray-500">Received</span>
              </div>
            </div>

            <div className="space-y-2 pt-4 border-t border-gray-800">
              <div className="flex justify-between">
                <span className="text-gray-400">Processed:</span>
                <span className="font-semibold text-white">{status.ehf_invoices.processed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Booked:</span>
                <span className="font-semibold text-green-400">{status.ehf_invoices.booked}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Pending:</span>
                <span className={`font-semibold ${status.ehf_invoices.pending > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {status.ehf_invoices.pending}
                </span>
              </div>
            </div>

            <div className="pt-2">
              <div className="text-xs text-gray-500 mb-1">Booking Rate</div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="h-full bg-green-500 rounded-full transition-all duration-500"
                  style={{ width: `${status.ehf_invoices.percentage_booked}%` }}
                ></div>
              </div>
              <div className="text-right text-xs text-gray-400 mt-1">{status.ehf_invoices.percentage_booked}%</div>
            </div>
          </div>
        </div>

        {/* Bank Transactions Card */}
        <div className={`bg-gray-900 rounded-lg shadow-xl p-6 border-l-4 ${getStatusBorder(status.bank_transactions.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Bank Transactions</h3>
            <div className={`w-3 h-3 rounded-full ${getStatusColor(status.bank_transactions.status)} shadow-lg`}></div>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-baseline">
                <span className="text-4xl font-bold text-white">{status.bank_transactions.total}</span>
                <span className="text-sm text-gray-500">Total</span>
              </div>
            </div>

            <div className="space-y-2 pt-4 border-t border-gray-800">
              <div className="flex justify-between">
                <span className="text-gray-400">Booked:</span>
                <span className="font-semibold text-green-400">{status.bank_transactions.booked}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Unbooked:</span>
                <span className={`font-semibold ${status.bank_transactions.unbooked > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {status.bank_transactions.unbooked}
                </span>
              </div>
            </div>

            <div className="pt-2 bg-gray-800 rounded p-3">
              <p className="text-xs text-gray-400 italic">{status.bank_transactions.note}</p>
            </div>
          </div>
        </div>

        {/* Review Queue Card */}
        <div className={`bg-gray-900 rounded-lg shadow-xl p-6 border-l-4 ${getStatusBorder(status.review_queue.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Review Queue</h3>
            <div className={`w-3 h-3 rounded-full ${getStatusColor(status.review_queue.status)} shadow-lg`}></div>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-baseline">
                <span className="text-4xl font-bold text-white">{status.review_queue.pending}</span>
                <span className="text-sm text-gray-500">Pending</span>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-800">
              {status.review_queue.pending === 0 ? (
                <div className="text-center py-4">
                  <div className="text-5xl mb-2">🎉</div>
                  <p className="text-green-400 font-semibold">All clear!</p>
                  <p className="text-xs text-gray-500 mt-1">No items need review</p>
                </div>
              ) : (
                <div className="text-center py-4">
                  <div className="text-5xl mb-2">⏳</div>
                  <p className="text-yellow-400 font-semibold">Attention needed</p>
                  <p className="text-xs text-gray-500 mt-1">{status.review_queue.pending} items waiting</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Footer */}
      <div className="bg-gray-900 rounded-lg shadow-xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold text-white mb-4">Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400">{status.summary.total_items}</div>
            <div className="text-sm text-gray-500 mt-1">Total Items</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">{status.summary.fully_tracked}</div>
            <div className="text-sm text-gray-500 mt-1">Fully Tracked</div>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${status.summary.needs_attention > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
              {status.summary.needs_attention}
            </div>
            <div className="text-sm text-gray-500 mt-1">Needs Attention</div>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getStatusText(status.overall_status)}`}>
              {status.summary.completion_rate}%
            </div>
            <div className="text-sm text-gray-500 mt-1">Complete</div>
          </div>
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-600">
        Last updated: <ClientSafeTimestamp date={status.timestamp} format="datetime" />
      </div>
    </div>
  );
};

export default ReceiptVerificationDashboard;
