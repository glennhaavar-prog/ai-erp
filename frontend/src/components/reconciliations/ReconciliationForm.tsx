/**
 * ReconciliationForm Component
 * Detail view with edit form for a single reconciliation
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Reconciliation, ReconciliationAttachment } from '@/lib/api/reconciliations';
import { AttachmentUpload } from './AttachmentUpload';
import { format } from 'date-fns';
import { nb } from 'date-fns/locale';

interface ReconciliationFormProps {
  reconciliation: Reconciliation;
  attachments: ReconciliationAttachment[];
  onUpdate: (data: { expected_balance?: number; notes?: string; status?: 'pending' | 'reconciled' }) => Promise<void>;
  onApprove: () => Promise<void>;
  onUploadAttachment: (file: File) => Promise<void>;
  onDeleteAttachment: (attachmentId: string) => Promise<void>;
  onRefreshAttachments: () => Promise<void>;
}

export const ReconciliationForm: React.FC<ReconciliationFormProps> = ({
  reconciliation,
  attachments,
  onUpdate,
  onApprove,
  onUploadAttachment,
  onDeleteAttachment,
  onRefreshAttachments,
}) => {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expectedBalance, setExpectedBalance] = useState<string>(
    reconciliation.expected_balance?.toString() || ''
  );
  const [notes, setNotes] = useState(reconciliation.notes || '');

  // Update form when reconciliation changes
  useEffect(() => {
    setExpectedBalance(reconciliation.expected_balance?.toString() || '');
    setNotes(reconciliation.notes || '');
  }, [reconciliation.id]);

  const isApproved = reconciliation.status === 'approved';
  const canApprove = reconciliation.status === 'reconciled';
  const canEdit = !isApproved;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'PPP', { locale: nb });
  };

  const calculateDifference = () => {
    if (!expectedBalance || expectedBalance === '') return null;
    const expected = parseFloat(expectedBalance);
    if (isNaN(expected)) return null;
    return reconciliation.closing_balance - expected;
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const data: any = {
        notes: notes || undefined,
      };

      if (expectedBalance && expectedBalance !== '') {
        const expected = parseFloat(expectedBalance);
        if (!isNaN(expected)) {
          data.expected_balance = expected;
        }
      }

      await onUpdate(data);
      setEditing(false);
    } catch (error) {
      console.error('Save error:', error);
      alert('Feil ved lagring');
    } finally {
      setSaving(false);
    }
  };

  const handleMarkReconciled = async () => {
    if (!expectedBalance || expectedBalance === '') {
      alert('Du må angi forventet balanse før du kan merke som avstemt');
      return;
    }

    const expected = parseFloat(expectedBalance);
    if (isNaN(expected)) {
      alert('Ugyldig beløp for forventet balanse');
      return;
    }

    setSaving(true);
    try {
      await onUpdate({
        expected_balance: expected,
        notes: notes || undefined,
        status: 'reconciled',
      });
      setEditing(false);
    } catch (error) {
      console.error('Update error:', error);
      alert('Feil ved oppdatering');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!confirm('Er du sikker på at du vil godkjenne denne avstemmingen? Den kan ikke endres etterpå.')) {
      return;
    }

    setSaving(true);
    try {
      await onApprove();
    } catch (error) {
      console.error('Approve error:', error);
      alert('Feil ved godkjenning');
    } finally {
      setSaving(false);
    }
  };

  const getDifferenceColor = (diff: number | null) => {
    if (diff === null) return 'text-gray-500';
    if (Math.abs(diff) < 0.01) return 'text-green-600 dark:text-green-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      pending: {
        label: 'Ventende',
        className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      },
      reconciled: {
        label: 'Avstemt',
        className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      },
      approved: {
        label: 'Godkjent',
        className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      },
    };

    const badge = badges[status as keyof typeof badges] || badges.pending;

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badge.className}`}>
        {badge.label}
      </span>
    );
  };

  const getTypeLabel = (type: string) => {
    const labels = {
      bank: 'Bank',
      receivables: 'Kundefordringer',
      payables: 'Leverandørgjeld',
      inventory: 'Varelager',
      other: 'Annet',
    };
    return labels[type as keyof typeof labels] || type;
  };

  const difference = calculateDifference();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {reconciliation.account_number} - {reconciliation.account_name}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {formatDate(reconciliation.period_start)} - {formatDate(reconciliation.period_end)}
          </p>
        </div>
        {getStatusBadge(reconciliation.status)}
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Type</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {getTypeLabel(reconciliation.reconciliation_type)}
          </div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Opprettet</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatDate(reconciliation.created_at)}
          </div>
        </div>
      </div>

      {/* Balances */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Balanser</h3>

        {/* Opening Balance - Read only */}
        <div className="flex justify-between items-center">
          <span className="text-gray-700 dark:text-gray-300">Åpningsbalanse:</span>
          <span className="font-mono text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(reconciliation.opening_balance)}
          </span>
        </div>

        {/* Closing Balance - Read only */}
        <div className="flex justify-between items-center">
          <span className="text-gray-700 dark:text-gray-300">Sluttbalanse (system):</span>
          <span className="font-mono text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(reconciliation.closing_balance)}
          </span>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 my-4"></div>

        {/* Expected Balance - Editable */}
        <div className="flex justify-between items-center">
          <span className="text-gray-700 dark:text-gray-300">Forventet balanse:</span>
          {editing && canEdit ? (
            <input
              type="number"
              step="0.01"
              value={expectedBalance}
              onChange={(e) => setExpectedBalance(e.target.value)}
              className="font-mono text-lg font-semibold text-right px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white w-48"
              placeholder="0.00"
            />
          ) : (
            <span className="font-mono text-lg font-semibold text-gray-900 dark:text-white">
              {reconciliation.expected_balance !== null
                ? formatCurrency(reconciliation.expected_balance)
                : '—'}
            </span>
          )}
        </div>

        {/* Difference - Calculated */}
        {(difference !== null || reconciliation.difference !== null) && (
          <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300 font-semibold">Differanse:</span>
            <span
              className={`font-mono text-xl font-bold ${getDifferenceColor(
                difference !== null ? difference : reconciliation.difference
              )}`}
            >
              {formatCurrency(
                Math.abs(difference !== null ? difference : reconciliation.difference!)
              )}
              {Math.abs(difference !== null ? difference : reconciliation.difference!) < 0.01 &&
                ' ✓ Balansert'}
            </span>
          </div>
        )}
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Notater
        </label>
        {editing && canEdit ? (
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Legg til notater..."
          />
        ) : (
          <div className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white min-h-[100px]">
            {reconciliation.notes || <span className="text-gray-500">Ingen notater</span>}
          </div>
        )}
      </div>

      {/* Attachments */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Vedlegg</h3>
        <AttachmentUpload
          reconciliationId={reconciliation.id}
          attachments={attachments}
          onUpload={onUploadAttachment}
          onDelete={onDeleteAttachment}
          disabled={isApproved}
        />
      </div>

      {/* Metadata (if reconciled/approved) */}
      {(reconciliation.reconciled_at || reconciliation.approved_at) && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-2 text-sm text-gray-600 dark:text-gray-400">
          {reconciliation.reconciled_at && (
            <div>
              Avstemt: {formatDate(reconciliation.reconciled_at)}
              {reconciliation.reconciled_by && ` av ${reconciliation.reconciled_by}`}
            </div>
          )}
          {reconciliation.approved_at && (
            <div>
              Godkjent: {formatDate(reconciliation.approved_at)}
              {reconciliation.approved_by && ` av ${reconciliation.approved_by}`}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {canEdit && (
        <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors"
              >
                {saving ? 'Lagrer...' : '💾 Lagre'}
              </button>
              <button
                onClick={handleMarkReconciled}
                disabled={saving || !expectedBalance}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors"
              >
                {saving ? 'Lagrer...' : '✓ Merk som avstemt'}
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setExpectedBalance(reconciliation.expected_balance?.toString() || '');
                  setNotes(reconciliation.notes || '');
                }}
                disabled={saving}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md font-medium transition-colors"
              >
                Avbryt
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditing(true)}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
              >
                ✏️ Rediger
              </button>
              {canApprove && (
                <button
                  onClick={handleApprove}
                  disabled={saving}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors"
                >
                  {saving ? 'Godkjenner...' : '✓ Godkjenn'}
                </button>
              )}
            </>
          )}
        </div>
      )}

      {isApproved && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <p className="text-green-800 dark:text-green-200 font-medium">
            ✓ Denne avstemmingen er godkjent og kan ikke lenger endres.
          </p>
        </div>
      )}
    </div>
  );
};
