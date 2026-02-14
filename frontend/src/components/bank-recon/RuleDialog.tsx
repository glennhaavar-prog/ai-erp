/**
 * RuleDialog - Modal for creating matching rules
 */
'use client';

import React, { useState } from 'react';
import { CreateRuleRequest } from '@/lib/api/bank-recon';
import { Button } from '@/components/ui/button';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface RuleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (rule: CreateRuleRequest) => void;
  clientId: string;
  isSubmitting?: boolean;
}

export function RuleDialog({
  isOpen,
  onClose,
  onSubmit,
  clientId,
  isSubmitting = false,
}: RuleDialogProps) {
  const [ruleType, setRuleType] = useState<'kid' | 'amount' | 'description' | 'date_range'>('kid');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(50);
  const [conditions, setConditions] = useState<Record<string, any>>({});

  // Condition fields based on rule type
  const [kidPattern, setKidPattern] = useState('');
  const [amountMin, setAmountMin] = useState('');
  const [amountMax, setAmountMax] = useState('');
  const [descriptionPattern, setDescriptionPattern] = useState('');
  const [dateRangeDays, setDateRangeDays] = useState('7');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Build conditions based on rule type
    let ruleConditions: Record<string, any> = {};
    
    switch (ruleType) {
      case 'kid':
        ruleConditions = { kid_pattern: kidPattern };
        break;
      case 'amount':
        ruleConditions = {
          min_amount: parseFloat(amountMin) || 0,
          max_amount: parseFloat(amountMax) || Infinity,
        };
        break;
      case 'description':
        ruleConditions = { description_pattern: descriptionPattern };
        break;
      case 'date_range':
        ruleConditions = { max_days_difference: parseInt(dateRangeDays) || 7 };
        break;
    }

    const rule: CreateRuleRequest = {
      client_id: clientId,
      rule_type: ruleType,
      name,
      description,
      conditions: ruleConditions,
      priority,
    };

    onSubmit(rule);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Opprett avstemmingsregel</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Rule Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Regelnavn *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="F.eks. 'KID-matching for faktura'"
            />
          </div>

          {/* Rule Type */}
          <div>
            <label htmlFor="ruleType" className="block text-sm font-medium text-gray-700 mb-2">
              Regeltype *
            </label>
            <select
              id="ruleType"
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="kid">KID-matching</option>
              <option value="amount">Beløp-matching</option>
              <option value="description">Beskrivelse-matching</option>
              <option value="date_range">Dato-område-matching</option>
            </select>
          </div>

          {/* Conditional Fields Based on Rule Type */}
          {ruleType === 'kid' && (
            <div>
              <label htmlFor="kidPattern" className="block text-sm font-medium text-gray-700 mb-2">
                KID-mønster *
              </label>
              <input
                type="text"
                id="kidPattern"
                value={kidPattern}
                onChange={(e) => setKidPattern(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="F.eks. '12345*' eller 'INV-*'"
              />
              <p className="text-xs text-gray-500 mt-1">
                Bruk * som wildcard (f.eks. 'INV-*' matcher 'INV-001', 'INV-002', etc.)
              </p>
            </div>
          )}

          {ruleType === 'amount' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="amountMin" className="block text-sm font-medium text-gray-700 mb-2">
                  Minimumsbeløp
                </label>
                <input
                  type="number"
                  id="amountMin"
                  value={amountMin}
                  onChange={(e) => setAmountMin(e.target.value)}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label htmlFor="amountMax" className="block text-sm font-medium text-gray-700 mb-2">
                  Maksimumsbeløp
                </label>
                <input
                  type="number"
                  id="amountMax"
                  value={amountMax}
                  onChange={(e) => setAmountMax(e.target.value)}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ubegrenset"
                />
              </div>
            </div>
          )}

          {ruleType === 'description' && (
            <div>
              <label htmlFor="descriptionPattern" className="block text-sm font-medium text-gray-700 mb-2">
                Beskrivelsesmønster *
              </label>
              <input
                type="text"
                id="descriptionPattern"
                value={descriptionPattern}
                onChange={(e) => setDescriptionPattern(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="F.eks. 'Lønn *' eller '*faktura*'"
              />
              <p className="text-xs text-gray-500 mt-1">
                Bruk * som wildcard. Case-insensitive matching.
              </p>
            </div>
          )}

          {ruleType === 'date_range' && (
            <div>
              <label htmlFor="dateRangeDays" className="block text-sm font-medium text-gray-700 mb-2">
                Maks dager mellom datoer *
              </label>
              <input
                type="number"
                id="dateRangeDays"
                value={dateRangeDays}
                onChange={(e) => setDateRangeDays(e.target.value)}
                required
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="7"
              />
              <p className="text-xs text-gray-500 mt-1">
                Matcher transaksjoner innenfor N dager fra hverandre
              </p>
            </div>
          )}

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Beskrivelse (valgfri)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Forklaring av regelens formål..."
            />
          </div>

          {/* Priority */}
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
              Prioritet (1-100)
            </label>
            <input
              type="number"
              id="priority"
              value={priority}
              onChange={(e) => setPriority(parseInt(e.target.value))}
              min="1"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Høyere nummer = høyere prioritet. Standard: 50.
            </p>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              onClick={onClose}
              variant="ghost"
              disabled={isSubmitting}
            >
              Avbryt
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="min-w-[120px]"
            >
              {isSubmitting ? 'Oppretter...' : 'Opprett regel'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
