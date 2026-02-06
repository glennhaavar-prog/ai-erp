import axios from 'axios';
import { HovedbokEntry, HovedbokFilters, HovedbokResponse, Vendor } from '@/types/hovedbok';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const hovedbokApi = {
  // Get hovedbok entries with filters
  getEntries: async (filters?: HovedbokFilters): Promise<HovedbokResponse> => {
    const { data } = await api.get('/api/reports/hovedbok/', { params: filters });
    return data;
  },

  // Get single entry details
  getEntry: async (id: string): Promise<HovedbokEntry> => {
    const { data } = await api.get(`/api/reports/hovedbok/${id}`);
    return data;
  },

  // Get vendors for dropdown
  getVendors: async (): Promise<Vendor[]> => {
    const { data } = await api.get('/api/vendors/');
    return data;
  },

  // Export to Excel (future implementation)
  exportToExcel: async (filters?: HovedbokFilters): Promise<Blob> => {
    const { data } = await api.get('/api/reports/hovedbok/export/', {
      params: filters,
      responseType: 'blob',
    });
    return data;
  },
};

export default hovedbokApi;
