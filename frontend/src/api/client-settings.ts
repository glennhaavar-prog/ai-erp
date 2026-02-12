/**
 * Client Settings API - FIRMAINNSTILLINGER
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AddressInfo {
  street?: string;
  postal_code?: string;
  city?: string;
}

export interface CompanyInfo {
  company_name: string;
  org_number: string;
  address: AddressInfo;
  phone?: string;
  email?: string;
  ceo_name?: string;
  chairman_name?: string;
  industry?: string;
  nace_code?: string;
  accounting_year_start_month: number;
  incorporation_date?: string;
  legal_form?: string;
}

export interface AccountingSettings {
  chart_of_accounts: string;
  vat_registered: boolean;
  vat_period: string;
  currency: string;
  rounding_rules: {
    decimals: number;
    method: string;
  };
  supported_currencies?: string[];
  auto_update_rates?: boolean;
  last_rate_update?: string | null;
}

export interface BankAccount {
  account_number: string;
  bank_name: string;
  iban?: string;
  swift?: string;
  is_primary: boolean;
}

export interface PayrollEmployees {
  has_employees: boolean;
  payroll_frequency?: string;
  employer_tax_zone?: string;
}

export interface ServicesProvided {
  bookkeeping: boolean;
  payroll: boolean;
  annual_accounts: boolean;
  vat_reporting: boolean;
  other: string[];
}

export interface Services {
  services_provided: ServicesProvided;
  task_templates: string[];
}

export interface ResponsibleAccountant {
  name?: string;
  email?: string;
  phone?: string;
}

export interface ClientSettings {
  id: string;
  client_id: string;
  company_info: CompanyInfo;
  accounting_settings: AccountingSettings;
  bank_accounts: BankAccount[];
  payroll_employees: PayrollEmployees;
  services: Services;
  responsible_accountant: ResponsibleAccountant;
  created_at: string;
  updated_at: string;
}

export interface ClientSettingsUpdateRequest {
  company_info?: Partial<CompanyInfo>;
  accounting_settings?: Partial<AccountingSettings>;
  bank_accounts?: BankAccount[];
  payroll_employees?: Partial<PayrollEmployees>;
  services?: Partial<Services>;
  responsible_accountant?: Partial<ResponsibleAccountant>;
}

export const clientSettingsApi = {
  get: async (clientId: string) => {
    const { data } = await api.get(`/api/clients/${clientId}/settings`);
    return data as ClientSettings;
  },

  update: async (clientId: string, settings: ClientSettingsUpdateRequest) => {
    const { data } = await api.put(`/api/clients/${clientId}/settings`, settings);
    return data as ClientSettings;
  },
};

export default clientSettingsApi;
