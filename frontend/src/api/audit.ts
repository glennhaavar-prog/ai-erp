import axios from 'axios';
import { AuditEntry, AuditFilters, AuditResponse, AuditTable } from '@/types/audit';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auditApi = {
  // Get audit trail entries with filters
  getEntries: async (filters: AuditFilters): Promise<AuditResponse> => {
    const { data } = await api.get('/api/audit/', { params: filters });
    return data;
  },

  // Get single audit entry details
  getEntry: async (id: string): Promise<AuditEntry> => {
    const { data } = await api.get(`/api/audit/${id}`);
    return data;
  },

  // Get list of tables that have audit entries
  getTables: async (client_id: string): Promise<{ tables: AuditTable[]; total_tables: number }> => {
    const { data } = await api.get('/api/audit/tables/list', { params: { client_id } });
    return data;
  },
};

export default auditApi;
