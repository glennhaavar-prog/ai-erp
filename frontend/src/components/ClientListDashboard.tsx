'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useTenant } from '@/contexts/TenantContext';
import { useViewMode } from '@/contexts/ViewModeContext';

interface ClientStatus {
  client_id: string;
  client_name: string;
  status: 'green' | 'yellow' | 'red';
  counts: {
    bilag: number;
    bank: number;
    avstemming: number;
  };
  urgent_items: number;
  review_items: number;
}

interface ClientListDashboardProps {
  onClientSelect?: (clientId: string) => void;
}

export function ClientListDashboard({ onClientSelect }: ClientListDashboardProps) {
  const [clients, setClients] = useState<ClientStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();
  
  // Get tenant from context
  const { tenantId, isLoading: tenantLoading, error: tenantError } = useTenant();
  
  // Get view mode context for setting selected item
  const { setSelectedItem } = useViewMode();

  useEffect(() => {
    console.log('ClientListDashboard: tenantId changed:', tenantId, 'tenantLoading:', tenantLoading);
    if (tenantId) {
      fetchClientStatuses();
    } else if (!tenantLoading && !tenantId) {
      // Tenant loading finished but no tenantId - show error
      setLoading(false);
      setError('Could not load tenant information');
    }
  }, [tenantId, tenantLoading]);

  const fetchClientStatuses = async () => {
    if (!tenantId) return;
    
    setLoading(true);
    setError(null);
    console.log('ClientListDashboard: Fetching client statuses for tenant:', tenantId);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=${tenantId}`);
      console.log('ClientListDashboard: API response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('ClientListDashboard: Received data:', data);
        
        // Transform tasks into client statuses with traffic light logic
        const clientMap = new Map<string, ClientStatus>();
        
        data.tasks.forEach((task: any) => {
          if (!clientMap.has(task.client_id)) {
            clientMap.set(task.client_id, {
              client_id: task.client_id,
              client_name: task.client_name,
              status: 'green',
              counts: {
                bilag: 0,
                bank: 0,
                avstemming: 0,
              },
              urgent_items: 0,
              review_items: 0,
            });
          }
          
          const client = clientMap.get(task.client_id)!;
          
          // Count by category
          if (task.category === 'invoicing') client.counts.bilag++;
          if (task.category === 'bank') client.counts.bank++;
          if (task.category === 'reporting') client.counts.avstemming++;
          
          // Determine status based on priority and confidence
          if (task.priority === 'high' || task.confidence > 80) {
            client.urgent_items++;
            client.status = 'red';
          } else if (task.priority === 'medium' || task.confidence > 60) {
            client.review_items++;
            if (client.status !== 'red') {
              client.status = 'yellow';
            }
          }
        });
        
        // Add clients with no tasks (all green)
        data.clients.forEach((client: any) => {
          if (!clientMap.has(client.id)) {
            clientMap.set(client.id, {
              client_id: client.id,
              client_name: client.name,
              status: 'green',
              counts: {
                bilag: 0,
                bank: 0,
                avstemming: 0,
              },
              urgent_items: 0,
              review_items: 0,
            });
          }
        });
        
        setClients(Array.from(clientMap.values()).sort((a, b) => {
          // Sort by status (red > yellow > green), then by name
          const statusOrder = { red: 0, yellow: 1, green: 2 };
          if (statusOrder[a.status] !== statusOrder[b.status]) {
            return statusOrder[a.status] - statusOrder[b.status];
          }
          return a.client_name.localeCompare(b.client_name);
        }));
      }
    } catch (err) {
      console.error('Failed to fetch client statuses:', err);
      setError(err instanceof Error ? err.message : 'Failed to load client data');
    } finally {
      setLoading(false);
    }
  };

  const filteredClients = clients.filter(client =>
    client.client_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTrafficLightEmoji = (status: 'green' | 'yellow' | 'red') => {
    switch (status) {
      case 'green': return '🟢';
      case 'yellow': return '🟡';
      case 'red': return '🔴';
    }
  };

  const getStatusBgColor = (status: 'green' | 'yellow' | 'red') => {
    switch (status) {
      case 'green': return 'bg-green-50 hover:bg-green-100 border-green-200';
      case 'yellow': return 'bg-yellow-50 hover:bg-yellow-100 border-yellow-200';
      case 'red': return 'bg-red-50 hover:bg-red-100 border-red-200';
    }
  };

  const handleClientClick = (clientId: string) => {
    // Find the client and set it as selected for RightPanel
    const client = clients.find(c => c.client_id === clientId);
    if (client) {
      setSelectedItem(client);
    }

    if (onClientSelect) {
      onClientSelect(clientId);
    } else {
      router.push(`/clients/${clientId}`);
    }
  };

  // Show tenant loading state
  if (tenantLoading) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster tenant info...</p>
        </div>
      </div>
    );
  }

  // Show tenant error
  if (tenantError) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-lg font-semibold text-foreground mb-2">Kunne ikke laste tenant</p>
          <p className="text-sm text-muted-foreground mb-4">{tenantError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Prøv igjen
          </button>
        </div>
      </div>
    );
  }

  // Show loading state for clients
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster klienter...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-lg font-semibold text-foreground mb-2">Kunne ikke laste klienter</p>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <button
            onClick={() => fetchClientStatuses()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Prøv igjen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header - Simplified for Unified Dashboard */}
      <div className="mb-3">
        <h2 className="text-xl font-bold text-foreground">Klienter</h2>
      </div>

      {/* Search - Enhanced visibility per Glenn's feedback 2026-02-09 */}
      <div className="mb-3">
        <input
          type="text"
          placeholder="Søk etter klient..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 rounded-lg border-2 border-muted-foreground/30 bg-card text-foreground placeholder:text-muted-foreground/70 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
        />
      </div>

      {/* Client List */}
      <div className="flex-1 overflow-y-auto space-y-1.5">
        {filteredClients.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Ingen klienter funnet
          </div>
        ) : (
          filteredClients.map((client) => (
            <motion.div
              key={client.client_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              onClick={() => handleClientClick(client.client_id)}
              className={`
                border rounded-lg p-2.5 cursor-pointer transition-all
                ${getStatusBgColor(client.status)}
              `}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-2xl flex-shrink-0">{getTrafficLightEmoji(client.status)}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-foreground truncate">{client.client_name}</h3>
                    {client.status === 'red' && client.urgent_items > 0 && (
                      <p className="text-[10px] text-red-700 leading-tight">
                        {client.urgent_items} haster
                      </p>
                    )}
                    {client.status === 'yellow' && client.review_items > 0 && (
                      <p className="text-[10px] text-yellow-700 leading-tight">
                        {client.review_items} til gjennomgang
                      </p>
                    )}
                    {client.status === 'green' && (
                      <p className="text-[10px] text-green-700 leading-tight">
                        Alt OK
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-3 text-xs flex-shrink-0">
                  {client.counts.bilag > 0 && (
                    <div className="text-center">
                      <div className="font-semibold text-foreground leading-tight">{client.counts.bilag}</div>
                      <div className="text-[10px] text-muted-foreground leading-tight">Bilag</div>
                    </div>
                  )}
                  {client.counts.bank > 0 && (
                    <div className="text-center">
                      <div className="font-semibold text-foreground leading-tight">{client.counts.bank}</div>
                      <div className="text-[10px] text-muted-foreground leading-tight">Bank</div>
                    </div>
                  )}
                  {client.counts.avstemming > 0 && (
                    <div className="text-center">
                      <div className="font-semibold text-foreground leading-tight">{client.counts.avstemming}</div>
                      <div className="text-[10px] text-muted-foreground leading-tight">Avstemming</div>
                    </div>
                  )}
                  {client.counts.bilag === 0 && client.counts.bank === 0 && client.counts.avstemming === 0 && (
                    <div className="text-[10px] text-muted-foreground italic">
                      Ingen oppgaver
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
