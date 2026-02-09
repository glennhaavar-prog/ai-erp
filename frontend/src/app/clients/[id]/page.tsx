"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Filter } from 'lucide-react';
import { useTenant } from '@/contexts/TenantContext';

interface Task {
  id: string;
  type: string;
  category: string;
  client_id: string;
  description: string;
  confidence: number;
  created_at: string;
  priority: 'high' | 'medium' | 'low';
  data: {
    invoice_id?: string;
    vendor_name?: string;
    amount?: number;
    invoice_number?: string;
  };
}

interface ClientData {
  client_id: string;
  client_name: string;
  tasks: Task[];
  summary: {
    total: number;
    by_category: {
      invoicing: number;
      bank: number;
      reporting: number;
    };
    by_priority: {
      high: number;
      medium: number;
      low: number;
    };
  };
}

type CategoryFilter = 'all' | 'invoicing' | 'bank' | 'reporting';

export default function ClientDrilldownPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params?.id as string;
  
  const [data, setData] = useState<ClientData | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all');
  
  // Get tenant from context
  const { tenantId, isLoading: tenantLoading } = useTenant();

  useEffect(() => {
    if (tenantId) {
      fetchClientTasks();
    }
  }, [clientId, tenantId]);

  const fetchClientTasks = async () => {
    if (!tenantId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=${tenantId}`);
      if (response.ok) {
        const allData = await response.json();
        
        // Filter tasks for this specific client
        const clientTasks = allData.tasks.filter((task: Task) => task.client_id === clientId);
        const client = allData.clients.find((c: any) => c.id === clientId);
        
        const summary = {
          total: clientTasks.length,
          by_category: {
            invoicing: clientTasks.filter((t: Task) => t.category === 'invoicing').length,
            bank: clientTasks.filter((t: Task) => t.category === 'bank').length,
            reporting: clientTasks.filter((t: Task) => t.category === 'reporting').length,
          },
          by_priority: {
            high: clientTasks.filter((t: Task) => t.priority === 'high').length,
            medium: clientTasks.filter((t: Task) => t.priority === 'medium').length,
            low: clientTasks.filter((t: Task) => t.priority === 'low').length,
          },
        };
        
        setData({
          client_id: clientId,
          client_name: client?.name || 'Unknown Client',
          tasks: clientTasks,
          summary,
        });
      }
    } catch (error) {
      console.error('Failed to fetch client tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = data?.tasks.filter(task => 
    categoryFilter === 'all' || task.category === categoryFilter
  ) || [];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'invoicing': return '📄';
      case 'bank': return '🏦';
      case 'reporting': return '📊';
      default: return '📋';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-50 border-red-200 text-red-900';
      case 'medium': return 'bg-yellow-50 border-yellow-200 text-yellow-900';
      case 'low': return 'bg-green-50 border-green-200 text-green-900';
      default: return 'bg-gray-50 border-gray-200 text-gray-900';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster klientdata...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Klient ikke funnet</p>
          <Link href="/" className="text-primary hover:underline mt-4 inline-block">
            ← Tilbake til oversikten
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-primary hover:underline font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Tilbake til oversikten
        </Link>
        
        <h1 className="text-3xl font-bold text-foreground mb-2">{data.client_name}</h1>
        <p className="text-muted-foreground">
          {data.summary.total} oppgaver totalt
          {data.summary.by_priority.high > 0 && (
            <span className="text-red-600 font-medium ml-2">
              • {data.summary.by_priority.high} haster
            </span>
          )}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📄</span>
            <span className="font-semibold text-foreground">Bilag</span>
          </div>
          <div className="text-2xl font-bold text-primary">{data.summary.by_category.invoicing}</div>
          <div className="text-sm text-muted-foreground">trenger gjennomgang</div>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🏦</span>
            <span className="font-semibold text-foreground">Bank</span>
          </div>
          <div className="text-2xl font-bold text-primary">{data.summary.by_category.bank}</div>
          <div className="text-sm text-muted-foreground">ventende transaksjoner</div>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📊</span>
            <span className="font-semibold text-foreground">Avstemming</span>
          </div>
          <div className="text-2xl font-bold text-primary">{data.summary.by_category.reporting}</div>
          <div className="text-sm text-muted-foreground">må avstemmes</div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-6 flex items-center gap-2 border-b border-border pb-2">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Filter:</span>
        {(['all', 'invoicing', 'bank', 'reporting'] as CategoryFilter[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setCategoryFilter(cat)}
            className={`px-3 py-1 text-sm rounded transition-colors ${
              categoryFilter === cat
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {cat === 'all' ? 'Alle' : cat === 'invoicing' ? 'Bilag' : cat === 'bank' ? 'Bank' : 'Avstemming'}
          </button>
        ))}
      </div>

      {/* Tasks List */}
      {filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-green-50 rounded-lg border border-green-200">
          <div className="text-4xl mb-2">✅</div>
          <h3 className="text-lg font-semibold text-green-900 mb-1">Alt i orden!</h3>
          <p className="text-green-700">Ingen oppgaver trenger oppmerksomhet akkurat nå.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`border rounded-lg p-4 ${getPriorityColor(task.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(task.category)}</span>
                    <div>
                      <h3 className="font-semibold">{task.description}</h3>
                      {task.data.vendor_name && (
                        <p className="text-sm opacity-80 mt-1">
                          <strong>Leverandør:</strong> {task.data.vendor_name}
                        </p>
                      )}
                      {task.data.invoice_number && (
                        <p className="text-sm opacity-80">
                          <strong>Faktura #:</strong> {task.data.invoice_number}
                        </p>
                      )}
                      {task.data.amount && (
                        <p className="text-sm opacity-80">
                          <strong>Beløp:</strong> {task.data.amount.toFixed(2)} NOK
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                    {task.priority === 'high' ? 'HASTER' : task.priority === 'medium' ? 'MEDIUM' : 'LAV'}
                  </span>
                  <p className="text-xs opacity-70 mt-2">
                    {new Date(task.created_at).toLocaleDateString('nb-NO')}
                  </p>
                  <div className="mt-2">
                    <span className="text-xs opacity-70">AI sikkerhet:</span>
                    <div className="w-20 h-1.5 bg-white/50 rounded-full mt-1">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${task.confidence}%` }}
                      />
                    </div>
                    <span className="text-xs opacity-70">{task.confidence}%</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => router.push(`/review-queue/${task.id}`)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 text-sm font-medium"
                >
                  Gjennomgå nå
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
