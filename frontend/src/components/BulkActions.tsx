/**
 * Bulk Actions Component
 * Multi-select with checkboxes for table actions
 * Actions: Delete (deactivate), Export CSV, Bulk edit status
 */
'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  TrashIcon,
  ArrowDownTrayIcon,
  PencilSquareIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import axios from 'axios';
import { toast } from 'sonner';

interface BulkActionsProps {
  selectedIds: string[];
  totalCount: number;
  entityType: 'suppliers' | 'customers' | 'vouchers' | 'invoices';
  onClearSelection: () => void;
  onRefresh: () => void;
}

export function BulkActions({
  selectedIds,
  totalCount,
  entityType,
  onClearSelection,
  onRefresh,
}: BulkActionsProps) {
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

  const handleBulkDelete = useCallback(async () => {
    if (!confirm(`Er du sikker på at du vil deaktivere ${selectedIds.length} element(er)?`)) {
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/${entityType}/bulk-deactivate`, {
        ids: selectedIds,
      });

      toast.success(`${selectedIds.length} element(er) deaktivert`);
      onClearSelection();
      onRefresh();
    } catch (error: any) {
      console.error('Bulk delete error:', error);
      toast.error(error.response?.data?.message || 'Kunne ikke deaktivere');
    } finally {
      setLoading(false);
    }
  }, [selectedIds, entityType, onClearSelection, onRefresh]);

  const handleBulkExport = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/${entityType}/export`,
        { ids: selectedIds },
        { responseType: 'blob' }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${entityType}-export-${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`${selectedIds.length} element(er) eksportert`);
      onClearSelection();
    } catch (error: any) {
      console.error('Bulk export error:', error);
      toast.error('Kunne ikke eksportere');
    } finally {
      setLoading(false);
    }
  }, [selectedIds, entityType, onClearSelection]);

  const handleBulkStatusChange = useCallback(async (status: string) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/${entityType}/bulk-update-status`, {
        ids: selectedIds,
        status,
      });

      toast.success(`Status oppdatert for ${selectedIds.length} element(er)`);
      onClearSelection();
      onRefresh();
    } catch (error: any) {
      console.error('Bulk status change error:', error);
      toast.error(error.response?.data?.message || 'Kunne ikke oppdatere status');
    } finally {
      setLoading(false);
    }
  }, [selectedIds, entityType, onClearSelection, onRefresh]);

  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-gray-900 dark:bg-gray-800 text-white rounded-lg shadow-2xl border border-gray-700 px-6 py-4">
      <div className="flex items-center gap-6">
        {/* Selection info */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-6 h-6 bg-blue-500 rounded-full">
            <CheckIcon className="w-4 h-4" />
          </div>
          <span className="font-medium">
            {selectedIds.length} av {totalCount} valgt
          </span>
        </div>

        {/* Divider */}
        <div className="h-8 w-px bg-gray-600" />

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Export */}
          <Button
            onClick={handleBulkExport}
            disabled={loading}
            variant="ghost"
            size="sm"
            className="text-white hover:bg-gray-700"
          >
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Eksporter CSV
          </Button>

          {/* Status change (for vouchers/invoices) */}
          {(entityType === 'vouchers' || entityType === 'invoices') && (
            <div className="relative group">
              <Button
                disabled={loading}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-gray-700"
              >
                <PencilSquareIcon className="w-4 h-4 mr-2" />
                Endre status
              </Button>
              
              {/* Status dropdown */}
              <div className="absolute bottom-full mb-2 left-0 hidden group-hover:block bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 min-w-[150px]">
                {entityType === 'vouchers' && (
                  <>
                    <button
                      onClick={() => handleBulkStatusChange('draft')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Utkast
                    </button>
                    <button
                      onClick={() => handleBulkStatusChange('review')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Til godkjenning
                    </button>
                    <button
                      onClick={() => handleBulkStatusChange('approved')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Godkjent
                    </button>
                  </>
                )}
                {entityType === 'invoices' && (
                  <>
                    <button
                      onClick={() => handleBulkStatusChange('sent')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Sendt
                    </button>
                    <button
                      onClick={() => handleBulkStatusChange('paid')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Betalt
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Delete */}
          <Button
            onClick={handleBulkDelete}
            disabled={loading}
            variant="ghost"
            size="sm"
            className="text-red-400 hover:bg-red-900/20 hover:text-red-300"
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Deaktiver
          </Button>
        </div>

        {/* Divider */}
        <div className="h-8 w-px bg-gray-600" />

        {/* Clear selection */}
        <Button
          onClick={onClearSelection}
          variant="ghost"
          size="sm"
          className="text-gray-400 hover:bg-gray-700 hover:text-white"
        >
          Avbryt
        </Button>
      </div>
    </div>
  );
}

// Hook for managing bulk selection
export function useBulkSelection<T extends { id: string }>(items: T[]) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const toggleSelection = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  }, []);

  const toggleAll = useCallback(() => {
    if (selectedIds.length === items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(items.map((item) => item.id));
    }
  }, [items, selectedIds.length]);

  const clearSelection = useCallback(() => {
    setSelectedIds([]);
  }, []);

  const isSelected = useCallback(
    (id: string) => selectedIds.includes(id),
    [selectedIds]
  );

  const isAllSelected = items.length > 0 && selectedIds.length === items.length;
  const isSomeSelected = selectedIds.length > 0 && selectedIds.length < items.length;

  return {
    selectedIds,
    toggleSelection,
    toggleAll,
    clearSelection,
    isSelected,
    isAllSelected,
    isSomeSelected,
  };
}
