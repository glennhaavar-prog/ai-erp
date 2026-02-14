/**
 * LedgerEntryList - Right Panel Component
 * Shows unmatched general ledger entries with checkboxes
 */
'use client';

import React from 'react';
import { GeneralLedger } from '@/lib/api/bank-recon';
import { formatCurrency, formatDate } from '@/lib/utils';

interface LedgerEntryListProps {
  items: GeneralLedger[];
  selectedIds: string[];
  onToggleSelection: (id: string) => void;
  loading?: boolean;
}

export function LedgerEntryList({
  items,
  selectedIds,
  onToggleSelection,
  loading = false,
}: LedgerEntryListProps) {
  
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
        <p className="text-lg font-medium">Ingen uavstemt hovedbokføringer</p>
        <p className="text-sm mt-2">Alle posteringer er avstemt</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {items.map((entry) => {
        const isSelected = selectedIds.includes(entry.id);
        
        // Calculate totals
        const totalDebit = entry.lines.reduce((sum, line) => sum + line.debit_amount, 0);
        const totalCredit = entry.lines.reduce((sum, line) => sum + line.credit_amount, 0);
        const netAmount = totalDebit - totalCredit;

        return (
          <div
            key={entry.id}
            onClick={() => onToggleSelection(entry.id)}
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

              {/* Ledger Entry Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {entry.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Bilag: {entry.voucher_number} • {formatDate(entry.accounting_date)}
                    </p>
                  </div>
                </div>

                {/* Ledger Lines */}
                <div className="mt-2 space-y-1">
                  {entry.lines.map((line, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">
                        {line.account_number} {line.account_name && `- ${line.account_name}`}
                      </span>
                      <div className="flex gap-3">
                        {line.debit_amount > 0 && (
                          <span className="text-green-600 font-medium">
                            Debet: {formatCurrency(line.debit_amount)}
                          </span>
                        )}
                        {line.credit_amount > 0 && (
                          <span className="text-red-600 font-medium">
                            Kredit: {formatCurrency(line.credit_amount)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Net Amount Summary */}
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 font-medium">Netto:</span>
                    <span className={`font-semibold ${netAmount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(Math.abs(netAmount))}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
