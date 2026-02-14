"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Plus, Search, Filter, Building2, Users } from 'lucide-react';
import { useTenant } from '@/contexts/TenantContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface Client {
  id: string;
  name: string;
  org_number?: string;
  status: 'active' | 'inactive';
  pending_tasks?: number;
  contact_person?: string;
  email?: string;
  phone?: string;
  created_at: string;
}

export default function ClientsListPage() {
  const router = useRouter();
  const { tenantId, isLoading: tenantLoading } = useTenant();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('active');

  useEffect(() => {
    if (tenantId) {
      fetchClients();
    }
  }, [tenantId, statusFilter]);

  const fetchClients = async () => {
    if (!tenantId) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        tenant_id: tenantId,
      });
      
      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      // Mock data for now - replace with actual API call
      // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clients?${params.toString()}`);
      // const data = await response.json();
      
      // Mock data
      const mockClients: Client[] = [
        {
          id: 'client-1',
          name: 'Acme Corporation AS',
          org_number: '123456789',
          status: 'active',
          pending_tasks: 5,
          contact_person: 'John Doe',
          email: 'john@acme.no',
          phone: '+47 12345678',
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 'client-2',
          name: 'Beta Solutions AS',
          org_number: '987654321',
          status: 'active',
          pending_tasks: 2,
          contact_person: 'Jane Smith',
          email: 'jane@beta.no',
          phone: '+47 87654321',
          created_at: '2024-02-20T14:30:00Z'
        },
        {
          id: 'client-3',
          name: 'Gamma Industries AS',
          org_number: '555666777',
          status: 'inactive',
          pending_tasks: 0,
          contact_person: 'Bob Johnson',
          email: 'bob@gamma.no',
          created_at: '2023-12-01T09:00:00Z'
        }
      ];
      
      setClients(mockClients);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.org_number?.includes(searchTerm) ||
                         client.contact_person?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || client.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500">Aktiv</Badge>;
      case 'inactive':
        return <Badge variant="outline">Inaktiv</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('nb-NO');
  };

  if (loading || tenantLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster klienter...</p>
        </div>
      </div>
    );
  }

  const activeCount = clients.filter(c => c.status === 'active').length;
  const totalTasks = clients.reduce((sum, c) => sum + (c.pending_tasks || 0), 0);

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Klienter</h1>
            <p className="text-muted-foreground">
              Administrer klienter og deres oppgaver
            </p>
          </div>
          <Button onClick={() => router.push('/innstillinger/klienter')}>
            <Plus className="w-4 h-4 mr-2" />
            Ny klient
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aktive klienter</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">
              av {clients.length} totalt
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ventende oppgaver</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTasks}</div>
            <p className="text-xs text-muted-foreground">
              Må behandles
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nye denne måneden</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.filter(c => {
                const date = new Date(c.created_at);
                const now = new Date();
                return date.getMonth() === now.getMonth() && 
                       date.getFullYear() === now.getFullYear();
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Registrert
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Søk etter klient, org.nr eller kontaktperson..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('all')}
              >
                Alle
              </Button>
              <Button
                variant={statusFilter === 'active' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('active')}
              >
                Aktive
              </Button>
              <Button
                variant={statusFilter === 'inactive' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('inactive')}
              >
                Inaktive
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Clients List */}
      <Card>
        <CardHeader>
          <CardTitle>Klientoversikt ({filteredClients.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredClients.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-semibold mb-2">Ingen klienter funnet</p>
              <p className="text-sm mb-4">
                {searchTerm ? 'Prøv et annet søk' : 'Kom i gang ved å legge til en ny klient'}
              </p>
              {!searchTerm && (
                <Button onClick={() => router.push('/innstillinger/klienter')}>
                  <Plus className="w-4 h-4 mr-2" />
                  Legg til klient
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredClients.map((client, index) => (
                <motion.div
                  key={client.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link href={`/clients/${client.id}`}>
                    <div className="border rounded-lg p-4 hover:bg-muted/50 cursor-pointer transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Building2 className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <h3 className="font-semibold text-lg">{client.name}</h3>
                              {client.org_number && (
                                <p className="text-sm text-muted-foreground">
                                  Org.nr: {client.org_number}
                                </p>
                              )}
                            </div>
                          </div>
                          
                          <div className="ml-8 space-y-1 text-sm">
                            {client.contact_person && (
                              <p className="text-muted-foreground">
                                <strong>Kontakt:</strong> {client.contact_person}
                              </p>
                            )}
                            {client.email && (
                              <p className="text-muted-foreground">
                                <strong>E-post:</strong> {client.email}
                              </p>
                            )}
                            {client.phone && (
                              <p className="text-muted-foreground">
                                <strong>Telefon:</strong> {client.phone}
                              </p>
                            )}
                          </div>
                        </div>
                        
                        <div className="text-right">
                          {getStatusBadge(client.status)}
                          
                          {client.pending_tasks !== undefined && client.pending_tasks > 0 && (
                            <div className="mt-3">
                              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                                {client.pending_tasks} {client.pending_tasks === 1 ? 'oppgave' : 'oppgaver'}
                              </Badge>
                            </div>
                          )}
                          
                          <p className="text-xs text-muted-foreground mt-2">
                            Opprettet: {formatDate(client.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
