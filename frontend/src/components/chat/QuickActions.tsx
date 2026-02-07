"use client";

import React, { useState } from 'react';
import { FileText, BarChart3, CheckCircle, AlertCircle, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface QuickActionsProps {
  onAction: (command: string) => void;
  disabled?: boolean;
}

const QUICK_ACTIONS = [
  {
    label: 'Fakturaer som venter',
    icon: FileText,
    command: 'Vis meg fakturaer som venter',
    color: 'blue'
  },
  {
    label: 'Status oversikt',
    icon: BarChart3,
    command: 'Hva er status på alle fakturaer?',
    color: 'green'
  },
  {
    label: 'Lav confidence',
    icon: AlertCircle,
    command: 'Vis meg fakturaer med lav confidence',
    color: 'orange'
  },
  {
    label: 'Hjelp',
    icon: HelpCircle,
    command: 'help',
    color: 'purple'
  }
];

export default function QuickActions({ onAction, disabled }: QuickActionsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200',
    green: 'bg-green-50 text-green-600 hover:bg-green-100 border-green-200',
    orange: 'bg-orange-50 text-orange-600 hover:bg-orange-100 border-orange-200',
    purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100 border-purple-200'
  };

  return (
    <div className="border-b border-gray-200 bg-white">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium">Hurtigvalg</span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {/* Actions grid */}
      {isExpanded && (
        <div className="px-4 pb-3 grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((action, idx) => {
            const Icon = action.icon;
            return (
              <button
                key={idx}
                onClick={() => onAction(action.command)}
                disabled={disabled}
                className={`
                  flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors text-sm font-medium
                  ${colorClasses[action.color]}
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{action.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
