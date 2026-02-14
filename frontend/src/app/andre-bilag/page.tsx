'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { MasterDetailLayout } from '@/components/MasterDetailLayout';
import { ChatProvider, useChatContext } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';
import { useClient } from '@/contexts/ClientContext';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  fetchPendingOtherVouchers,
  approveOtherVoucher,
  rejectOtherVoucher,
  correctOtherVoucher,
  type OtherVoucher,
  type OtherVoucherType,
} from '@/lib/api/other-vouchers';
import { toast } from '@/lib/toast';
import { PDFUpload } from '@/components/PDFUpload';
import {
  Check,
  X,
  Edit,
  FileText,
  AlertCircle,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Clock,
  Receipt,
  Calculator,
  Package,
  Users,
  FileEdit,
  Filter,
  ChevronDown,
  Upload,
} from 'lucide-react';

// Types
interface CorrectionForm {
  account_number: string;
  vat_code: string;
  notes: string;
}

interface RejectForm {
  reason: string;
  notes: string;
}

// Confidence badge component
function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  
  let colorClass = 'bg-green-100 text-green-800 border-green-200';
  let label = 'Høy';
  
  if (percentage < 50) {
    colorClass = 'bg-red-100 text-red-800 border-red-200';
    label = 'Lav';
  } else if (percentage < 70) {
    colorClass = 'bg-yellow-100 text-yellow-800 border-yellow-200';
    label = 'Medium';
  }
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
      {percentage}% {label}
    </span>
  );
}

// Voucher type labels
const getVoucherTypeLabel = (type: OtherVoucherType): string => {
  const labels: Record<OtherVoucherType, string> = {
    employee_expense: 'Ansatteutlegg',
    inventory_adjustment: 'Lagerjustering',
    manual_correction: 'Manuell korreksjon',
    other: 'Annet',
  };
  return labels[type] || type;
};

// Voucher type icons
const getVoucherTypeIcon = (type: OtherVoucherType) => {
  const icons: Record<OtherVoucherType, React.ReactNode> = {
    employee_expense: <Users className="w-4 h-4" />,
    inventory_adjustment: <Package className="w-4 h-4" />,
    manual_correction: <FileEdit className="w-4 h-4" />,
    other: <FileText className="w-4 h-4" />,
  };
  return icons[type] || <FileText className="w-4 h-4" />;
};

// Voucher type colors
const getVoucherTypeColor = (type: OtherVoucherType): string => {
  const colors: Record<OtherVoucherType, string> = {
    employee_expense: 'bg-blue-100 text-blue-800 border-blue-200',
    inventory_adjustment: 'bg-purple-100 text-purple-800 border-purple-200',
    manual_correction: 'bg-orange-100 text-orange-800 border-orange-200',
    other: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
};

// Inner component that uses ChatContext
function AndreBilagContent() {
  const { selectedClient } = useClient();
  const { setSelectedItems, setModule } = useChatContext();
  
  const [items, setItems] = useState<OtherVoucher[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [multiSelectEnabled, setMultiSelectEnabled] = useState(true);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [correctionForm, setCorrectionForm] = useState<CorrectionForm>({
    account_number: '',
    vat_code: '',
    notes: '',
  });
  const [rejectForm, setRejectForm] = useState<RejectForm>({
    reason: '',
    notes: '',
  });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  
  // Filters
  const [typeFilter, setTypeFilter] = useState<OtherVoucherType | 'all'>('all');
  const [showTypeFilter, setShowTypeFilter] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  
  // Set module for chat context
  useEffect(() => {
    setModule('andre-bilag');
  }, [setModule]);
  
  // Update chat context when selection changes
  useEffect(() => {
    setSelectedItems(selectedIds.length > 0 ? selectedIds : selectedId ? [selectedId] : []);
  }, [selectedIds, selectedId, setSelectedItems]);
  
  // Fetch items
  const fetchItems = useCallback(async () => {
    if (!selectedClient?.id) {
      setItems([]);
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetchPendingOtherVouchers(
        selectedClient.id,
        typeFilter === 'all' ? undefined : typeFilter
      );
      
      setItems(response.items || []);
      
      // Auto-select first item if none selected
      if (response.items.length > 0 && !selectedId) {
        setSelectedId(response.items[0].id);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching other vouchers:', err);
      setError('Kunne ikke laste bilag. Prøv igjen.');
    } finally {
      setLoading(false);
    }
  }, [selectedClient?.id, typeFilter, selectedId]);
  
  useEffect(() => {
    fetchItems();
  }, [fetchItems]);
  
  // Get selected item
  const selectedItem = items.find(item => item.id === selectedId) || null;
  
  // Handle approve single
  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await approveOtherVoucher(id, {
        notes: 'Godkjent via UI',
      });
      toast.success('Bilag godkjent og bokført!');
      
      // Update local state
      setItems(prev => prev.filter(item => item.id !== id));
      
      // Select next item if this was selected
      if (selectedId === id) {
        const remaining = items.filter(item => item.id !== id);
        setSelectedId(remaining[0]?.id || null);
      }
      
      // Remove from multi-select
      setSelectedIds(prev => prev.filter(sid => sid !== id));
    } catch (err: any) {
      console.error('Error approving item:', err);
      toast.error(err.message || 'Kunne ikke godkjenne bilag');
    } finally {
      setActionLoading(null);
    }
  };
  
  // Handle reject
  const handleReject = async () => {
    if (!selectedItem) return;
    
    if (!rejectForm.reason) {
      toast.error('Årsak er påkrevd');
      return;
    }
    
    setActionLoading(selectedItem.id);
    try {
      await rejectOtherVoucher(selectedItem.id, {
        reason: rejectForm.reason,
        notes: rejectForm.notes || undefined,
      });
      
      toast.success('Bilag avvist!');
      
      // Update local state
      setItems(prev => prev.filter(item => item.id !== selectedItem.id));
      
      // Reset form
      setShowRejectForm(false);
      setRejectForm({ reason: '', notes: '' });
      
      // Select next item
      const remaining = items.filter(item => item.id !== selectedItem.id);
      setSelectedId(remaining[0]?.id || null);
    } catch (err: any) {
      console.error('Error rejecting item:', err);
      toast.error(err.message || 'Kunne ikke avvise bilag');
    } finally {
      setActionLoading(null);
    }
  };
  
  // Handle correct
  const handleCorrect = async () => {
    if (!selectedItem) return;
    
    if (!correctionForm.account_number) {
      toast.error('Konto er påkrevd');
      return;
    }
    
    setActionLoading(selectedItem.id);
    try {
      await correctOtherVoucher(selectedItem.id, {
        bookingEntries: [{
          account_number: correctionForm.account_number,
          vat_code: correctionForm.vat_code || undefined,
          amount: selectedItem.ai_suggestion?.amount || 0,
        }],
        notes: correctionForm.notes || undefined,
      });
      
      toast.success('Bilag korrigert og bokført!');
      
      // Update local state
      setItems(prev => prev.filter(item => item.id !== selectedItem.id));
      
      // Reset form
      setShowCorrectionForm(false);
      setCorrectionForm({ account_number: '', vat_code: '', notes: '' });
      
      // Select next item
      const remaining = items.filter(item => item.id !== selectedItem.id);
      setSelectedId(remaining[0]?.id || null);
    } catch (err: any) {
      console.error('Error correcting item:', err);
      toast.error(err.message || 'Kunne ikke korrigere bilag');
    } finally {
      setActionLoading(null);
    }
  };
  
  // Handle bulk approve
  const handleBulkApprove = async () => {
    if (selectedIds.length === 0) return;
    
    setBulkLoading(true);
    let successCount = 0;
    let failCount = 0;
    
    for (const id of selectedIds) {
      try {
        await approveOtherVoucher(id, { notes: 'Godkjent via bulk action' });
        successCount++;
      } catch (err) {
        console.error(`Error approving ${id}:`, err);
        failCount++;
      }
    }
    
    setBulkLoading(false);
    
    if (successCount > 0) {
      toast.success(`${successCount} bilag godkjent!`);
      // Refresh list
      await fetchItems();
      setSelectedIds([]);
    }
    
    if (failCount > 0) {
      toast.error(`${failCount} bilag feilet`);
    }
  };
  
  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('no-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2,
    }).format(amount);
  };
  
  // Render item in list
  const renderItem = (item: OtherVoucher, isSelected: boolean, isMultiSelected: boolean) => {
    return (
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={`${getVoucherTypeColor(item.type)}`}>
                <span className="flex items-center gap-1">
                  {getVoucherTypeIcon(item.type)}
                  {getVoucherTypeLabel(item.type)}
                </span>
              </Badge>
            </div>
            <div className={`font-medium truncate mb-1 ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
              {item.title}
            </div>
            <div className="text-sm text-gray-600 line-clamp-2 mb-2">
              {item.description}
            </div>
            <div className="flex items-center gap-3">
              {item.ai_suggestion?.amount && (
                <span className="font-semibold text-gray-900 text-sm">
                  {formatCurrency(item.ai_suggestion.amount)}
                </span>
              )}
              <ConfidenceBadge confidence={item.ai_confidence} />
            </div>
          </div>
          <div className="text-xs text-gray-500 whitespace-nowrap">
            {new Date(item.created_at).toLocaleDateString('no-NO', {
              day: '2-digit',
              month: 'short',
            })}
          </div>
        </div>
      </div>
    );
  };
  
  // Render detail panel
  const renderDetail = (item: OtherVoucher | null) => {
    if (!item) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Ingen bilag valgt</h3>
            <p className="mt-1 text-sm text-gray-500">
              Velg et bilag fra listen for å se detaljer
            </p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="p-6 max-w-3xl">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <Badge className={`${getVoucherTypeColor(item.type)} text-base px-3 py-1`}>
              <span className="flex items-center gap-2">
                {getVoucherTypeIcon(item.type)}
                {getVoucherTypeLabel(item.type)}
              </span>
            </Badge>
            <ConfidenceBadge confidence={item.ai_confidence} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {item.title}
          </h1>
          <p className="text-gray-600">{item.description}</p>
          <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
            <Clock className="w-4 h-4" />
            Opprettet {new Date(item.created_at).toLocaleDateString('no-NO', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </div>
        </div>
        
        {/* Amount card */}
        {item.ai_suggestion?.amount && (
          <Card className="p-4 mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Beløp</p>
                <p className="text-3xl font-bold text-blue-900">
                  {formatCurrency(item.ai_suggestion.amount)}
                </p>
                {item.ai_suggestion.vat_amount && (
                  <p className="text-sm text-blue-600 mt-1">
                    MVA: {formatCurrency(item.ai_suggestion.vat_amount)}
                  </p>
                )}
              </div>
            </div>
          </Card>
        )}
        
        {/* AI Suggestion */}
        <Card className="p-4 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calculator className="w-5 h-5 text-purple-600" />
            AI-forslag
          </h2>
          
          {item.ai_suggestion ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-600">Konto</p>
                  <p className="font-semibold text-gray-900">
                    {item.ai_suggestion.account_number || 'Ikke foreslått'}
                  </p>
                  {item.ai_suggestion.account_name && (
                    <p className="text-xs text-gray-500">{item.ai_suggestion.account_name}</p>
                  )}
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-600">MVA-kode</p>
                  <p className="font-semibold text-gray-900">
                    {item.ai_suggestion.vat_code || 'Ikke foreslått'}
                  </p>
                </div>
              </div>
              
              {/* Show debit/credit for inventory adjustments */}
              {item.type === 'inventory_adjustment' && item.ai_suggestion.debit_account && (
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-600">Debetkonto</p>
                    <p className="font-semibold text-gray-900">
                      {item.ai_suggestion.debit_account}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-600">Kreditkonto</p>
                    <p className="font-semibold text-gray-900">
                      {item.ai_suggestion.credit_account || 'Ikke foreslått'}
                    </p>
                  </div>
                </div>
              )}
              
              {item.ai_reasoning && (
                <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-100">
                  <p className="text-sm text-purple-800">
                    <strong>Begrunnelse:</strong> {item.ai_reasoning}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Ingen AI-forslag tilgjengelig</p>
          )}
        </Card>
        
        {/* Rejection form */}
        {showRejectForm && (
          <Card className="p-4 mb-6 border-red-200 bg-red-50">
            <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center gap-2">
              <X className="w-5 h-5" />
              Avvis bilag
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Årsak (påkrevd)
                </label>
                <Input
                  value={rejectForm.reason}
                  onChange={(e) => setRejectForm(prev => ({
                    ...prev,
                    reason: e.target.value
                  }))}
                  placeholder="F.eks. Mangler dokumentasjon"
                  className="bg-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notater
                </label>
                <Textarea
                  value={rejectForm.notes}
                  onChange={(e) => setRejectForm(prev => ({
                    ...prev,
                    notes: e.target.value
                  }))}
                  placeholder="Legg til ytterligere notater..."
                  rows={3}
                  className="bg-white"
                />
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={handleReject}
                  disabled={actionLoading === item.id}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {actionLoading === item.id ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <X className="w-4 h-4 mr-2" />
                  )}
                  Avvis bilag
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowRejectForm(false);
                    setRejectForm({ reason: '', notes: '' });
                  }}
                >
                  Avbryt
                </Button>
              </div>
            </div>
          </Card>
        )}
        
        {/* Correction form */}
        {showCorrectionForm && (
          <Card className="p-4 mb-6 border-yellow-200 bg-yellow-50">
            <h3 className="text-lg font-semibold text-yellow-800 mb-4 flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Korrigering
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Konto (påkrevd)
                </label>
                <Input
                  value={correctionForm.account_number}
                  onChange={(e) => setCorrectionForm(prev => ({
                    ...prev,
                    account_number: e.target.value
                  }))}
                  placeholder="F.eks. 6000"
                  className="bg-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  MVA-kode
                </label>
                <Input
                  value={correctionForm.vat_code}
                  onChange={(e) => setCorrectionForm(prev => ({
                    ...prev,
                    vat_code: e.target.value
                  }))}
                  placeholder="F.eks. 1 (25% MVA)"
                  className="bg-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notater
                </label>
                <Textarea
                  value={correctionForm.notes}
                  onChange={(e) => setCorrectionForm(prev => ({
                    ...prev,
                    notes: e.target.value
                  }))}
                  placeholder="Legg til notater om korrigeringen..."
                  rows={3}
                  className="bg-white"
                />
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={handleCorrect}
                  disabled={actionLoading === item.id}
                  className="bg-yellow-600 hover:bg-yellow-700"
                >
                  {actionLoading === item.id ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Send korrigering
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCorrectionForm(false);
                    setCorrectionForm({ account_number: '', vat_code: '', notes: '' });
                  }}
                >
                  Avbryt
                </Button>
              </div>
            </div>
          </Card>
        )}
        
        {/* Action buttons */}
        {item.status === 'pending' && !showCorrectionForm && !showRejectForm && (
          <div className="space-y-3">
            <div className="flex gap-3 pt-4 border-t">
              <Button
                onClick={() => handleApprove(item.id)}
                disabled={actionLoading === item.id}
                className="bg-green-600 hover:bg-green-700 flex-1"
              >
                {actionLoading === item.id ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                )}
                Godkjenn
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowCorrectionForm(true)}
                className="border-yellow-500 text-yellow-700 hover:bg-yellow-50 flex-1"
              >
                <Edit className="w-4 h-4 mr-2" />
                Korriger
              </Button>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowRejectForm(true)}
              className="w-full border-red-500 text-red-700 hover:bg-red-50"
            >
              <X className="w-4 h-4 mr-2" />
              Avvis bilag
            </Button>
          </div>
        )}
      </div>
    );
  };
  
  // Show loading when client is loading
  if (!selectedClient) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg text-gray-600">
            Velg en klient fra menyen for å se andre bilag
          </p>
        </div>
      </div>
    );
  }
  
  // Filter to only show pending items
  const pendingItems = items.filter(item => item.status === 'pending');
  
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Andre bilag som trenger oppmerksomhet</h1>
            <p className="text-sm text-gray-600 mt-1">
              {pendingItems.length} bilag venter på gjennomgang
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Upload button */}
            <Button
              variant="outline"
              onClick={() => setShowUpload(!showUpload)}
              className="text-blue-600 border-blue-600 hover:bg-blue-50"
              title="Last opp andre bilag"
            >
              <Upload className="w-4 h-4 mr-2" />
              Last opp PDF
            </Button>
            
            {/* Type filter dropdown */}
            <div className="relative">
              <Button
                variant="outline"
                onClick={() => setShowTypeFilter(!showTypeFilter)}
                className="flex items-center gap-2"
              >
                <Filter className="w-4 h-4" />
                {typeFilter === 'all' ? 'Alle typer' : getVoucherTypeLabel(typeFilter)}
                <ChevronDown className="w-4 h-4" />
              </Button>
              
              {showTypeFilter && (
                <>
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowTypeFilter(false)}
                  />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                    <button
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${typeFilter === 'all' ? 'bg-blue-50 text-blue-700' : ''}`}
                      onClick={() => {
                        setTypeFilter('all');
                        setShowTypeFilter(false);
                      }}
                    >
                      Alle typer
                    </button>
                    <button
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 ${typeFilter === 'employee_expense' ? 'bg-blue-50 text-blue-700' : ''}`}
                      onClick={() => {
                        setTypeFilter('employee_expense');
                        setShowTypeFilter(false);
                      }}
                    >
                      <Users className="w-4 h-4" />
                      Ansatteutlegg
                    </button>
                    <button
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 ${typeFilter === 'inventory_adjustment' ? 'bg-blue-50 text-blue-700' : ''}`}
                      onClick={() => {
                        setTypeFilter('inventory_adjustment');
                        setShowTypeFilter(false);
                      }}
                    >
                      <Package className="w-4 h-4" />
                      Lagerjustering
                    </button>
                    <button
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 ${typeFilter === 'manual_correction' ? 'bg-blue-50 text-blue-700' : ''}`}
                      onClick={() => {
                        setTypeFilter('manual_correction');
                        setShowTypeFilter(false);
                      }}
                    >
                      <FileEdit className="w-4 h-4" />
                      Manuell korreksjon
                    </button>
                    <button
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 ${typeFilter === 'other' ? 'bg-blue-50 text-blue-700' : ''}`}
                      onClick={() => {
                        setTypeFilter('other');
                        setShowTypeFilter(false);
                      }}
                    >
                      <FileText className="w-4 h-4" />
                      Annet
                    </button>
                  </div>
                </>
              )}
            </div>
            
            {/* Bulk approve button */}
            {selectedIds.length > 0 && (
              <Button
                onClick={handleBulkApprove}
                disabled={bulkLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                {bulkLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                )}
                Godkjenn alle valgte ({selectedIds.length})
              </Button>
            )}
            
            {/* Refresh button */}
            <Button
              variant="outline"
              onClick={fetchItems}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            
            {/* Selected count */}
            {selectedIds.length > 0 && (
              <Badge variant="secondary" className="text-sm">
                {selectedIds.length} valgt
              </Badge>
            )}
          </div>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}
      
      {/* Upload section */}
      {showUpload && (
        <div className="p-4 bg-white border-b border-gray-200">
          <div className="max-w-3xl mx-auto">
            <PDFUpload
              uploadEndpoint="/api/review-queue/upload"
              onUploadSuccess={(result) => {
                // Refresh the list after successful upload
                fetchItems();
              }}
              compact={true}
              title="Last opp andre bilag"
            />
          </div>
        </div>
      )}
      
      {/* Main layout */}
      <div className="flex-1 overflow-hidden">
        <MasterDetailLayout
          items={pendingItems}
          selectedId={selectedId}
          selectedIds={selectedIds}
          onSelectItem={(id) => {
            setSelectedId(id);
            setShowCorrectionForm(false);
            setShowRejectForm(false);
          }}
          onMultiSelect={setSelectedIds}
          renderItem={renderItem}
          renderDetail={renderDetail}
          loading={loading}
          multiSelectEnabled={multiSelectEnabled}
        />
      </div>
      
      {/* Chat Window */}
      <ChatWindow />
    </div>
  );
}

// Main component with ChatProvider wrapper
export default function AndreBilagPage() {
  const { selectedClient } = useClient();
  
  return (
    <ChatProvider
      initialModule="andre-bilag"
      clientId={selectedClient?.id || 'default-client'}
      userId="current-user"
    >
      <AndreBilagContent />
    </ChatProvider>
  );
}
