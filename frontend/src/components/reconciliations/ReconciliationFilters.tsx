/**
 * ReconciliationFilters Component
 * Top bar with filters for reconciliations list
 */
'use client';

import React from 'react';

interface ReconciliationFiltersProps {
  // Period filters
  periodYear: number;
  periodMonth: number | null;
  onPeriodChange: (year: number, month: number | null) => void;

  // Status filter
  statusFilter: string;
  onStatusChange: (status: string) => void;

  // Type filter
  typeFilter: string;
  onTypeChange: (type: string) => void;

  // Create button
  onCreateNew: () => void;
}

export const ReconciliationFilters: React.FC<ReconciliationFiltersProps> = ({
  periodYear,
  periodMonth,
  onPeriodChange,
  statusFilter,
  onStatusChange,
  typeFilter,
  onTypeChange,
  onCreateNew,
}) => {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const months = [
    { value: 1, label: 'Januar' },
    { value: 2, label: 'Februar' },
    { value: 3, label: 'Mars' },
    { value: 4, label: 'April' },
    { value: 5, label: 'Mai' },
    { value: 6, label: 'Juni' },
    { value: 7, label: 'Juli' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'Oktober' },
    { value: 11, label: 'November' },
    { value: 12, label: 'Desember' },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Year picker */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              År
            </label>
            <select
              value={periodYear}
              onChange={(e) => onPeriodChange(parseInt(e.target.value), periodMonth)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          {/* Month picker */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Måned
            </label>
            <select
              value={periodMonth || ''}
              onChange={(e) =>
                onPeriodChange(periodYear, e.target.value ? parseInt(e.target.value) : null)
              }
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Alle måneder</option>
              {months.map((month) => (
                <option key={month.value} value={month.value}>
                  {month.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => onStatusChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Alle</option>
              <option value="pending">Ventende</option>
              <option value="reconciled">Avstemt</option>
              <option value="approved">Godkjent</option>
            </select>
          </div>

          {/* Type filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => onTypeChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Alle</option>
              <option value="bank">Bank</option>
              <option value="receivables">Kundefordringer</option>
              <option value="payables">Leverandørgjeld</option>
              <option value="inventory">Varelager</option>
              <option value="other">Annet</option>
            </select>
          </div>
        </div>

        {/* Create new button */}
        <button
          onClick={onCreateNew}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Ny avstemming
        </button>
      </div>
    </div>
  );
};
