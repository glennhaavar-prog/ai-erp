'use client';

import { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';

interface Accrual {
  id: string;
  client_id: string;
  description: string;
  from_date: string;
  to_date: string;
  total_amount: number;
  balance_account: string;
  result_account: string;
  frequency: string;
  next_posting_date: string | null;
  status: string;
  created_by: string;
  postings_count: number;
  postings_pending: number;
  postings_posted: number;
  ai_detected?: boolean;
}

interface AccrualPosting {
  id: string;
  posting_date: string;
  amount: number;
  period: string;
  status: string;
  posted_by: string | null;
  posted_at: string | null;
  general_ledger_id: string | null;
}

export default function AccrualsPage() {
  const { selectedClient } = useClient();
  const clientId = selectedClient?.id;
  const [accruals, setAccruals] = useState<Accrual[]>([]);
  const [selectedAccrual, setSelectedAccrual] = useState<string | null>(null);
  const [accrualDetails, setAccrualDetails] = useState<{
    accrual: Accrual;
    postings: AccrualPosting[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('active');

  // Form state for creating new accrual
  const [formData, setFormData] = useState({
    description: '',
    from_date: '',
    to_date: '',
    total_amount: '',
    balance_account: '1580', // Forskuddsbetalte kostnader
    result_account: '6820', // Annen kostnad
    frequency: 'monthly'
  });

  useEffect(() => {
    if (clientId) {
      loadAccruals();
    }
  }, [clientId, statusFilter]);

  useEffect(() => {
    if (selectedAccrual) {
      loadAccrualDetails(selectedAccrual);
    }
  }, [selectedAccrual]);

  const loadAccruals = async () => {
    if (!clientId) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        client_id: clientId,
        ...(statusFilter && { status: statusFilter })
      });
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/accruals/?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setAccruals(data.accruals);
      }
    } catch (error) {
      console.error('Failed to load accruals:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAccrualDetails = async (accrualId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/accruals/${accrualId}`);
      const data = await response.json();
      
      if (data.success) {
        setAccrualDetails({
          accrual: data.accrual,
          postings: data.postings
        });
      }
    } catch (error) {
      console.error('Failed to load accrual details:', error);
    }
  };

  const handleCreateAccrual = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/accruals/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          client_id: clientId,
          total_amount: parseFloat(formData.total_amount)
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setShowCreateModal(false);
        setFormData({
          description: '',
          from_date: '',
          to_date: '',
          total_amount: '',
          balance_account: '1580',
          result_account: '6820',
          frequency: 'monthly'
        });
        loadAccruals();
      }
    } catch (error) {
      console.error('Failed to create accrual:', error);
    }
  };

  const handlePostManually = async (accrualId: string, postingId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/accruals/${accrualId}/postings/${postingId}/post`,
        { method: 'POST' }
      );
      
      const data = await response.json();
      
      if (data.success) {
        loadAccrualDetails(accrualId);
        loadAccruals();
      }
    } catch (error) {
      console.error('Failed to post accrual:', error);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('nb-NO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-green-500/10 text-green-400 border-green-500/20',
      completed: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      cancelled: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
      pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      posted: 'bg-green-500/10 text-green-400 border-green-500/20'
    };
    
    return badges[status as keyof typeof badges] || badges.pending;
  };

  const getFrequencyLabel = (frequency: string) => {
    const labels = {
      monthly: 'Månedlig',
      quarterly: 'Kvartalsvis',
      yearly: 'Årlig'
    };
    return labels[frequency as keyof typeof labels] || frequency;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Periodisering
          </h1>
          <p className="text-text-secondary">
            Automatisk periodisering av kostnader og inntekter
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-accent-blue hover:bg-accent-blue-bright text-white rounded-lg font-medium transition-colors"
        >
          + Ny periodisering
        </button>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-6">
        {['active', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              statusFilter === status
                ? 'bg-accent-blue text-white'
                : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
            }`}
          >
            {status === 'active' && 'Aktive'}
            {status === 'completed' && 'Fullførte'}
            {status === 'cancelled' && 'Kansellerte'}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Accruals List */}
        <div className="bg-bg-secondary rounded-xl border border-border p-6">
          <h2 className="text-xl font-bold text-text-primary mb-4">
            Periodiseringer ({accruals.length})
          </h2>
          
          {loading ? (
            <div className="text-center py-8 text-text-muted">Laster...</div>
          ) : accruals.length === 0 ? (
            <div className="text-center py-8 text-text-muted">
              Ingen periodiseringer funnet
            </div>
          ) : (
            <div className="space-y-3">
              {accruals.map((accrual) => (
                <div
                  key={accrual.id}
                  onClick={() => setSelectedAccrual(accrual.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedAccrual === accrual.id
                      ? 'border-accent-blue bg-accent-blue/5'
                      : 'border-border hover:border-border-light bg-bg-primary'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-text-primary mb-1">
                        {accrual.description}
                        {accrual.ai_detected && (
                          <span className="ml-2 text-xs bg-accent-purple/10 text-accent-purple px-2 py-0.5 rounded">
                            AI
                          </span>
                        )}
                      </h3>
                      <div className="text-sm text-text-muted space-y-0.5">
                        <div>{formatDate(accrual.from_date)} → {formatDate(accrual.to_date)}</div>
                        <div>{getFrequencyLabel(accrual.frequency)} · {formatAmount(accrual.total_amount)}</div>
                      </div>
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded border ${getStatusBadge(accrual.status)}`}>
                      {accrual.status}
                    </span>
                  </div>
                  
                  <div className="flex gap-4 text-sm">
                    <span className="text-green-400">
                      {accrual.postings_posted} bokført
                    </span>
                    <span className="text-amber-400">
                      {accrual.postings_pending} ventende
                    </span>
                  </div>
                  
                  {accrual.next_posting_date && (
                    <div className="mt-2 text-xs text-text-muted">
                      Neste: {formatDate(accrual.next_posting_date)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Accrual Details */}
        <div className="bg-bg-secondary rounded-xl border border-border p-6">
          {!selectedAccrual ? (
            <div className="text-center py-16 text-text-muted">
              Velg en periodisering for å se detaljer
            </div>
          ) : !accrualDetails ? (
            <div className="text-center py-16 text-text-muted">Laster...</div>
          ) : (
            <div>
              <h2 className="text-xl font-bold text-text-primary mb-4">
                Posteringsplan
              </h2>
              
              <div className="mb-6 p-4 bg-bg-primary rounded-lg border border-border">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-text-muted">Balansekon to:</span>
                    <div className="font-mono text-text-primary">{accrualDetails.accrual.balance_account}</div>
                  </div>
                  <div>
                    <span className="text-text-muted">Resultatkonto:</span>
                    <div className="font-mono text-text-primary">{accrualDetails.accrual.result_account}</div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                {accrualDetails.postings.map((posting) => (
                  <div
                    key={posting.id}
                    className="p-3 bg-bg-primary rounded-lg border border-border"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-text-primary">
                          {formatDate(posting.posting_date)}
                        </span>
                        <span className="text-text-muted text-sm">
                          {posting.period}
                        </span>
                      </div>
                      <span className={`text-xs font-medium px-2 py-1 rounded border ${getStatusBadge(posting.status)}`}>
                        {posting.status}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-accent-blue font-semibold">
                        {formatAmount(posting.amount)}
                      </span>
                      
                      {posting.status === 'pending' && (
                        <button
                          onClick={() => handlePostManually(accrualDetails.accrual.id, posting.id)}
                          className="px-3 py-1 text-xs bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded font-medium transition-colors"
                        >
                          Bokfør nå
                        </button>
                      )}
                      
                      {posting.status === 'posted' && posting.posted_at && (
                        <span className="text-xs text-text-muted">
                          Bokført: {formatDate(posting.posted_at)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Accrual Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl border border-border p-6 w-full max-w-lg">
            <h2 className="text-2xl font-bold text-text-primary mb-4">
              Ny periodisering
            </h2>
            
            <form onSubmit={handleCreateAccrual} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Beskrivelse
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary"
                  placeholder="F.eks. Forsikring 2026"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Fra dato
                  </label>
                  <input
                    type="date"
                    value={formData.from_date}
                    onChange={(e) => setFormData({ ...formData, from_date: e.target.value })}
                    className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Til dato
                  </label>
                  <input
                    type="date"
                    value={formData.to_date}
                    onChange={(e) => setFormData({ ...formData, to_date: e.target.value })}
                    className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Totalbeløp
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                  className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary"
                  placeholder="12000.00"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Balansekon to
                  </label>
                  <input
                    type="text"
                    value={formData.balance_account}
                    onChange={(e) => setFormData({ ...formData, balance_account: e.target.value })}
                    className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary font-mono"
                    placeholder="1580"
                    required
                  />
                  <span className="text-xs text-text-muted">Forskuddsbetalte kostnader</span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Resultatkonto
                  </label>
                  <input
                    type="text"
                    value={formData.result_account}
                    onChange={(e) => setFormData({ ...formData, result_account: e.target.value })}
                    className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary font-mono"
                    placeholder="6820"
                    required
                  />
                  <span className="text-xs text-text-muted">Kostnadskonto</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Frekvens
                </label>
                <select
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full px-3 py-2 bg-bg-primary border border-border rounded-lg text-text-primary"
                  required
                >
                  <option value="monthly">Månedlig</option>
                  <option value="quarterly">Kvartalsvis</option>
                  <option value="yearly">Årlig</option>
                </select>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 bg-bg-primary hover:bg-bg-hover text-text-secondary rounded-lg font-medium transition-colors"
                >
                  Avbryt
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-accent-blue hover:bg-accent-blue-bright text-white rounded-lg font-medium transition-colors"
                >
                  Opprett
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
