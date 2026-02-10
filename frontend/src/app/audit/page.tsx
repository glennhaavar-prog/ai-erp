'use client';

import React, { useState, useEffect } from 'react';
import { AuditEntry, AuditFilters, AuditAction, ChangedByType, AuditTable } from '@/types/audit';
import { auditApi } from '@/api/audit';
import { useClient } from '@/contexts/ClientContext';

export default function AuditTrailPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [tables, setTables] = useState<AuditTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 50;

  // Filter state
  const [filters, setFilters] = useState<AuditFilters>({
    start_date: '',
    end_date: '',
    action: '',
    table_name: '',
    changed_by_type: '',
    search: '',
    sort_order: 'desc',
    page: 1,
    page_size: pageSize,
  });

  // Get selected client from context
  const { selectedClient, isLoading: clientLoading } = useClient();
  const clientId = selectedClient?.id;

  // Fetch tables for dropdown
  useEffect(() => {
    if (!clientId) return;
    
    const fetchTables = async () => {
      try {
        const data = await auditApi.getTables(clientId);
        setTables(data.tables);
      } catch (err) {
        console.error('Error fetching tables:', err);
      }
    };

    fetchTables();
  }, [clientId]);

  // Fetch audit entries from API
  useEffect(() => {
    if (!clientId) return;
    
    const fetchEntries = async () => {
      try {
        setLoading(true);
        const filterParams = {
          ...filters,
          client_id: clientId,
          page: currentPage,
          page_size: pageSize,
        };

        // Remove empty filters
        Object.keys(filterParams).forEach(key => {
          if (filterParams[key as keyof AuditFilters] === '' || 
              filterParams[key as keyof AuditFilters] === undefined) {
            delete filterParams[key as keyof AuditFilters];
          }
        });

        const data = await auditApi.getEntries(filterParams);
        setEntries(data.entries);
        setTotalPages(data.pagination.total_pages);
        setTotalCount(data.pagination.total_entries);
        setError(null);
      } catch (err) {
        console.error('Error fetching audit trail:', err);
        setError('Kunne ikke laste revisjonsloggen. Vennligst prøv igjen.');
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEntries();
  }, [filters, currentPage, clientId]);

  // Handle filter changes
  const handleFilterChange = (key: keyof AuditFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page on filter change
  };

  // Handle row click
  const handleRowClick = (entry: AuditEntry) => {
    setSelectedEntry(entry);
    setShowDetailModal(true);
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString('nb-NO', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Format date for input
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('nb-NO');
  };

  // Get action badge color
  const getActionBadgeColor = (action: AuditAction): string => {
    switch (action) {
      case 'create':
        return 'bg-accent-green/10 text-accent-green';
      case 'update':
        return 'bg-accent-blue/10 text-accent-blue';
      case 'delete':
        return 'bg-accent-red/10 text-accent-red';
      default:
        return 'bg-gray-500/10 text-gray-500';
    }
  };

  // Get changed_by_type badge color
  const getChangedByTypeBadgeColor = (type: ChangedByType): string => {
    switch (type) {
      case 'user':
        return 'bg-blue-500/10 text-blue-400';
      case 'ai_agent':
        return 'bg-purple-500/10 text-purple-400';
      case 'system':
        return 'bg-gray-500/10 text-gray-400';
      default:
        return 'bg-gray-500/10 text-gray-500';
    }
  };

  // Get action label
  const getActionLabel = (action: AuditAction): string => {
    switch (action) {
      case 'create':
        return 'Opprettet';
      case 'update':
        return 'Oppdatert';
      case 'delete':
        return 'Slettet';
      default:
        return action;
    }
  };

  // Get changed_by_type label
  const getChangedByTypeLabel = (type: ChangedByType): string => {
    switch (type) {
      case 'user':
        return 'Bruker';
      case 'ai_agent':
        return 'AI-Agent';
      case 'system':
        return 'System';
      default:
        return type;
    }
  };

  // Show loading when client context is loading
  if (clientLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster klient...</p>
        </div>
      </div>
    );
  }

  // Show message when no client is selected
  if (!clientId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            Velg en klient fra menyen øverst for å se revisjonslogg
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Revisjonslogg</h1>
            <p className="text-sm text-gray-400 mt-1">
              Komplett historikk over alle systemendringer
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Viser {entries.length} av {totalCount} hendelser
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-dark-card border border-dark-border rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Fra dato
              </label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Til dato
              </label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              />
            </div>

            {/* Action Type */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Handling
              </label>
              <select
                value={filters.action || ''}
                onChange={(e) => handleFilterChange('action', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="">Alle handlinger</option>
                <option value="create">Opprettet</option>
                <option value="update">Oppdatert</option>
                <option value="delete">Slettet</option>
              </select>
            </div>

            {/* Table Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tabell
              </label>
              <select
                value={filters.table_name || ''}
                onChange={(e) => handleFilterChange('table_name', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="">Alle tabeller</option>
                {tables.map(table => (
                  <option key={table.table_name} value={table.table_name}>
                    {table.table_name} ({table.event_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Changed By Type */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Utført av
              </label>
              <select
                value={filters.changed_by_type || ''}
                onChange={(e) => handleFilterChange('changed_by_type', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="">Alle typer</option>
                <option value="user">Bruker</option>
                <option value="ai_agent">AI-Agent</option>
                <option value="system">System</option>
              </select>
            </div>

            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Søk
              </label>
              <input
                type="text"
                placeholder="Søk i tabell, handling, eller bruker..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              />
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Sortering
              </label>
              <select
                value={filters.sort_order || 'desc'}
                onChange={(e) => handleFilterChange('sort_order', e.target.value as 'asc' | 'desc')}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="desc">Nyeste først</option>
                <option value="asc">Eldste først</option>
              </select>
            </div>
          </div>

          {/* Clear Filters Button */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => {
                setFilters({
                  start_date: '',
                  end_date: '',
                  action: '',
                  table_name: '',
                  changed_by_type: '',
                  search: '',
                  sort_order: 'desc',
                  page: 1,
                  page_size: pageSize,
                });
                setCurrentPage(1);
              }}
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              Nullstill filtre
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-accent-red/10 border border-accent-red/50 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-accent-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-accent-red">{error}</span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="bg-dark-card border border-dark-border rounded-lg p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-accent-blue border-t-transparent"></div>
            <p className="text-gray-400 mt-4">Laster revisjonslogg...</p>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-dark-hover border-b border-dark-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Tidspunkt
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Handling
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Tabell
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Post-ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Utført av
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Begrunnelse
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-border">
                    {entries.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-12 text-center text-gray-500">
                          Ingen hendelser funnet
                        </td>
                      </tr>
                    ) : (
                      entries.map((entry) => (
                        <tr
                          key={entry.id}
                          onClick={() => handleRowClick(entry)}
                          className="cursor-pointer hover:bg-dark-hover transition-colors"
                        >
                          <td className="px-4 py-3 text-sm text-gray-300 whitespace-nowrap">
                            {formatTimestamp(entry.timestamp)}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionBadgeColor(entry.action)}`}>
                              {getActionLabel(entry.action)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                            {entry.table_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 font-mono truncate max-w-xs">
                            {entry.record_id.substring(0, 8)}...
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-300">
                            {entry.changed_by_name || 'Ukjent'}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getChangedByTypeBadgeColor(entry.changed_by_type)}`}>
                              {getChangedByTypeLabel(entry.changed_by_type)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-400 truncate max-w-xs">
                            {entry.reason || '-'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between bg-dark-card border border-dark-border rounded-lg px-4 py-3">
                <div className="text-sm text-gray-400">
                  Side {currentPage} av {totalPages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Forrige
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Neste
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Detail Modal */}
        {showDetailModal && selectedEntry && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-dark-card border border-dark-border rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-dark-border sticky top-0 bg-dark-card z-10">
                <h3 className="text-xl font-bold text-gray-100">
                  Hendelsesdetaljer
                </h3>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="text-gray-400 hover:text-gray-300 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Tidspunkt
                    </label>
                    <p className="text-gray-100 font-medium">{formatTimestamp(selectedEntry.timestamp)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Handling
                    </label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionBadgeColor(selectedEntry.action)}`}>
                      {getActionLabel(selectedEntry.action)}
                    </span>
                  </div>
                </div>

                {/* Entity Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Tabell
                    </label>
                    <p className="text-gray-100 font-mono">{selectedEntry.table_name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Post-ID
                    </label>
                    <p className="text-gray-100 font-mono text-xs break-all">{selectedEntry.record_id}</p>
                  </div>
                </div>

                {/* Changed By Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Utført av
                    </label>
                    <p className="text-gray-100">{selectedEntry.changed_by_name || 'Ukjent'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Type
                    </label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getChangedByTypeBadgeColor(selectedEntry.changed_by_type)}`}>
                      {getChangedByTypeLabel(selectedEntry.changed_by_type)}
                    </span>
                  </div>
                </div>

                {/* Reason */}
                {selectedEntry.reason && (
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Begrunnelse
                    </label>
                    <p className="text-gray-100 bg-dark-bg p-3 rounded-lg border border-dark-border">
                      {selectedEntry.reason}
                    </p>
                  </div>
                )}

                {/* Technical Details */}
                <div className="pt-4 border-t border-dark-border">
                  <h4 className="text-sm font-medium text-gray-300 mb-3">Tekniske detaljer</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {selectedEntry.ip_address && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          IP-adresse
                        </label>
                        <p className="text-gray-400 font-mono">{selectedEntry.ip_address}</p>
                      </div>
                    )}
                    {selectedEntry.changed_by_id && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Bruker-ID
                        </label>
                        <p className="text-gray-400 font-mono text-xs break-all">{selectedEntry.changed_by_id}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Data Changes */}
                {(selectedEntry.old_value || selectedEntry.new_value) && (
                  <div className="pt-4 border-t border-dark-border">
                    <h4 className="text-sm font-medium text-gray-300 mb-3">Dataendringer</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {selectedEntry.old_value && (
                        <div>
                          <label className="block text-xs text-gray-500 mb-2">
                            Gammel verdi
                          </label>
                          <pre className="text-xs text-gray-400 bg-dark-bg p-3 rounded-lg border border-dark-border overflow-x-auto">
                            {JSON.stringify(selectedEntry.old_value, null, 2)}
                          </pre>
                        </div>
                      )}
                      {selectedEntry.new_value && (
                        <div>
                          <label className="block text-xs text-gray-500 mb-2">
                            Ny verdi
                          </label>
                          <pre className="text-xs text-gray-400 bg-dark-bg p-3 rounded-lg border border-dark-border overflow-x-auto">
                            {JSON.stringify(selectedEntry.new_value, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex justify-end items-center gap-3 p-6 border-t border-dark-border">
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg text-sm font-medium transition-colors"
                >
                  Lukk
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
