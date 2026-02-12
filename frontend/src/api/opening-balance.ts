/**
 * Opening Balance API - ÅPNINGSBALANSE
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface OpeningBalanceLine {
  line_number: number;
  account_number: string;
  account_name?: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
  is_bank_account?: boolean;
}

export interface ValidationError {
  severity: 'error' | 'warning';
  code: string;
  message: string;
  line_number?: number;
  account_number?: string;
  amount?: number;
}

export interface BankBalanceVerification {
  account_number: string;
  account_name: string;
  balance_in_import: number;
  actual_bank_balance?: number;
  verified: boolean;
  error?: string;
}

export interface OpeningBalance {
  id: string;
  client_id: string;
  accounting_date: string;
  status: 'draft' | 'validated' | 'imported' | 'failed';
  total_debit: number;
  total_credit: number;
  line_count: number;
  validation_errors: ValidationError[];
  bank_verifications: BankBalanceVerification[];
  imported_by?: string;
  imported_at?: string;
  created_at: string;
  updated_at: string;
}

export interface OpeningBalanceImportRequest {
  client_id: string;
  accounting_date: string;
  lines: OpeningBalanceLine[];
  manual_bank_balances?: { account_number: string; actual_balance: number }[];
}

export interface OpeningBalanceValidateRequest {
  opening_balance_id: string;
  manual_bank_balances?: { account_number: string; actual_balance: number }[];
}

export interface OpeningBalanceImportToLedgerRequest {
  opening_balance_id: string;
  description?: string;
}

export const openingBalanceApi = {
  // List all opening balances for a client
  list: async (clientId: string, params?: { status?: string; skip?: number; limit?: number }) => {
    const { data } = await api.get('/api/opening-balance/', {
      params: { client_id: clientId, ...params },
    });
    return data as OpeningBalance[];
  },

  // Get a specific opening balance with details
  get: async (openingBalanceId: string) => {
    const { data } = await api.get(`/api/opening-balance/${openingBalanceId}`);
    return data as OpeningBalance & { lines: OpeningBalanceLine[] };
  },

  // Import from CSV/manual entry
  import: async (request: OpeningBalanceImportRequest) => {
    const { data } = await api.post('/api/opening-balance/import', request);
    return data as OpeningBalance;
  },

  // Upload CSV file
  uploadCSV: async (clientId: string, file: File, accountingDate: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('client_id', clientId);
    formData.append('accounting_date', accountingDate);

    const { data } = await api.post('/api/opening-balance/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data as OpeningBalance;
  },

  // Validate opening balance
  validate: async (request: OpeningBalanceValidateRequest) => {
    const { data } = await api.post('/api/opening-balance/validate', request);
    return data as {
      valid: boolean;
      errors: ValidationError[];
      warnings: ValidationError[];
      bank_verifications: BankBalanceVerification[];
    };
  },

  // Import to general ledger (finalize)
  importToLedger: async (request: OpeningBalanceImportToLedgerRequest) => {
    const { data } = await api.post('/api/opening-balance/import-to-ledger', request);
    return data as { success: boolean; journal_entry_id: string; message: string };
  },

  // Delete draft
  delete: async (openingBalanceId: string) => {
    const { data } = await api.delete(`/api/opening-balance/${openingBalanceId}`);
    return data;
  },
};

export default openingBalanceApi;
