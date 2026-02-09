'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ConfidenceBreakdownProps {
  totalScore: number;
  breakdown?: {
    vendor_familiarity?: number;
    historical_similarity?: number;
    vat_validation?: number;
    pattern_matching?: number;
    amount_reasonableness?: number;
  };
  reasoning?: string;
}

export const ConfidenceBreakdown: React.FC<ConfidenceBreakdownProps> = ({
  totalScore,
  breakdown = {},
  reasoning
}) => {
  const factors = [
    {
      key: 'vendor_familiarity',
      label: 'Leverandør-kjennskap',
      max: 30,
      description: 'Basert på antall tidligere fakturaer'
    },
    {
      key: 'historical_similarity',
      label: 'Historisk likhet',
      max: 30,
      description: 'Sammenligning med tidligere konteringer'
    },
    {
      key: 'vat_validation',
      label: 'MVA-validering',
      max: 20,
      description: 'MVA-beløp og koder stemmer'
    },
    {
      key: 'pattern_matching',
      label: 'Mønstergjenkjenning',
      max: 15,
      description: 'Matcher lærte mønstre'
    },
    {
      key: 'amount_reasonableness',
      label: 'Beløp-rimelignet',
      max: 5,
      description: 'Beløpet er innenfor normal range'
    }
  ];

  const getConfidenceColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getConfidenceBgColor = (score: number) => {
    if (score >= 85) return 'bg-green-600';
    if (score >= 70) return 'bg-yellow-600';
    if (score >= 50) return 'bg-orange-600';
    return 'bg-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 85) return 'HØY - Auto-godkjent';
    if (score >= 70) return 'MIDDELS - Trenger vurdering';
    if (score >= 50) return 'LAV - Kritisk gjennomgang';
    return 'VELDIG LAV - Manuell håndtering';
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-100 mb-4">Confidence Score Analyse</h3>

      {/* Total Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Total Confidence</span>
          <span className={`text-2xl font-bold ${getConfidenceColor(totalScore)}`}>
            {totalScore}%
          </span>
        </div>
        
        <div className="w-full bg-gray-700 rounded-full h-3 mb-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${totalScore}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className={`h-3 rounded-full ${getConfidenceBgColor(totalScore)}`}
          />
        </div>
        
        <p className="text-sm text-gray-400 text-center">
          {getScoreLabel(totalScore)}
        </p>
      </div>

      {/* Breakdown */}
      <div className="space-y-4 mb-6">
        <h4 className="text-sm font-semibold text-gray-300 mb-2">Delscorer:</h4>
        
        {factors.map((factor) => {
          const score = breakdown[factor.key as keyof typeof breakdown] || 0;
          const percentage = (score / factor.max) * 100;
          
          return (
            <div key={factor.key} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{factor.label}</span>
                <span className="text-gray-400 font-medium">
                  {score} / {factor.max}
                </span>
              </div>
              
              <div className="w-full bg-gray-700 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }}
                  className={`h-2 rounded-full ${
                    percentage >= 80 ? 'bg-green-500' :
                    percentage >= 50 ? 'bg-yellow-500' :
                    percentage >= 30 ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}
                />
              </div>
              
              <p className="text-xs text-gray-500">{factor.description}</p>
            </div>
          );
        })}
      </div>

      {/* Reasoning */}
      {reasoning && (
        <div className="pt-4 border-t border-dark-border">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">AI Begrunnelse:</h4>
          <p className="text-sm text-gray-400 leading-relaxed">
            {reasoning}
          </p>
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-dark-border">
        <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase">Terskelverdier:</h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-600"></div>
            <span className="text-gray-400">&gt;85% = Auto-godkjenn</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-yellow-600"></div>
            <span className="text-gray-400">70-84% = Sjekk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-orange-600"></div>
            <span className="text-gray-400">50-69% = Gjennomgå</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-600"></div>
            <span className="text-gray-400">&lt;50% = Kritisk</span>
          </div>
        </div>
      </div>
    </div>
  );
};
