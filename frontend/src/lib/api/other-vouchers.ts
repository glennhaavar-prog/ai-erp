/**
 * Other Vouchers API Client
 * Module 3: Andre bilag (non-supplier invoice vouchers)
 * 
 * Backend endpoints: http://localhost:8000/api/other-vouchers
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Types ====================

export type OtherVoucherType = 
  | 'employee_expense' 
  | 'inventory_adjustment' 
  | 'manual_correction' 
  | 'other';

export type VoucherStatus = 'pending' | 'approved' | 'corrected' | 'rejected';

export type VoucherPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface OtherVoucher {
  id: string;
  type: OtherVoucherType;
  client_id: string;
  source_type: string;
  source_id: string;
  title: string;
  description: string;
  priority: VoucherPriority;
  status: VoucherStatus;
  issue_category: string;
  ai_confidence: number; // 0-1 scale
  ai_reasoning?: string;
  ai_suggestion?: {
    account_number?: string;
    account_name?: string;
    vat_code?: string;
    amount?: number;
    vat_amount?: number;
    debit_account?: string;
    credit_account?: string;
  };
  created_at: string;
  assigned_to_user_id?: string | null;
  reviewed_at?: string;
  reviewed_by?: string;
  resolution_notes?: string;
}

export interface PendingVouchersResponse {
  items: OtherVoucher[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApproveRequest {
  notes?: string;
}

export interface RejectRequest {
  reason: string;
  notes?: string;
}

export interface CorrectRequest {
  bookingEntries: Array<{
    account_number: string;
    account_name?: string;
    vat_code?: string;
    amount: number;
    description?: string;
  }>;
  notes?: string;
}

export interface ActionResponse {
  id: string;
  status: VoucherStatus;
  updated_at: string;
  message: string;
}

// ==================== API Functions ====================

/**
 * Fetch pending other vouchers (employee expenses, inventory adjustments, etc.)
 */
export async function fetchPendingOtherVouchers(
  clientId: string,
  type?: OtherVoucherType,
  priority?: VoucherPriority,
  page: number = 1,
  pageSize: number = 50
): Promise<PendingVouchersResponse> {
  const params = new URLSearchParams({
    client_id: clientId,
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (type) params.append('type', type);
  if (priority) params.append('priority', priority);

  const response = await fetch(`${API_BASE}/api/other-vouchers/pending?${params.toString()}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch other vouchers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get single voucher details
 */
export async function getOtherVoucher(voucherId: string): Promise<OtherVoucher> {
  const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch voucher: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Approve a voucher (AI suggestion is correct)
 */
export async function approveOtherVoucher(
  voucherId: string,
  data: ApproveRequest
): Promise<ActionResponse> {
  const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to approve voucher');
  }

  return response.json();
}

/**
 * Reject a voucher (invalid or should not be processed)
 */
export async function rejectOtherVoucher(
  voucherId: string,
  data: RejectRequest
): Promise<ActionResponse> {
  const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to reject voucher');
  }

  return response.json();
}

/**
 * Correct a voucher (AI suggestion needs changes)
 */
export async function correctOtherVoucher(
  voucherId: string,
  data: CorrectRequest
): Promise<ActionResponse> {
  const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}/correct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to correct voucher');
  }

  return response.json();
}

/**
 * Get statistics about other vouchers
 */
export async function getOtherVoucherStats(clientId: string): Promise<{
  pending: number;
  approved: number;
  rejected: number;
  corrected: number;
  by_type: Record<OtherVoucherType, number>;
  by_priority: Record<VoucherPriority, number>;
}> {
  const response = await fetch(
    `${API_BASE}/api/other-vouchers/stats?client_id=${clientId}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  return response.json();
}
