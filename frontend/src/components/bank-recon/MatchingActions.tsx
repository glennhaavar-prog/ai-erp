/**
 * MatchingActions - Middle Panel Component
 * Action buttons for matching operations
 */
'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { LinkIcon, SparklesIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

interface MatchingActionsProps {
  selectedBankCount: number;
  selectedLedgerCount: number;
  onMatch: () => void;
  onAutoMatch: () => void;
  onCreateRule: () => void;
  isMatching?: boolean;
  isAutoMatching?: boolean;
}

export function MatchingActions({
  selectedBankCount,
  selectedLedgerCount,
  onMatch,
  onAutoMatch,
  onCreateRule,
  isMatching = false,
  isAutoMatching = false,
}: MatchingActionsProps) {
  
  const canMatch = selectedBankCount > 0 && selectedLedgerCount > 0;

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-6 bg-gray-50 border-y border-gray-200">
      {/* Selection Summary */}
      <div className="text-center">
        <p className="text-sm text-gray-600">
          <span className="font-medium text-blue-600">{selectedBankCount}</span> bank
          {selectedBankCount !== 1 ? 'transaksjoner' : 'transaksjon'} og{' '}
          <span className="font-medium text-blue-600">{selectedLedgerCount}</span> hovedbok
          {selectedLedgerCount !== 1 ? 'føringer' : 'føring'} valgt
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col w-full max-w-xs gap-3">
        {/* Match Selected */}
        <Button
          onClick={onMatch}
          disabled={!canMatch || isMatching}
          className="w-full"
          variant="default"
        >
          <LinkIcon className="w-4 h-4 mr-2" />
          {isMatching ? 'Avstemmer...' : 'Avstem valgte'}
        </Button>

        {/* Auto-Match */}
        <Button
          onClick={onAutoMatch}
          disabled={isAutoMatching}
          className="w-full"
          variant="outline"
        >
          <SparklesIcon className="w-4 h-4 mr-2" />
          {isAutoMatching ? 'Kjører auto-avstemming...' : 'Auto-avstemming'}
        </Button>

        {/* Create Rule */}
        <Button
          onClick={onCreateRule}
          disabled={!canMatch}
          className="w-full"
          variant="ghost"
        >
          <Cog6ToothIcon className="w-4 h-4 mr-2" />
          Opprett regel
        </Button>
      </div>

      {/* Help Text */}
      {!canMatch && (
        <p className="text-xs text-gray-500 text-center max-w-xs">
          Velg minst én banktransaksjon og én hovedbokføring for å avstemme
        </p>
      )}
    </div>
  );
}
