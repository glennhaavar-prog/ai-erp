'use client';

import { useState, useEffect } from 'react';
import {
  fetchAutoBookingStats,
  fetchAutoBookingStatus,
  fetchAutoBookingHealth,
  startAutoBookingBatch,
  processSingleInvoice,
  type AutoBookingStatsResponse,
  type AutoBookingStatusResponse,
  type AutoBookingHealthResponse,
} from '@/lib/api-client';
import { toast } from '@/lib/toast';

export default function AutoBookingDashboard() {
  const [stats, setStats] = useState<AutoBookingStatsResponse | null>(null);
  const [status, setStatus] = useState<AutoBookingStatusResponse | null>(null);
  const [health, setHealth] = useState<AutoBookingHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');

  // Polling interval (every 5 seconds)
  const POLLING_INTERVAL = 5000;

  // Load data
  const loadData = async () => {
    try {
      const [statsData, statusData, healthData] = await Promise.all([
        fetchAutoBookingStats(),
        fetchAutoBookingStatus(),
        fetchAutoBookingHealth(),
      ]);

      setStats(statsData);
      setStatus(statusData);
      setHealth(healthData);
    } catch (error) {
      console.error('Failed to load auto-booking data:', error);
      toast.error('Kunne ikke laste auto-bokføring data');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadData();
  }, []);

  // Polling for real-time updates
  useEffect(() => {
    const interval = setInterval(loadData, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  // Handle batch processing
  const handleStartBatch = async () => {
    try {
      setProcessing(true);
      const result = await startAutoBookingBatch();
      toast.success(`Prosessert: ${result.auto_booked_count}/${result.processed_count} fakturaer`);
      await loadData(); // Refresh stats
    } catch (error) {
      console.error('Batch processing failed:', error);
      toast.error('Batch-prosessering feilet');
    } finally {
      setProcessing(false);
    }
  };

  // Handle single invoice processing
  const handleProcessSingle = async () => {
    if (!selectedInvoiceId.trim()) {
      toast.error('Vennligst skriv inn faktura-ID');
      return;
    }

    try {
      setProcessing(true);
      const result = await processSingleInvoice(selectedInvoiceId);
      
      if (result.status === 'success') {
        toast.success(`Faktura ${selectedInvoiceId} prosessert`);
        setSelectedInvoiceId('');
      } else {
        toast.error(`Feil: ${result.error || 'Ukjent feil'}`);
      }
      
      await loadData(); // Refresh stats
    } catch (error) {
      console.error('Single invoice processing failed:', error);
      toast.error('Kunne ikke prosessere faktura');
    } finally {
      setProcessing(false);
    }
  };

  // Health status indicator
  const getHealthIcon = (health: AutoBookingHealthResponse | null) => {
    if (!health) return '⚪';
    switch (health.status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'unhealthy':
        return '🔴';
      default:
        return '⚪';
    }
  };

  // Format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Aldri';
    return new Date(dateStr).toLocaleString('nb-NO');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-blue mx-auto mb-4"></div>
          <p className="text-text-secondary">Laster auto-bokføring...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-background">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">AI Auto-Bokføring</h1>
            <p className="text-text-secondary mt-1">
              Automatisk bokføring med kunstig intelligens
            </p>
          </div>
          
          {/* Health Status */}
          <div className="flex items-center gap-3 bg-bg-secondary px-4 py-3 rounded-lg">
            <span className="text-3xl">{getHealthIcon(health)}</span>
            <div>
              <p className="text-sm font-medium text-foreground">System Status</p>
              <p className="text-xs text-text-secondary capitalize">
                {health?.status || 'Ukjent'}
              </p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Processed */}
          <div className="bg-bg-secondary border border-border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Totalt Prosessert</p>
                <p className="text-3xl font-bold text-foreground">
                  {stats?.stats.processed_count || 0}
                </p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </div>

          {/* Success Rate */}
          <div className="bg-bg-secondary border border-border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Suksessrate</p>
                <p className="text-3xl font-bold text-green-500">
                  {stats?.stats.success_rate ? `${stats.stats.success_rate.toFixed(1)}%` : '0%'}
                </p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
            <div className="mt-2 text-xs text-text-secondary">
              {stats?.stats.auto_booked_count || 0} av {stats?.stats.processed_count || 0} fakturaer
            </div>
          </div>

          {/* Failed Count */}
          <div className="bg-bg-secondary border border-border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Feilet</p>
                <p className="text-3xl font-bold text-red-500">
                  {stats?.stats.review_queue_count || 0}
                </p>
              </div>
              <div className="text-4xl">❌</div>
            </div>
            {stats && stats.stats.review_queue_count > 0 && (
              <button className="mt-2 text-xs text-accent-blue hover:underline">
                Se detaljer
              </button>
            )}
          </div>

          {/* Processing Speed */}
          <div className="bg-bg-secondary border border-border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Gjennomsnittlig Tid</p>
                <p className="text-3xl font-bold text-foreground">
                  {stats?.stats.avg_confidence_auto_booked 
                    ? `${stats.stats.avg_confidence_auto_booked.toFixed(1)}s` 
                    : '0s'}
                </p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-bg-secondary border border-border rounded-lg p-6">
          <h2 className="text-xl font-bold text-foreground mb-4">Handlinger</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Batch Processing */}
            <div className="space-y-3">
              <h3 className="font-medium text-foreground">Batch-Prosessering</h3>
              <p className="text-sm text-text-secondary">
                Start automatisk bokføring av alle ventende fakturaer
              </p>
              <button
                onClick={handleStartBatch}
                disabled={processing || status?.status.processing_available}
                className={`
                  w-full px-6 py-3 rounded-lg font-medium transition-all
                  ${processing || status?.status.processing_available
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-accent-blue text-white hover:bg-blue-600 shadow-md hover:shadow-lg'
                  }
                `}
              >
                {status?.status.processing_available ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Pågår...
                  </span>
                ) : processing ? (
                  'Starter...'
                ) : (
                  '🚀 Start Auto-Bokføring'
                )}
              </button>
              
              {status?.status.processing_available && (
                <div className="text-sm text-text-secondary">
                  Prosesserer: {status?.status.auto_booked_today || 0} av {status?.status.pending_invoices || 0}
                </div>
              )}
            </div>

            {/* Single Invoice Processing */}
            <div className="space-y-3">
              <h3 className="font-medium text-foreground">Prosesser Enkelt Faktura</h3>
              <p className="text-sm text-text-secondary">
                Skriv inn faktura-ID for å prosessere én faktura
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={selectedInvoiceId}
                  onChange={(e) => setSelectedInvoiceId(e.target.value)}
                  placeholder="Faktura-ID"
                  className="flex-1 px-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-blue"
                  disabled={processing}
                />
                <button
                  onClick={handleProcessSingle}
                  disabled={processing || !selectedInvoiceId.trim()}
                  className={`
                    px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap
                    ${processing || !selectedInvoiceId.trim()
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-green-500 text-white hover:bg-green-600 shadow-md hover:shadow-lg'
                    }
                  `}
                >
                  {processing ? 'Prosesserer...' : 'Prosesser'}
                </button>
              </div>
            </div>
          </div>

          {/* Refresh Button */}
          <div className="mt-6 pt-6 border-t border-border">
            <button
              onClick={loadData}
              className="px-4 py-2 text-sm bg-bg-hover hover:bg-border rounded-lg transition-colors"
            >
              🔄 Oppdater Statistikk
            </button>
            <span className="ml-3 text-xs text-text-secondary">
              Oppdateres automatisk hvert 5. sekund
            </span>
          </div>
        </div>

        {/* System Health Details */}
        {health && (
          <div className="bg-bg-secondary border border-border rounded-lg p-6">
            <h2 className="text-xl font-bold text-foreground mb-4">Systemhelse</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-3 bg-background rounded-lg">
                <span className="text-2xl">{health.status === 'operational' ? '✅' : '❌'}</span>
                <div>
                  <p className="font-medium text-foreground">{health.service}</p>
                  <p className="text-xs text-text-secondary">
                    {health.status === 'operational' ? 'Operativ' : 'Ikke operativ'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-background rounded-lg">
                <span className="text-2xl">🕐</span>
                <div>
                  <p className="font-medium text-foreground">Sist sjekket</p>
                  <p className="text-xs text-text-secondary">
                    {new Date(health.timestamp).toLocaleString('nb-NO')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Last Run Info */}
        {stats?.stats.period_end && (
          <div className="text-center text-sm text-text-secondary">
            Siste kjøring: {formatDate(stats.stats.period_end)}
          </div>
        )}
      </div>
    </div>
  );
}
