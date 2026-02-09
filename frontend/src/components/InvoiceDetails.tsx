'use client';

import React from 'react';
import { ReviewItem } from '@/types/review-queue';
import { ConfidenceScore } from './ConfidenceScore';
import clsx from 'clsx';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface InvoiceDetailsProps {
  item: ReviewItem;
}

export const InvoiceDetails: React.FC<InvoiceDetailsProps> = ({ item }) => {
  const priorityColors = {
    high: 'text-accent-red bg-red-500/10 border-accent-red',
    medium: 'text-accent-yellow bg-yellow-500/10 border-accent-yellow',
    low: 'text-accent-blue bg-blue-500/10 border-accent-blue',
  };

  const statusColors = {
    pending: 'text-gray-400 bg-gray-500/10 border-gray-500',
    approved: 'text-accent-green bg-green-500/10 border-accent-green',
    corrected: 'text-accent-yellow bg-yellow-500/10 border-accent-yellow',
    rejected: 'text-accent-red bg-red-500/10 border-accent-red',
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-6 bg-dark-bg border-b border-dark-border">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-100 mb-1">{item.supplier}</h2>
            <p className="text-gray-400">{item.description}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-100">
              {item.amount.toLocaleString('nb-NO', { minimumFractionDigits: 2 })} kr
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className={clsx('px-3 py-1 rounded-full text-xs font-medium border', priorityColors[item.priority])}>
            {item.priority.toUpperCase()} PRIORITET
          </span>
          <span className={clsx('px-3 py-1 rounded-full text-xs font-medium border', statusColors[item.status])}>
            {item.status.toUpperCase()}
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-dark-hover text-gray-300">
            {item.type === 'invoice' ? 'FAKTURA' : 'KVITTERING'}
          </span>
        </div>
      </div>

      {/* Details Grid */}
      <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Fakturanummer</div>
          <div className="font-mono text-gray-100">{item.invoiceNumber || 'N/A'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Dato</div>
          <div className="text-gray-100"><ClientSafeTimestamp date={item.date} format="date" /></div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Mottatt</div>
          <div className="text-gray-100"><ClientSafeTimestamp date={item.createdAt} format="datetime" /></div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">AI Konfidensgrad</div>
          <ConfidenceScore score={item.confidence} size="sm" />
        </div>
      </div>

      {/* Review Info (if reviewed) */}
      {item.reviewedAt && (
        <div className="px-6 pb-6">
          <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
            <div className="text-sm text-gray-400">
              Godkjent av <span className="text-gray-100 font-medium">{item.reviewedBy}</span>
              {' '}den <ClientSafeTimestamp date={item.reviewedAt} format="datetime" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
