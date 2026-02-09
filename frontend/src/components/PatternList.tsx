'use client';

import React from 'react';
import { Pattern } from '@/types/review-queue';
import { ConfidenceScore } from './ConfidenceScore';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface PatternListProps {
  patterns: Pattern[];
}

export const PatternList: React.FC<PatternListProps> = ({ patterns }) => {
  if (patterns.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Ingen mønstre funnet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {patterns.map((pattern) => (
        <div
          key={pattern.id}
          className="bg-dark-card border border-dark-border rounded-lg p-4 hover:border-accent-blue transition-colors"
        >
          <div className="flex items-start justify-between mb-2">
            <h4 className="font-medium text-gray-100">{pattern.description}</h4>
            <span className="text-xs text-gray-500 bg-dark-bg px-2 py-1 rounded">
              {pattern.matchCount} treff
            </span>
          </div>
          
          <div className="mb-2">
            <ConfidenceScore score={pattern.confidence} size="sm" />
          </div>
          
          <div className="text-xs text-gray-500">
            Sist brukt: <ClientSafeTimestamp date={pattern.lastUsed} format="datetime" />
          </div>
        </div>
      ))}
    </div>
  );
};
