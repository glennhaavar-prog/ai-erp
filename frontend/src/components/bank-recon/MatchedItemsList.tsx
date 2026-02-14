/**
 * MatchedItemsList - Bottom Panel Component
 * Shows already matched bank-to-ledger pairs
 */
'use client';

import React from 'react';
import { MatchedItem } from '@/lib/api/bank-recon';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface MatchedItemsListProps {
  items: MatchedItem[];
  onUnlink: (bankTransactionId: string, ledgerEntryId: string) => void;
  loading?: boolean;
}

export function MatchedItemsList({
  items,
  onUnlink,
  loading = false,
}: MatchedItemsListProps) {
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500">
        <p className="text-sm">Ingen avstemte poster ennå</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {items.map((match) => {
        const isCredit = match.bank_transaction.amount > 0;

        return (
          <div
            key={match.id}
            className="p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-4">
              {/* Match Status Icon */}
              <div className="flex-shrink-0">
                <CheckCircleIcon className="w-6 h-6 text-green-500" />
              </div>

              {/* Bank Transaction */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  Bank: {match.bank_transaction.description}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatDate(match.bank_transaction.transaction_date)} •{' '}
                  <span className={isCredit ? 'text-green-600' : 'text-red-600'}>
                    {formatCurrency(match.bank_transaction.amount)}
                  </span>
                </p>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 text-gray-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>

              {/* Ledger Entry */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  Hovedbok: {match.ledger_entry.description}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Bilag {match.ledger_entry.voucher_number} • {formatDate(match.ledger_entry.accounting_date)}
                </p>
              </div>

              {/* Match Type Badge */}
              <div className="flex-shrink-0">
                <span
                  className={`
                    px-2 py-1 text-xs font-medium rounded
                    ${match.match_type === 'auto' ? 'bg-purple-100 text-purple-700' : ''}
                    ${match.match_type === 'manual' ? 'bg-blue-100 text-blue-700' : ''}
                    ${match.match_type === 'rule' ? 'bg-green-100 text-green-700' : ''}
                  `}
                >
                  {match.match_type === 'auto' ? 'Auto' : match.match_type === 'manual' ? 'Manuell' : 'Regel'}
                </span>
              </div>

              {/* Unlink Button */}
              <div className="flex-shrink-0">
                <Button
                  onClick={() => onUnlink(match.bank_transaction.id, match.ledger_entry.id)}
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <XMarkIcon className="w-4 h-4 mr-1" />
                  Fjern
                </Button>
              </div>
            </div>

            {/* Confidence Score (if available) */}
            {match.confidence !== undefined && (
              <div className="mt-2 ml-10">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Konfidensgrad:</span>
                  <div className="flex-1 max-w-xs">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          match.confidence >= 0.8 ? 'bg-green-500' :
                          match.confidence >= 0.5 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${match.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs text-gray-600 font-medium">
                    {Math.round(match.confidence * 100)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
