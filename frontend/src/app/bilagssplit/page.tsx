'use client';

import React, { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  fetchVoucherControlOverview,
  type VoucherControlItem,
  type TreatmentType,
  type VoucherType,
  type VoucherStatus,
} from '@/lib/api/voucher-control';
import AuditTrailPanel from '@/components/voucher-control/AuditTrailPanel';
import {
  Filter,
  RefreshCw,
  FileText,
  Search,
  Calendar,
  ChevronDown,
  CheckCircle2,
  Clock,
  XCircle,
  FileEdit,
  Shield,
  Bot,
  User,
  Receipt,
} from 'lucide-react';

/**
 * MODUL 5: Bilagssplit og kontroll
 * 
 * Oversikt som aggregerer data fra ALLE moduler:
 * - Leverandørfakturaer (Modul 1)
 * - Andre bilag (Modul 3)
 * - Bankavstemming (Modul 4)
 * - Balanseavstemming
 * 
 * Features:
 * - Filtrering på behandlingsmåte, bilagstype, dato
 * - Full audit trail for hvert bilag
 * - Sanntidsvisning av AI-konfidensgrad
 * - Status-oversikt
 */

export default function BilagssplitPage() {
  const { selectedClient } = useClient();
  const [vouchers, setVouchers] = useState<VoucherControlItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [treatmentFilter, setTreatmentFilter] = useState<TreatmentType | ''>('');
  const [voucherTypeFilter, setVoucherTypeFilter] = useState<VoucherType | ''>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;
  
  // Audit trail panel
  const [selectedVoucher, setSelectedVoucher] = useState<VoucherControlItem | null>(null);

  // Load vouchers on mount and filter changes
  useEffect(() => {
    if (selectedClient?.id) {
      loadVouchers();
    }
  }, [selectedClient?.id, treatmentFilter, voucherTypeFilter, startDate, endDate, page]);

  const loadVouchers = async () => {
    if (!selectedClient?.id) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetchVoucherControlOverview({
        clientId: selectedClient.id,
        treatmentType: treatmentFilter || undefined,
        voucherType: voucherTypeFilter || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      });

      setVouchers(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to load vouchers:', err);
      setError(err instanceof Error ? err.message : 'Failed to load vouchers');
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setTreatmentFilter('');
    setVoucherTypeFilter('');
    setStartDate('');
    setEndDate('');
    setSearchQuery('');
    setPage(1);
  };

  // Treatment type labels and icons
  const getTreatmentLabel = (type: TreatmentType): string => {
    const labels: Record<TreatmentType, string> = {
      auto_approved: 'Auto-godkjent (uten berøring)',
      pending: 'Venter på godkjenning',
      corrected: 'Korrigert av regnskapsfører',
      rule_based: 'Godkjent via regel',
      manager_approved: 'Godkjent av daglig leder',
    };
    return labels[type];
  };

  const getTreatmentIcon = (type: TreatmentType) => {
    const icons: Record<TreatmentType, React.ReactNode> = {
      auto_approved: '🤖',
      pending: '⏳',
      corrected: '✏️',
      rule_based: '📋',
      manager_approved: '👤',
    };
    return icons[type];
  };

  const getTreatmentBadgeClass = (type: TreatmentType): string => {
    const classes: Record<TreatmentType, string> = {
      auto_approved: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      corrected: 'bg-blue-100 text-blue-800 border-blue-200',
      rule_based: 'bg-purple-100 text-purple-800 border-purple-200',
      manager_approved: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    };
    return classes[type];
  };

  // Voucher type labels
  const getVoucherTypeLabel = (type: VoucherType): string => {
    const labels: Record<VoucherType, string> = {
      supplier_invoice: 'Leverandørfaktura',
      other_voucher: 'Andre bilag',
      bank_recon: 'Bankavstemming',
      balance_recon: 'Balansekonto',
    };
    return labels[type];
  };

  const getVoucherTypeBadgeClass = (type: VoucherType): string => {
    const classes: Record<VoucherType, string> = {
      supplier_invoice: 'bg-blue-100 text-blue-800 border-blue-200',
      other_voucher: 'bg-purple-100 text-purple-800 border-purple-200',
      bank_recon: 'bg-green-100 text-green-800 border-green-200',
      balance_recon: 'bg-orange-100 text-orange-800 border-orange-200',
    };
    return classes[type];
  };

  // Status labels and icons
  const getStatusLabel = (status: VoucherStatus): string => {
    const labels: Record<VoucherStatus, string> = {
      approved: 'Godkjent',
      pending: 'Venter',
      rejected: 'Avvist',
    };
    return labels[status];
  };

  const getStatusIcon = (status: VoucherStatus) => {
    const icons: Record<VoucherStatus, React.ReactNode> = {
      approved: <CheckCircle2 className="w-4 h-4" />,
      pending: <Clock className="w-4 h-4" />,
      rejected: <XCircle className="w-4 h-4" />,
    };
    return icons[status];
  };

  const getStatusBadgeClass = (status: VoucherStatus): string => {
    const classes: Record<VoucherStatus, string> = {
      approved: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      rejected: 'bg-red-100 text-red-800 border-red-200',
    };
    return classes[status];
  };

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  // Format date/time
  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('nb-NO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Filter vouchers by search query
  const filteredVouchers = vouchers.filter(voucher => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      voucher.voucher_number.toLowerCase().includes(query) ||
      voucher.vendor_name?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Bilagssplit og kontroll
          </h1>
          <p className="text-gray-600 mt-1">
            Oversikt over alle bilag med behandlingshistorikk
          </p>
        </div>
        <Button
          onClick={loadVouchers}
          disabled={loading}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Oppdater
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-500" />
            <h2 className="text-lg font-semibold">Filtre</h2>
            {(treatmentFilter || voucherTypeFilter || startDate || endDate) && (
              <Button
                onClick={resetFilters}
                variant="ghost"
                size="sm"
                className="ml-auto text-blue-600 hover:text-blue-700"
              >
                Nullstill filtre
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Treatment Type Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Behandlingsmåte
              </label>
              <select
                value={treatmentFilter}
                onChange={(e) => {
                  setTreatmentFilter(e.target.value as TreatmentType | '');
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Alle</option>
                <option value="auto_approved">🤖 Auto-godkjent (uten berøring)</option>
                <option value="pending">⏳ Venter på godkjenning</option>
                <option value="corrected">✏️ Korrigert av regnskapsfører</option>
                <option value="rule_based">📋 Godkjent via regel</option>
                <option value="manager_approved">👤 Godkjent av daglig leder</option>
              </select>
            </div>

            {/* Voucher Type Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Bilagstype
              </label>
              <select
                value={voucherTypeFilter}
                onChange={(e) => {
                  setVoucherTypeFilter(e.target.value as VoucherType | '');
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Alle</option>
                <option value="supplier_invoice">Leverandørfaktura</option>
                <option value="other_voucher">Andre bilag</option>
                <option value="bank_recon">Bankavstemming</option>
                <option value="balance_recon">Balansekonto</option>
              </select>
            </div>

            {/* Start Date */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Fra dato
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* End Date */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Til dato
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Søk etter bilagsnummer eller leverandør..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          Viser {filteredVouchers.length} av {total} bilag
        </span>
        {loading && <span>Laster...</span>}
      </div>

      {/* Table */}
      {error && (
        <Card className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">Feil ved lasting av bilag</p>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </Card>
      )}

      {!loading && !error && filteredVouchers.length === 0 && (
        <Card className="p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Ingen bilag funnet
          </h3>
          <p className="text-gray-600">
            Prøv å justere filtrene dine
          </p>
        </Card>
      )}

      {!loading && !error && filteredVouchers.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bilagsnummer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Leverandør/Beskrivelse
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Beløp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Behandlingsmåte
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI-konfidensgrad
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tidsstempel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredVouchers.map((voucher) => (
                  <tr
                    key={voucher.id}
                    onClick={() => setSelectedVoucher(voucher)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    {/* Voucher Number */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Receipt className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-blue-600 hover:text-blue-800">
                          {voucher.voucher_number}
                        </span>
                      </div>
                    </td>

                    {/* Voucher Type */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant="outline"
                        className={getVoucherTypeBadgeClass(voucher.voucher_type)}
                      >
                        {getVoucherTypeLabel(voucher.voucher_type)}
                      </Badge>
                    </td>

                    {/* Vendor/Description */}
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {voucher.vendor_name || '-'}
                      </div>
                    </td>

                    {/* Amount */}
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="font-medium text-gray-900">
                        {formatCurrency(voucher.amount)}
                      </span>
                    </td>

                    {/* Treatment Type */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant="outline"
                        className={getTreatmentBadgeClass(voucher.treatment_type)}
                      >
                        <span className="mr-1">
                          {getTreatmentIcon(voucher.treatment_type)}
                        </span>
                        {getTreatmentLabel(voucher.treatment_type)}
                      </Badge>
                    </td>

                    {/* AI Confidence */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {voucher.ai_confidence !== undefined && (
                        <div className="flex flex-col gap-1">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                voucher.ai_confidence >= 0.8
                                  ? 'bg-green-500'
                                  : voucher.ai_confidence >= 0.6
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${voucher.ai_confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-600">
                            {Math.round(voucher.ai_confidence * 100)}%
                          </span>
                        </div>
                      )}
                    </td>

                    {/* Timestamp */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDateTime(voucher.created_at)}
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant="outline"
                        className={`${getStatusBadgeClass(voucher.status)} flex items-center gap-1 w-fit`}
                      >
                        {getStatusIcon(voucher.status)}
                        {getStatusLabel(voucher.status)}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between">
          <Button
            onClick={() => setPage(page - 1)}
            disabled={page === 1 || loading}
            variant="outline"
          >
            Forrige
          </Button>
          <span className="text-sm text-gray-600">
            Side {page} av {Math.ceil(total / pageSize)}
          </span>
          <Button
            onClick={() => setPage(page + 1)}
            disabled={page >= Math.ceil(total / pageSize) || loading}
            variant="outline"
          >
            Neste
          </Button>
        </div>
      )}

      {/* Audit Trail Panel (Modal) */}
      {selectedVoucher && (
        <AuditTrailPanel
          voucherId={selectedVoucher.id}
          voucherNumber={selectedVoucher.voucher_number}
          onClose={() => setSelectedVoucher(null)}
        />
      )}
    </div>
  );
}
