/**
 * Klienter (Clients) Page - Client Management
 * List all clients, create new clients
 */
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { clientsApi, Client, ClientCreateRequest, BrregCompany } from '@/api/clients';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PlusIcon, BuildingOfficeIcon, PencilIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';

// Hardcoded tenant ID for demo purposes
// TODO: Get this from auth context or environment
const DEFAULT_TENANT_ID = 'c23eacc0-fbe8-4390-866b-7fc031002cea';

export const Klienter: React.FC = () => {
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // Brreg autocomplete state
  const [brregSuggestions, setBrregSuggestions] = useState<BrregCompany[]>([]);
  const [showBrregDropdown, setShowBrregDropdown] = useState(false);
  const [brregSearching, setBrregSearching] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const [formData, setFormData] = useState<ClientCreateRequest>({
    name: '',
    org_number: '',
    industry: '',
    start_date: new Date().toISOString().split('T')[0],
    address: '',
    contact_person: '',
    contact_email: '',
    fiscal_year_start: '01-01',
    vat_registered: true,
  });

  useEffect(() => {
    fetchClients();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowBrregDropdown(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await clientsApi.list({
        status: 'all',
        limit: 100,
      });
      setClients(response.items);
    } catch (error) {
      console.error('Error fetching clients:', error);
      toast.error('Kunne ikke laste klienter');
    } finally {
      setLoading(false);
    }
  };

  const searchBrregCompanies = async (query: string) => {
    if (query.length < 2) {
      setBrregSuggestions([]);
      setShowBrregDropdown(false);
      return;
    }
    
    setBrregSearching(true);
    try {
      const results = await clientsApi.searchBrreg(query);
      setBrregSuggestions(results);
      setShowBrregDropdown(results.length > 0);
    } catch (error) {
      console.error('Brreg search error:', error);
      setBrregSuggestions([]);
      setShowBrregDropdown(false);
    } finally {
      setBrregSearching(false);
    }
  };

  const handleNameChange = (value: string) => {
    setFormData({ ...formData, name: value });
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Debounce search (300ms)
    searchTimeoutRef.current = setTimeout(() => {
      searchBrregCompanies(value);
    }, 300);
  };

  const selectBrregCompany = (company: BrregCompany) => {
    // Auto-fill all fields from Brreg data
    const addressParts = [company.address, company.postal_code, company.city].filter(Boolean);
    const fullAddress = addressParts.join(', ');
    
    setFormData({
      ...formData,
      name: company.name,
      org_number: company.org_number,
      address: fullAddress,
      industry: company.nace_description || '',
    });
    
    setShowBrregDropdown(false);
    setBrregSuggestions([]);
    
    toast.success(`Autofylt fra Brønnøysundregistrene: ${company.name}`);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate org_number (9 digits)
    if (!/^\d{9}$/.test(formData.org_number)) {
      toast.error('Org.nummer må være 9 siffer');
      return;
    }
    
    try {
      setCreating(true);
      const newClient = await clientsApi.create(DEFAULT_TENANT_ID, formData);
      toast.success(`Klient "${newClient.name}" opprettet`);
      setIsCreateDialogOpen(false);
      fetchClients();
      
      // Reset form
      setFormData({
        name: '',
        org_number: '',
        industry: '',
        start_date: new Date().toISOString().split('T')[0],
        address: '',
        contact_person: '',
        contact_email: '',
        fiscal_year_start: '01-01',
        vat_registered: true,
      });
      
      // Navigate to client detail or settings page
      // router.push(`/clients/${newClient.id}`);
    } catch (error: any) {
      console.error('Error creating client:', error);
      const errorMessage = error.response?.data?.detail || 'Kunne ikke opprette klient';
      toast.error(errorMessage);
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
    };
    const labels = {
      active: 'Aktiv',
      inactive: 'Inaktiv',
      suspended: 'Suspendert',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || colors.active}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Laster klienter...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Klienter</h1>
          <p className="text-gray-600 mt-1">Administrer klientbedrifter</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusIcon className="h-5 w-5 mr-2" />
              Opprett ny klient
            </Button>
          </DialogTrigger>
          
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleCreate}>
              <DialogHeader>
                <DialogTitle>Opprett ny klient</DialogTitle>
                <DialogDescription>
                  Legg til en ny klientbedrift i systemet
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                {/* Company Name with Brreg Autocomplete */}
                <div className="relative" ref={dropdownRef}>
                  <Label htmlFor="name">
                    Firmanavn *
                    <span className="text-xs text-gray-500 ml-2">
                      (Søk i Brønnøysundregistrene)
                    </span>
                  </Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    onFocus={() => {
                      if (brregSuggestions.length > 0) {
                        setShowBrregDropdown(true);
                      }
                    }}
                    placeholder="Skriv firmanavn, f.eks. GHB"
                    required
                    autoComplete="off"
                  />
                  
                  {/* Autocomplete Dropdown */}
                  {showBrregDropdown && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto">
                      {brregSearching ? (
                        <div className="p-4 text-center text-gray-500">
                          Søker i Brønnøysundregistrene...
                        </div>
                      ) : brregSuggestions.length > 0 ? (
                        <div className="py-1">
                          {brregSuggestions.map((company) => (
                            <button
                              key={company.org_number}
                              type="button"
                              onClick={() => selectBrregCompany(company)}
                              className="w-full px-4 py-3 text-left hover:bg-gray-100 transition-colors border-b border-gray-100 last:border-0"
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <div className="font-medium text-gray-900">
                                    {company.name}
                                  </div>
                                  <div className="text-sm text-gray-600 mt-1">
                                    Org.nr: {company.org_number}
                                  </div>
                                  {company.address && (
                                    <div className="text-sm text-gray-500 mt-1">
                                      📍 {company.address}
                                      {company.postal_code && `, ${company.postal_code}`}
                                      {company.city && ` ${company.city}`}
                                    </div>
                                  )}
                                  {company.nace_description && (
                                    <div className="text-xs text-gray-500 mt-1">
                                      🏢 {company.nace_description}
                                    </div>
                                  )}
                                </div>
                                {company.organizational_form && (
                                  <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                    {company.organizational_form}
                                  </span>
                                )}
                              </div>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-gray-500">
                          Ingen treff i Brønnøysundregistrene
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Org Number */}
                <div>
                  <Label htmlFor="org_number">Organisasjonsnummer (9 siffer) *</Label>
                  <Input
                    id="org_number"
                    value={formData.org_number}
                    onChange={(e) => setFormData({ ...formData, org_number: e.target.value.replace(/\D/g, '') })}
                    placeholder="123456789"
                    pattern="\d{9}"
                    maxLength={9}
                    required
                  />
                </div>
                
                {/* Industry */}
                <div>
                  <Label htmlFor="industry">Bransje</Label>
                  <Input
                    id="industry"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    placeholder="F.eks. Retail, Consulting, etc."
                  />
                </div>
                
                {/* Start Date */}
                <div>
                  <Label htmlFor="start_date">Startdato for regnskap *</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>
                
                {/* Address */}
                <div>
                  <Label htmlFor="address">Adresse</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Gate 1, 0001 Oslo"
                  />
                </div>
                
                {/* Contact Person */}
                <div>
                  <Label htmlFor="contact_person">Kontaktperson</Label>
                  <Input
                    id="contact_person"
                    value={formData.contact_person}
                    onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                    placeholder="Ola Nordmann"
                  />
                </div>
                
                {/* Contact Email */}
                <div>
                  <Label htmlFor="contact_email">E-post</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    placeholder="kontakt@firma.no"
                  />
                </div>
                
                {/* Fiscal Year Start */}
                <div>
                  <Label htmlFor="fiscal_year_start">Regnskapsår start (MM-DD)</Label>
                  <Input
                    id="fiscal_year_start"
                    value={formData.fiscal_year_start}
                    onChange={(e) => setFormData({ ...formData, fiscal_year_start: e.target.value })}
                    placeholder="01-01"
                    pattern="\d{2}-\d{2}"
                  />
                  <p className="text-sm text-gray-500 mt-1">Standard: 01-01 (kalenderår)</p>
                </div>
                
                {/* VAT Registered */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="vat_registered"
                    checked={formData.vat_registered}
                    onCheckedChange={(checked) => 
                      setFormData({ ...formData, vat_registered: checked === true })
                    }
                  />
                  <Label htmlFor="vat_registered" className="cursor-pointer">
                    MVA-registrert
                  </Label>
                </div>
              </div>
              
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  disabled={creating}
                >
                  Avbryt
                </Button>
                <Button type="submit" disabled={creating}>
                  {creating ? 'Oppretter...' : 'Opprett klient'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Clients Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Navn</TableHead>
              <TableHead>Org.nr</TableHead>
              <TableHead>Bransje</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Startdato</TableHead>
              <TableHead className="text-right">Handlinger</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                  <BuildingOfficeIcon className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                  <p>Ingen klienter funnet</p>
                  <p className="text-sm">Opprett din første klient for å komme i gang</p>
                </TableCell>
              </TableRow>
            ) : (
              clients.map((client) => (
                <TableRow key={client.id}>
                  <TableCell className="font-medium">
                    {client.name}
                  </TableCell>
                  <TableCell>{client.org_number}</TableCell>
                  <TableCell>{client.industry || '-'}</TableCell>
                  <TableCell>{getStatusBadge(client.status)}</TableCell>
                  <TableCell>{client.start_date || '-'}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        // Navigate to client detail/settings
                        toast.info('Redigeringsvisning kommer snart');
                      }}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      {/* Summary */}
      <div className="text-sm text-gray-600">
        Totalt: {clients.length} klient{clients.length !== 1 ? 'er' : ''}
      </div>
    </div>
  );
};

export default Klienter;
