'use client';

import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { 
  AuditTrailEntry, 
  AuditTrailResponse,
  fetchVoucherAuditTrail 
} from '@/lib/api/voucher-control';

interface AuditTrailPanelProps {
  voucherId: string;
  voucherNumber: string;
  onClose: () => void;
}

/**
 * Audit Trail Panel - Timeline view of all actions on a voucher
 * Shows: AI suggestions → manual review → approval/correction/rejection
 */
export default function AuditTrailPanel({
  voucherId,
  voucherNumber,
  onClose,
}: AuditTrailPanelProps) {
  const [auditTrail, setAuditTrail] = useState<AuditTrailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAuditTrail();
  }, [voucherId]);

  const loadAuditTrail = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchVoucherAuditTrail(voucherId);
      setAuditTrail(data);
    } catch (err) {
      console.error('Failed to load audit trail:', err);
      setError(err instanceof Error ? err.message : 'Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  };

  const getIconForPerformedBy = (performedBy: AuditTrailEntry['performed_by']) => {
    switch (performedBy) {
      case 'ai':
        return '🤖';
      case 'accountant':
        return '✏️';
      case 'supervisor':
        return '📋';
      case 'manager':
        return '👤';
      default:
        return '📝';
    }
  };

  const getIconForAction = (action: string) => {
    const lowerAction = action.toLowerCase();
    if (lowerAction.includes('godkjent') || lowerAction.includes('approved')) return '✅';
    if (lowerAction.includes('korrigert') || lowerAction.includes('corrected')) return '✏️';
    if (lowerAction.includes('avvist') || lowerAction.includes('rejected')) return '❌';
    if (lowerAction.includes('regel') || lowerAction.includes('rule')) return '📋';
    if (lowerAction.includes('manager') || lowerAction.includes('leder')) return '👤';
    if (lowerAction.includes('ai') || lowerAction.includes('auto')) return '🤖';
    return '📝';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('nb-NO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatConfidence = (confidence?: number) => {
    if (!confidence) return null;
    return `${Math.round(confidence * 100)}% konfidensgrad`;
  };

  const renderDetails = (details: any) => {
    if (!details) return null;

    return (
      <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm space-y-1">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex gap-2">
            <span className="font-medium text-gray-600 capitalize">
              {key.replace(/_/g, ' ')}:
            </span>
            <span className="text-gray-900">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Audit Trail
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Bilag #{voucherNumber}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Lukk"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 font-medium">Feil ved lasting av audit trail</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          )}

          {!loading && !error && auditTrail && (
            <div className="space-y-6">
              {/* Timeline */}
              <div className="relative">
                {/* Vertical line */}
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                {/* Timeline entries */}
                <div className="space-y-6">
                  {auditTrail.entries.map((entry, index) => (
                    <div key={entry.id} className="relative flex gap-4">
                      {/* Icon */}
                      <div className="flex-shrink-0 w-12 h-12 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center text-2xl z-10">
                        {getIconForAction(entry.action)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                        {/* Action header */}
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 text-lg">
                              {entry.action}
                            </h3>
                            <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                              <span className="flex items-center gap-1">
                                {getIconForPerformedBy(entry.performed_by)}
                                {entry.user_name || 
                                  (entry.performed_by === 'ai' ? 'AI System' : 
                                   entry.performed_by === 'accountant' ? 'Regnskapsfører' :
                                   entry.performed_by === 'supervisor' ? 'Supervisor' :
                                   'Manager')}
                              </span>
                              <span className="text-gray-400">•</span>
                              <span>{formatTimestamp(entry.timestamp)}</span>
                            </div>
                          </div>

                          {/* AI Confidence badge */}
                          {entry.ai_confidence && (
                            <div className="flex-shrink-0">
                              <div className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                                {formatConfidence(entry.ai_confidence)}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Details */}
                        {entry.details && renderDetails(entry.details)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary footer */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-600">
                  <strong>{auditTrail.entries.length}</strong> hendelser registrert for dette bilaget
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
          >
            Lukk
          </button>
        </div>
      </div>
    </div>
  );
}
