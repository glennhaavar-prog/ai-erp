'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import ClientStatusRow from '@/components/ClientStatusRow';
import InvoicePreviewModal from '@/components/InvoicePreviewModal';
import { Filter, SortAsc, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { ClientStatusRowSkeleton } from '@/components/ui/skeleton';
import {
  fetchMultiClientDashboard,
  calculateClientStatuses,
  type ClientStatus,
  type MultiClientDashboardResponse,
  APIError,
} from '@/lib/api-client';

type SortOption = 'name' | 'priority' | 'bilag' | 'bank';

// HARDCODED DEMO TENANT ID - In production, this would come from auth/context
const DEMO_TENANT_ID = '863d8bad-a56d-4527-b607-0d97d242672c';

export default function MultiClientDashboard() {
  const [dashboard, setDashboard] = useState<MultiClientDashboardResponse | null>(null);
  const [clientStatuses, setClientStatuses] = useState<ClientStatus[]>([]);
  const [hideCompleted, setHideCompleted] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('priority');
  const [selectedInvoice, setSelectedInvoice] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);
        
        const data = await fetchMultiClientDashboard(DEMO_TENANT_ID);
        setDashboard(data);
        
        const statuses = calculateClientStatuses(data);
        setClientStatuses(statuses);
      } catch (err) {
        console.error('Failed to load dashboard:', err);
        if (err instanceof APIError) {
          setError(`API Error: ${err.message}`);
        } else {
          setError('Failed to load dashboard. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  // Calculate priority for sorting
  const getClientPriority = (client: ClientStatus) => {
    return client.bilag + client.bank + client.avstemming;
  };

  // Filter and sort clients
  const processedClients = clientStatuses
    .filter(c => !hideCompleted || getClientPriority(c) > 0)
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'priority':
          return getClientPriority(b) - getClientPriority(a);
        case 'bilag':
          return b.bilag - a.bilag;
        case 'bank':
          return b.bank - a.bank;
        default:
          return 0;
      }
    });

  // Calculate totals
  const totalBilag = clientStatuses.reduce((sum, c) => sum + c.bilag, 0);
  const totalBank = clientStatuses.reduce((sum, c) => sum + c.bank, 0);
  const totalClients = clientStatuses.length;
  const clientsWithWork = clientStatuses.filter(c => getClientPriority(c) > 0).length;

  const handleClientClick = (client: ClientStatus) => {
    // Find first task for this client
    if (!dashboard) return;
    
    const clientTask = dashboard.tasks.find(t => t.client_id === client.id);
    if (!clientTask) return;

    // Build invoice object from task data
    const invoice = {
      id: clientTask.id,
      vendor_name: clientTask.data.vendor_name || 'Unknown Vendor',
      invoice_number: clientTask.data.invoice_number || 'N/A',
      amount: clientTask.data.amount || 0,
      suggested_account: clientTask.data.suggested_account || '',
      suggested_vat_code: clientTask.data.suggested_vat_code || '',
      confidence_score: clientTask.confidence,
      ai_reasoning: clientTask.description,
    };

    setSelectedInvoice(invoice);
    setIsModalOpen(true);
  };

  const handleApprove = (invoiceId: string) => {
    console.log('Approve:', invoiceId);
    setIsModalOpen(false);
    // TODO: Call API to approve
  };

  const handleReject = (invoiceId: string) => {
    console.log('Reject:', invoiceId);
    setIsModalOpen(false);
    // TODO: Call API to reject
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header Skeleton */}
          <div className="mb-8 space-y-4">
            <div className="h-8 w-64 bg-muted/50 rounded animate-pulse" />
            <div className="h-4 w-96 bg-muted/30 rounded animate-pulse" />
          </div>

          {/* Stats Skeleton */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-card border border-border rounded-xl p-6 space-y-2">
                <div className="h-4 w-24 bg-muted/50 rounded animate-pulse" />
                <div className="h-8 w-16 bg-muted/30 rounded animate-pulse" />
              </div>
            ))}
          </div>

          {/* Client Rows Skeleton */}
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <ClientStatusRowSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-foreground mb-2">Noe gikk galt</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors"
          >
            Prøv igjen
          </button>
        </div>
      </div>
    );
  }

  // No data state (shouldn't happen if API works)
  if (!dashboard || clientStatuses.length === 0) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-2xl mb-2">🏢</p>
          <p className="text-lg font-medium text-muted-foreground">Ingen klienter funnet</p>
          <p className="text-sm text-muted-foreground/60">Kontakt support hvis dette er en feil.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-4xl font-bold text-foreground">
            Multi-klient Oversikt
          </h1>
          <p className="text-lg text-muted-foreground">
            Unntaksrapport – Viser kun det som krever oppmerksomhet
          </p>
        </motion.div>

        {/* Summary Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6"
        >
          <div className="bg-card border border-border rounded-2xl p-6 hover:border-primary/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Aktive klienter
                </p>
                <p className="text-4xl font-bold text-primary">
                  {clientsWithWork}/{totalClients}
                </p>
              </div>
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary text-2xl">👥</span>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 hover:border-warning/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Åpne bilag
                </p>
                <p className="text-4xl font-bold text-warning">{totalBilag}</p>
              </div>
              <div className="w-12 h-12 bg-warning/10 rounded-full flex items-center justify-center">
                <span className="text-warning text-2xl">📄</span>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 hover:border-info/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Bank avstemming
                </p>
                <p className="text-4xl font-bold text-info">{totalBank}</p>
              </div>
              <div className="w-12 h-12 bg-info/10 rounded-full flex items-center justify-center">
                <span className="text-info text-2xl">🏦</span>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 hover:border-success/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Ferdig i dag
                </p>
                <p className="text-4xl font-bold text-success">
                  {totalClients - clientsWithWork}
                </p>
              </div>
              <div className="w-12 h-12 bg-success/10 rounded-full flex items-center justify-center">
                <span className="text-success text-2xl">✓</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setHideCompleted(!hideCompleted)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all
                ${hideCompleted 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-card border border-border text-foreground hover:border-primary/50'}
              `}
            >
              {hideCompleted ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              {hideCompleted ? 'Vis alle' : 'Skjul ferdige'}
            </button>

            <div className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-xl">
              <SortAsc className="w-4 h-4 text-muted-foreground" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
              >
                <option value="priority">Sorter: Prioritet</option>
                <option value="name">Sorter: Navn</option>
                <option value="bilag">Sorter: Bilag</option>
                <option value="bank">Sorter: Bank</option>
              </select>
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            Viser {processedClients.length} av {totalClients} klienter
          </div>
        </motion.div>

        {/* Client List */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="space-y-4"
        >
          {processedClients.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <p className="text-2xl mb-2">🎉</p>
              <p className="text-lg font-medium">Alle klienter er ferdig behandlet!</p>
              <p className="text-sm">Ingen åpne poster krever oppmerksomhet.</p>
            </div>
          ) : (
            processedClients.map((client, idx) => (
              <motion.div
                key={client.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 * idx }}
              >
                <ClientStatusRow 
                  client={client} 
                  onClick={() => handleClientClick(client)}
                />
              </motion.div>
            ))
          )}
        </motion.div>
      </div>

      {/* Invoice Preview Modal */}
      <InvoicePreviewModal
        invoice={selectedInvoice}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
}
