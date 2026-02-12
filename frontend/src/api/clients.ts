/**
 * Clients API - Manage client companies
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface StatusSummary {
  vouchers_pending: number;
  bank_items_open: number;
  reconciliation_status: string;
  vat_status: string;
}

export interface Client {
  id: string;
  name: string;
  org_number: string;
  industry?: string;
  start_date?: string;
  address?: string;
  contact_person?: string;
  contact_email?: string;
  fiscal_year_start: string;
  vat_registered: boolean;
  status: string;
  status_summary?: StatusSummary;
}

export interface ClientCreateRequest {
  name: string;
  org_number: string;
  industry?: string;
  start_date: string;
  address?: string;
  contact_person?: string;
  contact_email?: string;
  fiscal_year_start?: string;
  vat_registered?: boolean;
}

export interface ClientUpdateRequest {
  name?: string;
  industry?: string;
  address?: string;
  contact_person?: string;
  contact_email?: string;
  fiscal_year_start?: string;
  vat_registered?: boolean;
  status?: 'active' | 'inactive' | 'suspended';
}

export interface ClientListResponse {
  items: Client[];
  total: number;
  limit: number;
  offset: number;
  page_number: number;
}

export interface BrregCompany {
  name: string;
  org_number: string;
  address?: string;
  postal_code?: string;
  city?: string;
  municipality?: string;
  nace_code?: string;
  nace_description?: string;
  organizational_form?: string;
  organizational_form_desc?: string;
}

export const clientsApi = {
  /**
   * Search Norwegian company registry (Brønnøysundregistrene) for autocomplete
   */
  searchBrreg: async (query: string): Promise<BrregCompany[]> => {
    if (!query || query.length < 2) return [];
    
    try {
      const { data } = await api.get('/api/clients/search-brreg', {
        params: { q: query, limit: 10 },
      });
      return data as BrregCompany[];
    } catch (error) {
      console.error('Brreg search error:', error);
      return [];
    }
  },

  /**
   * Get company details from Brønnøysundregistrene by org number
   */
  getBrregCompany: async (orgNumber: string): Promise<BrregCompany | null> => {
    try {
      const { data } = await api.get(`/api/clients/brreg/${orgNumber}`);
      return data as BrregCompany;
    } catch (error) {
      console.error('Brreg fetch error:', error);
      return null;
    }
  },

  /**
   * List all clients with pagination and filtering
   */
  list: async (params?: {
    tenant_id?: string;
    status?: 'active' | 'inactive' | 'all';
    limit?: number;
    offset?: number;
  }) => {
    const { data } = await api.get('/api/clients/', { params });
    return data as ClientListResponse;
  },

  /**
   * Get a single client by ID
   */
  get: async (clientId: string) => {
    const { data } = await api.get(`/api/clients/${clientId}`);
    return data as Client;
  },

  /**
   * Create a new client
   */
  create: async (tenantId: string, client: ClientCreateRequest) => {
    const { data } = await api.post('/api/clients/', client, {
      params: { tenant_id: tenantId },
    });
    return data as Client;
  },

  /**
   * Update an existing client
   */
  update: async (clientId: string, client: ClientUpdateRequest) => {
    const { data } = await api.put(`/api/clients/${clientId}`, client);
    return data as Client;
  },

  /**
   * Soft delete a client (set inactive)
   */
  deactivate: async (clientId: string) => {
    const { data } = await api.delete(`/api/clients/${clientId}`);
    return data as { message: string; client_id: string };
  },
};

export default clientsApi;
