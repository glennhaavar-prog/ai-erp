import React from 'react';
import { ReviewItem } from '@/types/review-queue';
import { ConfidenceScore } from './ConfidenceScore';
import { format } from 'date-fns';
import { nb } from 'date-fns/locale';
import clsx from 'clsx';

interface ReviewQueueItemProps {
  item: ReviewItem;
  onClick: () => void;
  isSelected?: boolean;
}

export const ReviewQueueItem: React.FC<ReviewQueueItemProps> = ({ item, onClick, isSelected }) => {
  const priorityIndicators = {
    high: 'bg-accent-red',
    medium: 'bg-accent-yellow',
    low: 'bg-accent-blue',
  };

  const statusIcons = {
    pending: '⏳',
    approved: '✓',
    corrected: '✎',
    rejected: '✗',
  };

  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-dark-card border-2 rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg',
        isSelected ? 'border-accent-blue shadow-lg' : 'border-dark-border hover:border-dark-hover'
      )}
    >
      {/* Priority Indicator */}
      <div className="flex items-start gap-3">
        <div className={clsx('w-1 h-full rounded-full', priorityIndicators[item.priority])} />
        
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-100 truncate">{item.supplier}</h3>
              <p className="text-sm text-gray-400 truncate">{item.description}</p>
            </div>
            <div className="text-right ml-3">
              <div className="font-bold text-gray-100 whitespace-nowrap">
                {item.amount.toLocaleString('nb-NO')} kr
              </div>
              <div className="text-xs text-gray-500">
                {statusIcons[item.status]} {item.status}
              </div>
            </div>
          </div>

          {/* Confidence Score */}
          <div className="mb-3">
            <ConfidenceScore score={item.confidence} size="sm" />
          </div>

          {/* Meta Info */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span>📅</span>
              {format(new Date(item.date), 'dd.MM.yyyy', { locale: nb })}
            </span>
            {item.invoiceNumber && (
              <span className="font-mono">{item.invoiceNumber}</span>
            )}
            <span className={clsx('px-2 py-0.5 rounded', {
              'bg-red-500/20 text-accent-red': item.priority === 'high',
              'bg-yellow-500/20 text-accent-yellow': item.priority === 'medium',
              'bg-blue-500/20 text-accent-blue': item.priority === 'low',
            })}>
              {item.priority}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
