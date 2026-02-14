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
import { reviewQueueApi } from '@/api/review-queue';
import { toast } from '@/lib/toast';
import { ThresholdSettingsModal } from '@/components/ThresholdSettingsModal';
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
  Building2,
  Receipt,
  Calculator,
  Settings,
  Plus,
  Upload,
} from 'lucide-react';
import { VendorEditPanel } from '@/components/vendors/VendorEditPanel';
import { VendorCreateModal } from '@/components/vendors/VendorCreateModal';
import { PDFUpload } from '@/components/PDFUpload';

// Types
interface ReviewItem {
  id: string;
  supplier: string;
  supplier_id?: string; // ID for editing vendor
  amount: number;
  currency: string;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  description?: string;
  status: 'pending' | 'approved' | 'corrected' | 'rejected';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  ai_confidence: number; // 0-1 scale
  ai_reasoning?: string;
  ai_suggestion?: {
    account_number?: string;
    account_name?: string;
    vat_code?: string;
    vat_rate?: number;
  };
  created_at: string;
  reviewed_at?: string;
}

interface CorrectionForm {
  account_number: string;
  vat_code: string;
  notes: string;
}

// Confidence badge component
function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  
  let colorClass = 'bg-green-100 text-green-800 border-green-200';
  let label = 'Høy';
  
  if (percentage < 80) {
    colorClass = 'bg-red-100 text-red-800 border-red-200';
    label = 'Lav';
  } else if (percentage < 90) {
    colorClass = 'bg-yellow-100 text-yellow-800 border-yellow-200';
    label = 'Medium';
  }
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
      {percentage}% {label}
    </span>
  );
}

// Inner component that uses ChatContext
function ReviewQueueContent() {
  const { selectedClient } = useClient();
  const { setSelectedItems, setModule } = useChatContext();
  
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [multiSelectEnabled, setMultiSelectEnabled] = useState(true);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [correctionForm, setCorrectionForm] = useState<CorrectionForm>({
    account_number: '',
    vat_code: '',
    notes: '',
  });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  
  // Vendor panels state
  const [vendorEditPanelOpen, setVendorEditPanelOpen] = useState(false);
  const [vendorCreateModalOpen, setVendorCreateModalOpen] = useState(false);
  const [selectedVendorId, setSelectedVendorId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  
  // Set module for chat context
  useEffect(() => {
    setModule('review-queue');
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
      const response = await reviewQueueApi.getReviewItems({
        client_id: selectedClient.id,
        status: 'pending' as any,
      });
      
      const itemsArray = Array.isArray(response) ? response : ((response as any).items || []);
      setItems(itemsArray);
      
      // Auto-select first item if none selected
      if (itemsArray.length > 0 && !selectedId) {
        setSelectedId(itemsArray[0].id);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching review items:', err);
      setError('Kunne ikke laste leverandørbilag. Prøv igjen.');
    } finally {
      setLoading(false);
    }
  }, [selectedClient?.id, selectedId]);
  
  useEffect(() => {
    fetchItems();
  }, [fetchItems]);
  
  // Get selected item
  const selectedItem = items.find(item => item.id === selectedId) || null;
  
  // Handle approve single
  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await reviewQueueApi.approveItem(id);
      toast.success('Faktura godkjent og bokført!');
      
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
      toast.error(err.response?.data?.detail || 'Kunne ikke godkjenne faktura');
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
      await reviewQueueApi.correctItem(selectedItem.id, {
        bookingEntries: [{
          account_number: correctionForm.account_number,
          vat_code: correctionForm.vat_code || undefined,
        }],
        notes: correctionForm.notes || undefined,
      } as any);
      
      toast.success('Faktura korrigert og bokført!');
      
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
      toast.error(err.response?.data?.detail || 'Kunne ikke korrigere faktura');
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
        await reviewQueueApi.approveItem(id);
        successCount++;
      } catch (err) {
        console.error(`Error approving ${id}:`, err);
        failCount++;
      }
    }
    
    setBulkLoading(false);
    
    if (successCount > 0) {
      toast.success(`${successCount} faktura(er) godkjent!`);
      // Refresh list
      await fetchItems();
      setSelectedIds([]);
    }
    
    if (failCount > 0) {
      toast.error(`${failCount} faktura(er) feilet`);
    }
  };
  
  // Format currency
  const formatCurrency = (amount: number, currency: string = 'NOK') => {
    return new Intl.NumberFormat('no-NO', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };
  
  // Render item in list
  const renderItem = (item: ReviewItem, isSelected: boolean, isMultiSelected: boolean) => {
    return (
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className={`font-medium truncate ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                {item.supplier}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span className="font-semibold text-gray-900">
                {formatCurrency(item.amount, item.currency)}
              </span>
              <span className="text-gray-400">|</span>
              <span>{item.invoice_number}</span>
            </div>
            <div className="mt-2">
              <ConfidenceBadge confidence={item.ai_confidence} />
            </div>
          </div>
          <div className="text-xs text-gray-500 whitespace-nowrap">
            {new Date(item.created_at).toLocaleDateString('no-NO')}
          </div>
        </div>
      </div>
    );
  };
  
  // Render detail panel
  const renderDetail = (item: ReviewItem | null) => {
    if (!item) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Ingen faktura valgt</h3>
            <p className="mt-1 text-sm text-gray-500">
              Velg en faktura fra listen for å se detaljer
            </p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="p-6 max-w-3xl">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            <h1 
              className="text-2xl font-bold text-gray-900 hover:text-blue-600 cursor-pointer transition-colors"
              onClick={() => {
                if (item.supplier_id) {
                  setSelectedVendorId(item.supplier_id);
                  setVendorEditPanelOpen(true);
                }
              }}
              title={item.supplier_id ? 'Klikk for å redigere leverandør' : 'Leverandør ID mangler'}
            >
              {item.supplier}
            </h1>
            {item.supplier_id && (
              <Edit className="w-4 h-4 text-gray-400" />
            )}
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Receipt className="w-4 h-4" />
              {item.invoice_number}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {new Date(item.invoice_date || item.created_at).toLocaleDateString('no-NO')}
            </span>
          </div>
        </div>
        
        {/* Amount card */}
        <Card className="p-4 mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Beløp</p>
              <p className="text-3xl font-bold text-blue-900">
                {formatCurrency(item.amount, item.currency)}
              </p>
            </div>
            <ConfidenceBadge confidence={item.ai_confidence} />
          </div>
          {item.due_date && (
            <p className="mt-2 text-sm text-blue-600">
              Forfallsdato: {new Date(item.due_date).toLocaleDateString('no-NO')}
            </p>
          )}
        </Card>
        
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
                  {item.ai_suggestion.vat_rate !== undefined && (
                    <p className="text-xs text-gray-500">{item.ai_suggestion.vat_rate}% MVA</p>
                  )}
                </div>
              </div>
              
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
        {item.status === 'pending' && !showCorrectionForm && (
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
              Avvis & Korriger
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
            Velg en klient fra menyen for å se leverandørbilag
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
            <h1 className="text-2xl font-bold text-gray-900">Leverandørbilag</h1>
            <p className="text-sm text-gray-600 mt-1">
              {pendingItems.length} faktura{pendingItems.length !== 1 ? 'er' : ''} venter på gjennomgang
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Upload button */}
            <Button
              variant="outline"
              onClick={() => setShowUpload(!showUpload)}
              className="text-blue-600 border-blue-600 hover:bg-blue-50"
              title="Last opp leverandørfakturaer"
            >
              <Upload className="w-4 h-4 mr-2" />
              Last opp PDF
            </Button>
            
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
            
            {/* Create vendor button */}
            <Button
              variant="outline"
              onClick={() => setVendorCreateModalOpen(true)}
              className="text-green-600 border-green-600 hover:bg-green-50"
              title="Opprett ny leverandør"
            >
              <Plus className="w-4 h-4 mr-2" />
              Ny leverandør
            </Button>
            
            {/* Settings button */}
            <Button
              variant="outline"
              onClick={() => setSettingsModalOpen(true)}
              title="AI Innstillinger"
            >
              <Settings className="w-4 h-4" />
            </Button>
            
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
              title="Last opp leverandørfakturaer"
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
      
      {/* Threshold Settings Modal */}
      {selectedClient && (
        <ThresholdSettingsModal
          open={settingsModalOpen}
          onOpenChange={setSettingsModalOpen}
          clientId={selectedClient.id}
        />
      )}
      
      {/* Vendor Edit Panel */}
      <VendorEditPanel
        open={vendorEditPanelOpen}
        onOpenChange={setVendorEditPanelOpen}
        supplierId={selectedVendorId}
        onSaved={() => {
          // Refresh the review queue items after vendor update
          fetchItems();
          toast.success('Leverandør oppdatert');
        }}
      />
      
      {/* Vendor Create Modal */}
      {selectedClient && (
        <VendorCreateModal
          open={vendorCreateModalOpen}
          onOpenChange={setVendorCreateModalOpen}
          clientId={selectedClient.id}
          onCreated={(supplierId) => {
            // Refresh the review queue items after vendor creation
            fetchItems();
            toast.success('Leverandør opprettet');
          }}
        />
      )}
    </div>
  );
}

// Main component with ChatProvider wrapper
export default function ReviewQueuePage() {
  const { selectedClient } = useClient();
  
  return (
    <ChatProvider
      initialModule="review-queue"
      clientId={selectedClient?.id || 'default-client'}
      userId="current-user"
    >
      <ReviewQueueContent />
    </ChatProvider>
  );
}
