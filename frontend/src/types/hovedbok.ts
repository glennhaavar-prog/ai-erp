export type EntryStatus = 'posted' | 'reversed';

export interface HovedbokEntry {
  id: string;
  voucher_number: string;
  accounting_date: string;
  account_number: string;
  account_name?: string;
  debit_amount: number;
  credit_amount: number;
  description: string;
  vat_code?: string;
  source_type: string;
  vendor_id?: string;
  vendor_name?: string;
  status: EntryStatus;
  created_at: string;
  reversed_at?: string;
}

export interface HovedbokFilters {
  start_date?: string;
  end_date?: string;
  account_number?: string;
  vendor_id?: string;
  status?: EntryStatus;
  page?: number;
  page_size?: number;
}

export interface HovedbokResponse {
  entries: HovedbokEntry[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Vendor {
  id: string;
  name: string;
  organization_number?: string;
}
