/**
 * Contacts API - Suppliers and Customers (Kontaktregister)
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// === SUPPLIERS ===

export interface SupplierAddress {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country: string;
}

export interface SupplierContact {
  person?: string;
  phone?: string;
  email?: string;
  website?: string;
}

export interface SupplierFinancial {
  bank_account?: string;
  iban?: string;
  swift_bic?: string;
  payment_terms_days: number;
  currency: string;
  vat_code?: string;
  default_expense_account?: string;
}

export interface Supplier {
  id: string;
  client_id: string;
  supplier_number: string;
  company_name: string;
  org_number?: string;
  address: SupplierAddress;
  contact: SupplierContact;
  financial: SupplierFinancial;
  status: 'active' | 'inactive';
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
  balance?: number;
  recent_transactions?: any[];
  open_invoices?: any[];
}

export interface SupplierCreateRequest {
  client_id: string;
  company_name: string;
  org_number?: string;
  address?: Partial<SupplierAddress>;
  contact?: Partial<SupplierContact>;
  financial?: Partial<SupplierFinancial>;
  notes?: string;
}

export interface SupplierUpdateRequest {
  company_name?: string;
  org_number?: string;
  address?: Partial<SupplierAddress>;
  contact?: Partial<SupplierContact>;
  financial?: Partial<SupplierFinancial>;
  notes?: string;
  status?: 'active' | 'inactive';
}

export const suppliersApi = {
  list: async (params: {
    client_id: string;
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => {
    const { data } = await api.get('/api/contacts/suppliers/', { params });
    return data as Supplier[];
  },

  get: async (supplierId: string, params?: {
    include_balance?: boolean;
    include_transactions?: boolean;
    include_invoices?: boolean;
  }) => {
    const { data } = await api.get(`/api/contacts/suppliers/${supplierId}`, { params });
    return data as Supplier;
  },

  create: async (supplier: SupplierCreateRequest) => {
    const { data } = await api.post('/api/contacts/suppliers/', supplier);
    return data as Supplier;
  },

  update: async (supplierId: string, supplier: SupplierUpdateRequest) => {
    const { data } = await api.put(`/api/contacts/suppliers/${supplierId}`, supplier);
    return data as Supplier;
  },

  deactivate: async (supplierId: string) => {
    const { data } = await api.delete(`/api/contacts/suppliers/${supplierId}`);
    return data;
  },

  getAuditLog: async (supplierId: string, params?: { skip?: number; limit?: number }) => {
    const { data } = await api.get(`/api/contacts/suppliers/${supplierId}/audit-log`, { params });
    return data;
  },
};

// === CUSTOMERS ===

export interface CustomerAddress {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country: string;
}

export interface CustomerContact {
  person?: string;
  phone?: string;
  email?: string;
}

export interface CustomerFinancial {
  payment_terms_days: number;
  currency: string;
  vat_code?: string;
  default_revenue_account?: string;
  kid_prefix?: string;
  use_kid: boolean;
  credit_limit?: number;
  reminder_fee: number;
}

export interface Customer {
  id: string;
  client_id: string;
  customer_number: string;
  is_company: boolean;
  name: string;
  org_number?: string;
  birth_number?: string;
  address: CustomerAddress;
  contact: CustomerContact;
  financial: CustomerFinancial;
  status: 'active' | 'inactive';
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
  balance?: number;
  recent_transactions?: any[];
  open_invoices?: any[];
}

export interface CustomerCreateRequest {
  client_id: string;
  is_company: boolean;
  name: string;
  org_number?: string;
  birth_number?: string;
  address?: Partial<CustomerAddress>;
  contact?: Partial<CustomerContact>;
  financial?: Partial<CustomerFinancial>;
  notes?: string;
}

export interface CustomerUpdateRequest {
  is_company?: boolean;
  name?: string;
  org_number?: string;
  birth_number?: string;
  address?: Partial<CustomerAddress>;
  contact?: Partial<CustomerContact>;
  financial?: Partial<CustomerFinancial>;
  notes?: string;
  status?: 'active' | 'inactive';
}

export const customersApi = {
  list: async (params: {
    client_id: string;
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => {
    const { data } = await api.get('/api/contacts/customers/', { params });
    return data as Customer[];
  },

  get: async (customerId: string, params?: {
    include_balance?: boolean;
    include_transactions?: boolean;
    include_invoices?: boolean;
  }) => {
    const { data } = await api.get(`/api/contacts/customers/${customerId}`, { params });
    return data as Customer;
  },

  create: async (customer: CustomerCreateRequest) => {
    const { data } = await api.post('/api/contacts/customers/', customer);
    return data as Customer;
  },

  update: async (customerId: string, customer: CustomerUpdateRequest) => {
    const { data } = await api.put(`/api/contacts/customers/${customerId}`, customer);
    return data as Customer;
  },

  deactivate: async (customerId: string) => {
    const { data } = await api.delete(`/api/contacts/customers/${customerId}`);
    return data;
  },

  getAuditLog: async (customerId: string, params?: { skip?: number; limit?: number }) => {
    const { data } = await api.get(`/api/contacts/customers/${customerId}/audit-log`, { params });
    return data;
  },
};

export default { suppliersApi, customersApi };
