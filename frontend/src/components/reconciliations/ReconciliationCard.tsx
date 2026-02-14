/**
 * ReconciliationCard Component
 * List item for a single reconciliation in the master list
 */
'use client';

import React from 'react';
import { Reconciliation } from '@/lib/api/reconciliations';
import { format } from 'date-fns';
import { nb } from 'date-fns/locale';

interface ReconciliationCardProps {
  reconciliation: Reconciliation;
  isSelected: boolean;
  onClick: () => void;
}

export const ReconciliationCard: React.FC<ReconciliationCardProps> = ({
  reconciliation,
  isSelected,
  onClick,
}) => {
  const getStatusBadge = (status: string) => {
    const badges = {
      pending: {
        label: 'Ventende',
        className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      },
      reconciled: {
        label: 'Avstemt',
        className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      },
      approved: {
        label: 'Godkjent',
        className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      },
    };

    const badge = badges[status as keyof typeof badges] || badges.pending;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.className}`}>
        {badge.label}
      </span>
    );
  };

  const formatPeriod = () => {
    const start = new Date(reconciliation.period_start);
    const end = new Date(reconciliation.period_end);
    
    // If same month, show "Februar 2026"
    if (start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()) {
      return format(start, 'MMMM yyyy', { locale: nb });
    }
    
    // Otherwise show range
    return `${format(start, 'MMM', { locale: nb })} - ${format(end, 'MMM yyyy', { locale: nb })}`;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getDifferenceColor = () => {
    if (reconciliation.difference === null) return 'text-gray-500';
    if (Math.abs(reconciliation.difference) < 0.01) return 'text-green-600 dark:text-green-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div
      onClick={onClick}
      className={`
        p-4 cursor-pointer transition-all hover:bg-blue-50 dark:hover:bg-blue-900/20
        ${isSelected ? 'bg-blue-100 dark:bg-blue-900/30 border-l-4 border-blue-600' : 'border-l-4 border-transparent'}
      `}
    >
      {/* Header: Account number + name */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white">
              {reconciliation.account_number}
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {reconciliation.account_name}
            </span>
          </div>
        </div>
        {getStatusBadge(reconciliation.status)}
      </div>

      {/* Period */}
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{formatPeriod()}</span>
      </div>

      {/* Balances */}
      <div className="flex justify-between items-center text-sm mb-1">
        <span className="text-gray-600 dark:text-gray-400">Balanse:</span>
        <span className="font-medium text-gray-900 dark:text-white">
          {formatCurrency(reconciliation.closing_balance)}
        </span>
      </div>

      {/* Difference (if set) */}
      {reconciliation.difference !== null && (
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-gray-400">Differanse:</span>
          <span className={`font-bold ${getDifferenceColor()}`}>
            {formatCurrency(Math.abs(reconciliation.difference))}
            {Math.abs(reconciliation.difference) < 0.01 && ' ✓'}
          </span>
        </div>
      )}

      {/* Attachments indicator */}
      {reconciliation.attachments_count > 0 && (
        <div className="flex items-center gap-1 mt-2 text-xs text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <span>{reconciliation.attachments_count} vedlegg</span>
        </div>
      )}
    </div>
  );
};
