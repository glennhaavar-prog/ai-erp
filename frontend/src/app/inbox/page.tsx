"use client";

import React, { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  FileText, 
  Upload, 
  Download, 
  Filter, 
  Search,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

interface InboxItem {
  id: string;
  type: 'supplier_invoice' | 'bank_transaction' | 'customer_invoice' | 'document';
  filename: string;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'reviewed' | 'posted';
  vendor_name?: string;
  amount?: number;
  confidence?: number;
  description?: string;
}

export default function InboxPage() {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    if (selectedClient && selectedClient.id) {
      fetchInboxItems(selectedClient.id);
    }
  }, [selectedClient, filterStatus]);

  const fetchInboxItems = async (clientId: string) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        client_id: clientId,
        limit: '50',
      });
      
      if (filterStatus && filterStatus !== 'all') {
        params.append('status', filterStatus);
      }

      // Call real API endpoint
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${API_URL}/api/inbox/?${params.toString()}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setItems(data.items || []);
    } catch (error) {
      console.error('Error fetching inbox items:', error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">Venter</Badge>;
      case 'processing':
        return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Behandles</Badge>;
      case 'reviewed':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Gjennomgått</Badge>;
      case 'posted':
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">Bokført</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'supplier_invoice':
        return '📄';
      case 'bank_transaction':
        return '🏦';
      case 'customer_invoice':
        return '💰';
      case 'document':
        return '📎';
      default:
        return '📋';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'supplier_invoice':
        return 'Leverandørfaktura';
      case 'bank_transaction':
        return 'Banktransaksjon';
      case 'customer_invoice':
        return 'Kundefaktura';
      case 'document':
        return 'Dokument';
      default:
        return type;
    }
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('nb-NO');
  };

  if (clientLoading || loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          {clientLoading ? 'Laster klientinformasjon...' : 'Laster innboks...'}
        </div>
      </div>
    );
  }

  if (!selectedClient) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center text-muted-foreground">
          Velg en klient fra menyen øverst for å se innboksen
        </div>
      </div>
    );
  }

  const pendingCount = items.filter(i => i.status === 'pending').length;
  const processingCount = items.filter(i => i.status === 'processing').length;

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Innboks</h1>
        <p className="text-muted-foreground">
          Innkommende bilag og transaksjoner som venter på behandling
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Venter på behandling</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
            <p className="text-xs text-muted-foreground">Må behandles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Under behandling</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{processingCount}</div>
            <p className="text-xs text-muted-foreground">AI behandler</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Totalt i dag</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{items.length}</div>
            <p className="text-xs text-muted-foreground">Mottatt</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter Bar */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <div className="flex gap-2">
              <Button
                variant={filterStatus === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('all')}
              >
                Alle
              </Button>
              <Button
                variant={filterStatus === 'pending' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('pending')}
              >
                Venter
              </Button>
              <Button
                variant={filterStatus === 'processing' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('processing')}
              >
                Behandles
              </Button>
            </div>
            
            <div className="ml-auto">
              <Button variant="outline" size="sm">
                <Upload className="h-4 w-4 mr-2" />
                Last opp
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items List */}
      <Card>
        <CardHeader>
          <CardTitle>Innkommende dokumenter ({items.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-semibold mb-2">Ingen nye dokumenter</p>
              <p className="text-sm">Alle dokumenter er behandlet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="border rounded-lg p-4 hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => window.location.href = `/review-queue/${item.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex gap-4 flex-1">
                      <div className="text-3xl">{getTypeIcon(item.type)}</div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{item.filename}</h3>
                          {getStatusBadge(item.status)}
                        </div>
                        
                        <p className="text-sm text-muted-foreground mb-2">
                          {item.description || getTypeLabel(item.type)}
                        </p>
                        
                        {item.vendor_name && (
                          <p className="text-sm">
                            <strong>Leverandør:</strong> {item.vendor_name}
                          </p>
                        )}
                        
                        {item.amount && (
                          <p className="text-sm">
                            <strong>Beløp:</strong> {formatCurrency(item.amount)}
                          </p>
                        )}
                        
                        <p className="text-xs text-muted-foreground mt-2">
                          Mottatt: {formatDate(item.uploaded_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      {item.confidence && (
                        <div className="mb-2">
                          <span className="text-xs text-muted-foreground">AI sikkerhet:</span>
                          <div className="w-20 h-1.5 bg-gray-200 rounded-full mt-1">
                            <div
                              className="h-full bg-green-500 rounded-full"
                              style={{ width: `${item.confidence}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">{item.confidence}%</span>
                        </div>
                      )}
                      
                      <Button variant="outline" size="sm" className="mt-2">
                        Gjennomgå
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
