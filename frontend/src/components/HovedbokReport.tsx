'use client';

import React, { useState, useEffect } from 'react';
import { HovedbokEntry, HovedbokFilters, EntryStatus, Vendor } from '@/types/hovedbok';
import { hovedbokApi } from '@/api/hovedbok';
import { PdfViewerModal } from './PdfViewerModal';
import { useClient } from '@/contexts/ClientContext';

export const HovedbokReport: React.FC = () => {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [entries, setEntries] = useState<HovedbokEntry[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<HovedbokEntry | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showPdfViewer, setShowPdfViewer] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 50;

  // Filter state
  const [filters, setFilters] = useState<HovedbokFilters>({
    start_date: '',
    end_date: '',
    account_number: '',
    vendor_id: '',
    status: undefined,
    page: 1,
    page_size: pageSize,
  });

  // Sorting state
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fetch vendors for dropdown
  useEffect(() => {
    const fetchVendors = async () => {
      try {
        const vendorData = await hovedbokApi.getVendors();
        setVendors(vendorData);
      } catch (err) {
        console.error('Error fetching vendors:', err);
        // Non-critical, continue without vendor dropdown
      }
    };

    fetchVendors();
  }, []);

  // Fetch entries from API
  useEffect(() => {
    // Don't fetch if no client is selected
    if (!selectedClient) {
      setLoading(false);
      return;
    }

    const fetchEntries = async () => {
      try {
        setLoading(true);
        const filterParams = {
          ...filters,
          client_id: selectedClient.id,
          page: currentPage,
          page_size: pageSize,
        };
        
        // Remove empty filters
        Object.keys(filterParams).forEach(key => {
          if (filterParams[key as keyof HovedbokFilters] === '' || 
              filterParams[key as keyof HovedbokFilters] === undefined) {
            delete filterParams[key as keyof HovedbokFilters];
          }
        });

        const data = await hovedbokApi.getEntries(filterParams);
        setEntries(data.entries);
        setTotalPages(data.total_pages);
        setTotalCount(data.total_count);
        setError(null);
      } catch (err) {
        console.error('Error fetching hovedbok entries:', err);
        setError('Kunne ikke laste hovedboken. Vennligst prøv igjen.');
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEntries();
  }, [filters, currentPage, selectedClient]);

  // Calculate running balance
  const calculateBalance = (index: number): number => {
    let balance = 0;
    for (let i = 0; i <= index; i++) {
      const entry = entries[i];
      if (entry.status !== 'reversed') {
        balance += entry.debit_amount - entry.credit_amount;
      }
    }
    return balance;
  };

  // Sort entries by date
  const sortedEntries = [...entries].sort((a, b) => {
    const dateA = new Date(a.accounting_date).getTime();
    const dateB = new Date(b.accounting_date).getTime();
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
  });

  // Handle filter changes
  const handleFilterChange = (key: keyof HovedbokFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page on filter change
  };

  // Handle row click
  const handleRowClick = (entry: HovedbokEntry) => {
    setSelectedEntry(entry);
    setShowDetailModal(true);
  };

  // Handle export
  const handleExport = async () => {
    try {
      const filterParams = { ...filters };
      // Remove empty filters
      Object.keys(filterParams).forEach(key => {
        if (filterParams[key as keyof HovedbokFilters] === '' || 
            filterParams[key as keyof HovedbokFilters] === undefined) {
          delete filterParams[key as keyof HovedbokFilters];
        }
      });

      const blob = await hovedbokApi.exportToExcel(filterParams);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hovedbok_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting to Excel:', err);
      alert('Kunne ikke eksportere til Excel. Funksjonen kommer snart.');
    }
  };

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('nb-NO');
  };

  // Show message if no client selected
  if (!selectedClient && !clientLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-xl text-gray-400 mb-2">Ingen klient valgt</p>
          <p className="text-sm text-gray-500">
            Velg en klient fra dropdown-menyen øverst for å se hovedboken.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Hovedbok</h1>
          <p className="text-sm text-gray-400 mt-1">
            Viser {entries.length} av {totalCount} posteringer
          </p>
        </div>
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-accent-green hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Eksporter til Excel
        </button>
      </div>

      {/* Filters */}
      <div className="bg-dark-card border border-dark-border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

          {/* Account Number */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Kontonummer
            </label>
            <input
              type="text"
              placeholder="F.eks. 2400"
              value={filters.account_number || ''}
              onChange={(e) => handleFilterChange('account_number', e.target.value)}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            />
          </div>

          {/* Vendor */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Leverandør
            </label>
            <select
              value={filters.vendor_id || ''}
              onChange={(e) => handleFilterChange('vendor_id', e.target.value)}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            >
              <option value="">Alle leverandører</option>
              {vendors.map(vendor => (
                <option key={vendor.id} value={vendor.id}>
                  {vendor.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value as EntryStatus | '')}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            >
              <option value="">Alle statuser</option>
              <option value="posted">Postert</option>
              <option value="reversed">Reversert</option>
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
                account_number: '',
                vendor_id: '',
                status: undefined,
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
          <p className="text-gray-400 mt-4">Laster posteringer...</p>
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
                      Bilagsnr
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:text-accent-blue transition-colors"
                      onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                    >
                      <div className="flex items-center gap-1">
                        Dato
                        <svg className={`w-4 h-4 transition-transform ${sortOrder === 'asc' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Konto
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Debet
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Kredit
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Tekst
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      MVA-kode
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Bilagsart
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Saldo
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {sortedEntries.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-12 text-center text-gray-500">
                        Ingen posteringer funnet
                      </td>
                    </tr>
                  ) : (
                    sortedEntries.map((entry, index) => (
                      <tr
                        key={entry.id}
                        onClick={() => handleRowClick(entry)}
                        className={`cursor-pointer hover:bg-dark-hover transition-colors ${
                          entry.status === 'reversed' ? 'opacity-50' : ''
                        }`}
                      >
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {entry.voucher_number}
                          {entry.status === 'reversed' && (
                            <span className="ml-2 text-xs text-accent-red">(REV)</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {formatDate(entry.accounting_date)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="text-gray-300 font-medium">{entry.account_number}</div>
                          {entry.account_name && (
                            <div className="text-xs text-gray-500">{entry.account_name}</div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-right text-gray-300">
                          {entry.debit_amount > 0 ? formatCurrency(entry.debit_amount) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-right text-gray-300">
                          {entry.credit_amount > 0 ? formatCurrency(entry.credit_amount) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300 max-w-xs truncate">
                          {entry.description}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {entry.vat_code || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-blue/10 text-accent-blue">
                            {entry.source_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-right">
                          <span className={`font-medium ${
                            calculateBalance(index) >= 0 ? 'text-accent-green' : 'text-accent-red'
                          }`}>
                            {formatCurrency(calculateBalance(index))}
                          </span>
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
          <div className="bg-dark-card border border-dark-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-dark-border">
              <h3 className="text-xl font-bold text-gray-100">
                Posteringsdetaljer
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
              {/* Status Badge */}
              {selectedEntry.status === 'reversed' && (
                <div className="bg-accent-red/10 border border-accent-red/50 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-accent-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-accent-red font-medium">
                      Denne posteringen er reversert
                      {selectedEntry.reversed_at && ` den ${formatDate(selectedEntry.reversed_at)}`}
                    </span>
                  </div>
                </div>
              )}

              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Bilagsnummer
                  </label>
                  <p className="text-gray-100 font-medium">{selectedEntry.voucher_number}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Dato
                  </label>
                  <p className="text-gray-100 font-medium">{formatDate(selectedEntry.accounting_date)}</p>
                </div>
              </div>

              {/* Account Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Kontonummer
                  </label>
                  <p className="text-gray-100 font-medium">{selectedEntry.account_number}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Kontonavn
                  </label>
                  <p className="text-gray-100">{selectedEntry.account_name || '-'}</p>
                </div>
              </div>

              {/* Amounts */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Debet
                  </label>
                  <p className="text-gray-100 font-medium text-lg">
                    {selectedEntry.debit_amount > 0 ? formatCurrency(selectedEntry.debit_amount) : '-'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Kredit
                  </label>
                  <p className="text-gray-100 font-medium text-lg">
                    {selectedEntry.credit_amount > 0 ? formatCurrency(selectedEntry.credit_amount) : '-'}
                  </p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Beskrivelse
                </label>
                <p className="text-gray-100">{selectedEntry.description}</p>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    MVA-kode
                  </label>
                  <p className="text-gray-100">{selectedEntry.vat_code || '-'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Bilagsart
                  </label>
                  <p className="text-gray-100">{selectedEntry.source_type}</p>
                </div>
              </div>

              {/* Vendor Info */}
              {selectedEntry.vendor_name && (
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Leverandør
                  </label>
                  <p className="text-gray-100">{selectedEntry.vendor_name}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-4 border-t border-dark-border">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Opprettet
                    </label>
                    <p className="text-gray-400">{formatDate(selectedEntry.created_at)}</p>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Status
                    </label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      selectedEntry.status === 'posted' 
                        ? 'bg-accent-green/10 text-accent-green'
                        : 'bg-accent-red/10 text-accent-red'
                    }`}>
                      {selectedEntry.status === 'posted' ? 'Postert' : 'Reversert'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-between items-center gap-3 p-6 border-t border-dark-border">
              {selectedEntry.source_invoice_id && (
                <button
                  onClick={() => setShowPdfViewer(true)}
                  className="px-4 py-2 bg-accent-blue hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Vis PDF-bilag
                </button>
              )}
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg text-sm font-medium transition-colors ml-auto"
              >
                Lukk
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        isOpen={showPdfViewer}
        onClose={() => setShowPdfViewer(false)}
        invoiceId={selectedEntry?.source_invoice_id || null}
        documentId={null}
        invoiceNumber={selectedEntry?.invoice_number || selectedEntry?.voucher_number}
      />
    </div>
  );
};

export default HovedbokReport;
