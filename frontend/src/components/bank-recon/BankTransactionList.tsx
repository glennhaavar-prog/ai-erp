/**
 * BankTransactionList - Left Panel Component
 * Shows unmatched bank transactions with checkboxes
 */
'use client';

import React from 'react';
import { BankTransaction } from '@/lib/api/bank-recon';
import { formatCurrency, formatDate } from '@/lib/utils';

interface BankTransactionListProps {
  items: BankTransaction[];
  selectedIds: string[];
  onToggleSelection: (id: string) => void;
  loading?: boolean;
}

export function BankTransactionList({
  items,
  selectedIds,
  onToggleSelection,
  loading = false,
}: BankTransactionListProps) {
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <p className="text-lg font-medium">Ingen uavstemt banktransaksjoner</p>
        <p className="text-sm mt-2">Alle transaksjoner er avstemt</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {items.map((transaction) => {
        const isSelected = selectedIds.includes(transaction.id);
        const isCredit = transaction.amount > 0;

        return (
          <div
            key={transaction.id}
            onClick={() => onToggleSelection(transaction.id)}
            className={`
              p-4 cursor-pointer transition-colors hover:bg-blue-50
              ${isSelected ? 'bg-blue-100 border-l-4 border-blue-600' : 'border-l-4 border-transparent'}
            `}
          >
            <div className="flex items-start gap-3">
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => {}} // Handled by parent div onClick
                className="mt-1 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />

              {/* Transaction Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {transaction.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(transaction.transaction_date)}
                    </p>
                    {transaction.kid && (
                      <p className="text-xs text-gray-500 mt-1">
                        KID: {transaction.kid}
                      </p>
                    )}
                  </div>
                  
                  {/* Amount */}
                  <div className="flex-shrink-0">
                    <p
                      className={`text-sm font-semibold ${
                        isCredit ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {isCredit ? '+' : ''}{formatCurrency(transaction.amount)}
                    </p>
                  </div>
                </div>

                {/* Account */}
                <p className="text-xs text-gray-400 mt-1">
                  Konto: {transaction.bank_account}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
