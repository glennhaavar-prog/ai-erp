'use client';

import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';

interface StatusData {
  receipts_total: number;
  receipts_processed: number;
  completion_rate: number;
  clients_total: number;
  clients_needs_attention: number;
}

export function MiniStatusWidget() {
  const [data, setData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const { tenantId } = useTenant();

  useEffect(() => {
    if (tenantId) {
      fetchStatusData();
    }
  }, [tenantId]);

  const fetchStatusData = async () => {
    if (!tenantId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=${tenantId}`);
      if (response.ok) {
        const result = await response.json();
        
        // Calculate stats
        const clientsNeedingAttention = result.clients?.filter((c: any) => 
          result.tasks.some((t: any) => t.client_id === c.id && (t.priority === 'high' || t.confidence > 80))
        ).length || 0;

        setData({
          receipts_total: 922, // TODO: Get from API
          receipts_processed: 14, // TODO: Get from API
          completion_rate: 1.5, // TODO: Calculate
          clients_total: result.clients?.length || 0,
          clients_needs_attention: clientsNeedingAttention,
        });
      }
    } catch (err) {
      console.error('Failed to fetch status data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-card border rounded-lg p-4 mb-4 animate-pulse">
        <div className="h-4 bg-muted rounded w-1/3 mb-2"></div>
        <div className="h-8 bg-muted rounded"></div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="bg-card border rounded-lg p-4 mb-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Receipts Total */}
        <div>
          <div className="text-xs text-muted-foreground mb-1">Kvitteringer mottatt</div>
          <div className="text-2xl font-bold text-foreground">{data.receipts_total}</div>
        </div>

        {/* Receipts Processed */}
        <div>
          <div className="text-xs text-muted-foreground mb-1">Behandlet</div>
          <div className="text-2xl font-bold text-foreground">{data.receipts_processed}</div>
          <div className="text-xs text-muted-foreground">{data.completion_rate.toFixed(1)}% ferdig</div>
        </div>

        {/* Clients Total */}
        <div>
          <div className="text-xs text-muted-foreground mb-1">Klienter</div>
          <div className="text-2xl font-bold text-foreground">{data.clients_total}</div>
        </div>

        {/* Clients Needing Attention */}
        <div>
          <div className="text-xs text-muted-foreground mb-1">Trenger oppmerksomhet</div>
          <div className="text-2xl font-bold text-red-600">{data.clients_needs_attention}</div>
        </div>
      </div>
    </div>
  );
}
