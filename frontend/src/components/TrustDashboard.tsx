'use client';

import React, { useState, useEffect } from 'react';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface DashboardStatus {
  status: 'green' | 'yellow' | 'red';
  message: string;
  timestamp: string;
  counters: {
    review_queue: {
      pending: number;
      total: number;
      approved: number;
      percentage_approved: number;
    };
    invoices: {
      total: number;
      recent_24h: number;
      auto_booked: number;
      auto_booking_rate: number;
    };
    ehf: {
      received: number;
      processed: number;
      pending: number;
      errors: number;
    };
    bank: {
      total: number;
      matched: number;
      unmatched: number;
      pending: number;
    };
  };
  health_checks: {
    database: string;
    ai_agent: string;
    review_queue: string;
  };
}

export const TrustDashboard: React.FC = () => {
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/status');
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard status:', err);
        setError('Failed to load dashboard status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600">{error || 'No data available'}</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'green':
        return '✓';
      case 'yellow':
        return '⚠';
      case 'red':
        return '✕';
      default:
        return '?';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header with Traffic Light */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Status</h1>
            <p className="text-gray-600 mt-2">{status.message}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`w-24 h-24 rounded-full ${getStatusColor(status.status)} flex items-center justify-center text-white text-4xl font-bold shadow-lg`}>
              {getStatusIcon(status.status)}
            </div>
          </div>
        </div>
      </div>

      {/* Counters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Review Queue */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Review Queue</h3>
          <div className="mt-4">
            <div className="text-4xl font-bold text-gray-900">{status.counters.review_queue.pending}</div>
            <p className="text-sm text-gray-600">Pending items</p>
          </div>
          <div className="mt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total:</span>
              <span className="font-semibold">{status.counters.review_queue.total}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-gray-600">Approved:</span>
              <span className="font-semibold">{status.counters.review_queue.approved}</span>
            </div>
          </div>
        </div>

        {/* Invoices */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Invoices</h3>
          <div className="mt-4">
            <div className="text-4xl font-bold text-gray-900">{status.counters.invoices.recent_24h}</div>
            <p className="text-sm text-gray-600">Last 24 hours</p>
          </div>
          <div className="mt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total:</span>
              <span className="font-semibold">{status.counters.invoices.total}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-gray-600">Auto-booked:</span>
              <span className="font-semibold">{status.counters.invoices.auto_booking_rate}%</span>
            </div>
          </div>
        </div>

        {/* EHF */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">EHF (PEPPOL)</h3>
          <div className="mt-4">
            <div className="text-4xl font-bold text-gray-900">{status.counters.ehf.processed}</div>
            <p className="text-sm text-gray-600">Processed</p>
          </div>
          <div className="mt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Received:</span>
              <span className="font-semibold">{status.counters.ehf.received}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-gray-600">Pending:</span>
              <span className="font-semibold text-yellow-600">{status.counters.ehf.pending}</span>
            </div>
          </div>
        </div>

        {/* Bank */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Bank Transactions</h3>
          <div className="mt-4">
            <div className="text-4xl font-bold text-gray-900">{status.counters.bank.matched}</div>
            <p className="text-sm text-gray-600">Matched</p>
          </div>
          <div className="mt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total:</span>
              <span className="font-semibold">{status.counters.bank.total}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-gray-600">Unmatched:</span>
              <span className="font-semibold text-yellow-600">{status.counters.bank.unmatched}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Health Checks */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Checks</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(status.health_checks).map(([key, value]) => (
            <div key={key} className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${value === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium text-gray-700 capitalize">{key.replace('_', ' ')}</span>
              <span className="text-sm text-gray-500">({value})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: <ClientSafeTimestamp date={status.timestamp} format="datetime" />
      </div>
    </div>
  );
};

export default TrustDashboard;
